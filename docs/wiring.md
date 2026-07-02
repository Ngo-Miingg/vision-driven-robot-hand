# Wiring

## UART ESP32 -> Arduino Uno

Dung dung 2 day UART/GND sau:

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
```

Khong noi them Uno TX ve ESP32 RX trong cau hinh dieu khien mot chieu nay.

## Servo signal

```text
Uno D3  -> S0 signal
Uno D5  -> S1 signal
Uno D6  -> S2 signal
Uno D9  -> S3 signal
Uno D10 -> S4 signal
```

## Nguon servo

- Dung nguon servo rieng 5V-6V du dong.
- GND nguon servo phai noi chung voi GND Uno va GND ESP32.
- Khong cap 5 servo tu chan 5V cua Uno hoac ESP32.
- Nen dat tu 1000uF-2200uF gan nguon servo de giam sut ap khi servo khoi dong.

## Luu y khi upload Uno

Neu upload Uno bi loi, rut day `ESP32 GPIO17 / TX2 -> Uno RX D0` truoc, upload xong moi cam lai.
