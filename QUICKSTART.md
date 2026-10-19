# QUICKSTART - 6 servo S4 D8 (2026-10-15)

Doc `README_6SERVO_D8_UPDATE.md` va `docs/wiring.md` truoc khi cap nguon.

1. Tat nguon servo, thao GPIO17 -> Uno RX/D0. Mo `firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino` trong Arduino IDE; nap day du nhom file .cpp/.h. Uno duoc dieu khien 6 servo bang packet9.
2. Mo `firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino`; nap ESP32 voi thu vien WebSockets by Markus Sattler. ESP32 115200, Uno 250000.
3. Tat nguon, noi lai ESP32 TX2/GPIO17 -> Uno D0/RX. Noi chung GND. Nguon servo 5-6V rieng va du dong.
4. Ket noi PC Wi-Fi RobotHand_ESP32 / 12345678. `Test-NetConnection 192.168.4.1 -Port 81` phai True.
5. Khoi dong dashboard bang `run_master_control.bat` (setup Python truoc) hoac `docker_up.bat` tren Docker Desktop.
6. Mo http://127.0.0.1:8080/master_control.html, nhan Connect. Kiem tra http://127.0.0.1:8080/api/packet-test -> 9 byte/packet.
7. Kiem tra moi co cau an toan, ARM, gui OPEN roi GRIP khoang nho, quan sat ESP32 rx/fwd tang.

Luu y: software ESTOP chi detach PWM, khong cat nguon servo, va khong co ACK tu Uno. D8 da chuyen sang servo S4, khong phai ESTOP. Khi chay code moi, khong dung cac firmware 8 byte cu.
