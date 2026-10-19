# Calibration 6 servo (2026-10-15)

| S | D | MO | NAM | Ghi chu |
|---|---|---:|---:|---|
| 0 | 2 | 170 | 40 | Chieu S0 dao theo feedback moi |
| 1 | 3 | 180 | 0 | Da xac nhan |
| 2 | 4 | 0 | 180 | Da chay lai |
| 3 | 5 | 0 | 180 | Da xac nhan |
| 4 | 8 | 0 | 180 | Moi xac nhan truc tiep bang test D8 |
| 5 | 7 | 180 | 0 | Da xac nhan |

Chinh `firmware/arduino_uno/robot_hand_uno_realtime_final/Config.cpp` khi can cap nhat.
`OPEN_ANGLE` va `CLOSED_ANGLE` da duoc dong bo trong Python CV, voice, web JS.
Cac so do VOI DANH GIA CV cho S5 la khoi tao tham khao, CHUA phai calibration thuc te.
Can calibration lai pose cua ban tay trong CV truoc khi tin ket qua realtime.
