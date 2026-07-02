# Robot Hand Realtime - Handover

## Muc tieu

Du an dieu khien ban tay robot 5 servo theo thoi gian thuc:

```text
Camera / UI / Voice
-> PC Python hoac Web dashboard
-> WebSocket binary 8 byte
-> ESP32 bridge
-> UART2 GPIO17/TX2
-> Arduino Uno RX D0
-> 5 servo
```

## Phan cung

- 1 ESP32.
- 1 Arduino Uno.
- 1 MG90S.
- 4 MG996R.
- Nguon servo rieng 5V-6V du dong, khuyen nghi toi thieu 6V 10A.
- GND servo, GND Uno va GND ESP32 phai noi chung.

## Calibration khong duoc doi

```text
OPEN  = 40,180,0,0,80
CLOSE = 170,0,180,180,0
```

Servo mapping:

```text
S0 thumb curl    -> Uno D3
S1 index         -> Uno D5
S2 middle        -> Uno D6
S3 ring+pinky    -> Uno D9
S4 thumb oppose  -> Uno D10
```

UART:

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
Baud               -> 250000
```

## Thu tu chay nhanh

1. Nap firmware Uno.
2. Nap firmware ESP32.
3. Ket noi PC vao Wi-Fi `RobotHand_ESP32`.
4. Chay link test:

```powershell
.\run_link_test.bat
```

5. Chay dashboard master:

```powershell
.\run_master_control.bat
```

6. Chay CV realtime:

```powershell
.\run_realtime_cv.bat
```

## File quan trong

- `firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino`
- `firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino`
- `pc_client/cv_sender_template.py`
- `web_client/master_control.html`
- `web_client/master_control_server.py`
- `docs/wiring.md`
- `docs/protocol.md`
- `docs/calibration.md`

## Trang thai hien tai

- Manual command va link test da co.
- CV realtime da co cac mode `direct`, `simple`, `tendon`, `stable`.
- Master UI co camera preview, voice command va HTTP API bridge.
- ESP32 bridge da co packet counter/log de debug WebSocket.

## Luu y khi demo

- Neu upload Uno loi, rut day `ESP32 TX2 -> Uno RX D0`, upload xong cam lai.
- Neu UI khong dieu khien duoc, xem o Master UI dong WebSocket phai la `Online`.
- Trong Master UI, o ket noi mac dinh la `/api/send`, khong phai IP ESP32.
- Neu WebSocket rut khi stream, xem Serial Monitor ESP32 o `115200` de doc `STATUS rx=... fwd=... drop_... heap=...`.
