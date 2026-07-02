# Known Issues

## WebSocket co the rot khi stream nhanh

Trieu chung:

```text
WinError 10054
An existing connection was forcibly closed by the remote host
```

Huong xu ly:

- Nap firmware ESP32 bridge moi co `STATUS rx/fwd/drop/heap`.
- Test theo bac thang `5 Hz -> 10 Hz -> 20 Hz -> 35 Hz`.
- Neu `WS DISCONNECTED` xuat hien dung luc stream, giam `send_hz` va kiem tra nguon/ESP32.

## CV skeleton co nhieu khi anh sang kem hoac tay xoay lech

Huong xu ly:

- Dung `--stable` khi can on dinh hon.
- Chup lai calibration `z/m/x/s`.
- Dung nen sang deu, tay nam trong khung hinh.

## Voice command phu thuoc trinh duyet

Master UI hien dung Web Speech API cua browser.

Huong nang cap:

- Neu can offline/on dinh ngoai troi, nen chuyen voice engine sang Python offline nhu Vosk hoac Whisper local.

## Khong co cam bien phan hoi tu mo hinh

He hien tai gui goc servo theo lenh, nhung khong biet:

- luc kep that
- day bi chung hay khong
- ngon robot da cham vat hay chua
- servo co bi ket hay khong

Day la gioi han phan cung, khong the sua triệt de chi bang phan mem.
