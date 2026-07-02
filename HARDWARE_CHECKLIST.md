# Hardware Checklist

## Truoc khi cap nguon

- Servo dung nguon rieng 5V-6V du dong.
- Khuyen nghi nguon servo toi thieu 6V 10A cho 4 MG996R + 1 MG90S.
- GND nguon servo noi chung voi GND Uno va GND ESP32.
- Khong cap 5 servo tu chan 5V cua Uno hoac ESP32.
- Nen co tu 2200uF-4700uF gan cum servo.

## Day tin hieu

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
```

Khong noi Uno TX ve ESP32 RX trong cau hinh mot chieu.

## Servo signal

```text
Uno D3  -> S0 thumb curl
Uno D5  -> S1 index
Uno D6  -> S2 middle
Uno D9  -> S3 ring+pinky
Uno D10 -> S4 thumb oppose
```

## Upload

- Upload Uno: rut day `ESP32 TX2 -> Uno RX D0` neu gap loi sync.
- Upload ESP32: Serial Monitor `115200`.
- Uno baud realtime: `250000`.
- ESP32 UART2 baud: `250000`.

## Log can thay tren ESP32

```text
ESP32 WS BRIDGE READY
AP SSID: RobotHand_ESP32
AP IP: 192.168.4.1
WS PORT: 81
UART2 TX: GPIO17
UART BAUD: 250000
STATUS clients=...
```

## Test sau khi lap

```powershell
.\run_link_test.bat
```

Test theo bac thang:

```powershell
cd pc_client
python cv_sender_template.py --link-test --link-test-hz 5  --link-test-stream-s 10
python cv_sender_template.py --link-test --link-test-hz 10 --link-test-stream-s 10
python cv_sender_template.py --link-test --link-test-hz 20 --link-test-stream-s 10
```
