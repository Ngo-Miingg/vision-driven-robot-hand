<div align="center">

# Vision-Driven Robot Hand

### A realtime AIoT system where human hand motion becomes live motion on a physical robotic hand

<p>
  <img src="https://img.shields.io/badge/AI-Computer%20Vision-blueviolet?style=for-the-badge" alt="AI Computer Vision" />
  <img src="https://img.shields.io/badge/Control-Realtime-success?style=for-the-badge" alt="Realtime Control" />
  <img src="https://img.shields.io/badge/Hardware-5%20Servos-red?style=for-the-badge" alt="5 Servos" />
  <img src="https://img.shields.io/badge/Embedded-ESP32%20%2B%20Arduino-orange?style=for-the-badge" alt="ESP32 and Arduino" />
</p>

<p>
  <img src="poster/robot_hand_poster_khung_final.png" alt="Vision-Driven Robot Hand Poster" width="84%" />
</p>

<p>
  <b>Camera sees.</b>
  <b>PC interprets.</b>
  <b>ESP32 relays.</b>
  <b>Arduino executes.</b>
  <b>Robot hand moves.</b>
</p>

</div>

## Project In One Sentence

`Vision-Driven Robot Hand` is a full-stack AIoT robotics project that captures human hand motion from camera input, translates it into compact control packets, and drives a real 5-servo tendon-based robotic hand in realtime.

## Why This Project Stands Out

Many vision projects stop at detection.

Many embedded projects stop at manual actuation.

This project pushes all the way through the full system chain:

- perception from live camera input
- pose-to-servo translation
- browser and PC-based operator control
- realtime packet transport
- embedded bridging
- physical actuator execution

That end-to-end continuity is what gives the project real engineering weight.

## Quick Facts

| Item | Value |
| --- | --- |
| Core idea | Human hand motion mirrored by a real robot hand |
| Realtime transport | WebSocket -> ESP32 -> UART -> Arduino Uno |
| Actuation | 5-servo tendon-driven hand |
| Input modes | Computer vision, dashboard, voice command |
| Safety model | `ARM`, `DISARM`, `ESTOP`, link-first workflow |
| Control payload | Fixed 8-byte binary packet |

## The Core Experience

This is the moment the project is built around:

```text
Your hand moves
-> the camera captures it
-> the PC interprets it
-> the ESP32 relays it
-> the Arduino executes it
-> the robot hand responds
```

That direct cause-and-effect is what makes the demo memorable.

## Full Live Pipeline

```text
Camera / Voice / Dashboard
-> PC client or browser UI
-> Binary packet (8 bytes)
-> ESP32 WebSocket bridge
-> UART2 TX2 GPIO17
-> Arduino Uno RX D0
-> 5-servo tendon-driven robot hand
```

## System Personality

This repository feels strong because it does not pretend hardware is simple.

It acknowledges that:

- communication can fail
- power can sag
- servo motion can be unstable
- browser transport is not always enough on its own
- calibration is part of the real system, not an afterthought

That is why the project includes:

- `ARM`
- `DISARM`
- `ESTOP`
- preview-before-live workflow
- link testing before CV blaming
- fixed calibration references

## What The System Can Do

| Area | Capability |
| --- | --- |
| Vision pipeline | Hand skeleton tracking, calibration, preview, realtime send |
| Hand control | Open, close, grip percentage, direct servo commands |
| Dashboard operation | Connect, arm, disarm, estop, grip, manual control |
| Voice control | Basic spoken actions for key commands |
| Communication | Compact binary control packets over WebSocket and UART |
| Verification | Link test and staged validation before live motion |

## Showcase Architecture

### 1. Perception Layer

The PC client reads camera input, tracks hand pose, previews the interpretation, and decides when live control data should be sent.

Main file:

- [`pc_client/cv_sender_template.py`](pc_client/cv_sender_template.py)

### 2. Operator Layer

The operator dashboard provides direct control when you want deterministic behavior, quick testing, or a cleaner demo flow.

Main files:

- [`web_client/master_control.html`](web_client/master_control.html)
- [`web_client/master_control_server.py`](web_client/master_control_server.py)

### 3. Transport Layer

ESP32 acts as the wireless transport bridge between high-level control and low-level serial communication.

Firmware:

- [`firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino`](firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/esp32_robot_hand_ws_bridge.ino)

### 4. Actuation Layer

Arduino Uno is the final execution node. It receives the packet, enforces runtime control state, and drives the servos.

Firmware:

- [`firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino`](firmware/arduino_uno/robot_hand_uno_realtime_final/robot_hand_uno_realtime_final.ino)

## Hardware Identity

This build uses a compact but meaningful hardware stack:

- 1 ESP32
- 1 Arduino Uno
- 1 MG90S
- 4 MG996R
- dedicated high-current servo power supply

Servo mapping:

```text
S0 thumb curl    -> Uno D3
S1 index         -> Uno D5
S2 middle        -> Uno D6
S3 ring+pinky    -> Uno D9
S4 thumb oppose  -> Uno D10
```

UART wiring:

```text
ESP32 GPIO17 / TX2 -> Uno RX D0
ESP32 GND          -> Uno GND
```

Recommended power rule:

```text
Use a dedicated 5V-6V servo PSU
Recommended minimum: 6V 10A
All grounds must be shared
```

## Locked Calibration

These values define the hand's hard reference points and must remain synchronized across firmware, PC-side logic, and dashboard control.

```text
OPEN  = {40, 180, 0,   0,   80}
CLOSE = {170, 0,   180, 180, 0}
```

## Binary Protocol

The control path is intentionally minimal and deterministic.

```text
Byte 0: 0xAA
Byte 1: mode
Byte 2..6: payload
Byte 7: XOR checksum
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

This matters because realtime actuator control benefits from:

- predictable payload size
- low parsing overhead
- easy checksum validation
- embedded-friendly transport behavior

## Demo Choreography

For the best live presentation, use this order:

1. Show the hardware and power rule.
2. Explain the communication pipeline.
3. Run the link test.
4. Open the dashboard and demonstrate direct servo control.
5. Show CV preview mode.
6. Run realtime hand mirroring.
7. End with voice commands or grip presets.

This gives the audience a clean progression from trust, to control, to intelligence.

## Quick Launch

```powershell
.\setup_python_env.bat
.\run_link_test.bat
.\run_master_control.bat
.\run_preview_cv.bat
.\run_realtime_cv.bat
```

## Why It Matters As A Portfolio Project

This is the kind of project that signals more than coding ability.

It shows you can:

- connect AI with real hardware
- think in systems, not isolated scripts
- design safety into physical control flows
- structure multi-layer architecture clearly
- build something that is both technically valid and demo-worthy

That combination is rare, and it is exactly why this project feels strong.

## Supporting Documents

- [`README.md`](README.md)
- [`QUICKSTART.md`](QUICKSTART.md)
- [`HANDOVER.md`](HANDOVER.md)
- [`HARDWARE_CHECKLIST.md`](HARDWARE_CHECKLIST.md)
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- [`docs/protocol.md`](docs/protocol.md)
- [`docs/calibration.md`](docs/calibration.md)
- [`docs/realtime_notes.md`](docs/realtime_notes.md)

## Final Impression

`Vision-Driven Robot Hand` stands out because it is not just a vision demo, not just a hardware prototype, and not just a dashboard project.

It is a complete AIoT artifact where sensing, communication, safety, and motion come together in one realtime robotic system.
