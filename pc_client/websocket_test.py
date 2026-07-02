import time

import websocket


WS_URL = "ws://192.168.4.1:81"
MODE_DIRECT = 0x01
MODE_GRIP = 0x02
MODE_ARM = 0x10
MODE_DISARM = 0x11
MODE_OPEN = 0x13
MODE_CLOSE = 0x14


def checksum_xor(data):
    value = 0
    for byte in data:
        value ^= byte & 0xFF
    return value


def make_packet(mode, payload=None):
    frame = [0] * 8
    frame[0] = 0xAA
    frame[1] = mode & 0xFF
    payload = payload or []
    for index in range(min(5, len(payload))):
        frame[2 + index] = int(payload[index]) & 0xFF
    frame[7] = checksum_xor(frame[:7])
    return bytes(frame)


def send_packet(ws, mode, payload=None):
    packet = make_packet(mode, payload)
    ws.send(packet, opcode=websocket.ABNF.OPCODE_BINARY)
    print("TX", packet.hex(" "))


def main():
    ws = websocket.create_connection(WS_URL, timeout=5)
    ws.settimeout(2)
    try:
        send_packet(ws, MODE_ARM)
        time.sleep(0.2)
        send_packet(ws, MODE_OPEN)
        time.sleep(0.2)
        send_packet(ws, MODE_CLOSE)
        time.sleep(0.2)

        for grip in (0, 25, 50, 75, 100):
            send_packet(ws, MODE_GRIP, [grip])
            time.sleep(0.2)

        send_packet(ws, MODE_DISARM)
    finally:
        ws.close()


if __name__ == "__main__":
    main()
