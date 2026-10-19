#include "RobotState.h"
#include "Config.h"
#include "ServoMotion.h"
static HandState handState = STATE_DISARMED;
static unsigned long lastSignalMs = 0UL;
void initializeRobot() {
  initializeMotion();
  handState = STATE_DISARMED;
  lastSignalMs = millis();
}
HandState robotState() { return handState; }
void markControlReceived() { lastSignalMs = millis(); }
void handleArm() {
  if (handState == STATE_FAULT) return;
  if (handState != STATE_ARMED) {
    handState = STATE_ARMED;
    attachAllServos();
  }
}
void handleDisarm() {
  detachAllServos();
  handState = STATE_DISARMED;
}
void handleEstop() {
  detachAllServos();
  handState = STATE_FAULT;
}
void handleReset() {
  detachAllServos();
  handState = STATE_DISARMED;
}
void updateRobotState() {
  if (handState == STATE_ARMED && millis() - lastSignalMs > SIGNAL_TIMEOUT_MS) {
    // Timeout is observational ONLY; no safe hardware power cutoff is installed.
    // Last commanded position remains as-is. Not a physical fail-safe.
  }
}
