#include <WiFi.h>
#include <WebSocketsServer.h>

static const char *AP_SSID = "RobotHand_ESP32";
static const char *AP_PASSWORD = "12345678";
static const uint16_t WS_PORT = 81;
static const uint32_t UART_BAUD = 250000UL;
static const int UART2_RX = 16;
static const int UART2_TX = 17;
static const unsigned long STATUS_INTERVAL_MS = 2000UL;

WebSocketsServer webSocket(WS_PORT);

uint32_t wsConnectCount = 0;
uint32_t wsDisconnectCount = 0;
uint32_t binaryRxCount = 0;
uint32_t binaryForwardCount = 0;
uint32_t binaryDropLengthCount = 0;
uint32_t binaryDropStartCount = 0;
uint32_t binaryDropChecksumCount = 0;
uint32_t textForwardCount = 0;
uint8_t activeClient = 255;
unsigned long lastStatusMs = 0;

uint8_t xorChecksum(const uint8_t *data, size_t length) {
  uint8_t checksum = 0;
  for (size_t i = 0; i < length; i++) {
    checksum ^= data[i];
  }
  return checksum;
}

bool validBinaryPacket(const uint8_t *payload, size_t length) {
  if (length != 8) {
    binaryDropLengthCount++;
    return false;
  }
  if (payload[0] != 0xAA) {
    binaryDropStartCount++;
    return false;
  }
  if (xorChecksum(payload, 7) != payload[7]) {
    binaryDropChecksumCount++;
    return false;
  }
  return true;
}

void forwardBinaryPacket(const uint8_t *payload, size_t length) {
  binaryRxCount++;
  if (!validBinaryPacket(payload, length)) {
    return;
  }
  Serial2.write(payload, length);
  binaryForwardCount++;
}

void forwardTextPacket(const uint8_t *payload, size_t length) {
  Serial2.write(payload, length);
  Serial2.write('\n');
  textForwardCount++;
}

void printStatus() {
  Serial.print(F("STATUS clients="));
  Serial.print(WiFi.softAPgetStationNum());
  Serial.print(F(" active="));
  if (activeClient == 255) {
    Serial.print(F("none"));
  } else {
    Serial.print(activeClient);
  }
  Serial.print(F(" rx="));
  Serial.print(binaryRxCount);
  Serial.print(F(" fwd="));
  Serial.print(binaryForwardCount);
  Serial.print(F(" drop_len="));
  Serial.print(binaryDropLengthCount);
  Serial.print(F(" drop_start="));
  Serial.print(binaryDropStartCount);
  Serial.print(F(" drop_sum="));
  Serial.print(binaryDropChecksumCount);
  Serial.print(F(" text="));
  Serial.print(textForwardCount);
  Serial.print(F(" heap="));
  Serial.println(ESP.getFreeHeap());
}

void webSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      wsConnectCount++;
      if (activeClient != 255 && activeClient != num) {
        webSocket.disconnect(activeClient);
      }
      activeClient = num;
      Serial.print(F("WS CONNECTED "));
      Serial.print(num);
      Serial.print(F(" ip="));
      Serial.println(webSocket.remoteIP(num));
      break;

    case WStype_DISCONNECTED:
      wsDisconnectCount++;
      if (activeClient == num) {
        activeClient = 255;
      }
      Serial.print(F("WS DISCONNECTED "));
      Serial.print(num);
      Serial.print(F(" total="));
      Serial.println(wsDisconnectCount);
      break;

    case WStype_TEXT:
      if (num == activeClient) {
        forwardTextPacket(payload, length);
      }
      break;

    case WStype_BIN:
      if (num == activeClient) {
        forwardBinaryPacket(payload, length);
      }
      break;

    case WStype_PING:
      break;

    case WStype_PONG:
      break;

    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);

  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);
  WiFi.softAP(AP_SSID, AP_PASSWORD, 1, false, 1);
  Serial2.begin(UART_BAUD, SERIAL_8N1, UART2_RX, UART2_TX);

  webSocket.begin();
  webSocket.onEvent(webSocketEvent);

  Serial.println(F("ESP32 WS BRIDGE READY"));
  Serial.print(F("AP SSID: "));
  Serial.println(AP_SSID);
  Serial.print(F("AP IP: "));
  Serial.println(WiFi.softAPIP());
  Serial.print(F("WS PORT: "));
  Serial.println(WS_PORT);
  Serial.print(F("UART2 TX: GPIO"));
  Serial.println(UART2_TX);
  Serial.print(F("UART BAUD: "));
  Serial.println(UART_BAUD);
}

void loop() {
  webSocket.loop();

  unsigned long now = millis();
  if (now - lastStatusMs >= STATUS_INTERVAL_MS) {
    lastStatusMs = now;
    printStatus();
  }
}
