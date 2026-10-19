#pragma once
#include <Arduino.h>
static const byte SERVO_COUNT = 6;
static const unsigned long SERIAL_BAUD = 250000UL;
static const unsigned long SIGNAL_TIMEOUT_MS = 800UL;
static const byte ANGLE_DEADBAND = 1;
extern const byte SERVO_PINS[SERVO_COUNT];
extern const byte OPEN_ANGLE[SERVO_COUNT];
extern const byte CLOSED_ANGLE[SERVO_COUNT];
extern const byte MIN_ANGLE[SERVO_COUNT];
extern const byte MAX_ANGLE[SERVO_COUNT];
