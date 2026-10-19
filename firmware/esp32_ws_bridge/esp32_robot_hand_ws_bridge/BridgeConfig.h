#pragma once
#include <Arduino.h>
static const char AP_SSID[] = "RobotHand_ESP32";
static const char AP_PASSWORD[] = "12345678";
static const uint16_t WS_PORT = 81;
static const uint32_t UART_BAUD = 250000UL;
static const int UART2_RX = 16;
static const int UART2_TX = 17;
static const unsigned long STATUS_INTERVAL_MS = 2000UL;
static const byte PACKET_SIZE = 9;
