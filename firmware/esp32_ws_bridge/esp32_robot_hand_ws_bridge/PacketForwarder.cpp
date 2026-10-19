#include "PacketForwarder.h"
#include "BridgeConfig.h"
uint32_t binaryRxCount = 0;
uint32_t binaryForwardCount = 0;
uint32_t binaryDropLengthCount = 0;
uint32_t binaryDropStartCount = 0;
uint32_t binaryDropChecksumCount = 0;
uint32_t textForwardCount = 0;
static uint8_t checksum(const uint8_t *frame, size_t len) {
  uint8_t s = 0;
  for (size_t i = 0; i < len; i++) s ^= frame[i];
  return s;
}
void forwardBinaryPacket(const uint8_t *payload, size_t length) {
  binaryRxCount++;
  if (length != PACKET_SIZE) { binaryDropLengthCount++; return; }
  if (payload[0] != 0xAA) { binaryDropStartCount++; return; }
  if (checksum(payload, PACKET_SIZE - 1) != payload[PACKET_SIZE - 1]) { binaryDropChecksumCount++; return; }
  Serial2.write(payload, length);
  binaryForwardCount++;
}
void forwardTextPacket(const uint8_t *payload, size_t length) {
  Serial2.write(payload, length);
  Serial2.write('\n');
  textForwardCount++;
}
