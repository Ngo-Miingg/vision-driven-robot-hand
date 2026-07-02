# Release Checklist

Dung checklist nay truoc khi ban giao hoac tao file zip.

## Code

- `README.md` cap nhat dung tinh nang hien tai.
- `QUICKSTART.md` chay duoc theo thu tu.
- `HANDOVER.md` mo ta dung luong he thong.
- `.gitignore` khong cho `.venv`, cache, release zip vao repo.
- Khong co file tam, log, video test trong goi release.

## Firmware

- Uno firmware dung calibration:

```text
OPEN  = 40,180,0,0,80
CLOSE = 170,0,180,180,0
```

- ESP32 firmware dung:

```text
SSID: RobotHand_ESP32
WS PORT: 81
UART2 TX: GPIO17
UART BAUD: 250000
```

## Test khong can servo chay

```powershell
.\.venv\Scripts\python.exe pc_client\cv_sender_template.py --self-test
```

## Test co phan cung

```powershell
.\run_link_test.bat
```

Mo Serial Monitor ESP32 `115200` va kiem tra:

```text
STATUS clients=... rx=... fwd=... drop_len=0 drop_start=0 drop_sum=0 heap=...
```

## Build release

```powershell
.\scripts\build_release.ps1
```

Ket qua nam trong:

```text
release\
```
