"""Docker entrypoint for the existing Robot Hand Python server.

Keep application code mounted unchanged. Does not flash Arduino / ESP32.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def command_from_env() -> list[str]:
    script = Path("/app/web_client/master_control_server.py")
    if not script.is_file():
        raise SystemExit(
            "ERROR: /app/web_client/master_control_server.py is missing. "
            "Place the Docker kit in the root of your existing Robot Hand project."
        )
    esp_url = os.environ.get("ESP32_WS_URL", "ws://192.168.4.1:81")
    http_port = int(os.environ.get("CONTAINER_HTTP_PORT", "8080"))
    proxy_port = int(os.environ.get("CONTAINER_WS_PORT", "8765"))
    args = [
        sys.executable, "-u", str(script),
        "--http-host", "0.0.0.0", "--http-port", str(http_port),
        "--proxy-host", "0.0.0.0", "--proxy-port", str(proxy_port),
        "--esp-url", esp_url,
        "--no-browser",
    ]
    if os.environ.get("SIMULATE", "0").strip().lower() in {"1", "true", "yes", "on"}:
        args.append("--simulate")
    return args


if __name__ == "__main__":
    command = command_from_env()
    print("[Docker] Starting master control:", " ".join(command), flush=True)
    os.execv(sys.executable, command)
