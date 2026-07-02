from __future__ import annotations

import argparse
from collections import deque
import json
import math
import threading
import time
from pathlib import Path
from typing import Deque, List, Sequence

import cv2
import mediapipe as mp
import numpy as np
import websocket


WS_URL = "ws://192.168.4.1:81"
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CAMERA_FPS = 60
PROCESS_WIDTH = 320
PROCESS_HEIGHT = 240
SEND_HZ = 50.0
EMA_ALPHA = 0.45
DEADBAND_DEG = 1
LIVE_MAX_DEG_PER_SEC = 45.0
ARM_SETTLE_MS = 800
MODEL_TEST_MAX_DEG_PER_SEC = 360.0
MODEL_TEST_ARM_SETTLE_MS = 500
MODEL_TEST_ALPHA = 0.90
MODEL_TEST_TARGET_DEADBAND_DEG = [1, 1, 1, 1, 2]
REALTIME_SEND_HZ = 35.0
STABLE_RATIO_WINDOW = 5
STABLE_ALPHA = 0.55
STABLE_SEND_HZ = 15.0
STABLE_TARGET_DEADBAND_DEG = [4, 4, 4, 4, 5]
CV_MODE_TENDON = "tendon"
CV_MODE_SIMPLE = "simple"
CV_MODE_DIRECT = "direct"
OPEN_ANGLE = [40, 180, 0, 0, 80]
CLOSED_ANGLE = [170, 0, 180, 180, 0]
SERVO_NAMES = [
    "S0 thumb curl",
    "S1 index",
    "S2 middle",
    "S3 ring+pinky",
    "S4 thumb oppose",
]
CALIBRATION_FILE = Path(__file__).with_name("hand_pose_calibration.json")
CALIBRATION_METRIC = "hand_local_world_v1"
SERVO_PROFILE_FILE = Path(__file__).with_name("servo_tendon_profile.json")
DEFAULT_SERVO_PROFILES = [
    {"open_deadzone": 0.05, "close_saturation": 0.74, "curve": 0.88},
    {"open_deadzone": 0.05, "close_saturation": 0.62, "curve": 0.66},
    {"open_deadzone": 0.05, "close_saturation": 0.68, "curve": 0.72},
    {"open_deadzone": 0.05, "close_saturation": 0.66, "curve": 0.70},
    {"open_deadzone": 0.04, "close_saturation": 0.70, "curve": 0.92},
]
SIMPLE_CLOSE_GAIN = [1.02, 1.16, 1.14, 1.08, 1.00]
DIRECT_CLOSE_SATURATION = [0.95, 0.95, 0.86, 0.82, 0.78]
TARGET_DEADBAND_DEG = [3, 3, 3, 3, 4]
REALTIME_TARGET_DEADBAND_DEG = [1, 1, 1, 1, 2]

MODE_DIRECT = 0x01
MODE_GRIP = 0x02
MODE_ARM = 0x10
MODE_DISARM = 0x11
MODE_ESTOP = 0x12
MODE_OPEN = 0x13
MODE_CLOSE = 0x14


def checksum_xor(data: Sequence[int]) -> int:
    value = 0
    for byte in data:
        value ^= int(byte) & 0xFF
    return value


def make_packet(mode: int, payload: Sequence[int] | None = None) -> bytes:
    frame = [0] * 8
    frame[0] = 0xAA
    frame[1] = mode & 0xFF
    payload = list(payload or [])
    for index in range(min(5, len(payload))):
        frame[2 + index] = int(payload[index]) & 0xFF
    frame[7] = checksum_xor(frame[:7])
    return bytes(frame)


def connect_ws(url: str) -> websocket.WebSocket:
    try:
        ws = websocket.create_connection(url, timeout=5)
        ws.settimeout(1)
        return ws
    except Exception as exc:
        raise RuntimeError(
            f"Cannot connect to ESP32 WebSocket at {url}. "
            "Check that the PC is connected to Wi-Fi 'RobotHand_ESP32', "
            "ESP32 is still running, and the AP IP is 192.168.4.1."
        ) from exc


def send_packet(ws: websocket.WebSocket, packet: bytes) -> None:
    ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)


def send_angles(ws: websocket.WebSocket, angles: Sequence[int]) -> None:
    send_packet(ws, make_packet(MODE_DIRECT, angles))


def send_grip(ws: websocket.WebSocket, grip_percent: int) -> None:
    send_packet(ws, make_packet(MODE_GRIP, [grip_percent]))


def send_control(ws: websocket.WebSocket, command: str) -> None:
    mapping = {
        "ARM": MODE_ARM,
        "DISARM": MODE_DISARM,
        "ESTOP": MODE_ESTOP,
        "OPEN": MODE_OPEN,
        "CLOSE": MODE_CLOSE,
    }
    key = command.strip().upper()
    if key not in mapping:
        raise ValueError(f"Unsupported command: {command}")
    send_packet(ws, make_packet(mapping[key]))


def close_ws_quietly(ws: websocket.WebSocket | None) -> None:
    if ws is None:
        return
    try:
        ws.close()
    except Exception:
        pass


def try_send_angles(ws: websocket.WebSocket | None, angles: Sequence[int]) -> tuple[bool, str | None]:
    if ws is None:
        return False, "socket unavailable"
    try:
        send_angles(ws, angles)
        return True, None
    except Exception as exc:
        return False, str(exc)


def try_send_control(ws: websocket.WebSocket | None, command: str) -> tuple[bool, str | None]:
    if ws is None:
        return False, "socket unavailable"
    try:
        send_control(ws, command)
        return True, None
    except Exception as exc:
        return False, str(exc)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def grip_ratio_to_angles(close_ratio: float) -> List[int]:
    ratio = clamp(close_ratio, 0.0, 1.0)
    return [
        int(round(OPEN_ANGLE[i] + (CLOSED_ANGLE[i] - OPEN_ANGLE[i]) * ratio))
        for i in range(5)
    ]


def ratios_to_angles(close_ratios: Sequence[float]) -> List[int]:
    return [
        int(round(OPEN_ANGLE[i] + (CLOSED_ANGLE[i] - OPEN_ANGLE[i]) * clamp(close_ratios[i], 0.0, 1.0)))
        for i in range(5)
    ]


def default_open_ratios() -> List[float]:
    return [0.0] * 5


def default_close_ratios() -> List[float]:
    return [1.0] * 5


def default_mid_ratios(open_ratios: Sequence[float], close_ratios: Sequence[float]) -> List[float]:
    return [(float(open_ratios[i]) + float(close_ratios[i])) * 0.5 for i in range(5)]


def load_pose_calibration() -> tuple[List[float], List[float], List[float], bool, bool]:
    if not CALIBRATION_FILE.exists():
        open_ratios = default_open_ratios()
        close_ratios = default_close_ratios()
        return open_ratios, default_mid_ratios(open_ratios, close_ratios), close_ratios, False, True
    try:
        payload = json.loads(CALIBRATION_FILE.read_text(encoding="utf-8"))
        if payload.get("metric") != CALIBRATION_METRIC:
            open_ratios = default_open_ratios()
            close_ratios = default_close_ratios()
            return open_ratios, default_mid_ratios(open_ratios, close_ratios), close_ratios, False, False
        open_ratios = [float(value) for value in payload.get("open_ratios", default_open_ratios())]
        close_ratios = [float(value) for value in payload.get("close_ratios", default_close_ratios())]
        mid_payload = payload.get("mid_ratios")
        if mid_payload is None:
            mid_ratios = default_mid_ratios(open_ratios, close_ratios)
            mid_ready = False
        else:
            mid_ratios = [float(value) for value in mid_payload]
            mid_ready = True
        if len(open_ratios) != 5 or len(close_ratios) != 5 or len(mid_ratios) != 5:
            raise ValueError("Invalid calibration length")
        return open_ratios, mid_ratios, close_ratios, mid_ready, True
    except Exception:
        open_ratios = default_open_ratios()
        close_ratios = default_close_ratios()
        return open_ratios, default_mid_ratios(open_ratios, close_ratios), close_ratios, False, False


def save_pose_calibration(open_ratios: Sequence[float], mid_ratios: Sequence[float], close_ratios: Sequence[float]) -> None:
    payload = {
        "metric": CALIBRATION_METRIC,
        "open_ratios": [round(float(value), 6) for value in open_ratios],
        "mid_ratios": [round(float(value), 6) for value in mid_ratios],
        "close_ratios": [round(float(value), 6) for value in close_ratios],
    }
    CALIBRATION_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def default_servo_profiles() -> List[dict[str, float]]:
    return [{key: float(value) for key, value in profile.items()} for profile in DEFAULT_SERVO_PROFILES]


def sanitize_servo_profile(profile: dict[str, float] | None, fallback: dict[str, float]) -> dict[str, float]:
    source = profile or {}
    open_deadzone = clamp(float(source.get("open_deadzone", fallback["open_deadzone"])), 0.0, 0.9)
    close_saturation = clamp(float(source.get("close_saturation", fallback["close_saturation"])), 0.05, 1.0)
    if close_saturation <= open_deadzone + 0.05:
        close_saturation = clamp(open_deadzone + 0.05, 0.05, 1.0)
    curve = clamp(float(source.get("curve", fallback["curve"])), 0.35, 2.5)
    return {
        "open_deadzone": open_deadzone,
        "close_saturation": close_saturation,
        "curve": curve,
    }


def load_servo_profiles() -> List[dict[str, float]]:
    defaults = default_servo_profiles()
    if not SERVO_PROFILE_FILE.exists():
        return defaults
    try:
        payload = json.loads(SERVO_PROFILE_FILE.read_text(encoding="utf-8"))
        profile_items = payload.get("profiles") if isinstance(payload, dict) else payload
        if not isinstance(profile_items, list) or len(profile_items) != 5:
            raise ValueError("Invalid profile list")
        return [
            sanitize_servo_profile(dict(profile_items[index]), defaults[index])
            for index in range(5)
        ]
    except Exception:
        return defaults


def save_servo_profiles(profiles: Sequence[dict[str, float]]) -> None:
    payload = {
        "kind": "tendon_servo_profile_v1",
        "profiles": [
            {
                "open_deadzone": round(float(profile["open_deadzone"]), 6),
                "close_saturation": round(float(profile["close_saturation"]), 6),
                "curve": round(float(profile["curve"]), 6),
            }
            for profile in profiles
        ],
    }
    SERVO_PROFILE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def format_servo_profile(profile: dict[str, float]) -> str:
    return (
        f"odz {profile['open_deadzone']:.2f} "
        f"sat {profile['close_saturation']:.2f} "
        f"curve {profile['curve']:.2f}"
    )


def remap_tendon_ratio(value: float, profile: dict[str, float]) -> float:
    raw_value = clamp(float(value), 0.0, 1.0)
    open_deadzone = float(profile["open_deadzone"])
    close_saturation = float(profile["close_saturation"])
    if raw_value <= open_deadzone:
        return 0.0
    if raw_value >= close_saturation:
        return 1.0
    linear = clamp((raw_value - open_deadzone) / max(1e-6, close_saturation - open_deadzone), 0.0, 1.0)
    curved = linear ** float(profile["curve"])
    return clamp(curved, 0.0, 1.0)


def tendon_drive_ratios(close_ratios: Sequence[float], servo_profiles: Sequence[dict[str, float]]) -> List[float]:
    return [remap_tendon_ratio(close_ratios[index], servo_profiles[index]) for index in range(5)]


def simple_drive_ratios(close_ratios: Sequence[float]) -> List[float]:
    def soft_close_boost(value: float, gain: float) -> float:
        base = clamp(float(value), 0.0, 1.0)
        if gain <= 1.0:
            return clamp(base * gain, 0.0, 1.0)
        boosted = base ** (1.0 / gain)
        blended = 0.55 * base + 0.45 * boosted
        return clamp(blended, 0.0, 1.0)

    return [
        soft_close_boost(float(close_ratios[index]), float(SIMPLE_CLOSE_GAIN[index]))
        for index in range(5)
    ]


def direct_drive_ratios(close_ratios: Sequence[float]) -> List[float]:
    return [
        clamp(float(close_ratios[index]) / float(DIRECT_CLOSE_SATURATION[index]), 0.0, 1.0)
        for index in range(5)
    ]


def median_filter_ratios(
    history: Deque[List[float]],
    close_ratios: Sequence[float],
    window_size: int,
) -> List[float]:
    history.append([float(value) for value in close_ratios])
    while len(history) > window_size:
        history.popleft()
    return [
        float(np.median([sample[index] for sample in history]))
        for index in range(5)
    ]


def stabilize_angles(
    previous_angles: Sequence[int] | None,
    current_angles: Sequence[int],
    deadbands: Sequence[int],
) -> List[int]:
    if previous_angles is None:
        return [int(value) for value in current_angles]
    stable: List[int] = []
    for index in range(5):
        previous = int(previous_angles[index])
        current = int(current_angles[index])
        if abs(current - previous) <= int(deadbands[index]):
            stable.append(previous)
        else:
            stable.append(current)
    return stable


def calibration_mode_for_servo(open_value: float, mid_value: float, close_value: float) -> str:
    if close_value <= open_value + 1e-6:
        return "bad"
    if open_value < mid_value < close_value:
        return "3pt"
    return "2pt"


def calibration_modes(
    open_ratios: Sequence[float],
    mid_ratios: Sequence[float],
    close_ratios: Sequence[float],
) -> List[str]:
    return [
        calibration_mode_for_servo(float(open_ratios[i]), float(mid_ratios[i]), float(close_ratios[i]))
        for i in range(5)
    ]


def normalize_close_ratios(
    raw_ratios: Sequence[float],
    open_ratios: Sequence[float],
    mid_ratios: Sequence[float],
    close_ratios: Sequence[float],
) -> List[float]:
    normalized: List[float] = []
    for index in range(5):
        open_value = float(open_ratios[index])
        mid_value = float(mid_ratios[index])
        close_value = float(close_ratios[index])
        raw_value = float(raw_ratios[index])
        mode = calibration_mode_for_servo(open_value, mid_value, close_value)

        if mode == "bad":
            normalized.append(clamp(raw_value, 0.0, 1.0))
            continue

        if mode == "2pt":
            span = close_value - open_value
            if abs(span) < 1e-6:
                normalized.append(clamp(raw_value, 0.0, 1.0))
            else:
                normalized.append(clamp((raw_value - open_value) / span, 0.0, 1.0))
            continue

        low_span = mid_value - open_value
        high_span = close_value - mid_value
        if raw_value <= mid_value:
            if abs(low_span) < 1e-6:
                normalized_value = 0.5
            else:
                normalized_value = 0.5 * clamp((raw_value - open_value) / low_span, 0.0, 1.0)
        else:
            if abs(high_span) < 1e-6:
                normalized_value = 1.0
            else:
                normalized_value = 0.5 + 0.5 * clamp((raw_value - mid_value) / high_span, 0.0, 1.0)
        normalized.append(clamp(normalized_value, 0.0, 1.0))
    return normalized


def ema_angles(previous: Sequence[float] | None, current: Sequence[int], alpha: float) -> List[float]:
    if previous is None:
        return [float(value) for value in current]
    return [
        float(previous[i]) + alpha * (float(current[i]) - float(previous[i]))
        for i in range(5)
    ]


def should_send_angles(previous: Sequence[int] | None, current: Sequence[int]) -> bool:
    if previous is None:
        return True
    return any(abs(int(current[i]) - int(previous[i])) > DEADBAND_DEG for i in range(5))


def slew_limit_angles(
    previous_angles: Sequence[float],
    target_angles: Sequence[int],
    max_deg_per_sec: float,
    dt: float,
) -> List[float]:
    if max_deg_per_sec <= 0 or dt <= 0:
        return [float(value) for value in target_angles]
    max_step = max_deg_per_sec * dt
    limited: List[float] = []
    for index in range(5):
        prev_value = float(previous_angles[index])
        target_value = float(target_angles[index])
        delta = target_value - prev_value
        if delta > max_step:
            next_value = prev_value + max_step
        elif delta < -max_step:
            next_value = prev_value - max_step
        else:
            next_value = target_value
        limited.append(float(next_value))
    return limited


def point(landmarks: Sequence[np.ndarray], index: int) -> np.ndarray:
    return np.asarray(landmarks[index], dtype=np.float32)


def landmark_xyz(landmark) -> np.ndarray:
    return np.array(
        [
            float(landmark.x),
            float(landmark.y),
            float(getattr(landmark, "z", 0.0)),
        ],
        dtype=np.float32,
    )


def normalize_vector(vector: np.ndarray) -> np.ndarray | None:
    length = float(np.linalg.norm(vector))
    if length <= 1e-6:
        return None
    return vector / length


def hand_local_landmarks(landmarks) -> List[np.ndarray]:
    points = [landmark_xyz(landmark) for landmark in landmarks]
    wrist = points[0]
    index_mcp = points[5]
    pinky_mcp = points[17]
    middle_mcp = points[9]

    x_axis = normalize_vector(index_mcp - pinky_mcp)
    y_seed = middle_mcp - wrist
    if x_axis is None:
        return [point - wrist for point in points]

    z_axis = normalize_vector(np.cross(x_axis, y_seed))
    if z_axis is None:
        z_axis = normalize_vector(np.cross(x_axis, index_mcp - wrist))
    if z_axis is None:
        return [point - wrist for point in points]

    y_axis = normalize_vector(np.cross(z_axis, x_axis))
    if y_axis is None:
        return [point - wrist for point in points]

    return [
        np.array(
            [
                float(np.dot(point - wrist, x_axis)),
                float(np.dot(point - wrist, y_axis)),
                float(np.dot(point - wrist, z_axis)),
            ],
            dtype=np.float32,
        )
        for point in points
    ]


def image_landmarks_2d(landmarks) -> List[np.ndarray]:
    return [np.array([float(landmark.x), float(landmark.y)], dtype=np.float32) for landmark in landmarks]


def extract_pose_landmarks(image_landmarks, world_landmarks) -> tuple[List[np.ndarray], str]:
    if world_landmarks is not None and len(world_landmarks) == 21:
        return hand_local_landmarks(world_landmarks), "3D world/local"
    return image_landmarks_2d(image_landmarks), "2D image/fallback"


def angle_degrees(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = float(np.linalg.norm(ba) * np.linalg.norm(bc))
    if denom <= 1e-6:
        return 180.0
    cosine = float(np.dot(ba, bc) / denom)
    return math.degrees(math.acos(clamp(cosine, -1.0, 1.0)))


def joint_angle_to_close_ratio(angle: float, open_angle: float = 170.0, closed_angle: float = 75.0) -> float:
    return clamp((open_angle - angle) / (open_angle - closed_angle), 0.0, 1.0)


def finger_close_ratio(landmarks: Sequence[np.ndarray], mcp: int, pip: int, dip: int, tip: int) -> float:
    pip_angle = angle_degrees(point(landmarks, mcp), point(landmarks, pip), point(landmarks, dip))
    dip_angle = angle_degrees(point(landmarks, pip), point(landmarks, dip), point(landmarks, tip))
    return clamp(0.65 * joint_angle_to_close_ratio(pip_angle) + 0.35 * joint_angle_to_close_ratio(dip_angle), 0.0, 1.0)


def thumb_close_ratio(landmarks: Sequence[np.ndarray]) -> float:
    mcp_angle = angle_degrees(point(landmarks, 1), point(landmarks, 2), point(landmarks, 3))
    ip_angle = angle_degrees(point(landmarks, 2), point(landmarks, 3), point(landmarks, 4))
    return clamp(0.55 * joint_angle_to_close_ratio(mcp_angle, 165.0, 75.0) + 0.45 * joint_angle_to_close_ratio(ip_angle, 165.0, 75.0), 0.0, 1.0)


def thumb_oppose_ratio(landmarks: Sequence[np.ndarray]) -> float:
    wrist = point(landmarks, 0)
    index_mcp = point(landmarks, 5)
    pinky_mcp = point(landmarks, 17)
    thumb_tip = point(landmarks, 4)
    palm_width = float(np.linalg.norm(index_mcp - pinky_mcp))
    if palm_width <= 1e-6:
        return 0.0
    dist = float(np.linalg.norm(thumb_tip - index_mcp)) / palm_width
    wrist_dist = float(np.linalg.norm(thumb_tip - wrist)) / palm_width
    close_by_index = 1.0 - clamp((dist - 0.45) / (1.25 - 0.45), 0.0, 1.0)
    close_by_wrist = 1.0 - clamp((wrist_dist - 0.90) / (1.70 - 0.90), 0.0, 1.0)
    return clamp(0.75 * close_by_index + 0.25 * close_by_wrist, 0.0, 1.0)


def landmarks_to_close_ratios(landmarks: Sequence[np.ndarray]) -> List[float]:
    thumb = thumb_close_ratio(landmarks)
    index = finger_close_ratio(landmarks, 5, 6, 7, 8)
    middle = finger_close_ratio(landmarks, 9, 10, 11, 12)
    ring = finger_close_ratio(landmarks, 13, 14, 15, 16)
    pinky = finger_close_ratio(landmarks, 17, 18, 19, 20)
    ring_pinky = clamp((ring + pinky) * 0.5, 0.0, 1.0)
    oppose = thumb_oppose_ratio(landmarks)
    return [thumb, index, middle, ring_pinky, oppose]


def check_runtime_dependencies() -> None:
    if not hasattr(cv2, "VideoCapture"):
        raise RuntimeError(
            "OpenCV import is broken: cv2.VideoCapture is missing. "
            "Run: pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python "
            "then: pip install -r requirements.txt"
        )
    if not hasattr(mp, "solutions"):
        raise RuntimeError("MediaPipe import is broken. Run: pip install -r requirements.txt")


def open_low_latency_camera(camera_index: int, width: int, height: int, fps: int):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    return cap


class LatestFrameCamera:
    def __init__(self, cap) -> None:
        self.cap = cap
        self.lock = threading.Lock()
        self.latest_frame = None
        self.stopped = False
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()

    def _reader_loop(self) -> None:
        while not self.stopped:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.002)
                continue
            with self.lock:
                self.latest_frame = frame

    def read(self):
        with self.lock:
            frame = None if self.latest_frame is None else self.latest_frame.copy()
        return (frame is not None), frame

    def stop(self) -> None:
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join(timeout=0.5)


def draw_servo_panel(
    frame,
    angles: Sequence[int] | None,
    close_ratios: Sequence[float] | None,
    raw_close_ratios: Sequence[float] | None,
    drive_ratios: Sequence[float] | None,
    open_calibration: Sequence[float],
    mid_calibration: Sequence[float],
    close_calibration: Sequence[float],
    servo_profiles: Sequence[dict[str, float]],
    selected_servo: int,
    calibration_modes_per_servo: Sequence[str],
    calibration_ready: bool,
    mid_calibration_ready: bool,
) -> None:
    panel_x = 12
    panel_y = 92
    panel_w = 610
    panel_h = 192
    overlay = frame.copy()
    cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (18, 18, 18), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0.0, frame)
    cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h), (110, 110, 110), 1)

    cv2.putText(frame, "Servo detail", (panel_x + 10, panel_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (255, 255, 255), 2)
    cv2.putText(frame, "name            angle   drv   norm   raw    pose calib(open->mid->close)   profile", (panel_x + 10, panel_y + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (210, 210, 210), 1)

    if angles is None:
        cv2.putText(frame, "No hand detected", (panel_x + 10, panel_y + 66), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 2)
    else:
        for index, name in enumerate(SERVO_NAMES):
            angle = int(angles[index])
            drive_ratio = drive_ratios[index] if drive_ratios is not None else None
            norm_ratio = close_ratios[index] if close_ratios is not None else None
            raw_ratio = raw_close_ratios[index] if raw_close_ratios is not None else None
            row_y = panel_y + 58 + index * 18
            drive_text = f"{drive_ratio:0.2f}" if drive_ratio is not None else "--"
            norm_text = f"{norm_ratio:0.2f}" if norm_ratio is not None else "--"
            raw_text = f"{raw_ratio:0.2f}" if raw_ratio is not None else "--"
            pose_text = f"{OPEN_ANGLE[index]:3d}->{CLOSED_ANGLE[index]:3d}"
            calib_text = f"{open_calibration[index]:0.2f}->{mid_calibration[index]:0.2f}->{close_calibration[index]:0.2f}"
            mode_text = calibration_modes_per_servo[index]
            profile_text = format_servo_profile(servo_profiles[index])
            selected_prefix = ">" if index == selected_servo else " "
            text = f"{selected_prefix}{name:<14} {angle:>3d}deg  {drive_text:>4}  {norm_text:>4}  {raw_text:>4}   {pose_text:<8} {calib_text} {mode_text} {profile_text}"
            color = (255, 255, 180) if index == selected_servo else (240, 240, 240)
            cv2.putText(frame, text, (panel_x + 10, row_y), cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 1)

    if all(mode == "3pt" for mode in calibration_modes_per_servo):
        calib_status = "POSE CAL READY"
        calib_color = (0, 220, 0)
    elif any(mode == "2pt" for mode in calibration_modes_per_servo):
        calib_status = "POSE CAL MIXED - some servos fallback to 2-point"
        calib_color = (0, 220, 255)
    else:
        calib_status = "POSE CAL DEFAULT/INVALID - press z/m/x/s"
        calib_color = (0, 220, 255)
    cv2.putText(frame, calib_status, (panel_x + 10, panel_y + panel_h - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, calib_color, 1)
    tune_help = "1..5 select servo | -/= odz | ,/. sat | [/] curve | p save profile | r reset selected"
    cv2.putText(frame, tune_help, (panel_x + 10, panel_y + panel_h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (210, 210, 210), 1)


def draw_hud(
    frame,
    angles: Sequence[int] | None,
    commanded_angles: Sequence[int] | None,
    close_ratios: Sequence[float] | None,
    raw_close_ratios: Sequence[float] | None,
    drive_ratios: Sequence[float] | None,
    fps: float,
    connected: bool,
    live_send: bool,
    arm_active: bool,
    settle_remaining_ms: int,
    max_deg_per_sec: float,
    cv_mode: str,
    send_reason: str,
    open_calibration: Sequence[float],
    mid_calibration: Sequence[float],
    close_calibration: Sequence[float],
    pose_metric_label: str,
    servo_profiles: Sequence[dict[str, float]],
    selected_servo: int,
    calibration_modes_per_servo: Sequence[str],
    calibration_ready: bool,
    mid_calibration_ready: bool,
) -> None:
    if live_send and connected:
        if arm_active and settle_remaining_ms > 0:
            status = f"ARM SETTLE {settle_remaining_ms}ms"
            color = (0, 220, 255)
        elif arm_active:
            status = f"LIVE SAFE {max_deg_per_sec:.0f}deg/s"
            color = (0, 220, 0)
        else:
            status = "LIVE CONNECTED - PRESS A TO ARM"
            color = (0, 220, 255)
    else:
        status = "DRY RUN - NO SERVO"
        color = (0, 220, 255)
    cv2.putText(frame, status, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"FPS {fps:4.1f}", (12, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(frame, pose_metric_label, (200, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (230, 230, 180), 1)
    cv2.putText(frame, f"CV {cv_mode.upper()}", (460, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (180, 230, 255), 1)
    cv2.putText(frame, f"TX {send_reason}", (460, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 220, 180), 1)
    if angles is not None:
        text = "target " + " ".join(f"{value:3d}" for value in angles)
        cv2.putText(frame, text, (12, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 255, 255), 2)
    if commanded_angles is not None:
        text = "send   " + " ".join(f"{value:3d}" for value in commanded_angles)
        cv2.putText(frame, text, (12, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (180, 255, 200), 2)
    draw_servo_panel(
        frame,
        commanded_angles or angles,
        close_ratios,
        raw_close_ratios,
        drive_ratios,
        open_calibration,
        mid_calibration,
        close_calibration,
        servo_profiles,
        selected_servo,
        calibration_modes_per_servo,
        calibration_ready,
        mid_calibration_ready,
    )
    if live_send:
        help_text = "a ARM | d DISARM | o OPEN | c CLOSE | e ESTOP | z open | m mid | x close | s save calib | q quit"
    else:
        help_text = "draft only | z open | m mid | x close | s save calib | add --send for ESP32 | q quit"
    cv2.putText(frame, help_text, (12, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1)


def run_demo_loop(args: argparse.Namespace) -> None:
    ws = connect_ws(args.url) if args.send else None
    try:
        if ws is not None and args.auto_arm:
            send_control(ws, "ARM")
        filtered_ratio: float | None = None
        last_angles: List[int] | None = None
        period = 1.0 / SEND_HZ
        tick = 0
        while True:
            loop_start = time.perf_counter()
            raw_ratio = 0.5 + 0.5 * math.sin(tick * 0.08)
            filtered_ratio = raw_ratio if filtered_ratio is None else filtered_ratio + EMA_ALPHA * (raw_ratio - filtered_ratio)
            angles = grip_ratio_to_angles(filtered_ratio)
            if should_send_angles(last_angles, angles):
                if ws is not None:
                    send_angles(ws, angles)
                last_angles = angles
                print("DRY" if ws is None else "TX", angles)
            tick += 1
            sleep_time = period - (time.perf_counter() - loop_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
    finally:
        if ws is not None:
            try:
                send_control(ws, "DISARM")
            except Exception:
                pass
            ws.close()


class _FailingWebSocket:
    def send(self, _packet: bytes, opcode=None) -> int:
        raise ConnectionResetError(10054, "simulated disconnect")


def run_self_test() -> None:
    packet = make_packet(MODE_DIRECT, OPEN_ANGLE)
    assert len(packet) == 8
    assert packet[0] == 0xAA
    assert packet[1] == MODE_DIRECT
    assert list(packet[2:7]) == OPEN_ANGLE
    assert checksum_xor(packet[:7]) == packet[7]

    assert ratios_to_angles([0.0] * 5) == OPEN_ANGLE
    assert ratios_to_angles([1.0] * 5) == CLOSED_ANGLE

    open_cal, mid_cal, close_cal, _mid_ready, _metric_ok = load_pose_calibration()
    assert normalize_close_ratios(open_cal, open_cal, mid_cal, close_cal) == [0.0] * 5
    mid_norm = normalize_close_ratios(mid_cal, open_cal, mid_cal, close_cal)
    close_norm = normalize_close_ratios(close_cal, open_cal, mid_cal, close_cal)
    assert all(abs(value - 0.5) < 1e-6 for value in mid_norm)
    assert close_norm == [1.0] * 5

    direct = direct_drive_ratios([0.0, 0.25, 0.5, 0.75, 1.0])
    assert direct[0] == 0.0
    assert direct[-1] == 1.0
    assert direct[2] > 0.5

    stable = stabilize_angles([100, 100, 100, 100, 100], [102, 104, 97, 110, 103], TARGET_DEADBAND_DEG)
    assert stable == [100, 104, 100, 110, 100]

    ratio_history: Deque[List[float]] = deque(maxlen=3)
    median_filter_ratios(ratio_history, [0.1, 0.1, 0.1, 0.1, 0.1], 3)
    median_filter_ratios(ratio_history, [0.9, 0.9, 0.9, 0.9, 0.9], 3)
    median = median_filter_ratios(ratio_history, [0.1, 0.1, 0.1, 0.1, 0.1], 3)
    assert median == [0.1, 0.1, 0.1, 0.1, 0.1]

    limited = slew_limit_angles([180.0] * 5, [0, 0, 0, 0, 0], 16.0, 0.02)
    assert all(179.0 < value < 180.0 for value in limited)

    ok, error_text = try_send_angles(_FailingWebSocket(), OPEN_ANGLE)
    assert not ok
    assert error_text

    print("self-test ok: packet, calibration mapping, direct mode, slew limiter, websocket failure handling")


def link_test_send_control(ws: websocket.WebSocket, command: str) -> bool:
    ok, error_text = try_send_control(ws, command)
    print(f"{command}: {'ok' if ok else error_text}")
    return ok


def link_test_send_angles(ws: websocket.WebSocket, label: str, angles: Sequence[int]) -> bool:
    ok, error_text = try_send_angles(ws, angles)
    print(f"{label}: {'ok' if ok else error_text} {list(angles)}")
    return ok


def run_link_test(args: argparse.Namespace) -> None:
    print(f"Connecting to {args.url}")
    ws = connect_ws(args.url)
    try:
        print("Connected. Idle hold...")
        time.sleep(args.link_test_idle_s)

        if not link_test_send_control(ws, "ARM"):
            return
        time.sleep(1.0)

        if not link_test_send_angles(ws, "OPEN direct", OPEN_ANGLE):
            return
        time.sleep(1.0)

        mid_angles = ratios_to_angles([0.5] * 5)
        if not link_test_send_angles(ws, "MID direct", mid_angles):
            return
        time.sleep(1.0)

        if not link_test_send_angles(ws, "CLOSE direct", CLOSED_ANGLE):
            return
        time.sleep(1.0)

        print(f"Streaming direct packets at {args.link_test_hz:g} Hz for {args.link_test_stream_s:g}s...")
        end_time = time.perf_counter() + args.link_test_stream_s
        tick = 0
        period = 1.0 / max(1.0, args.link_test_hz)
        while time.perf_counter() < end_time:
            ratio = 0.5 + 0.5 * math.sin(tick * 0.20)
            angles = ratios_to_angles([ratio] * 5)
            if not link_test_send_angles(ws, "STREAM", angles):
                return
            tick += 1
            time.sleep(period)

        link_test_send_control(ws, "DISARM")
        print("link-test ok")
    finally:
        close_ws_quietly(ws)


def run_cv_loop(args: argparse.Namespace) -> None:
    active_target_deadband_deg = list(TARGET_DEADBAND_DEG)
    if args.model_test:
        args.send = True
        if args.max_deg_per_sec == LIVE_MAX_DEG_PER_SEC:
            args.max_deg_per_sec = MODEL_TEST_MAX_DEG_PER_SEC
        if args.arm_settle_ms == ARM_SETTLE_MS:
            args.arm_settle_ms = MODEL_TEST_ARM_SETTLE_MS
        if args.alpha == EMA_ALPHA:
            args.alpha = MODEL_TEST_ALPHA
        active_target_deadband_deg = list(MODEL_TEST_TARGET_DEADBAND_DEG)
    if args.realtime:
        if args.process_width == PROCESS_WIDTH:
            args.process_width = 320
        if args.process_height == PROCESS_HEIGHT:
            args.process_height = 240
        if args.send_hz == SEND_HZ:
            args.send_hz = REALTIME_SEND_HZ
        active_target_deadband_deg = list(REALTIME_TARGET_DEADBAND_DEG)
    if args.stable:
        args.ratio_window = max(args.ratio_window, STABLE_RATIO_WINDOW)
        if args.alpha == EMA_ALPHA or args.alpha == MODEL_TEST_ALPHA:
            args.alpha = STABLE_ALPHA
        if args.send_hz == SEND_HZ or args.send_hz == REALTIME_SEND_HZ:
            args.send_hz = STABLE_SEND_HZ
        args.min_detection = max(args.min_detection, 0.65)
        args.min_tracking = max(args.min_tracking, 0.75)
        active_target_deadband_deg = list(STABLE_TARGET_DEADBAND_DEG)
    if args.model_test and args.cv_mode == CV_MODE_TENDON:
        args.cv_mode = CV_MODE_DIRECT

    check_runtime_dependencies()
    cv2.setUseOptimized(True)
    cap = open_low_latency_camera(args.camera, args.width, args.height, args.camera_fps)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera index {args.camera}")
    camera_reader = LatestFrameCamera(cap)

    ws = None
    if args.send:
        try:
            ws = connect_ws(args.url)
        except RuntimeError as exc:
            print(f"{exc} Starting preview without live link; background reconnect is enabled.")
    mp_hands = mp.solutions.hands
    mp_draw = mp.solutions.drawing_utils
    last_send_time = 0.0
    last_fps_time = time.perf_counter()
    fps = 0.0
    frame_count = 0
    ratio_history: Deque[List[float]] = deque(maxlen=max(1, args.ratio_window))
    filtered_angles: List[float] | None = None
    stable_target_angles: List[int] | None = None
    last_sent_angles: List[int] | None = None
    last_commanded_angles: List[float] = [float(value) for value in OPEN_ANGLE]
    connected = ws is not None
    open_calibration, mid_calibration, close_calibration, mid_calibration_ready, calibration_metric_match = load_pose_calibration()
    servo_profiles = load_servo_profiles()
    calibration_modes_per_servo = calibration_modes(open_calibration, mid_calibration, close_calibration)
    calibration_ready = open_calibration != default_open_ratios() or close_calibration != default_close_ratios()
    arm_active = False
    allow_send_after = 0.0
    previous_loop_time = time.perf_counter()
    pose_metric_label = "POSE 2D FALLBACK"
    selected_servo = 0
    no_send_reason = "waiting hand"
    next_reconnect_time = 0.0

    if ws is not None and args.auto_arm:
        ok, error_text = try_send_control(ws, "ARM")
        if ok:
            arm_active = True
            allow_send_after = time.perf_counter() + args.arm_settle_ms / 1000.0
        else:
            print(f"ARM failed: {error_text}")
            close_ws_quietly(ws)
            ws = None
    if ws is None:
        print("CV draft preview started. No WebSocket, no servo command. Press q to quit.")
    else:
        print("CV live sender started. Press a to ARM, q to quit.")
    if not calibration_metric_match and CALIBRATION_FILE.exists():
        print(
            "Calibration file metric is legacy and has been ignored. "
            "Capture new z/m/x poses and press s to save with the new 3D hand-local metric."
        )

    try:
        with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=args.min_detection,
            min_tracking_confidence=args.min_tracking,
        ) as hands:
            while True:
                ok, frame = camera_reader.read()
                if not ok:
                    continue

                if args.mirror:
                    frame = cv2.flip(frame, 1)

                process_frame = frame
                if args.process_width > 0 and args.process_height > 0 and (
                    frame.shape[1] != args.process_width or frame.shape[0] != args.process_height
                ):
                    process_frame = cv2.resize(frame, (args.process_width, args.process_height), interpolation=cv2.INTER_LINEAR)

                rgb = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                result = hands.process(rgb)
                now = time.perf_counter()
                if args.send and ws is None and now >= next_reconnect_time:
                    try:
                        ws = connect_ws(args.url)
                        connected = True
                        next_reconnect_time = now + 1.0
                        no_send_reason = "reconnected"
                        print("WebSocket reconnected. Press a to ARM.")
                    except RuntimeError:
                        connected = False
                        next_reconnect_time = now + 1.0
                loop_dt = max(1e-3, now - previous_loop_time)
                previous_loop_time = now
                angles: List[int] | None = None
                commanded_angles: List[int] | None = None
                commanded_angle_floats: List[float] | None = None
                close_ratios: List[float] | None = None
                raw_close_ratios: List[float] | None = None
                drive_ratios: List[float] | None = None
                no_send_reason = "waiting hand"

                if result.multi_hand_landmarks:
                    hand_landmarks = result.multi_hand_landmarks[0]
                    world_landmarks = None
                    if getattr(result, "multi_hand_world_landmarks", None):
                        world_landmarks = result.multi_hand_world_landmarks[0].landmark
                    pose_landmarks, pose_metric_label = extract_pose_landmarks(hand_landmarks.landmark, world_landmarks)
                    raw_close_ratios = landmarks_to_close_ratios(pose_landmarks)
                    close_ratios = normalize_close_ratios(raw_close_ratios, open_calibration, mid_calibration, close_calibration)
                    if args.ratio_window > 1:
                        close_ratios = median_filter_ratios(ratio_history, close_ratios, args.ratio_window)
                    if args.cv_mode == CV_MODE_DIRECT:
                        drive_ratios = direct_drive_ratios(close_ratios)
                    elif args.cv_mode == CV_MODE_SIMPLE:
                        drive_ratios = simple_drive_ratios(close_ratios)
                    else:
                        drive_ratios = tendon_drive_ratios(close_ratios, servo_profiles)
                    raw_angles = ratios_to_angles(drive_ratios)
                    stable_target_angles = stabilize_angles(stable_target_angles, raw_angles, active_target_deadband_deg)
                    filtered_angles = ema_angles(filtered_angles, stable_target_angles, args.alpha)
                    angles = [int(round(value)) for value in filtered_angles]
                    commanded_angle_floats = slew_limit_angles(last_commanded_angles, angles, args.max_deg_per_sec, loop_dt)
                    last_commanded_angles = commanded_angle_floats
                    commanded_angles = [int(round(value)) for value in commanded_angle_floats]

                    can_stream = (
                        ws is not None
                        and arm_active
                        and now >= allow_send_after
                        and now - last_send_time >= 1.0 / args.send_hz
                    )
                    angle_changed = should_send_angles(last_sent_angles, commanded_angles)
                    if can_stream and angle_changed:
                        ok, error_text = try_send_angles(ws, commanded_angles)
                        if ok:
                            last_sent_angles = commanded_angles
                            last_send_time = now
                            no_send_reason = "streaming"
                        else:
                            print(f"WebSocket send failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            arm_active = False
                            next_reconnect_time = now + 1.0
                            no_send_reason = "ws dropped"
                    elif ws is None:
                        last_sent_angles = commanded_angles
                        no_send_reason = "ws down" if args.send else "dry run"
                    elif not arm_active:
                        no_send_reason = "not armed"
                    elif now < allow_send_after:
                        no_send_reason = "arm settle"
                    elif now - last_send_time < 1.0 / args.send_hz:
                        no_send_reason = "send gate"
                    elif not angle_changed:
                        no_send_reason = "deadband"
                    else:
                        no_send_reason = "unknown gate"

                    if not args.no_preview:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                frame_count += 1
                if now - last_fps_time >= 0.5:
                    fps = frame_count / (now - last_fps_time)
                    frame_count = 0
                    last_fps_time = now

                if not args.no_preview:
                    settle_remaining_ms = max(0, int((allow_send_after - now) * 1000)) if arm_active else 0
                    draw_hud(
                        frame,
                        angles or last_sent_angles,
                        commanded_angles or last_sent_angles,
                        close_ratios,
                        raw_close_ratios,
                        drive_ratios,
                        fps,
                        connected,
                        ws is not None,
                        arm_active,
                        settle_remaining_ms,
                        args.max_deg_per_sec,
                        args.cv_mode,
                        no_send_reason,
                        open_calibration,
                        mid_calibration,
                        close_calibration,
                        pose_metric_label,
                        servo_profiles,
                        selected_servo,
                        calibration_modes_per_servo,
                        calibration_ready,
                        mid_calibration_ready,
                    )
                    cv2.imshow("Robot hand CV realtime", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        break
                    if key == ord("z") and raw_close_ratios is not None:
                        open_calibration = list(raw_close_ratios)
                        calibration_modes_per_servo = calibration_modes(open_calibration, mid_calibration, close_calibration)
                        calibration_ready = True
                        print("Captured OPEN pose calibration:", [round(value, 3) for value in open_calibration])
                    elif key == ord("m") and raw_close_ratios is not None:
                        mid_calibration = list(raw_close_ratios)
                        calibration_modes_per_servo = calibration_modes(open_calibration, mid_calibration, close_calibration)
                        calibration_ready = True
                        mid_calibration_ready = True
                        print("Captured MID pose calibration:", [round(value, 3) for value in mid_calibration])
                    elif key == ord("x") and raw_close_ratios is not None:
                        close_calibration = list(raw_close_ratios)
                        calibration_modes_per_servo = calibration_modes(open_calibration, mid_calibration, close_calibration)
                        calibration_ready = True
                        print("Captured CLOSE pose calibration:", [round(value, 3) for value in close_calibration])
                    elif key == ord("s"):
                        save_pose_calibration(open_calibration, mid_calibration, close_calibration)
                        print("Saved pose calibration to", CALIBRATION_FILE)
                    elif key == ord("p"):
                        save_servo_profiles(servo_profiles)
                        print("Saved tendon servo profile to", SERVO_PROFILE_FILE)
                    elif key == ord("r"):
                        defaults = default_servo_profiles()
                        servo_profiles[selected_servo] = sanitize_servo_profile(defaults[selected_servo], defaults[selected_servo])
                        print(f"Reset {SERVO_NAMES[selected_servo]} profile:", format_servo_profile(servo_profiles[selected_servo]))
                    elif ord("1") <= key <= ord("5"):
                        selected_servo = key - ord("1")
                        print(f"Selected {SERVO_NAMES[selected_servo]}:", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord("-"):
                        profile = dict(servo_profiles[selected_servo])
                        profile["open_deadzone"] -= 0.01
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord("="):
                        profile = dict(servo_profiles[selected_servo])
                        profile["open_deadzone"] += 0.01
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord(","):
                        profile = dict(servo_profiles[selected_servo])
                        profile["close_saturation"] -= 0.01
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord("."):
                        profile = dict(servo_profiles[selected_servo])
                        profile["close_saturation"] += 0.01
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord("["):
                        profile = dict(servo_profiles[selected_servo])
                        profile["curve"] -= 0.05
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    elif key == ord("]"):
                        profile = dict(servo_profiles[selected_servo])
                        profile["curve"] += 0.05
                        servo_profiles[selected_servo] = sanitize_servo_profile(profile, default_servo_profiles()[selected_servo])
                        print(f"{SERVO_NAMES[selected_servo]} ->", format_servo_profile(servo_profiles[selected_servo]))
                    if ws is not None and key == ord("a"):
                        ok, error_text = try_send_control(ws, "ARM")
                        if ok:
                            arm_active = True
                            allow_send_after = time.perf_counter() + args.arm_settle_ms / 1000.0
                            last_commanded_angles = [float(value) for value in OPEN_ANGLE]
                            stable_target_angles = None
                            filtered_angles = None
                            ratio_history.clear()
                            last_sent_angles = None
                        else:
                            print(f"ARM failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            next_reconnect_time = time.perf_counter() + 1.0
                    elif ws is not None and key == ord("d"):
                        ok, error_text = try_send_control(ws, "DISARM")
                        if ok:
                            arm_active = False
                        else:
                            print(f"DISARM failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            arm_active = False
                            next_reconnect_time = time.perf_counter() + 1.0
                    elif ws is not None and key == ord("o"):
                        ok, error_text = try_send_control(ws, "OPEN")
                        if not ok:
                            print(f"OPEN failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            next_reconnect_time = time.perf_counter() + 1.0
                    elif ws is not None and key == ord("c"):
                        ok, error_text = try_send_control(ws, "CLOSE")
                        if not ok:
                            print(f"CLOSE failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            next_reconnect_time = time.perf_counter() + 1.0
                    elif ws is not None and key == ord("e"):
                        ok, error_text = try_send_control(ws, "ESTOP")
                        if ok:
                            arm_active = False
                        else:
                            print(f"ESTOP failed: {error_text}")
                            close_ws_quietly(ws)
                            ws = None
                            connected = False
                            arm_active = False
                            next_reconnect_time = time.perf_counter() + 1.0
                else:
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
    finally:
        if ws is not None:
            try:
                send_control(ws, "DISARM")
            except Exception:
                pass
            close_ws_quietly(ws)
        camera_reader.stop()
        cap.release()
        cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime CV sender for ESP32 robot hand bridge.")
    parser.add_argument("--url", default=WS_URL, help="WebSocket URL, default ws://192.168.4.1:81")
    parser.add_argument("--camera", type=int, default=CAMERA_INDEX, help="OpenCV camera index")
    parser.add_argument("--width", type=int, default=FRAME_WIDTH)
    parser.add_argument("--height", type=int, default=FRAME_HEIGHT)
    parser.add_argument("--camera-fps", type=int, default=CAMERA_FPS)
    parser.add_argument("--process-width", type=int, default=PROCESS_WIDTH, help="Inference width for CV processing")
    parser.add_argument("--process-height", type=int, default=PROCESS_HEIGHT, help="Inference height for CV processing")
    parser.add_argument("--send-hz", type=float, default=SEND_HZ)
    parser.add_argument("--alpha", type=float, default=EMA_ALPHA, help="EMA alpha, higher is faster, lower is smoother")
    parser.add_argument("--min-detection", type=float, default=0.55)
    parser.add_argument("--min-tracking", type=float, default=0.55)
    parser.add_argument("--no-preview", action="store_true", help="Disable OpenCV preview window")
    parser.add_argument("--no-mirror", dest="mirror", action="store_false", help="Disable mirror view")
    parser.add_argument("--demo", action="store_true", help="Run synthetic grip demo instead of camera CV")
    parser.add_argument("--self-test", action="store_true", help="Run non-hardware checks for packet and CV mapping logic")
    parser.add_argument("--link-test", action="store_true", help="Test WebSocket and servo command path without camera CV")
    parser.add_argument("--link-test-idle-s", type=float, default=2.0, help="Idle seconds after WebSocket connect in --link-test")
    parser.add_argument("--link-test-stream-s", type=float, default=4.0, help="Streaming seconds in --link-test")
    parser.add_argument("--link-test-hz", type=float, default=5.0, help="Packet rate for streaming phase in --link-test")
    parser.add_argument("--realtime", action="store_true", help="Low-latency preset: latest-frame capture and lighter CV inference")
    parser.add_argument("--stable", action="store_true", help="Prefer steadier CV control over maximum responsiveness")
    parser.add_argument("--ratio-window", type=int, default=1, help="Median filter window for normalized finger ratios")
    parser.add_argument("--cv-mode", choices=[CV_MODE_TENDON, CV_MODE_SIMPLE, CV_MODE_DIRECT], default=CV_MODE_TENDON, help="CV to servo mapping mode")
    parser.add_argument("--send", action="store_true", help="Enable WebSocket servo command output")
    parser.add_argument("--auto-arm", action="store_true", help="Send ARM automatically when --send is enabled")
    parser.add_argument("--model-test", action="store_true", help="Safe live test preset for the real tendon-driven hand model")
    parser.add_argument("--max-deg-per-sec", type=float, default=LIVE_MAX_DEG_PER_SEC, help="Safety speed limit for live servo command")
    parser.add_argument("--arm-settle-ms", type=int, default=ARM_SETTLE_MS, help="Delay after ARM before CV commands are streamed")
    parser.set_defaults(mirror=True)
    return parser.parse_args()


if __name__ == "__main__":
    cli_args = parse_args()
    if cli_args.self_test:
        run_self_test()
    elif cli_args.link_test:
        run_link_test(cli_args)
    elif cli_args.demo:
        run_demo_loop(cli_args)
    else:
        run_cv_loop(cli_args)
