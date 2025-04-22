// SwissAirDry Sekundäres Board für Wemos D1 Mini
// Erweiterungsboard für zusätzliche Sensoren und Funktionen
// Kommunikation über I2C mit dem Hauptboard

#include <Wire.h>
#include <ESP8266WiFi.h>
#include <EEPROM.h>

// ----- HARDWARE-KONFIGURATION -----
#define LED_PIN 2         // GPIO2 (D4 auf Wemos D1 Mini) - Blau LED on-board
#define LED_ON LOW        // LED ist aktiv LOW (invertiert)
#define LED_OFF HIGH

// Freie Pins für Sensoren und Aktoren
#define GPIO_D5 D5        // Freier GPIO-Pin
#define GPIO_D6 D6        // Freier GPIO-Pin
#define GPIO_D7 D7        // Freier GPIO-Pin
#define GPIO_D8 D8        // Freier GPIO-Pin
#define ANALOG_PIN A0     // Analoger Eingang

// I2C-Konfiguration
#define I2C_SLAVE_ADDR 0x42  // I2C-Slave-Adresse des Sekundärboards

// Datenstruktur für den Austausch mit dem Hauptboard
struct SensorData {
  float temperature;       // Temperatur in °C
  float humidity;          // Luftfeuchtigkeit in %
  float pressure;          // Luftdruck in hPa
  float voltage;           // Spannung in V
  uint16_t light;          // Lichtsensor-Wert
  uint8_t status;          // Status-Flags
};

SensorData sensorData;     // Aktuelle Sensordaten
bool hasNewData = false;   // Flag für neue Daten

// Puffer für eingehende I2C-Befehle
volatile uint8_t receiveBuffer[32];
volatile uint8_t receiveIndex = 0;

// Hostname mit eindeutiger Chip-ID
String hostname = "SwissAirDry-Secondary-";

void setup() {
  // Serielle Verbindung starten
  Serial.begin(115200);
  Serial.println("\n\nSwissAirDry Secondary Board");

  // EEPROM initialisieren (für Einstellungen)
  EEPROM.begin(512);

  // Eindeutigen Hostnamen erstellen
  uint16_t chipId = ESP.getChipId() & 0xFFFF;
  hostname += String(chipId, HEX);
  Serial.print("Hostname: ");
  Serial.println(hostname);

  // LED konfigurieren
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LED_OFF);

  // GPIOs konfigurieren
  pinMode(GPIO_D5, INPUT_PULLUP);  // Kann nach Bedarf geändert werden
  pinMode(GPIO_D6, INPUT_PULLUP);  // Kann nach Bedarf geändert werden
  pinMode(GPIO_D7, OUTPUT);        // Kann nach Bedarf geändert werden
  pinMode(GPIO_D8, OUTPUT);        // Kann nach Bedarf geändert werden

  // I2C als Slave starten
  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(requestEvent);
  
  Serial.println("I2C-Slave gestartet, bereit für Kommunikation");
  Serial.print("I2C-Adresse: 0x");
  Serial.println(I2C_SLAVE_ADDR, HEX);

  // Initialisierung der Sensordaten
  resetSensorData();

  // Bereit-Signal mit LED
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, LED_ON);
    delay(100);
    digitalWrite(LED_PIN, LED_OFF);
    delay(100);
  }
}

void loop() {
  // Sensoren regelmäßig auslesen
  readSensors();
  
  // Status-LED blinken lassen (Heartbeat)
  static unsigned long lastBlinkTime = 0;
  if (millis() - lastBlinkTime > 5000) { // Alle 5 Sekunden
    lastBlinkTime = millis();
    digitalWrite(LED_PIN, LED_ON);
    delay(50);
    digitalWrite(LED_PIN, LED_OFF);
  }
  
  // Debug-Ausgabe falls neue Daten verfügbar sind
  static unsigned long lastDebugTime = 0;
  if (hasNewData && millis() - lastDebugTime > 10000) { // Alle 10 Sekunden
    lastDebugTime = millis();
    printSensorData();
    hasNewData = false;
  }
  
  // Auf I2C-Kommunikation warten (wird durch Interrupts behandelt)
  delay(100);
}

// Sensordaten zurücksetzen
void resetSensorData() {
  sensorData.temperature = 0.0;
  sensorData.humidity = 0.0;
  sensorData.pressure = 0.0;
  sensorData.voltage = 0.0;
  sensorData.light = 0;
  sensorData.status = 0;
}

// Sensoren auslesen
void readSensors() {
  // Analogwert vom A0-Pin lesen (z.B. für Lichtsensor)
  int analogValue = analogRead(ANALOG_PIN);
  sensorData.light = analogValue;
  
  // Spannung messen (Beispiel)
  float voltage = analogValue * (3.3 / 1023.0);
  sensorData.voltage = voltage;
  
  // Weitere Sensordaten könnten hier gelesen werden
  // z.B. von DHT22, BMP280, etc.
  
  // Status-Flags aktualisieren (Beispiel)
  if (digitalRead(GPIO_D5) == LOW) {
    sensorData.status |= 0x01;  // Bit 0 setzen
  } else {
    sensorData.status &= ~0x01; // Bit 0 zurücksetzen
  }
  
  hasNewData = true;
}

// I2C-Daten an Master senden
void requestEvent() {
  // Sensordaten als Binärdaten senden
  Wire.write((uint8_t*)&sensorData, sizeof(SensorData));
  
  // LED kurz blinken lassen, um Datenübertragung anzuzeigen
  digitalWrite(LED_PIN, LED_ON);
  delayMicroseconds(100);
  digitalWrite(LED_PIN, LED_OFF);
}

// I2C-Daten vom Master empfangen
void receiveEvent(int numBytes) {
  receiveIndex = 0;
  
  while (Wire.available()) {
    if (receiveIndex < sizeof(receiveBuffer)) {
      receiveBuffer[receiveIndex++] = Wire.read();
    } else {
      // Pufferüberlauf vermeiden
      Wire.read();
    }
  }
  
  // Befehle verarbeiten, wenn mindestens 1 Byte empfangen wurde
  if (receiveIndex > 0) {
    processCommand();
  }
}

// Empfangene Befehle verarbeiten
void processCommand() {
  uint8_t command = receiveBuffer[0];
  
  switch (command) {
    case 0x01:  // Reset-Befehl
      resetSensorData();
      break;
      
    case 0x02:  // GPIO-Befehl
      if (receiveIndex >= 3) {
        uint8_t pin = receiveBuffer[1];
        uint8_t value = receiveBuffer[2];
        
        // GPIO-Pin setzen (Beispiel)
        if (pin == 7) {
          digitalWrite(GPIO_D7, value ? HIGH : LOW);
        } else if (pin == 8) {
          digitalWrite(GPIO_D8, value ? HIGH : LOW);
        }
      }
      break;
      
    case 0x03:  // Konfigurationsbefehl
      // Hier könnten Konfigurationseinstellungen gesetzt werden
      break;
      
    default:
      // Unbekannter Befehl
      break;
  }
}

// Sensordaten zur Debug-Ausgabe anzeigen
void printSensorData() {
  Serial.println("--- Sensordaten ---");
  Serial.print("Licht: ");
  Serial.println(sensorData.light);
  Serial.print("Spannung: ");
  Serial.print(sensorData.voltage);
  Serial.println(" V");
  
  if (sensorData.temperature > 0) {
    Serial.print("Temperatur: ");
    Serial.print(sensorData.temperature);
    Serial.println(" °C");
  }
  
  if (sensorData.humidity > 0) {
    Serial.print("Luftfeuchtigkeit: ");
    Serial.print(sensorData.humidity);
    Serial.println(" %");
  }
  
  if (sensorData.pressure > 0) {
    Serial.print("Luftdruck: ");
    Serial.print(sensorData.pressure);
    Serial.println(" hPa");
  }
  
  Serial.print("Status: 0x");
  Serial.println(sensorData.status, HEX);
  Serial.println("------------------");
}