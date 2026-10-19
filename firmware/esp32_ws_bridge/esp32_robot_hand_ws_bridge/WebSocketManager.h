#pragma once
#include <Arduino.h>
extern uint8_t activeClient;
void startWebSockets();
void pollWebSockets();
