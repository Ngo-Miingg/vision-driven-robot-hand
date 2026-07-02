# Robot Hand Realtime AIoT

## Abstract

Du an nay xay dung mot he thong dieu khien ban tay robot 5 servo theo thoi gian thuc, trong do PC xu ly giao dien, computer vision va voice command, ESP32 dong vai tro WebSocket bridge, va Arduino Uno dieu khien co cau servo cuoi cung.

Luong tong quat:

```text
Camera / Voice / Dashboard / CV
-> PC client hoac browser dashboard
-> Binary packet 8 byte
-> ESP32 WebSocket bridge
-> UART2 GPIO17 / TX2
-> Arduino Uno RX D0
-> 5 servo
```

Muc tieu cua repository:

- Giu nguyen calibration servo da khoa cung.
- Tach ro tung lop he thong: UI/CV, ESP32 bridge, Uno actuator.
- Ho tro test tung lop rieng de debug nhanh.
- Cho phep ban giao code cho nguoi khac theo quy trinh co the lap lai.

## Quick Start

Neu moi keo code ve, doc lan luot:

```text
QUICKSTART.md
HANDOVER.md
HARDWARE_CHECKLIST.md
KNOWN_ISSUES.md
```

Lenh nhanh tu thu muc goc:

```powershell
.\setup_python_env.bat
.\run_link_test.bat
.\run_master_control.bat
.\run_preview_cv.bat
.\run_realtime_cv.bat
```

Script verify truoc khi ban giao hoac demo:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_project.ps1
```

## System Architecture

### 1. Arduino Uno layer

Uno la lop actuator cuoi cung:

- Nhan packet binary 8 byte tu ESP32 qua UART.
- Duy tri state machine `DISARMED`, `ARMED`, `FAULT`.
- Chi attach servo sau lenh `ARM`.
- Ho tro `OPEN`, `CLOSE`, `GRIP`, `DIRECT`, `DISARM`, `ESTOP`.
- Giu nguyen vi tri khi mat tin hieu, khong auto mo tay.

Firmware:

```text
firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino
```

### 2. ESP32 layer

ESP32 dong vai tro bridge:

- Tao Access Point `RobotHand_ESP32`.
- Mo WebSocket server cong `81`.
- Nhan binary frame tu PC/browser.
- Kiem tra start byte va checksum.
- Forward nguyen packet sang Uno qua `Serial2`.

Firmware:

```text
firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino
```

### 3. PC layer

PC co 3 nhom thanh phan:

- `pc_client/cv_sender_template.py`: preview CV, calibration skeleton, CV realtime send.
- `pc_client/websocket_test.py` va `serial_direct_test.py`: test tung lop giao tiep.
- `web_client/master_control.html` + `master_control_server.py`: dashboard master co camera preview, voice command va local HTTP API bridge.

## Hardware Configuration

Phan cung dang duoc nham den:

- 1 ESP32
- 1 Arduino Uno
- 1 MG90S
- 4 MG996R

### Servo mapping

```text
S0 thumb curl    -> Uno D3
S1 index         -> Uno D5
S2 middle        -> Uno D6
S3 ring+pinky    -> Uno D9
S4 thumb oppose  -> Uno D10
```

### UART wiring

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
```

Khong can noi Uno TX ve ESP32 RX trong cau hinh dieu khien mot chieu nay.

### Servo power

- Dung nguon servo rieng 5V-6V du dong.
- Voi 4 MG996R + 1 MG90S, khuyen nghi toi thieu 6V 10A.
- GND nguon servo phai noi chung voi GND Uno va GND ESP32.
- Khong cap 5 servo tu chan 5V cua Uno hoac ESP32.
- Nen dat tu 2200uF-4700uF gan cum servo.

## Calibration Lock

Calibration nay la rang buoc phan cung va khong duoc thay doi tuy y:

```text
OPEN_ANGLE   = {40, 180, 0,   0,   80}
CLOSED_ANGLE = {170, 0,   180, 180, 0}
```

Y nghia:

- `S0`: 40 -> 170
- `S1`: 180 -> 0
- `S2`: 0 -> 180
- `S3`: 0 -> 180
- `S4`: 80 -> 0

Tat ca lop phai dong bo gia tri nay:

- Uno firmware
- PC CV client
- Web dashboard
- Tool test packet

## Binary Protocol

Realtime khong dung JSON.

Packet co do dai co dinh 8 byte:

```text
Byte 0: 0xAA
Byte 1: mode
Byte 2..6: payload
Byte 7: checksum XOR cua byte 0..6
```

Mode:

```text
0x01 = direct angles (S0..S4)
0x02 = grip percent
0x10 = ARM
0x11 = DISARM
0x12 = ESTOP
0x13 = OPEN
0x14 = CLOSE
```

Packet reference:

```text
tools/make_packet_reference.py
docs/protocol.md
```

## Repository Layout

```text
robot_hand_realtime/
|-- README.md
|-- QUICKSTART.md
|-- HANDOVER.md
|-- HARDWARE_CHECKLIST.md
|-- KNOWN_ISSUES.md
|-- RELEASE_CHECKLIST.md
|-- requirements.txt
|-- setup_python_env.bat
|-- run_link_test.bat
|-- run_preview_cv.bat
|-- run_realtime_cv.bat
|-- run_master_control.bat
|-- docs/
|-- firmware/
|-- pc_client/
|-- web_client/
|-- tools/
`-- scripts/
```

## Environment Setup

### Python

Script setup chinh thuc:

```powershell
.\setup_python_env.bat
```

Script nay:

- Tao `.venv` neu chua co.
- Nang cap `pip`.
- Cai dependency tu `requirements.txt`.

Root requirements hien tai tro den:

```text
pc_client/requirements.txt
```

### Python dependencies

Dependency dang dung:

```text
websocket-client
opencv-contrib-python==4.10.0.84
mediapipe==0.10.9
numpy<2
pyserial
```

## Firmware Upload

### Arduino Uno

1. Mo file:

```text
firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino
```

2. Chon board `Arduino Uno`.
3. Chon cong COM dung.
4. Upload sketch.
5. Neu upload loi sync, rut day `ESP32 TX2 -> Uno RX D0`, upload xong moi cam lai.

### ESP32

1. Mo file:

```text
firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino
```

2. Chon board ESP32 phu hop.
3. Upload sketch.
4. Mo Serial Monitor `115200`.

Log can thay:

```text
ESP32 WS BRIDGE READY
AP SSID: RobotHand_ESP32
AP IP: 192.168.4.1
WS PORT: 81
UART2 TX: GPIO17
UART BAUD: 250000
STATUS clients=...
```

## Operating Modes

### 1. Link test

Test tung duong PC -> ESP32 -> Uno ma khong dung camera:

```powershell
.\run_link_test.bat
```

Hoac:

```powershell
cd pc_client
python cv_sender_template.py --link-test
```

Ban test nay gui:

- `ARM`
- `OPEN`
- `MID`
- `CLOSE`
- stream direct packet theo song sin

### 2. CV preview only

Che do an toan, khong gui lenh servo:

```powershell
.\run_preview_cv.bat
```

Hoac:

```powershell
cd pc_client
python cv_sender_template.py
```

Man hinh hien:

- skeleton hand
- raw ratio
- normalized ratio
- target/send angle
- calibration mode
- tendon profile

### 3. CV realtime

Preset cho mo hinh that:

```powershell
.\run_realtime_cv.bat
```

Lenh tuong duong:

```powershell
cd pc_client
python cv_sender_template.py --model-test --realtime --cv-mode direct
```

Hien tai, `--model-test` se dat:

- `--send`
- `max_deg_per_sec = 360`
- `arm_settle_ms = 500`
- `alpha = 0.90`

`--realtime` se dat:

- latest-frame camera reader
- process frame nho hon
- `send_hz = 35`
- target deadband nho hon

Neu uu tien on dinh hon:

```powershell
python cv_sender_template.py --model-test --realtime --stable --cv-mode direct
```

### 4. Master dashboard

Dashboard tong hop:

```powershell
.\run_master_control.bat
```

Ban nay mo:

- `web_client/master_control.html`
- `web_client/master_control_server.py`

Dashboard cung cap:

- camera preview realtime
- manual command
- direct servo slider
- grip slider
- voice command
- local HTTP API bridge

Duong di cua dashboard:

```text
Browser -> /api/send -> Python server -> ws://192.168.4.1:81 -> ESP32
```

Dashboard khong can browser noi WebSocket truc tiep toi ESP32 nua.

## CV Calibration Workflow

Trong cua so CV:

```text
z = chup moc tay mo het
m = chup moc tay nam nua chung
x = chup moc tay gap het
s = luu calibration
```

Quy trinh:

1. Mo tay het muc, bam `z`
2. Nam tay vua phai, bam `m`
3. Gap tay het muc, bam `x`
4. Bam `s`
5. Kiem tra cot `norm`, `raw`, `target/send`

File du lieu:

```text
pc_client/hand_pose_calibration.json
pc_client/servo_tendon_profile.json
```

## Verification Pipeline

### Software verification

Chay verify script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_project.ps1
```

Script nay:

- chay `cv_sender_template.py --self-test`
- py_compile cho `master_control_server.py`
- syntax-check JavaScript trong `master_control.html`

### Packet verification

Dashboard server co endpoint:

```text
/api/packet-test
```

Dung de kiem tra packet `ARM`, `OPEN`, `MID`, `CLOSE` ma khong can dong den servo.

### WebSocket stability ladder

Sau khi nap firmware ESP32 moi, test theo bac thang:

```powershell
cd pc_client
python cv_sender_template.py --link-test --link-test-hz 5  --link-test-stream-s 10
python cv_sender_template.py --link-test --link-test-hz 10 --link-test-stream-s 10
python cv_sender_template.py --link-test --link-test-hz 20 --link-test-stream-s 10
python cv_sender_template.py --link-test --link-test-hz 35 --link-test-stream-s 10
```

Dong thoi xem Serial Monitor ESP32:

```text
STATUS clients=... active=... rx=... fwd=... drop_len=... drop_start=... drop_sum=... heap=...
```

Giai thich:

- `rx` tang: ESP32 nhan packet
- `fwd` tang: packet hop le va da forward
- `drop_len` tang: do dai packet sai
- `drop_start` tang: start byte sai
- `drop_sum` tang: checksum sai

## Troubleshooting

### 1. Uno upload fail

Trieu chung:

```text
not in sync
unable to open port
```

Xu ly:

- Rut day `ESP32 TX2 -> Uno RX D0`
- Upload lai Uno
- Cam lai day sau khi xong

### 2. Python ket noi duoc, dashboard khong dieu khien duoc

Xu ly:

- Dung `run_master_control.bat`
- O dashboard, field ket noi mac dinh phai la `/api/send`
- Bam `Connect`
- Kiem tra console cua `master_control_server.py`

### 3. WebSocket bi `10054`

Trieu chung:

```text
An existing connection was forcibly closed by the remote host
```

Xu ly:

- Kiem tra nguon servo
- Giam `send_hz`
- Chay ladder test
- Xem log `WS DISCONNECTED`
- Xem `drop_*` va `heap` tren ESP32

### 4. Tay dung yen nhung mo hinh van nhay

Xu ly:

- Chay them `--stable`
- Chup lai calibration `z/m/x/s`
- Giam `alpha` neu can
- Tang chat luong anh va anh sang

### 5. Camera dashboard khong hien

Xu ly:

- Bam `Cam ON`
- Cap quyen webcam cho browser
- Thu `Refresh`
- Chon camera khac trong dropdown

### 6. Voice command nhan sai

Xu ly:

- Bam `Cal Noise` trong dashboard khi moi truong dang im
- Bat `Wake word`
- Dung mic gan hon
- Neu can on dinh hon nua, doi sang voice engine offline trong Python

## Release and Handover

Build release bang script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_release.ps1
```

Release sinh ra tai:

```text
release\
```

Goi release da duoc loai:

- `.venv`
- `__pycache__`
- `.pyc`
- log file
- zip long nhau

Checklist ban giao:

```text
RELEASE_CHECKLIST.md
HANDOVER.md
HARDWARE_CHECKLIST.md
KNOWN_ISSUES.md
```

## Important Files

- `firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino`
- `firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino`
- `pc_client/cv_sender_template.py`
- `web_client/master_control.html`
- `web_client/master_control_server.py`
- `docs/wiring.md`
- `docs/protocol.md`
- `docs/calibration.md`

## Current Limitations

- He thong chua co cam bien phan hoi tu mo hinh.
- Khong biet luc kep that, do chung day hoac servo ket chi bang software.
- Voice tren dashboard hien tai dua tren browser API, chua phai offline engine.
- WebSocket voi ESP32 da co log/bridge/verification tot hon, nhung van phu thuoc nguon va do on dinh cua ESP32 khi stream.

## Citation-style Summary

Neu xem repository nay nhu mot prototype nghien cuu, dong gop hien tai la:

- Mot luong realtime ro rang tu PC den robot hand 5 servo.
- Protocol binary co dinh 8 byte, de debug va reproducible.
- CV client co calibration 3 moc va retargeting sang servo theo calibration khoa cung.
- Dashboard co local control API bridge, camera preview va voice command.
- Release pipeline co the lap lai de ban giao cho nguoi khac ma khong keo theo moi truong tam.
