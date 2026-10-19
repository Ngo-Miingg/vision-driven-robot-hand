#pragma once
#include "Config.h"
void initializeMotion();
void attachAllServos();
void detachAllServos();
void applyAnglesNow(const byte angles[SERVO_COUNT]);
void applyGripPercent(byte percent);
void setAllToOpen();
void setAllToClose();
void handleSetOne(byte index, int angle);
const byte* getCurrentAngles();
const byte* getTargetAngles();
bool isServoAttached(byte index);
