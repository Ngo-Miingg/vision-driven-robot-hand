#include "Protocol.h"
#include "Config.h"
#include "RobotState.h"
#include "ServoMotion.h"
#include "Diagnostics.h"
#include <stdlib.h>
#include <string.h>

static const byte PACKET_SIZE = 9;
static char lineBuffer[64];
static byte lineLength = 0;
static byte packet[PACKET_SIZE];
static byte packetIndex = 0;
static bool packetActive = false;

static byte checksum(const byte *data, byte length) {
  byte v = 0;
  for (byte i = 0; i < length; ++i) v ^= data[i];
  return v;
}

static void processText(char *line) {
  char *cmd = strtok(line, " \t");
  if (!cmd) return;
  // Exact matches: DISARM must not accidentally be parsed as ARM.
  if (strcmp(cmd, "DISARM") == 0) { handleDisarm(); Serial.println(F("OK DISARM")); return; }
  if (strcmp(cmd, "ARM") == 0) { handleArm(); Serial.println(F("OK ARM")); return; }
  if (strcmp(cmd, "ESTOP") == 0) { handleEstop(); Serial.println(F("OK ESTOP")); return; }
  if (strcmp(cmd, "RESET") == 0) { handleReset(); Serial.println(F("OK RESET")); return; }
  if (strcmp(cmd, "PRINT") == 0) { printState(); return; }
  if (strcmp(cmd, "OPEN") == 0) { if (robotState() == STATE_ARMED) setAllToOpen(); Serial.println(F("OK OPEN")); return; }
  if (strcmp(cmd, "CLOSE") == 0) { if (robotState() == STATE_ARMED) setAllToClose(); Serial.println(F("OK CLOSE")); return; }
  if (strcmp(cmd, "GRIP") == 0) {
    char *p = strtok(NULL, " \t");
    if (p && robotState() == STATE_ARMED) applyGripPercent((byte)constrain(atoi(p), 0, 100));
    Serial.println(F("OK GRIP"));
    return;
  }
  if (strcmp(cmd, "SET") == 0) {
    char *index = strtok(NULL, " \t");
    char *angle = strtok(NULL, " \t");
    if (index && angle && robotState() == STATE_ARMED) {
      int id = atoi(index);
      if (id >= 0 && id < SERVO_COUNT) handleSetOne((byte)id, atoi(angle));
    }
    Serial.println(F("OK SET"));
    return;
  }
  Serial.println(F("ERR UNKNOWN"));
}

static void processPacket(const byte frame[PACKET_SIZE]) {
  if (frame[0] != 0xAA || checksum(frame, 8) != frame[8]) return;
  markControlReceived();
  byte mode = frame[1];
  if (mode == 0x10) { handleArm(); return; }
  if (mode == 0x11) { handleDisarm(); return; }
  if (mode == 0x12) { handleEstop(); return; }
  if (mode == 0x13) { if (robotState() == STATE_ARMED) setAllToOpen(); return; }
  if (mode == 0x14) { if (robotState() == STATE_ARMED) setAllToClose(); return; }
  if (robotState() != STATE_ARMED) return;
  if (mode == 0x01) {
    byte angles[SERVO_COUNT];
    for (byte i = 0; i < SERVO_COUNT; i++) angles[i] = frame[i + 2];
    applyAnglesNow(angles);
  } else if (mode == 0x02) {
    applyGripPercent(frame[2]);
  }
}

static void acceptByte(byte c) {
  if (packetActive) {
    packet[packetIndex++] = c;
    if (packetIndex == PACKET_SIZE) {
      processPacket(packet);
      packetIndex = 0;
      packetActive = false;
    }
    return;
  }
  if (c == 0xAA) {
    packetActive = true;
    packetIndex = 1;
    packet[0] = c;
    lineLength = 0;
    return;
  }
  if (c == '\r' || c == '\n') {
    if (lineLength) {
      lineBuffer[lineLength] = 0;
      processText(lineBuffer);
      lineLength = 0;
    }
  } else if (lineLength < sizeof(lineBuffer) - 1) {
    lineBuffer[lineLength++] = (char)c;
  } else {
    lineLength = 0;
  }
}
void initializeProtocol() {
  lineLength = 0;
  packetIndex = 0;
  packetActive = false;
}
void pollProtocol() {
  while (Serial.available()) acceptByte((byte)Serial.read());
}
