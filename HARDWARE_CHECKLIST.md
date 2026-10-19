# Hardware checklist - 6 servo 2026-10-15

- S0 D2 OPEN170 CLOSE40 (reverse from original)
- S1 D3 OPEN180 CLOSE0
- S2 D4 OPEN0 CLOSE180
- S3 D5 OPEN0 CLOSE180
- S4 **D8** OPEN0 CLOSE180 (latest calibration)
- S5 D7 OPEN180 CLOSE0
- GPIO17 ESP32 TX2 -> Uno D0/RX, GND chung; signal D6 not used
- Never connect Uno 5V TX/D1 directly to ESP32 3.3V RX2.
- Separate regulated high-current 5-6V supply for servos.
- Disconnect GPIO17-to-D0 wire while uploading Uno.
- NO hardware E-STOP at D8, no servo power cut controlled by firmware.
- Test with no mechanical load before ARM/full travel.
