# Robot Hand 6 servo - Update D8 2026-10-15

## Pinout + endpoints

| Channel | Finger | Uno signal | OPEN | CLOSE |
|---|---|---|---:|---:|
| S0 | Thumb curl | D2 | 170 | 40 |
| S1 | Index | D3 | 180 | 0 |
| S2 | Middle | D4 | 0 | 180 |
| S3 | Ring | D5 | 0 | 180 |
| S4 | Thumb opposition | D8 | 0 | 180 |
| S5 | Pinky | D7 | 180 | 0 |

**Latest D8: OPEN 0, CLOSE 180 (confirmed by manual testing). S0 reverse from the earlier endpoints (170 OPEN, 40 CLOSE).**

- Uno main: `firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino`.
- Calibration mapping: Uno `Config.cpp`.
- ESP32 main: `firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino`.
- Protocol: `docs/protocol.md`; nine-byte packet on both firmware and PC.
- Dashboard: `web_client/master_control.html`, API `web_client/master_control_server.py`.
- PC camera: `pc_client/cv_sender_template.py`; web camera: `web_client/realtime_cv_preview.html`.
- Voice: `web_client/offline_voice_engine.py`.
- Docker optional: `docker_up.bat`, `compose.yaml` (Docker Desktop required).
- `firmware/models/` holds offline Vosk models; browser MediaPipe assets are in `web_client/vendor`.

## Deploy

1. Turn off external servo power and remove ESP32 TX17 -> Uno D0 wire before uploading Uno.
2. Upload *the new Uno 9-byte sketch* and reconnect wire after power down.
3. Upload *the new ESP32 9-byte sketch* (requires WebSockets by Markus Sattler).
4. Start server via `run_master_control.bat` or Docker `docker_up.bat`. Connect PC to RobotHand_ESP32 Wi-Fi (password 12345678). ESP32 endpoint ws://192.168.4.1:81.
5. Confirm API GET /api/packet-test: every sample must contain 9 bytes. ARM only after mechanism and servo power safely prepared.
6. Test OPEN/GRIP at low load before executing any gesture or CV stream.

## Limitations

This release was programmatically rebuilt from the available original ZIP (older five-servo source), migrated to six channels, and modularized. It is **not** a byte-identical patch of a prior modular archive that was unavailable in this work session.
Software-ESTOP detaches servo signals but does not cut motor power; there is no physical ESTOP power circuit. UART feedback is one-way; dashboard status cannot prove actual Uno state. CV S5 calibration values are provisional and should be captured against real hand landmarks.
No claims of real-board verified flash/physical movement are made.
