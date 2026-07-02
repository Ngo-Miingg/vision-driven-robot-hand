# Vision-Driven Robot Hand

Real-time robotic hand control with computer vision, voice commands, ESP32, Arduino Uno, WebSocket, and a tendon-driven 5-servo hand.

## Why This Project Stands Out

- Real hardware control, not just simulation
- Live computer vision to map human hand motion to robot finger motion
- Master dashboard for direct servo control, camera preview, and voice command
- Layered architecture so each part can be tested independently
- Safety-first workflow with ARM, DISARM, ESTOP, link test, and dry-run preview

## What It Can Do

| Module | Current capability |
| --- | --- |
| Servo hand | Open, close, grip, direct servo angles, hold pose |
| Computer vision | Skeleton tracking, calibration, preview, realtime control send |
| Voice control | Basic command phrases such as open hand, close hand, arm, disarm, estop |
| Web dashboard | Connect, arm/disarm, grip slider, direct servo sliders, camera preview |
| Communication | Binary 8-byte packet over WebSocket -> ESP32 -> UART -> Uno |
| Debugging | Link test, packet test, protocol reference, software verification scripts |

## System Flow

```text
Camera / Voice / Dashboard
-> PC client or browser UI
-> Binary packet
-> ESP32 WebSocket bridge
-> UART2 TX2 GPIO17
-> Arduino Uno RX D0
-> 5-servo tendon-driven robot hand
```

## Hardware Used

- 1 ESP32
- 1 Arduino Uno
- 1 MG90S
- 4 MG996R

### Servo Mapping

```text
S0 thumb curl    -> Uno D3
S1 index         -> Uno D5
S2 middle        -> Uno D6
S3 ring+pinky    -> Uno D9
S4 thumb oppose  -> Uno D10
```

### UART Wiring

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
```

One-way control only, so Uno TX does not need to return to ESP32 RX in this setup.

### Servo Power Rule

- Use a dedicated 5V-6V servo power supply
- For 4 MG996R + 1 MG90S, target at least 6V 10A
- All grounds must be common: servo PSU, Uno, and ESP32
- Do not power all servos directly from Uno or ESP32 5V

## Locked Calibration

These angles are hardware-locked and must stay consistent across firmware, PC client, and dashboard:

```text
OPEN  = {40, 180, 0,   0,   80}
CLOSE = {170, 0,   180, 180, 0}
```

Meaning:

- `S0`: 40 -> 170
- `S1`: 180 -> 0
- `S2`: 0 -> 180
- `S3`: 0 -> 180
- `S4`: 80 -> 0

## Quick Start

### 1. Clone and setup

```powershell
git clone https://github.com/Ngo-Miingg/vision-driven-robot-hand.git
cd vision-driven-robot-hand
.\setup_python_env.bat
```

### 2. Flash firmware

- Arduino Uno:
  [firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino](firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino)
- ESP32 bridge:
  [firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino](firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino)

### 3. Test communication first

```powershell
.\run_link_test.bat
```

### 4. Run what you need

```powershell
.\run_master_control.bat
.\run_preview_cv.bat
.\run_realtime_cv.bat
```

## Main Operating Modes

### Master dashboard

Use this for the most complete control workflow:

- Web control panel
- ARM / DISARM / ESTOP
- Grip presets and direct servo sliders
- Voice command panel
- Realtime local camera preview

Run:

```powershell
.\run_master_control.bat
```

### CV preview only

Use this when calibrating or checking skeleton quality without moving hardware.

```powershell
.\run_preview_cv.bat
```

### CV realtime control

Use this when the link test already passes and you want live hand-to-hand control.

```powershell
.\run_realtime_cv.bat
```

### Link test

Use this before blaming CV, dashboard, or firmware. It checks the transport path directly.

```powershell
.\run_link_test.bat
```

## Software Architecture

### Arduino Uno layer

- Final actuator layer
- Receives 8-byte binary packets from ESP32
- Handles `DISARMED`, `ARMED`, and safety behavior
- Executes `OPEN`, `CLOSE`, `GRIP`, `DIRECT`, `DISARM`, `ESTOP`

### ESP32 layer

- Creates AP `RobotHand_ESP32`
- Hosts WebSocket server on port `81`
- Verifies packet framing and checksum
- Forwards packets to Uno through `Serial2`

### PC layer

- [pc_client/cv_sender_template.py](pc_client/cv_sender_template.py):
  CV preview, pose calibration, realtime send, dry-run and model-test flow
- [web_client/master_control.html](web_client/master_control.html):
  operator dashboard
- [web_client/master_control_server.py](web_client/master_control_server.py):
  local bridge server for browser-safe control to ESP32

## Communication Protocol

Realtime control uses a fixed binary packet, not JSON.

```text
Byte 0: 0xAA
Byte 1: mode
Byte 2..6: payload
Byte 7: XOR checksum of byte 0..6
```

Modes:

```text
0x01 = direct angles
0x02 = grip percent
0x10 = ARM
0x11 = DISARM
0x12 = ESTOP
0x13 = OPEN
0x14 = CLOSE
```

More detail:

- [docs/protocol.md](docs/protocol.md)
- [tools/make_packet_reference.py](tools/make_packet_reference.py)

## Project Layout

```text
vision-driven-robot-hand/
|-- firmware/      Arduino Uno and ESP32 firmware
|-- pc_client/     CV sender, calibration, protocol-side tests
|-- web_client/    dashboard UI and local control bridge
|-- docs/          wiring, calibration, protocol, realtime notes
|-- scripts/       verify and release build scripts
|-- tools/         protocol helpers and angle notes
|-- QUICKSTART.md
|-- HANDOVER.md
|-- HARDWARE_CHECKLIST.md
`-- README.md
```

## Important Files

- [QUICKSTART.md](QUICKSTART.md):
  fastest setup path
- [HANDOVER.md](HANDOVER.md):
  handoff notes for another developer or demo operator
- [HARDWARE_CHECKLIST.md](HARDWARE_CHECKLIST.md):
  power and wiring sanity check
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md):
  practical failure cases already seen in testing
- [docs/calibration.md](docs/calibration.md):
  CV calibration notes
- [docs/wiring.md](docs/wiring.md):
  hardware wiring summary
- [docs/realtime_notes.md](docs/realtime_notes.md):
  realtime behavior and tuning notes

## Verification and Release

Run verification:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_project.ps1
```

Build a handover package:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_release.ps1
```

## Current Limitations

- CV tracking still depends on lighting, hand orientation, and camera quality
- Tendon-driven fingers do not behave like rigid joint robots, so angle mapping needs calibration care
- Servo speed, grip force, and smoothness are constrained by power delivery and mechanical friction
- Browser dashboard depends on the local Python bridge for reliable ESP32 communication

## Suggested Demo Order

For the best first impression:

1. Show hardware wiring and power setup
2. Run link test
3. Open master dashboard
4. Show direct servo control
5. Show CV preview
6. Show CV realtime
7. Show voice command

## License

No license has been added yet.
