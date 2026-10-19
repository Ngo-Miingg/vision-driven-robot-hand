#include "WebSocketManager.h"
#include "BridgeConfig.h"
#include "PacketForwarder.h"
#include <WebSocketsServer.h>
static WebSocketsServer webSocket(WS_PORT);
uint8_t activeClient = 255;
static uint32_t disconnectCount = 0;
static void onWsEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      if (activeClient != 255 && activeClient != num) webSocket.disconnect(activeClient);
      activeClient = num;
      Serial.print(F("WS CONNECTED ")); Serial.println(num);
      break;
    case WStype_DISCONNECTED:
      disconnectCount++;
      if (activeClient == num) activeClient = 255;
      Serial.print(F("WS DISCONNECTED ")); Serial.println(num);
      break;
    case WStype_BIN:
      if (num == activeClient) forwardBinaryPacket(payload, length);
      break;
    case WStype_TEXT:
      if (num == activeClient) forwardTextPacket(payload, length);
      break;
    default: break;
  }
}
void startWebSockets() { webSocket.begin(); webSocket.onEvent(onWsEvent); }
void pollWebSockets() { webSocket.loop(); }
