> HISTORICAL NOTE: Some content below reflects the older five-servo system. Current pinout and firmware: [README_6SERVO_D8_UPDATE.md](README_6SERVO_D8_UPDATE.md).

<div align="center">

# Vision-Driven Robot Hand

### A realtime AIoT robotic-hand system that feels like a complete product demo, not just a codebase

<p>
  <img src="https://img.shields.io/badge/AI-Computer%20Vision-blueviolet?style=for-the-badge" alt="AI Computer Vision" />
  <img src="https://img.shields.io/badge/Control-Realtime-success?style=for-the-badge" alt="Realtime Control" />
  <img src="https://img.shields.io/badge/Embedded-ESP32%20%2B%20Arduino-orange?style=for-the-badge" alt="Embedded" />
  <img src="https://img.shields.io/badge/Hardware-5%20Servos-red?style=for-the-badge" alt="5 Servos" />
</p>

<p>
  <a href="web_poster/poster_full_vector.pdf">
    <img src="reports/assets/robot_hand_model_real.png" alt="Vision-Driven Robot Hand Real Build" width="84%" />
  </a>
</p>

<p>
  <b>Perception.</b>
  <b>Transport.</b>
  <b>Embedded control.</b>
  <b>Physical motion.</b>
</p>

</div>

## Project Statement

This project is built around one simple but compelling promise:

**a human hand moves, a robot hand responds, and the whole path from vision to actuation is visible, testable, and real.**

## Why It Feels More Serious Than A Typical Student Project

Many repositories can show a model prediction.

Many hardware demos can move a servo.

This one does both and connects the layers between them:

- camera input
- hand interpretation
- packetized transport
- WebSocket to UART bridging
- actuator execution
- safety-aware operation

That full-system continuity is the main strength of the project.

## Showcase Stack

| Dimension | What it proves |
| --- | --- |
| Real build | This is a physical robotic hand, not a simulated idea |
| Embedded path | ESP32 and Arduino are integrated into the control chain |
| Operator tooling | A dashboard exists for controlled live use |
| Safety layer | The system respects disarm, estop, and preflight testing |
| Technical depth | Wiring, protocol, architecture, CV, and state behavior are documented visually |

## Official Poster

- [`web_poster/poster_full_vector.pdf`](web_poster/poster_full_vector.pdf)

The project poster is now carried as a vector PDF so it can serve both as a presentation asset and as a polished companion to the repository.

## Visual Core

| Real Robot Hand | Dashboard |
| --- | --- |
| <img src="reports/assets/robot_hand_model_real.png" alt="Real Robot Hand" width="100%" /> | <img src="poster/dashboard_capture_hd.png" alt="Dashboard Demo" width="100%" /> |

| Architecture | Wiring |
| --- | --- |
| <img src="reports/assets/fig_03_system_architecture.png" alt="System Architecture" width="100%" /> | <img src="reports/assets/fig_04_hardware_wiring.png" alt="Hardware Wiring" width="100%" /> |

These visuals make the project instantly more trustworthy because they answer two key questions fast:

- is the hardware real?
- is the system architecture actually thought through?

## The Core Demo Moment

```text
Your hand moves
-> the camera sees it
-> the PC interprets it
-> the ESP32 relays it
-> the Arduino executes it
-> the robot hand mirrors it
```

That is the emotional center of the entire repository.

## Live Control Pipeline

```text
Camera / Voice / Dashboard
-> PC client or browser UI
-> Binary packet (8 bytes)
-> ESP32 WebSocket bridge
-> UART2 TX2 GPIO17
-> Arduino Uno RX D0
-> 5-servo tendon-driven robot hand
```

## Technical Depth Gallery

| Packet Format | Safety State Machine |
| --- | --- |
| <img src="reports/assets/fig_06_packet_format.png" alt="Packet Format" width="100%" /> | <img src="reports/assets/fig_07_state_machine.png" alt="State Machine" width="100%" /> |

| CV Algorithm | Skeleton View |
| --- | --- |
| <img src="reports/assets/fig_08_cv_algorithm.png" alt="CV Algorithm" width="100%" /> | <img src="reports/assets/cv_skeleton.png" alt="CV Skeleton" width="100%" /> |

| Hardware Reference | Operator View |
| --- | --- |
| <img src="reports/assets/hardware_reference.png" alt="Hardware Reference" width="100%" /> | <img src="poster/dashboard_capture_hd.png" alt="Dashboard Operator View" width="100%" /> |

This is where the repository stops being decorative and starts feeling technically grounded.

## What The System Can Do

| Area | Capability |
| --- | --- |
| Hand control | Open, close, grip percentage, direct servo commands |
| Vision pipeline | Hand tracking, calibration, preview, realtime send |
| Operator control | Dashboard for connect, arm, disarm, estop, and manual control |
| Voice control | Basic spoken actions for core commands |
| Communication | Binary control packets over WebSocket and UART |
| Testing | Link test and staged validation before live motion |

## Why The Engineering Feels Credible

This project respects the non-glamorous truths of physical systems:

- power can dip
- transport can fail
- servo behavior can be unstable
- safety states matter
- debugging the link often matters more than blaming the AI first

That is why the design includes:

- `ARM`
- `DISARM`
- `ESTOP`
- preview-first workflow
- fixed calibration references
- transport-first verification

## Quick Launch

```powershell
.\setup_python_env.bat
.\run_link_test.bat
.\run_master_control.bat
.\run_preview_cv.bat
.\run_realtime_cv.bat
```

## Best Demo Sequence

1. Show the real hand and the power rule.
2. Open the official poster or architecture image.
3. Run the link test.
4. Demonstrate direct dashboard control.
5. Show CV preview.
6. Run realtime hand mirroring.
7. End with grip presets or voice commands.

This gives the audience a progression from trust, to clarity, to impact.

## Supporting Files

- [`README.md`](README.md)
- [`QUICKSTART.md`](QUICKSTART.md)
- [`HANDOVER.md`](HANDOVER.md)
- [`HARDWARE_CHECKLIST.md`](HARDWARE_CHECKLIST.md)
- [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- [`docs/protocol.md`](docs/protocol.md)
- [`docs/calibration.md`](docs/calibration.md)
- [`docs/realtime_notes.md`](docs/realtime_notes.md)

## Final Impression

`Vision-Driven Robot Hand` stands out because it is not just a model demo, not just a hardware assembly, and not just a UI prototype.

It is a compact but complete AIoT system where perception, communication, safety, and motion all meet in one convincing physical artifact.
