# Quickstart

Huong dan nay danh cho nguoi moi keo code ve va muon chay du an nhanh nhat.

## 1. Chuan bi

- Windows 10/11.
- Python 3.10 hoac 3.11.
- Arduino IDE.
- Arduino Uno.
- ESP32.
- Nguon servo rieng 5V-6V du dong.

## 2. Cai moi truong Python

Tai thu muc goc du an:

```powershell
.\setup_python_env.bat
```

Script nay se tao `.venv` va cai cac goi trong `pc_client/requirements.txt`.

## 3. Nap firmware

Nap Uno:

```text
firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino
```

Neu upload Uno bi loi sync, rut day `ESP32 TX2 -> Uno RX D0`, upload xong cam lai.

Nap ESP32:

```text
firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino
```

Mo Serial Monitor ESP32 `115200`, can thay:

```text
ESP32 WS BRIDGE READY
AP SSID: RobotHand_ESP32
AP IP: 192.168.4.1
WS PORT: 81
```

## 4. Ket noi Wi-Fi

Ket noi PC vao:

```text
SSID: RobotHand_ESP32
Pass: 12345678
```

## 5. Test link khong dung camera

```powershell
.\run_link_test.bat
```

Neu test nay khong qua, chua nen chay CV.

## 6. Chay dashboard master

```powershell
.\run_master_control.bat
```

Tren UI:

```text
Connect -> ARM -> OPEN/CLOSE/GRIP
```

O ket noi mac dinh phai la:

```text
/api/send
```

## 7. Chay CV preview

```powershell
.\run_preview_cv.bat
```

Day la che do an toan, khong gui lenh servo.

## 8. Chay CV realtime tren mo hinh

```powershell
.\run_realtime_cv.bat
```

Trong cua so camera, bam `a` de ARM.

## 9. File can doc khi ban giao

- `HANDOVER.md`
- `HARDWARE_CHECKLIST.md`
- `KNOWN_ISSUES.md`
- `docs/wiring.md`
- `docs/protocol.md`
- `docs/calibration.md`
