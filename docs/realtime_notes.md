# Ghi chú realtime

- CV nên gửi 30-60 Hz.
- UART ESP32 -> Uno dùng 250000 baud.
- WebSocket gửi binary frame.
- ESP32 chỉ forward packet, không parse JSON.
- Uno không dùng `String`.
- Uno không `Serial.println` trong mỗi frame realtime.
- Có deadband 1 độ để giảm rung do landmark nhiễu.
- Có EMA smoothing ở PC client với `alpha = 0.35`.
- Nếu mất tín hiệu thì giữ nguyên vị trí hiện tại, không tự giật về OPEN.

## Khuyến nghị

- Khi landmark chưa đủ tin cậy, đừng gửi quá nhiều packet một lúc.
- Nên giữ logic CV ở PC hoặc browser, để ESP32 chỉ làm cầu nối UART.
- Nếu cần debug, dùng text command riêng thay vì nhét debug vào luồng realtime.
