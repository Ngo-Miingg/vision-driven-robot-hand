from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import socket
import socketserver
import struct
import threading
import time
import traceback
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

try:
    import websocket
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: websocket-client. Run from project venv or install pc_client/requirements.txt"
    ) from exc

from offline_voice_engine import OfflineVoiceEngine


DEFAULT_ESP_URL = "ws://192.168.4.1:81"
DEFAULT_HTTP_HOST = "127.0.0.1"
DEFAULT_HTTP_PORT = 8080
DEFAULT_PROXY_HOST = "127.0.0.1"
DEFAULT_PROXY_PORT = 8765
WS_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def format_traceback(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip()


def log_exception(scope: str, phase: str, exc: BaseException, extra: str = "") -> None:
    suffix = f" | {extra}" if extra else ""
    print(f"[{scope}] {phase} failed: {type(exc).__name__}: {exc}{suffix}")
    print(format_traceback(exc))


def preview_bytes(data: bytes, limit: int = 16) -> str:
    head = data[:limit].hex(" ")
    if len(data) > limit:
        return f"{head} ... ({len(data)} bytes)"
    return f"{head} ({len(data)} bytes)"


def read_until(sock: socket.socket, marker: bytes, limit: int = 8192) -> bytes:
    data = bytearray()
    while marker not in data:
        chunk = sock.recv(1)
        if not chunk:
            break
        data += chunk
        if len(data) > limit:
            raise ConnectionError("WebSocket header too large")
    return bytes(data)


def read_exact(sock: socket.socket, length: int) -> bytes:
    data = bytearray()
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return bytes(data)


def recv_browser_frame(sock: socket.socket) -> tuple[int, bytes]:
    head = read_exact(sock, 2)
    opcode = head[0] & 0x0F
    masked = bool(head[1] & 0x80)
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", read_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", read_exact(sock, 8))[0]
    mask = read_exact(sock, 4) if masked else b"\x00\x00\x00\x00"
    payload = bytearray(read_exact(sock, length))
    if masked:
        for index in range(length):
            payload[index] ^= mask[index % 4]
    return opcode, bytes(payload)


def send_browser_frame(sock: socket.socket, opcode: int, payload: bytes = b"") -> None:
    first = 0x80 | (opcode & 0x0F)
    length = len(payload)
    if length < 126:
        header = bytes([first, length])
    elif length <= 0xFFFF:
        header = bytes([first, 126]) + struct.pack("!H", length)
    else:
        header = bytes([first, 127]) + struct.pack("!Q", length)
    sock.sendall(header + payload)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def checksum_xor(data: list[int]) -> int:
    value = 0
    for item in data:
        value ^= int(item) & 0xFF
    return value


def make_packet(mode: int, payload: list[int] | None = None) -> bytes:
    frame = [0] * 9
    frame[0] = 0xAA
    frame[1] = int(mode) & 0xFF
    for index, value in enumerate((payload or [])[:6]):
        frame[2 + index] = int(value) & 0xFF
    frame[8] = checksum_xor(frame[:8])
    return bytes(frame)


class Esp32Bridge:
    def __init__(self, esp_url: str, simulate: bool = False) -> None:
        self.esp_url = esp_url
        self.ws: websocket.WebSocket | None = None
        self.lock = threading.Lock()
        self.sent_count = 0
        self.last_error = ""
        self.last_connect_attempt_at = 0.0
        self.connect_cooldown_s = 1.5
        self.simulate = simulate
        self.simulated_connected = simulate
        self.last_packet_hex = ""

    def close(self) -> None:
        with self.lock:
            self._close_unlocked()

    def _close_unlocked(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

    def _connect_unlocked(self) -> websocket.WebSocket:
        if self.simulate:
            self.simulated_connected = True
            self.last_error = ""
            return self.ws  # type: ignore[return-value]
        if self.ws is not None:
            return self.ws
        now = time.monotonic()
        if self.last_error and (now - self.last_connect_attempt_at) < self.connect_cooldown_s:
            raise RuntimeError(
                f"ESP32 reconnect cooldown active ({self.connect_cooldown_s:.1f}s). Last error: {self.last_error}"
            )
        self.last_connect_attempt_at = now
        print(f"[API] Connecting ESP32 {self.esp_url}")
        try:
            self.ws = websocket.create_connection(self.esp_url, timeout=5)
            self.ws.settimeout(1)
            self.last_error = ""
            print("[API] ESP32 connected")
            return self.ws
        except Exception as exc:
            self.last_error = f"{type(exc).__name__}: {exc}"
            log_exception("API", "ESP32 connect", exc, extra=f"url={self.esp_url}")
            self._close_unlocked()
            raise

    def send_packet(self, packet: bytes) -> None:
        with self.lock:
            if self.simulate:
                self.simulated_connected = True
                self.last_error = ""
                self.sent_count += 1
                self.last_packet_hex = packet.hex(" ")
                print(f"[SIM] Packet {preview_bytes(packet)}")
                return
            last_exc: Exception | None = None
            for attempt in range(2):
                try:
                    ws = self._connect_unlocked()
                    ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)
                    self.sent_count += 1
                    if attempt > 0:
                        print("[API] Send recovered after reconnect")
                    return
                except Exception as exc:
                    last_exc = exc
                    self.last_error = f"{type(exc).__name__}: {exc}"
                    log_exception(
                        "API",
                        f"Send attempt {attempt + 1}",
                        exc,
                        extra=f"url={self.esp_url} packet={preview_bytes(packet)} sent_count={self.sent_count}",
                    )
                    self._close_unlocked()
                    time.sleep(0.08)
            if last_exc is not None:
                raise last_exc

    def connect(self) -> None:
        with self.lock:
            if self.simulate:
                self.simulated_connected = True
                self.last_error = ""
                print("[SIM] Bridge connected")
                return
            try:
                self._connect_unlocked()
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                self._close_unlocked()
                raise

    def set_simulation(self, enabled: bool) -> None:
        with self.lock:
            if enabled:
                self._close_unlocked()
                self.simulate = True
                self.simulated_connected = True
                self.last_error = ""
                print("[SIM] Software-only mode enabled")
            else:
                self.simulate = False
                self.simulated_connected = False
                self.last_error = ""
                print("[SIM] Software-only mode disabled")

    def status(self) -> dict[str, Any]:
        with self.lock:
            return {
                "esp_url": self.esp_url,
                "connected": self.simulated_connected if self.simulate else self.ws is not None,
                "sent_count": self.sent_count,
                "last_error": self.last_error,
                "simulate": self.simulate,
                "last_packet_hex": self.last_packet_hex,
            }


class MasterHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    bridge: Esp32Bridge
    voice_engine: OfflineVoiceEngine

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print(f"[HTTP] {self.address_string()} {format % args}")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/status":
            query = urllib.parse.parse_qs(parsed.query)
            connect_values = query.get("connect")
            if connect_values is None:
                connect_flag = False
            else:
                connect_raw = connect_values[0]
                connect_flag = str(connect_raw).strip().rstrip(". ") in {"1", "true", "yes", "on"}
            if connect_flag:
                try:
                    self.bridge.connect()
                except Exception as exc:
                    self.send_json(502, {"ok": False, "error": str(exc), **self.bridge.status()})
                    return
            self.send_json(200, {"ok": True, **self.bridge.status()})
            return
        if parsed.path == "/api/packet-test":
            samples = {
                "arm": list(make_packet(0x10)),
                "open": list(make_packet(0x01, [170, 180, 0, 0, 0, 180])),
                "mid": list(make_packet(0x01, [105, 90, 90, 90, 90, 90])),
                "close": list(make_packet(0x01, [40, 0, 180, 180, 180, 0])),
            }
            self.send_json(200, {"ok": True, "samples": samples})
            return
        if parsed.path == "/api/offline-voice/status":
            self.send_json(200, {"ok": True, **self.voice_engine.status()})
            return
        if parsed.path == "/api/offline-voice/devices":
            self.send_json(200, {"ok": True, "devices": self.voice_engine.list_input_devices()})
            return
        if parsed.path == "/api/offline-voice/models":
            self.send_json(200, {"ok": True, "models": self.voice_engine.list_model_presets()})
            return
        if parsed.path == "/api/sim-mode":
            self.send_json(200, {"ok": True, **self.bridge.status()})
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.startswith("/api/offline-voice/"):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length > 0 else b"{}"
                request = json.loads(body.decode("utf-8") or "{}")
                if self.path == "/api/offline-voice/start":
                    status = self.voice_engine.start(request)
                    self.send_json(200, {"ok": not bool(status.get("last_error")), **status})
                    return
                if self.path == "/api/offline-voice/stop":
                    status = self.voice_engine.stop()
                    self.send_json(200, {"ok": True, **status})
                    return
                if self.path == "/api/offline-voice/calibrate":
                    duration_s = float(request.get("duration_s", 2.2))
                    status = self.voice_engine.calibrate(duration_s)
                    self.send_json(200, {"ok": True, **status})
                    return
                if self.path == "/api/offline-voice/text":
                    text = str(request.get("text", "")).strip()
                    status = self.voice_engine.process_manual_text(text)
                    self.send_json(200, {"ok": not bool(status.get("last_error")), **status})
                    return
                self.send_json(404, {"ok": False, "error": "voice route not found"})
                return
            except Exception as exc:
                log_exception("VOICE", f"HTTP {self.path}", exc)
                self.send_json(502, {"ok": False, "error": str(exc), **self.voice_engine.status()})
                return
        if self.path == "/api/sim-mode":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length > 0 else b"{}"
                request = json.loads(body.decode("utf-8") or "{}")
                enabled = bool(request.get("enabled"))
                self.bridge.set_simulation(enabled)
                self.send_json(200, {"ok": True, **self.bridge.status()})
                return
            except Exception as exc:
                log_exception("SIM", "HTTP /api/sim-mode", exc)
                self.send_json(502, {"ok": False, "error": str(exc), **self.bridge.status()})
                return
        if self.path != "/api/send":
            self.send_json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            request = json.loads(body.decode("utf-8"))
            mode = int(request["mode"])
            payload = [int(value) for value in request.get("payload", [])[:6]]
            print(f"[API] POST /api/send mode=0x{mode:02X} payload={payload}")
            packet = make_packet(mode, payload)
            self.bridge.send_packet(packet)
            self.send_json(200, {"ok": True, "sent_count": self.bridge.sent_count})
        except Exception as exc:
            log_exception("API", "HTTP /api/send", exc)
            self.send_json(502, {"ok": False, "error": str(exc), **self.bridge.status()})


class ProxyConfig:
    def __init__(self, esp_url: str, bridge: Esp32Bridge) -> None:
        self.esp_url = esp_url
        self.bridge = bridge


class BrowserWsProxyHandler(socketserver.BaseRequestHandler):
    config: ProxyConfig

    def handle(self) -> None:
        browser = self.request
        browser.settimeout(20)
        browser_label = f"{self.client_address[0]}:{self.client_address[1]}"
        try:
            self.handshake(browser, browser_label)
            print(f"[WS] Browser connected from {browser_label}")
            self.config.bridge.connect()
            print(f"[WS] Bridged to ESP32 via shared bridge {self.config.esp_url}")

            while True:
                opcode, payload = recv_browser_frame(browser)
                print(f"[WS] Frame from {browser_label}: opcode=0x{opcode:X} payload={preview_bytes(payload)}")
                if opcode == 0x8:
                    print(f"[WS] Browser requested close: {browser_label}")
                    break
                if opcode == 0x9:
                    send_browser_frame(browser, 0xA, payload)
                    continue
                if opcode == 0x1:
                    text = payload.decode("utf-8", errors="ignore").strip()
                    print(f"[WS] Ignored text frame: {text}")
                elif opcode == 0x2:
                    self.config.bridge.send_packet(payload)
        except Exception as exc:
            log_exception("WS", "Browser proxy session", exc, extra=f"client={browser_label} esp_url={self.config.esp_url}")
        finally:
            try:
                send_browser_frame(browser, 0x8)
            except Exception:
                pass

    @staticmethod
    def handshake(sock: socket.socket, browser_label: str) -> None:
        header = read_until(sock, b"\r\n\r\n").decode("iso-8859-1", errors="replace")
        request_line = header.split("\r\n", 1)[0] if header else ""
        print(f"[WS] Handshake request from {browser_label}: {request_line}")
        key = ""
        for line in header.split("\r\n"):
            if line.lower().startswith("sec-websocket-key:"):
                key = line.split(":", 1)[1].strip()
                break
        if not key:
            raise ConnectionError("Missing Sec-WebSocket-Key")
        accept = base64.b64encode(hashlib.sha1((key + WS_GUID).encode("ascii")).digest()).decode("ascii")
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n"
            "\r\n"
        )
        sock.sendall(response.encode("ascii"))
        print(f"[WS] Handshake accepted for {browser_label}")


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def bind_http_server(
    host: str,
    preferred_port: int,
    directory: Path,
    bridge: Esp32Bridge,
    voice_engine: OfflineVoiceEngine,
) -> tuple[ThreadingHTTPServer, int]:
    handler_class = type(
        "ConfiguredMasterHTTPRequestHandler",
        (MasterHTTPRequestHandler,),
        {"bridge": bridge, "voice_engine": voice_engine},
    )
    handler = lambda *args, **kwargs: handler_class(*args, directory=str(directory), **kwargs)
    for port in range(preferred_port, preferred_port + 20):
        try:
            return ThreadingHTTPServer((host, port), handler), port
        except OSError:
            continue
    raise OSError(f"No free HTTP port from {preferred_port} to {preferred_port + 19}")


def bind_proxy_server(host: str, port: int, esp_url: str, bridge: Esp32Bridge) -> ThreadingTCPServer:
    handler_class = type(
        "ConfiguredBrowserWsProxyHandler",
        (BrowserWsProxyHandler,),
        {"config": ProxyConfig(esp_url, bridge)},
    )
    return ThreadingTCPServer((host, port), handler_class)


def main() -> None:
    parser = argparse.ArgumentParser(description="Robot Hand Master Control HTTP server and local WebSocket proxy.")
    parser.add_argument("--esp-url", default=DEFAULT_ESP_URL)
    parser.add_argument("--http-host", default=DEFAULT_HTTP_HOST)
    parser.add_argument("--http-port", type=int, default=DEFAULT_HTTP_PORT)
    parser.add_argument("--proxy-host", default=DEFAULT_PROXY_HOST)
    parser.add_argument("--proxy-port", type=int, default=DEFAULT_PROXY_PORT)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    os.chdir(root)

    bridge = Esp32Bridge(args.esp_url, simulate=args.simulate)
    voice_engine = OfflineVoiceEngine(bridge.send_packet, make_packet)
    httpd, http_port = bind_http_server(args.http_host, args.http_port, root, bridge, voice_engine)
    proxy: ThreadingTCPServer | None = None
    try:
        proxy = bind_proxy_server(args.proxy_host, args.proxy_port, args.esp_url, bridge)
    except OSError as exc:
        print(f"[WS] Fallback local WS disabled: {exc}")

    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    http_thread.start()
    if proxy is not None:
        proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        proxy_thread.start()

    url = f"http://{args.http_host}:{http_port}/master_control.html"
    print("Robot Hand Master Control")
    print(f"HTTP UI     : {url}")
    print(f"HTTP API    : http://{args.http_host}:{http_port}/api/send")
    print(f"Voice API   : http://{args.http_host}:{http_port}/api/offline-voice/status")
    print(f"Sim mode    : {'ON' if args.simulate else 'OFF'}")
    if proxy is not None:
        print(f"Local WS    : ws://{args.proxy_host}:{args.proxy_port}")
    else:
        print("Local WS    : disabled")
    print(f"ESP32 target: {args.esp_url}")
    print("Press Ctrl+C to stop.")

    if not args.no_browser:
        webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        voice_engine.stop()
        bridge.close()
        if proxy is not None:
            proxy.shutdown()
        httpd.shutdown()
        if proxy is not None:
            proxy.server_close()
        httpd.server_close()


if __name__ == "__main__":
    main()
