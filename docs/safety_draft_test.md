# Safety draft test

Muc tieu cua giai doan nay la kiem tra nhan dien skeleton va logic map servo truoc khi cho servo chay that.

## Buoc 1: Chay skeleton preview, khong servo

Khong can ket noi ESP32. Khong can cap nguon servo.

```powershell
cd D:\Work\HocKy3\Deploying-AI-and-IoT-applications\robot_hand_realtime\pc_client
python cv_sender_template.py
```

Man hinh phai hien:

```text
DRY RUN - NO SERVO
```

Kiem tra:

- Skeleton bam tot vao ban tay.
- Landmark khong nhay qua vat the khac.
- Khi tay mo, `ratio` cua cac ngon gan `0.00`.
- Khi tay nam, `ratio` cua cac ngon tien gan `1.00`.
- Khi tay mo, `S0..S4` gan `40 180 0 0 80`.
- Khi tay nam, `S0..S4` gan `170 0 180 180 0`.

## Buoc 2: Kiem tra logic servo bang so

Chua cam day servo vao co khi neu chua chac huong.

Quan sat `S0..S4`:

```text
S0 thumb curl: tay mo gan 40, tay nam tang len gan 170
S1 index: tay mo gan 180, tay nam giam ve gan 0
S2 middle: tay mo gan 0, tay nam tang len gan 180
S3 ring+pinky: tay mo gan 0, tay nam tang len gan 180
S4 thumb oppose: tay mo gan 80, tay nam giam ve gan 0
```

Neu bat ky servo nao di nguoc voi bang tren, khong chay live. Can sua mapping CV truoc.

## Buoc 3: Test live nhung chua auto ARM

Chi dung khi Buoc 1 va Buoc 2 da on.

```powershell
python cv_sender_template.py --send
```

Che do nay ket noi ESP32 nhung khong tu ARM. Khi da san sang moi bam `a` trong cua so camera.

Hotkey:

```text
a = ARM
d = DISARM
o = OPEN
c = CLOSE
e = ESTOP
q = quit
```

## Buoc 4: Test co khi thuc te

- Bat dau voi servo khong gan tai nang.
- Dat tay robot o vi tri khong bi ket co khi.
- De ngon tay co khoang trong de quay.
- Luon san sang bam `e` de ESTOP hoac rut nguon servo.
- Neu servo keu rit, nong nhanh, hoac bi keo qua gioi han co khi: dung ngay.

Khong dung `--auto-arm` cho den khi huong servo va co khi da chac chan on.
