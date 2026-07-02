# Calibration khóa cứng

Calibration phần cứng cuối cùng đã được chốt như sau:

| Servo | Open | Close |
|---|---:|---:|
| S0 | 40 | 170 |
| S1 | 180 | 0 |
| S2 | 0 | 180 |
| S3 | 0 | 180 |
| S4 | 80 | 0 |

## Giá trị bắt buộc

- `OPEN_ANGLE = {40, 180, 0, 0, 80}`
- `CLOSED_ANGLE = {170, 0, 180, 180, 0}`

## Nhắc lại

- Không được tự ý đổi các giá trị này trong bất kỳ file nào.
- Mọi mapping của PC client, web client, Uno firmware và script test đều phải dùng đúng bảng này.
