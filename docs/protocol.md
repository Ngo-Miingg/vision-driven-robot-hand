# Binary protocol 8 byte

Realtime dùng binary packet cố định 8 byte, không dùng JSON và không dùng text command.
Text chỉ phục vụ debug.

## Cấu trúc packet

- Byte 0: `0xAA`
- Byte 1: `mode`
- Byte 2..6: dữ liệu theo mode
- Byte 7: checksum XOR của byte 0..6

## Mode

- `0x01` = direct angles, byte 2..6 là `S0..S4`
- `0x02` = grip percent, byte 2 là `0..100`
- `0x10` = ARM
- `0x11` = DISARM
- `0x12` = ESTOP
- `0x13` = OPEN
- `0x14` = CLOSE

## Checksum

Checksum được tính bằng XOR lần lượt toàn bộ byte từ 0 đến 6.

```text
checksum = byte0 ^ byte1 ^ byte2 ^ byte3 ^ byte4 ^ byte5 ^ byte6
```

## Ghi chú

- ESP32 chỉ kiểm tra start byte và checksum rồi forward nguyên packet sang Uno.
- Uno không parse JSON.
- Uno không dùng text cho realtime.
- Text command chỉ dành cho debug hoặc test thủ công.
