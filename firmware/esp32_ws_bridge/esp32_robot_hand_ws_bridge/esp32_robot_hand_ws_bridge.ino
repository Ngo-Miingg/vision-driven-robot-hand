#include "BridgeConfig.h"
#include "WiFiAccessPoint.h"
#include "PacketForwarder.h"
#include "WebSocketManager.h"
#include "BridgeDiagnostics.h"
void setup() {
  Serial.begin(115200);
  delay(200);
  startAccessPoint();
  Serial2.begin(UART_BAUD, SERIAL_8N1, UART2_RX, UART2_TX);
  startWebSockets();
  Serial.println(F("ESP32 WS BRIDGE READY PACKET9 / S4=D8 ON UNO"));
  printBridgeIdentity();
}
void loop() {
  pollWebSockets();
  pollBridgeDiagnostics();
}
