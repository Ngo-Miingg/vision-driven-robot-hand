# So do noi day (6 servo, firmware 2026-10-15)

| Servo | Co cau | Chan Uno | MO | NAM |
|---|---|---|---:|---:|
| S0 | Ngon cai gap | D2 | 170 | 40 |
| S1 | Ngon tro | D3 | 180 | 0 |
| S2 | Ngon giua | D4 | 0 | 180 |
| S3 | Ngon ap ut | D5 | 0 | 180 |
| S4 | Ngon cai doi chieu | **D8** | **0** | **180** |
| S5 | Ngon ut | D7 | 180 | 0 |

ESP32 TX2 GPIO17 -> Uno D0/RX. GND ESP32, Uno, nguon servo phai noi chung.
Khong noi Uno TX/D1 5V truc tiep vao ESP32 RX 3.3V. Khong co nut ESTOP vat ly o D8;
D8 bay gio la signal S4. D6 khong su dung. Nguon servo 5-6V rieng du dong,
khong lay 6 servo tu chan 5V cua Uno.

Khi nap sketch Uno: thao GPIO17 -> Uno D0. Sau khi nap, tat nguon roi noi lai.
Thoat khoi bai test de nap firmware realtime moi; can nap cap firmware Uno va ESP32 moi.

Luu y: ESTOP tren phan mem chi detach PWM, KHONG cat nguon servo; timeout UART 800ms chua cat nguon hay dua ve goc an toan. Moi lan ARM co the nhay goc hien tai.
