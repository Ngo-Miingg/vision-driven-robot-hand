#pragma once
#include <Arduino.h>
enum HandState : byte { STATE_DISARMED = 0, STATE_ARMED = 1, STATE_FAULT = 2 };
void initializeRobot();
HandState robotState();
void handleArm();
void handleDisarm();
void handleEstop();
void handleReset();
void updateRobotState();
void markControlReceived();
