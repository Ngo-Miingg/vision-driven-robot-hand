from __future__ import annotations

import audioop
import json
import queue
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency
    sd = None

try:
    from vosk import KaldiRecognizer, Model
except ImportError:  # pragma: no cover - optional dependency
    KaldiRecognizer = None
    Model = None


VOICE_SAMPLE_RATE = 16_000
VOICE_BLOCK_SIZE = 8_000
MODELS_DIR = Path(__file__).resolve().parent.parent / "firmware" / "models"
DEFAULT_VOSK_MODEL = MODELS_DIR / "vosk-model-small-vn-0.4"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
LOG_LIMIT = 80
WAKE_WORDS = ("robot", "ro bot", "ban tay", "tay may", "may")
MODEL_PRESETS = [
    {
        "id": "vi-small",
        "label": "Vietnamese small (recommended)",
        "path": str(MODELS_DIR / "vosk-model-small-vn-0.4"),
        "download_url": "https://alphacephei.com/vosk/models/vosk-model-small-vn-0.4.zip",
    },
    {
        "id": "en-small",
        "label": "English small",
        "path": str(MODELS_DIR / "vosk-model-small-en-us-0.15"),
        "download_url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    },
]

OPEN_ANGLE = [170, 180, 0, 0, 0, 180]
CLOSED_ANGLE = [40, 0, 180, 180, 180, 0]

GESTURE_PRESETS = {
    "open": {"angles": OPEN_ANGLE, "label": "OPEN PALM"},
    "fist": {"angles": CLOSED_ANGLE, "label": "FIST"},
    "like": {"angles": [170, 0, 180, 180, 0, 0], "label": "LIKE"},
    "point": {"angles": [40, 180, 180, 180, 180, 0], "label": "POINT"},
    "peace": {"angles": [40, 180, 0, 180, 180, 0], "label": "PEACE"},
    "gun": {"angles": [170, 180, 180, 180, 0, 0], "label": "FINGER GUN"},
    "ok": {"angles": [80, 45, 0, 0, 100, 180], "label": "OK SIGN"},
    "claw": {"angles": [90, 100, 95, 95, 100, 95], "label": "CLAW"},
    "relax": {"angles": [150, 145, 36, 36, 35, 145], "label": "RELAX"},
    "three": {"angles": [40, 180, 0, 0, 180, 0], "label": "THREE"},
    "pinch": {"angles": [80, 70, 0, 0, 150, 180], "label": "PINCH"},
    "power": {"angles": [40, 0, 180, 180, 180, 0], "label": "POWER GRIP"},
}

GESTURE_ALIASES = {
    "like": ["like", "thumbs up", "ra dau like", "lam like", "bieu tuong like"],
    "point": ["point", "chi", "chi tay", "chi tro", "pointing"],
    "peace": ["peace", "victory", "v sign", "chu v", "hoa binh", "hai ngon"],
    "gun": ["gun", "finger gun", "ban sung", "pistol"],
    "ok": ["ok", "okay", "dong y", "ra dau ok", "bieu tuong ok"],
    "claw": ["claw", "vuot", "mong vuot", "ban tay cong", "gap nua"],
    "relax": ["relax", "tha long", "nghi", "thu gian"],
    "three": ["three", "so ba", "ba ngon"],
    "pinch": ["pinch", "kep nhe", "chim tay"],
    "power": ["power grip", "kep manh", "nam chat", "grip manh"],
    "open": ["open palm", "long ban tay", "xoe tay", "mo tay", "open"],
    "fist": ["fist", "nam dam", "qua dam", "close", "nam tay"],
}

ROUTINE_ALIASES = {
    "wave": ["wave", "hello", "chao", "xin chao", "say hi"],
    "demo": ["demo", "trinh dien", "showtime", "biet dien"],
    "count": ["count", "dem so", "show number", "ra so"],
}

FINGER_ALIASES = {
    0: ["ngon cai", "thumb"],
    1: ["tro", "index"],
    2: ["giua", "middle"],
    3: ["ap ut", "ring"],
    4: ["thumb oppose", "doi", "oppos"],
    5: ["ngon ut", "ngon út", "pinky"],
}
PINKY_ALIASES = ("ngon ut", "ngon út", "ut", "pinky")


def normalize_text(input_text: str) -> str:
    text = (
        unicodedata.normalize("NFD", input_text.lower())
        .replace("đ", "d")
        .replace(",", " ")
        .replace(".", " ")
        .replace("?", " ")
        .replace("!", " ")
    )
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return " ".join(text.split())


def parse_number(text: str) -> int | None:
    parts = text.split()
    for part in parts:
        if part.isdigit():
            return max(0, min(100, int(part)))
    words = {
        "khong": 0,
        "mot": 1,
        "hai": 2,
        "ba": 3,
        "bon": 4,
        "nam": 5,
        "sau": 6,
        "bay": 7,
        "tam": 8,
        "chin": 9,
        "muoi": 10,
        "hai muoi lam": 25,
        "nam muoi": 50,
        "bay muoi lam": 75,
        "mot tram": 100,
    }
    for key, value in words.items():
        if key in text:
            return value
    return None


@dataclass
class VoiceConfig:
    wake_word: bool = True
    confirm_estop: bool = True
    noise_gate: float = 0.035
    model_path: str = str(DEFAULT_VOSK_MODEL)
    input_device: int | None = None
    use_llm: bool = True
    ollama_model: str = "qwen2.5:3b"
    ollama_url: str = DEFAULT_OLLAMA_URL


@dataclass
class VoiceStatus:
    running: bool = False
    listening: bool = False
    ready: bool = False
    noise_floor: float = 0.015
    noise_gate: float = 0.035
    last_heard: str = ""
    last_command: str = ""
    last_error: str = ""
    use_llm: bool = False
    llm_available: bool = False
    ollama_error: str = ""
    stt_available: bool = False
    model_exists: bool = False
    model_path: str = ""
    ollama_model: str = ""
    ollama_url: str = ""
    input_device: int | None = None
    input_device_name: str = ""
    logs: deque[str] = field(default_factory=lambda: deque(maxlen=LOG_LIMIT))


class LocalIntentPlanner:
    def __init__(self, status: VoiceStatus, log_func: Callable[[str], None]) -> None:
        self.status = status
        self.log = log_func

    @staticmethod
    def _has_any(text: str, phrases: list[str] | tuple[str, ...]) -> bool:
        return any(phrase in text for phrase in phrases)

    def _rule_based_intent(self, normalized_text: str) -> dict[str, Any] | None:
        text = normalized_text
        for wake_word in WAKE_WORDS:
            if wake_word in text:
                text = text.replace(wake_word, "").strip()

        if "xac nhan dung" in text or "confirm stop" in text:
            return {"kind": "control", "name": "ESTOP", "label": "ESTOP confirmed"}
        if "dung khan" in text or "estop" in text or "emergency" in text:
            return {"kind": "control", "name": "ESTOP", "label": "ESTOP"}
        if "disarm" in text or "tat servo" in text or "khoa" in text:
            return {"kind": "control", "name": "DISARM", "label": "DISARM"}
        if "arm" in text or "kich hoat" in text or "bat servo" in text:
            return {"kind": "control", "name": "ARM", "label": "ARM"}
        if "hold" in text or "giu" in text:
            return {"kind": "hold", "label": "HOLD"}
        if "grip" in text or "kep" in text:
            value = parse_number(text)
            if value is not None:
                return {"kind": "grip", "value": value, "label": f"GRIP {value}"}

        for gesture_name, aliases in GESTURE_ALIASES.items():
            if self._has_any(text, aliases):
                preset = GESTURE_PRESETS[gesture_name]
                return {"kind": "angles", "angles": preset["angles"], "label": preset["label"]}

        for routine_name, aliases in ROUTINE_ALIASES.items():
            if self._has_any(text, aliases):
                return {"kind": "routine", "name": routine_name, "text": text}

        for finger_index, aliases in FINGER_ALIASES.items():
            if self._has_any(text, aliases):
                if "mo" in text or "open" in text:
                    angles = OPEN_ANGLE.copy()
                    return {"kind": "set_one", "index": finger_index, "value": angles[finger_index], "label": f"FINGER {finger_index} OPEN"}
                if "dong" in text or "gap" in text or "close" in text:
                    angles = CLOSED_ANGLE.copy()
                    return {"kind": "set_one", "index": finger_index, "value": angles[finger_index], "label": f"FINGER {finger_index} CLOSE"}
                value = parse_number(text)
                if value is not None:
                    return {"kind": "set_percent", "index": finger_index, "value": value, "label": f"FINGER {finger_index} {value}%"}

        return None

    def _call_local_llm(self, normalized_text: str, config: VoiceConfig) -> dict[str, Any] | None:
        if not config.use_llm or not config.ollama_model:
            return None
        payload = {
            "model": config.ollama_model,
            "stream": False,
            "format": "json",
            "prompt": (
                "You map robot-hand voice commands to JSON.\n"
                "Return only JSON. Valid kinds: control, grip, gesture, routine, hold.\n"
                "control: {\"kind\":\"control\",\"name\":\"ARM|DISARM|ESTOP|OPEN|CLOSE\"}\n"
                "grip: {\"kind\":\"grip\",\"value\":0..100}\n"
                "gesture: {\"kind\":\"gesture\",\"name\":\"open|fist|like|point|peace|gun|ok|claw|relax|three|pinch|power\"}\n"
                "routine: {\"kind\":\"routine\",\"name\":\"wave|demo|count\",\"value\": optional number}\n"
                "hold: {\"kind\":\"hold\"}\n"
                f"Input: {normalized_text}"
            ),
        }
        request = urllib.request.Request(
            config.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=6) as response:
                raw = json.loads(response.read().decode("utf-8"))
                llm_json = json.loads(raw.get("response", "{}"))
                self.status.llm_available = True
                return llm_json
        except Exception as exc:
            self.status.llm_available = False
            self.log(f"LLM fallback unavailable: {type(exc).__name__}: {exc}")
            return None

    def parse(self, raw_text: str, config: VoiceConfig) -> dict[str, Any] | None:
        normalized_text = normalize_text(raw_text)
        if not normalized_text:
            return None
        result = self._rule_based_intent(normalized_text)
        if result is not None:
            return result
        llm_result = self._call_local_llm(normalized_text, config)
        if llm_result is None:
            return None
        kind = str(llm_result.get("kind", "")).strip().lower()
        if kind == "gesture":
            name = str(llm_result.get("name", "")).strip().lower()
            preset = GESTURE_PRESETS.get(name)
            if preset:
                return {"kind": "angles", "angles": preset["angles"], "label": preset["label"]}
        if kind == "routine":
            return {"kind": "routine", "name": str(llm_result.get("name", "")).strip().lower(), "value": llm_result.get("value")}
        if kind == "control":
            return {"kind": "control", "name": str(llm_result.get("name", "")).strip().upper(), "label": str(llm_result.get("name", "")).strip().upper()}
        if kind == "grip":
            value = int(llm_result.get("value", 0))
            return {"kind": "grip", "value": max(0, min(100, value)), "label": f"GRIP {value}"}
        if kind == "hold":
            return {"kind": "hold", "label": "HOLD"}
        return None


class OfflineVoiceEngine:
    def __init__(self, send_packet: Callable[[bytes], None], make_packet: Callable[[int, list[int] | None], bytes]) -> None:
        self._send_packet = send_packet
        self._make_packet = make_packet
        self._status = VoiceStatus()
        self._config = VoiceConfig()
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._queue: queue.Queue[bytes] = queue.Queue(maxsize=16)
        self._stream: Any = None
        self._awaiting_estop_confirm = False
        self._planner = LocalIntentPlanner(self._status, self._push_log)
        self._calibration_until = 0.0
        self._calibration_samples: list[float] = []
        self._last_ollama_probe_at = 0.0

    def _push_log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self._status.logs.appendleft(f"[{timestamp}] {message}")

    def _status_dict(self) -> dict[str, Any]:
        self._refresh_status_flags()
        self._probe_ollama(force=False)
        return {
            "running": self._status.running,
            "listening": self._status.listening,
            "ready": self._status.ready,
            "noise_floor": round(self._status.noise_floor, 5),
            "noise_gate": round(self._status.noise_gate, 5),
            "last_heard": self._status.last_heard,
            "last_command": self._status.last_command,
            "last_error": self._status.last_error,
            "use_llm": self._config.use_llm,
            "llm_available": self._status.llm_available,
            "ollama_error": self._status.ollama_error,
            "stt_available": self._status.stt_available,
            "model_exists": self._status.model_exists,
            "model_path": self._config.model_path,
            "ollama_model": self._config.ollama_model,
            "ollama_url": self._config.ollama_url,
            "input_device": self._config.input_device,
            "input_device_name": self._status.input_device_name,
            "logs": list(self._status.logs),
            "available": self.dependencies_ready(),
            "missing": self.missing_dependencies(),
        }

    def dependencies_ready(self) -> bool:
        return sd is not None and Model is not None and KaldiRecognizer is not None

    def missing_dependencies(self) -> list[str]:
        missing: list[str] = []
        if sd is None:
            missing.append("sounddevice")
        if Model is None or KaldiRecognizer is None:
            missing.append("vosk")
        return missing

    def status(self) -> dict[str, Any]:
        return self._status_dict()

    def list_model_presets(self) -> list[dict[str, Any]]:
        presets: list[dict[str, Any]] = []
        for item in MODEL_PRESETS:
            presets.append({**item, "exists": Path(item["path"]).exists()})
        return presets

    def _refresh_status_flags(self) -> None:
        self._status.use_llm = self._config.use_llm
        self._status.stt_available = self.dependencies_ready()
        self._status.model_path = self._config.model_path
        self._status.model_exists = Path(self._config.model_path).exists()
        self._status.ollama_model = self._config.ollama_model
        self._status.ollama_url = self._config.ollama_url
        self._status.input_device = self._config.input_device
        self._status.input_device_name = self._resolve_input_device_name(self._config.input_device)

    def _resolve_input_device_name(self, input_device: int | None) -> str:
        if sd is None:
            return ""
        if input_device is None:
            try:
                default_input, _ = sd.default.device
                input_device = int(default_input) if default_input is not None and int(default_input) >= 0 else None
            except Exception:
                input_device = None
        if input_device is None:
            return "System default"
        try:
            device = sd.query_devices(input_device)
            return str(device.get("name", f"Device {input_device}"))
        except Exception:
            return f"Device {input_device}"

    def _probe_ollama(self, force: bool = False) -> None:
        if not self._config.use_llm:
            self._status.llm_available = False
            self._status.ollama_error = "LLM disabled"
            return
        now = time.monotonic()
        if not force and now - self._last_ollama_probe_at < 5.0:
            return
        self._last_ollama_probe_at = now
        tags_url = self._config.ollama_url.replace("/api/generate", "/api/tags")
        request = urllib.request.Request(tags_url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=2.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            models = payload.get("models", []) if isinstance(payload, dict) else []
            installed_names = {str(item.get("name", "")).strip() for item in models if isinstance(item, dict)}
            if self._config.ollama_model in installed_names:
                self._status.llm_available = True
                self._status.ollama_error = ""
            else:
                self._status.llm_available = False
                self._status.ollama_error = f"Model not pulled: {self._config.ollama_model}"
        except Exception as exc:
            self._status.llm_available = False
            self._status.ollama_error = f"{type(exc).__name__}: {exc}"

    def configure(self, payload: dict[str, Any]) -> None:
        if "wake_word" in payload:
            self._config.wake_word = bool(payload["wake_word"])
        if "confirm_estop" in payload:
            self._config.confirm_estop = bool(payload["confirm_estop"])
        if "noise_gate" in payload:
            self._config.noise_gate = max(0.005, min(0.2, float(payload["noise_gate"])))
        if "model_path" in payload and payload["model_path"]:
            self._config.model_path = str(payload["model_path"])
        if "input_device" in payload:
            raw_device = payload["input_device"]
            self._config.input_device = None if raw_device in ("", None) else int(raw_device)
        if "use_llm" in payload:
            self._config.use_llm = bool(payload["use_llm"])
        if "ollama_model" in payload and payload["ollama_model"]:
            self._config.ollama_model = str(payload["ollama_model"])
        if "ollama_url" in payload and payload["ollama_url"]:
            self._config.ollama_url = str(payload["ollama_url"])
        self._status.noise_gate = self._config.noise_gate
        self._refresh_status_flags()
        self._probe_ollama(force=True)

    def start(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        self.configure(payload)
        if self._status.running:
            self._push_log("Offline voice already running")
            return self.status()
        if not self.dependencies_ready():
            self._status.last_error = f"Missing dependencies: {', '.join(self.missing_dependencies())}"
            self._push_log(self._status.last_error)
            return self.status()
        model_path = Path(self._config.model_path)
        if not model_path.exists():
            self._status.last_error = f"Vosk model not found: {model_path}"
            self._push_log(self._status.last_error)
            return self.status()

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._status.running = True
        self._status.ready = True
        self._status.last_error = ""
        self._push_log(f"Offline voice starting with model {model_path.name}")
        self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        self._status.running = False
        self._status.listening = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
        self._stream = None
        self._push_log("Offline voice stopped")
        return self.status()

    def calibrate(self, duration_s: float = 2.2) -> dict[str, Any]:
        self._calibration_samples.clear()
        self._calibration_until = time.monotonic() + max(0.8, min(6.0, duration_s))
        self._push_log("Noise calibration started")
        return self.status()

    def process_manual_text(self, text: str) -> dict[str, Any]:
        self._push_log(f"Manual text: {text}")
        self._dispatch_text(text, source="Manual")
        return self.status()

    def _record_action_error(self, source: str, exc: BaseException) -> None:
        self._status.last_error = f"{type(exc).__name__}: {exc}"
        self._push_log(f"{source} failed: {self._status.last_error}")

    def list_input_devices(self) -> list[dict[str, Any]]:
        if sd is None:
            return []
        try:
            devices = sd.query_devices()
        except Exception:
            return []
        output: list[dict[str, Any]] = []
        for index, device in enumerate(devices):
            if int(device.get("max_input_channels", 0)) > 0:
                output.append({"index": index, "name": str(device.get("name", f"Device {index}"))})
        return output

    def _execute_action(self, action: dict[str, Any], source: str) -> None:
        kind = action.get("kind")
        if kind == "control":
            mapping = {"ARM": 0x10, "DISARM": 0x11, "ESTOP": 0x12, "OPEN": 0x13, "CLOSE": 0x14}
            name = str(action.get("name", "")).upper()
            if name in mapping:
                self._send_packet(self._make_packet(mapping[name], []))
                self._status.last_command = name
                self._push_log(f"{source}: {name}")
            return
        if kind == "grip":
            value = max(0, min(100, int(action.get("value", 0))))
            self._send_packet(self._make_packet(0x02, [value]))
            self._status.last_command = f"GRIP {value}"
            self._push_log(f"{source}: GRIP {value}")
            return
        if kind == "angles":
            angles = [int(value) for value in action.get("angles", [])[:6]]
            self._send_packet(self._make_packet(0x01, angles))
            self._status.last_command = str(action.get("label", "ANGLES"))
            self._push_log(f"{source}: {self._status.last_command}")
            return
        if kind == "set_one":
            index = max(0, min(5, int(action.get("index", 0))))
            value = int(action.get("value", OPEN_ANGLE[index]))
            angles = OPEN_ANGLE.copy()
            angles[index] = value
            self._send_packet(self._make_packet(0x01, angles))
            self._status.last_command = str(action.get("label", f"FINGER {index}"))
            self._push_log(f"{source}: {self._status.last_command}")
            return
        if kind == "set_percent":
            index = max(0, min(5, int(action.get("index", 0))))
            value = max(0, min(100, int(action.get("value", 0))))
            angles = OPEN_ANGLE.copy()
            close_angle = CLOSED_ANGLE[index]
            open_angle = OPEN_ANGLE[index]
            angles[index] = int(round(open_angle + (close_angle - open_angle) * (value / 100.0)))
            self._send_packet(self._make_packet(0x01, angles))
            self._status.last_command = str(action.get("label", f"FINGER {index} {value}%"))
            self._push_log(f"{source}: {self._status.last_command}")
            return
        if kind == "hold":
            self._status.last_command = "HOLD"
            self._push_log(f"{source}: HOLD")
            return
        if kind == "note":
            self._status.last_command = str(action.get("label", "NOTE"))
            self._push_log(f"{source}: {action.get('message', self._status.last_command)}")
            return
        if kind == "routine":
            self._execute_routine(action, source)

    def _execute_routine(self, action: dict[str, Any], source: str) -> None:
        name = str(action.get("name", "")).lower()
        if name == "wave":
            for gesture_name in ("open", "relax", "open", "relax", "open"):
                self._execute_action({"kind": "angles", **GESTURE_PRESETS[gesture_name]}, source)
                time.sleep(0.28)
            return
        if name == "demo":
            for gesture_name in ("open", "like", "point", "peace", "ok", "fist", "open"):
                self._execute_action({"kind": "angles", **GESTURE_PRESETS[gesture_name]}, source)
                time.sleep(0.34)
            return
        if name == "count":
            value = action.get("value")
            if value is None:
                value = parse_number(str(action.get("text", ""))) or 1
            if int(value) == 1:
                self._execute_action({"kind": "angles", **GESTURE_PRESETS["point"]}, source)
            elif int(value) == 2:
                self._execute_action({"kind": "angles", **GESTURE_PRESETS["peace"]}, source)
            elif int(value) == 3:
                self._execute_action({"kind": "angles", **GESTURE_PRESETS["three"]}, source)
            else:
                self._execute_action({"kind": "angles", **GESTURE_PRESETS["open"]}, source)

    def _dispatch_text(self, raw_text: str, source: str) -> None:
        normalized = normalize_text(raw_text)
        if not normalized:
            return
        self._status.last_heard = raw_text
        if self._config.wake_word and source != "Manual":
            if not any(wake_word in normalized for wake_word in WAKE_WORDS):
                self._push_log(f"{source}: no wake word -> {raw_text}")
                return
        if self._awaiting_estop_confirm and ("xac nhan dung" in normalized or "confirm stop" in normalized):
            self._awaiting_estop_confirm = False
            self._execute_action({"kind": "control", "name": "ESTOP"}, source)
            return

        action = self._planner.parse(raw_text, self._config)
        if action is None:
            self._push_log(f"{source}: unmapped -> {raw_text}")
            return
        if action.get("kind") == "control" and action.get("name") == "ESTOP" and self._config.confirm_estop and source != "Manual":
            self._awaiting_estop_confirm = True
            self._push_log("Voice: say 'robot xac nhan dung' to ESTOP")
            return
        try:
            self._execute_action(action, source)
            self._status.last_error = ""
        except Exception as exc:
            self._record_action_error(source, exc)

    def _audio_callback(self, indata: bytes, frames: int, time_info: Any, status: Any) -> None:
        if status:
            self._status.last_error = str(status)
        try:
            self._queue.put_nowait(bytes(indata))
        except queue.Full:
            pass

    def _run_loop(self) -> None:
        model = Model(self._config.model_path)
        recognizer = KaldiRecognizer(model, VOICE_SAMPLE_RATE)
        recognizer.SetWords(False)
        self._status.listening = True
        self._status.last_error = ""
        try:
            self._stream = sd.RawInputStream(
                samplerate=VOICE_SAMPLE_RATE,
                blocksize=VOICE_BLOCK_SIZE,
                device=self._config.input_device,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            )
            self._stream.start()
            self._push_log("Offline voice listening on laptop mic")

            while not self._stop_event.is_set():
                try:
                    chunk = self._queue.get(timeout=0.25)
                except queue.Empty:
                    continue
                rms = audioop.rms(chunk, 2) / 32768.0
                if self._calibration_until > time.monotonic():
                    self._calibration_samples.append(rms)
                    continue
                if self._calibration_until and self._calibration_until <= time.monotonic():
                    if self._calibration_samples:
                        sorted_samples = sorted(self._calibration_samples)
                        self._status.noise_floor = sorted_samples[min(len(sorted_samples) - 1, int(len(sorted_samples) * 0.72))]
                        self._config.noise_gate = max(0.005, min(0.2, self._status.noise_floor * 3.0))
                        self._status.noise_gate = self._config.noise_gate
                        self._push_log(f"Noise calibrated floor={self._status.noise_floor:.4f} gate={self._status.noise_gate:.4f}")
                    self._calibration_until = 0.0
                    self._calibration_samples.clear()

                gate = max(self._config.noise_gate, self._status.noise_floor * 2.3)
                if rms <= gate * 0.65:
                    self._status.ready = False
                    continue
                self._status.ready = True
                if recognizer.AcceptWaveform(chunk):
                    payload = json.loads(recognizer.Result())
                    text = str(payload.get("text", "")).strip()
                    if text:
                        self._push_log(f"Heard: {text}")
                        self._dispatch_text(text, "Voice")
        except Exception as exc:
            self._status.last_error = f"{type(exc).__name__}: {exc}"
            self._push_log(f"Offline voice failed: {self._status.last_error}")
        finally:
            self._status.running = False
            self._status.listening = False
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
            self._stream = None
