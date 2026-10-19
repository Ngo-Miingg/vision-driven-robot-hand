#include "ServoMotion.h"
#include "RobotState.h"
#include <Servo.h>
static Servo servos[SERVO_COUNT];
static bool servoAttached[SERVO_COUNT];
static byte currentAngles[SERVO_COUNT];
static byte targetAngles[SERVO_COUNT];

static byte clampAngle(int value, byte lo, byte hi) {
  if (value < (int)lo) return lo;
  if (value > (int)hi) return hi;
  return (byte)value;
}

void initializeMotion() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    servoAttached[i] = false;
    currentAngles[i] = OPEN_ANGLE[i];
    targetAngles[i] = OPEN_ANGLE[i];
  }
}

void attachAllServos() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    // Set target before attaching to avoid an implicit 90-degree command.
    servos[i].write(targetAngles[i]);
    if (!servoAttached[i]) {
      servos[i].attach(SERVO_PINS[i]);
      servoAttached[i] = true;
    }
    servos[i].write(targetAngles[i]);
    currentAngles[i] = targetAngles[i];
  }
}

void detachAllServos() {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    if (servoAttached[i]) {
      servos[i].detach();
      servoAttached[i] = false;
    }
  }
}

void applyAnglesNow(const byte angles[SERVO_COUNT]) {
  for (byte i = 0; i < SERVO_COUNT; i++) {
    byte limited = clampAngle(angles[i], MIN_ANGLE[i], MAX_ANGLE[i]);
    targetAngles[i] = limited;
    if (robotState() == STATE_ARMED && servoAttached[i]) {
      if (abs((int)limited - (int)currentAngles[i]) > ANGLE_DEADBAND) {
        servos[i].write(limited);
      }
      currentAngles[i] = limited;
    }
  }
}

void applyGripPercent(byte percent) {
  if (percent > 100) percent = 100;
  byte angles[SERVO_COUNT];
  for (byte i = 0; i < SERVO_COUNT; i++) {
    // Signed math is needed for reverse-angle channels S0, S1, S5.
    long delta = (long)CLOSED_ANGLE[i] - (long)OPEN_ANGLE[i];
    long value = (long)OPEN_ANGLE[i] + delta * percent / 100L;
    angles[i] = clampAngle((int)value, MIN_ANGLE[i], MAX_ANGLE[i]);
  }
  applyAnglesNow(angles);
}

void setAllToOpen() { applyAnglesNow(OPEN_ANGLE); }
void setAllToClose() { applyAnglesNow(CLOSED_ANGLE); }
void handleSetOne(byte index, int angle) {
  if (index >= SERVO_COUNT) return;
  byte angles[SERVO_COUNT];
  for (byte i = 0; i < SERVO_COUNT; i++) angles[i] = targetAngles[i];
  angles[index] = clampAngle(angle, MIN_ANGLE[index], MAX_ANGLE[index]);
  applyAnglesNow(angles);
}
const byte* getCurrentAngles() { return currentAngles; }
const byte* getTargetAngles() { return targetAngles; }
bool isServoAttached(byte index) { return index < SERVO_COUNT && servoAttached[index]; }
