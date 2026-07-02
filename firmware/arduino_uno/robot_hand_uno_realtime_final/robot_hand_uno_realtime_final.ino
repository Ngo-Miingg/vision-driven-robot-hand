#include <Servo.h>

static const unsigned long SERIAL_BAUD = 250000UL;
static const byte SERVO_COUNT = 5;
static const byte SERVO_PINS[SERVO_COUNT] = {3, 5, 6, 9, 10};
const byte OPEN_ANGLE[SERVO_COUNT] = {40, 180, 0, 0, 80};
const byte CLOSED_ANGLE[SERVO_COUNT] = {170, 0, 180, 180, 0};
const byte MAX_ANGLE[SERVO_COUNT] = {170, 180, 180, 180, 80};
const byte ANGLE_DEADBAND = 1;
const byte ESTOP_PIN = 8;
const byte SERVO_POWER_PIN = 7;
const bool USE_SERVO_POWER_ENABLE = false;
const unsigned long SIGNAL_TIMEOUT_MS = 800UL;

enum HandState : byte {
  STATE_DISARMED = 0,
  STATE_ARMED = 1,
  STATE_FAULT = 2
};

Servo servos[SERVO_COUNT];
bool servoAttached[SERVO_COUNT] = {false, false, false, false, false};
byte currentAngle[SERVO_COUNT] = {40, 180, 0, 0, 80};
byte targetAngle[SERVO_COUNT] = {40, 180, 0, 0, 80};
HandState handState = STATE_DISARMED;
unsigned long lastSignalMs = 0UL;
char lineBuffer[64];
byte lineLength = 0;
byte binaryFrame[8];
byte binaryIndex = 0;
bool binaryActive = false;

byte clampByte(int value, byte minValue, byte maxValue) {
  if (value < minValue) {
    return minValue;
  }
  if (value > maxValue) {
    return maxValue;
  }
  return (byte)value;
}

byte xorChecksum(const byte *data, byte length) {
  byte checksum = 0;
  for (byte i = 0; i < length; i++) {
    checksum ^= data[i];
  }
  return checksum;
}

byte lerpAngle(byte openValue, byte closeValue, byte percent) {
  int delta = (int)closeValue - (int)openValue;
  int value = (int)openValue + ((delta * (int)percent) + 50) / 100;
  return clampByte(value, 0, 180);
}

void setServoPower(bool enabled) {
  if (!USE_SERVO_POWER_ENABLE) {
    return;
  }
  digitalWrite(SERVO_POWER_PIN, enabled ? HIGH : LOW);
}

void detachAllServos() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (servoAttached[i]) {
      servos[i].detach();
      servoAttached[i] = false;
    }
  }
}

void attachAllServos() {
  setServoPower(true);
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (!servoAttached[i]) {
      servos[i].attach(SERVO_PINS[i]);
      servoAttached[i] = true;
    }
    servos[i].write(targetAngle[i]);
    currentAngle[i] = targetAngle[i];
  }
}

void applyAnglesNow(const byte angles[SERVO_COUNT]) {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    byte limited = clampByte(angles[i], 0, MAX_ANGLE[i]);
    targetAngle[i] = limited;
    if (handState == STATE_ARMED && servoAttached[i]) {
      if (abs((int)limited - (int)currentAngle[i]) > ANGLE_DEADBAND) {
        servos[i].write(limited);
      }
      currentAngle[i] = limited;
    }
  }
}

void applyGripPercent(byte percent) {
  byte clampedPercent = clampByte(percent, 0, 100);
  byte nextAngles[SERVO_COUNT];
  for (byte i = 0; i < SERVO_COUNT; i++) {
    nextAngles[i] = lerpAngle(OPEN_ANGLE[i], CLOSED_ANGLE[i], clampedPercent);
  }
  applyAnglesNow(nextAngles);
}

void setAllToOpen() {
  applyAnglesNow(OPEN_ANGLE);
}

void setAllToClose() {
  applyAnglesNow(CLOSED_ANGLE);
}

void handleArm() {
  if (handState == STATE_FAULT) {
    return;
  }
  if (handState != STATE_ARMED) {
    handState = STATE_ARMED;
    attachAllServos();
  }
}

void handleDisarm() {
  detachAllServos();
  setServoPower(false);
  handState = STATE_DISARMED;
}

void handleEstop() {
  detachAllServos();
  setServoPower(false);
  handState = STATE_FAULT;
}

void handleReset() {
  detachAllServos();
  setServoPower(false);
  handState = STATE_DISARMED;
}

void handleSetOne(byte index, int angle) {
  if (index >= SERVO_COUNT) {
    return;
  }
  byte nextAngles[SERVO_COUNT];
  for (byte i = 0; i < SERVO_COUNT; i++) {
    nextAngles[i] = targetAngle[i];
  }
  nextAngles[index] = clampByte(angle, 0, MAX_ANGLE[index]);
  applyAnglesNow(nextAngles);
}

void printState() {
  Serial.print(F("STATE="));
  if (handState == STATE_DISARMED) {
    Serial.print(F("DISARMED"));
  } else if (handState == STATE_ARMED) {
    Serial.print(F("ARMED"));
  } else {
    Serial.print(F("FAULT"));
  }
  Serial.print(F(" ATTACHED="));
  Serial.println(servoAttached[0] ? F("1") : F("0"));

  Serial.print(F("CURRENT="));
  for (byte i = 0; i < SERVO_COUNT; i++) {
    Serial.print(currentAngle[i]);
    if (i + 1 < SERVO_COUNT) {
      Serial.print(' ');
    }
  }
  Serial.println();

  Serial.print(F("TARGET="));
  for (byte i = 0; i < SERVO_COUNT; i++) {
    Serial.print(targetAngle[i]);
    if (i + 1 < SERVO_COUNT) {
      Serial.print(' ');
    }
  }
  Serial.println();
}

void processTextCommand(char *line) {
  char *token = strtok(line, " \t");
  if (token == NULL) {
    return;
  }

  if (strcmp(token, "ARM") == 0) {
    handleArm();
    Serial.println(F("OK ARM"));
    return;
  }
  if (strcmp(token, "DISARM") == 0) {
    handleDisarm();
    Serial.println(F("OK DISARM"));
    return;
  }
  if (strcmp(token, "ESTOP") == 0) {
    handleEstop();
    Serial.println(F("OK ESTOP"));
    return;
  }
  if (strcmp(token, "RESET") == 0) {
    handleReset();
    Serial.println(F("OK RESET"));
    return;
  }
  if (strcmp(token, "OPEN") == 0) {
    if (handState == STATE_ARMED) {
      setAllToOpen();
    }
    Serial.println(F("OK OPEN"));
    return;
  }
  if (strcmp(token, "CLOSE") == 0) {
    if (handState == STATE_ARMED) {
      setAllToClose();
    }
    Serial.println(F("OK CLOSE"));
    return;
  }
  if (strcmp(token, "GRIP") == 0) {
    char *percentToken = strtok(NULL, " \t");
    if (percentToken != NULL && handState == STATE_ARMED) {
      applyGripPercent((byte)clampByte(atoi(percentToken), 0, 100));
    }
    Serial.println(F("OK GRIP"));
    return;
  }
  if (strcmp(token, "SET") == 0) {
    char *indexToken = strtok(NULL, " \t");
    char *angleToken = strtok(NULL, " \t");
    if (indexToken != NULL && angleToken != NULL && handState == STATE_ARMED) {
      handleSetOne((byte)clampByte(atoi(indexToken), 0, 4), atoi(angleToken));
    }
    Serial.println(F("OK SET"));
    return;
  }
  if (strcmp(token, "PRINT") == 0) {
    printState();
    return;
  }

  Serial.println(F("ERR UNKNOWN"));
}

void processBinaryFrame(const byte frame[8]) {
  if (frame[0] != 0xAA) {
    return;
  }
  if (xorChecksum(frame, 7) != frame[7]) {
    return;
  }

  lastSignalMs = millis();

  byte mode = frame[1];
  if (mode == 0x10) {
    handleArm();
    return;
  }
  if (mode == 0x11) {
    handleDisarm();
    return;
  }
  if (mode == 0x12) {
    handleEstop();
    return;
  }
  if (mode == 0x13) {
    if (handState == STATE_ARMED) {
      setAllToOpen();
    }
    return;
  }
  if (mode == 0x14) {
    if (handState == STATE_ARMED) {
      setAllToClose();
    }
    return;
  }
  if (handState != STATE_ARMED) {
    return;
  }
  if (mode == 0x01) {
    byte nextAngles[SERVO_COUNT];
    for (byte i = 0; i < SERVO_COUNT; i++) {
      nextAngles[i] = frame[2 + i];
    }
    applyAnglesNow(nextAngles);
    return;
  }
  if (mode == 0x02) {
    applyGripPercent(frame[2]);
  }
}

void handleIncomingByte(byte incoming) {
  if (binaryActive) {
    binaryFrame[binaryIndex++] = incoming;
    if (binaryIndex >= 8) {
      processBinaryFrame(binaryFrame);
      binaryActive = false;
      binaryIndex = 0;
    }
    return;
  }

  if (incoming == 0xAA) {
    binaryActive = true;
    binaryIndex = 1;
    binaryFrame[0] = incoming;
    lineLength = 0;
    return;
  }

  if (incoming == '\r' || incoming == '\n') {
    if (lineLength > 0) {
      lineBuffer[lineLength] = '\0';
      processTextCommand(lineBuffer);
      lineLength = 0;
    }
    return;
  }

  if (lineLength < sizeof(lineBuffer) - 1) {
    lineBuffer[lineLength++] = (char)incoming;
  }
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  pinMode(ESTOP_PIN, INPUT_PULLUP);
  if (USE_SERVO_POWER_ENABLE) {
    pinMode(SERVO_POWER_PIN, OUTPUT);
    setServoPower(false);
  }
  detachAllServos();
  handState = STATE_DISARMED;
  lastSignalMs = millis();
  Serial.println(F("UNO READY"));
}

void loop() {
  while (Serial.available() > 0) {
    handleIncomingByte((byte)Serial.read());
  }

  if (digitalRead(ESTOP_PIN) == LOW && handState != STATE_FAULT) {
    handleEstop();
  }

  if (handState == STATE_ARMED && (millis() - lastSignalMs > SIGNAL_TIMEOUT_MS)) {
    // Hold the current position; do not auto-open or force a fallback pose.
  }
}
