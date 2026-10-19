import time

import serial


COM_PORT = "COM5"
BAUD_RATE = 250000
SERIAL_TIMEOUT = 1.0

OPEN_ANGLE = [170, 180, 0, 0, 0, 180]
CLOSED_ANGLE = [40, 0, 180, 180, 180, 0]
MODE_DIRECT = 0x01
MODE_GRIP = 0x02
MODE_OPEN = 0x13
MODE_CLOSE = 0x14


def checksum_xor(data):
    value = 0
    for byte in data:
        value ^= byte & 0xFF
    return value


def make_packet(mode, payload=None):
    frame = [0] * 9
    frame[0] = 0xAA
    frame[1] = mode & 0xFF
    payload = payload or []
    for index in range(min(6, len(payload))):
        frame[2 + index] = int(payload[index]) & 0xFF
    frame[8] = checksum_xor(frame[:8])
    return bytes(frame)


def send_binary(ser, mode, payload=None):
    packet = make_packet(mode, payload)
    ser.write(packet)
    ser.flush()
    print("TX BIN", packet.hex(" "))


def send_text(ser, text):
    line = (text.strip() + "\n").encode("ascii")
    ser.write(line)
    ser.flush()
    print("TX TXT", text)


def direct_angle_tests(ser):
    # Test every independent servo, holding all other channels at OPEN.
    for index in range(len(OPEN_ANGLE)):
        for label, value in (("OPEN", OPEN_ANGLE[index]), ("CLOSE", CLOSED_ANGLE[index])):
            angles = OPEN_ANGLE.copy()
            angles[index] = value
            print(f"S{index} {label}", angles)
            send_binary(ser, MODE_DIRECT, angles)
            time.sleep(0.35)


def main():
    with serial.Serial(COM_PORT, BAUD_RATE, timeout=SERIAL_TIMEOUT) as ser:
        time.sleep(2.0)
        send_text(ser, "ARM")
        time.sleep(0.25)

        send_binary(ser, MODE_OPEN)
        time.sleep(0.35)
        send_binary(ser, MODE_CLOSE)
        time.sleep(0.35)
        send_binary(ser, MODE_GRIP, [50])
        time.sleep(0.35)

        direct_angle_tests(ser)

        send_text(ser, "DISARM")


if __name__ == "__main__":
    main()
