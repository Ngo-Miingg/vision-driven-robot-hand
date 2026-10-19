#include <Arduino.h>
#include "Config.h"
#include "ServoMotion.h"
#include "RobotState.h"
#include "Protocol.h"
#include "Diagnostics.h"

void setup() {
  Serial.begin(SERIAL_BAUD);
  initializeRobot();
  initializeProtocol();
  Serial.println(F("UNO READY S0..S5 PACKET9 S4=D8"));
  printState();
}

void loop() {
  pollProtocol();
  updateRobotState();
}
