# Realtime binary protocol 9 byte / 6 servo

Packet: `[0xAA, MODE, S0, S1, S2, S3, S4, S5, XOR]`

- Byte 0: 0xAA.
- Byte 1: MODE.
- Byte 2..7: payload 6 kenh; voi GRIP dung byte 2.
- Byte 8: XOR cua byte 0..7.
- 0x01 direct, 0x02 GRIP(0..100), 0x10 ARM, 0x11 DISARM,
  0x12 software ESTOP, 0x13 OPEN, 0x14 CLOSE.

Moi thanh phan Uno, ESP32, Python, JS phai la ban 9 byte. Firmware 8 byte cu khong tuong thich.
Co the gui text `RESET` de thoat FAULT qua WebSocket text va UART; khong co mode binary RESET.
Text debug qua Uno Serial: `ARM`, `DISARM`, `ESTOP`, `RESET`, `OPEN`, `CLOSE`,
`SET <0..5> <angle>`, `GRIP <0..100>`, `PRINT`.
UART ESP32 TX17 -> Uno D0, 250000 baud. ESP32 debug USB 115200; Uno debug 250000.
Khi nhan packet, ESP32 chi xac nhan da forward UART; khong co ACK tu Uno.
