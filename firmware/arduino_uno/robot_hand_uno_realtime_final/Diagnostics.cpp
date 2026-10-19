#include "Diagnostics.h"
#include "Config.h"
#include "RobotState.h"
#include "ServoMotion.h"
void printState() {
  Serial.print(F("STATE="));
  HandState s = robotState();
  Serial.print(s == STATE_ARMED ? F("ARMED") : (s == STATE_FAULT ? F("FAULT") : F("DISARMED")));
  Serial.print(F(" ATTACHED="));
  for (byte i = 0; i < SERVO_COUNT; ++i) Serial.print(isServoAttached(i) ? '1' : '0');
  Serial.println();
  Serial.print(F("PINS="));
  for (byte i = 0; i < SERVO_COUNT; ++i) { Serial.print(SERVO_PINS[i]); Serial.print(' '); }
  Serial.println();
  Serial.print(F("CURRENT="));
  for (byte i = 0; i < SERVO_COUNT; ++i) { Serial.print(getCurrentAngles()[i]); Serial.print(' '); }
  Serial.println();
  Serial.print(F("TARGET="));
  for (byte i = 0; i < SERVO_COUNT; ++i) { Serial.print(getTargetAngles()[i]); Serial.print(' '); }
  Serial.println();
}
