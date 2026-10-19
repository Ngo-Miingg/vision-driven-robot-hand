#include "Config.h"
// S0 thumb curl D2; S1 index D3; S2 middle D4;
// S3 ring D5; S4 thumb oppose D8; S5 pinky D7.
const byte SERVO_PINS[SERVO_COUNT] = {2, 3, 4, 5, 8, 7};
// Confirmed latest: S0 reversed; S4 D8 OPEN=0 CLOSE=180.
const byte OPEN_ANGLE[SERVO_COUNT]   = {170, 180,   0,   0,   0, 180};
const byte CLOSED_ANGLE[SERVO_COUNT] = { 40,   0, 180, 180, 180,   0};
const byte MIN_ANGLE[SERVO_COUNT]    = { 40,   0,   0,   0,   0,   0};
const byte MAX_ANGLE[SERVO_COUNT]    = {170, 180, 180, 180, 180, 180};
