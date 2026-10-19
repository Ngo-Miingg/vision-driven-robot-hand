#include "BridgeDiagnostics.h"
#include "BridgeConfig.h"
#include "PacketForwarder.h"
#include "WebSocketManager.h"
#include <WiFi.h>
void pollBridgeDiagnostics() {
  static unsigned long lastStatusMs = 0;
  unsigned long now = millis();
  if (now - lastStatusMs < STATUS_INTERVAL_MS) return;
  lastStatusMs = now;
  Serial.print(F("STATUS clients=")); Serial.print(WiFi.softAPgetStationNum());
  Serial.print(F(" active="));
  if (activeClient == 255) Serial.print(F("none")); else Serial.print(activeClient);
  Serial.print(F(" rx=")); Serial.print(binaryRxCount);
  Serial.print(F(" fwd=")); Serial.print(binaryForwardCount);
  Serial.print(F(" drop_len=")); Serial.print(binaryDropLengthCount);
  Serial.print(F(" drop_start=")); Serial.print(binaryDropStartCount);
  Serial.print(F(" drop_sum=")); Serial.print(binaryDropChecksumCount);
  Serial.print(F(" text=")); Serial.print(textForwardCount);
  Serial.print(F(" heap=")); Serial.println(ESP.getFreeHeap());
}
