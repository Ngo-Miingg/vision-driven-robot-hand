#pragma once
#include <Arduino.h>
extern uint32_t binaryRxCount;
extern uint32_t binaryForwardCount;
extern uint32_t binaryDropLengthCount;
extern uint32_t binaryDropStartCount;
extern uint32_t binaryDropChecksumCount;
extern uint32_t textForwardCount;
void forwardBinaryPacket(const uint8_t* payload, size_t length);
void forwardTextPacket(const uint8_t* payload, size_t length);
