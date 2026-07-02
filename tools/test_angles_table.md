# Bảng test góc

## Calibration

- OPEN = `40,180,0,0,80`
- CLOSE = `170,0,180,180,0`

## GRIP 50

- GRIP 50 là phép tính trung gian từ OPEN sang CLOSE với tỷ lệ 50%.

## Lệnh test Serial text

```text
ARM
OPEN
CLOSE
GRIP 50
SET 0 40
SET 0 170
SET 4 80
SET 4 0
```

## Gợi ý kiểm tra nhanh

- `ARM` rồi kiểm tra servo có attach không.
- `OPEN` và `CLOSE` để xác nhận mapping phần cứng cuối cùng.
- `GRIP 50` để xem trạng thái trung gian.
- `SET` để test từng servo theo từng góc riêng lẻ.
