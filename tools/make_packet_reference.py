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
    return frame


def format_frame(frame):
    return " ".join(f"0x{byte:02X}" for byte in frame)


if __name__ == "__main__":
    direct_open = make_packet(0x01, [170, 180, 0, 0, 0, 180])
    grip_50 = make_packet(0x02, [50])
    print("DIRECT OPEN :", format_frame(direct_open))
    print("GRIP 50     :", format_frame(grip_50))
