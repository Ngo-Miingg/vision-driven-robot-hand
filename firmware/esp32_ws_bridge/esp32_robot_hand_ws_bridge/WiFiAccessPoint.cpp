#include "WiFiAccessPoint.h"
#include "BridgeConfig.h"
#include <WiFi.h>
void startAccessPoint() {
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false);
  WiFi.softAP(AP_SSID, AP_PASSWORD, 1, false, 1);
}
void printBridgeIdentity() {
  Serial.print(F("AP SSID: ")); Serial.println(AP_SSID);
  Serial.print(F("AP IP: ")); Serial.println(WiFi.softAPIP());
  Serial.print(F("WS PORT: ")); Serial.println(WS_PORT);
  Serial.print(F("UART2 TX: GPIO")); Serial.println(UART2_TX);
  Serial.print(F("UART BAUD: ")); Serial.println(UART_BAUD);
}
