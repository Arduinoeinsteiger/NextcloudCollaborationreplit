"""
SwissAirDry API - Code-Beispiele

Diese Datei enthält Beispielcode für die Nutzung der SwissAirDry API in verschiedenen Programmiersprachen.

@author Swiss Air Dry Team <info@swissairdry.com>
@copyright 2023-2025 Swiss Air Dry Team
"""

# Python-Beispiele
python_examples = {
    "device_list": """
# Geräteliste abrufen mit Python und Requests
import requests

API_KEY = "ihr_api_schlüssel"
BASE_URL = "https://api.vgnc.org/v1"

headers = {
    "X-API-Key": API_KEY
}

response = requests.get(f"{BASE_URL}/api/devices", headers=headers)

if response.status_code == 200:
    devices = response.json()
    for device in devices:
        print(f"Gerät: {device['name']} (ID: {device['device_id']}) - Status: {device['status']}")
else:
    print(f"Fehler: {response.status_code} - {response.text}")
""",

    "sensor_data_send": """
# Sensordaten senden mit Python und Requests
import requests
import json
from datetime import datetime

API_KEY = "ihr_api_schlüssel"
BASE_URL = "https://api.vgnc.org/v1"
DEVICE_ID = "device001"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

data = {
    "temperature": 22.5,
    "humidity": 65.8,
    "power": 450.0,
    "energy": 12.5,
    "relay_state": True,
    "runtime": 3600
}

response = requests.post(
    f"{BASE_URL}/api/device/{DEVICE_ID}/data", 
    headers=headers,
    data=json.dumps(data)
)

if response.status_code == 200:
    result = response.json()
    print(f"Daten erfolgreich gesendet. Status: {result['status']}")
    if 'relay_control' in result:
        print(f"Relay-Steuerungsbefehl empfangen: {result['relay_control']}")
else:
    print(f"Fehler: {response.status_code} - {response.text}")
""",

    "send_command": """
# Befehl an ein Gerät senden mit Python und Requests
import requests
import json

API_KEY = "ihr_api_schlüssel"
BASE_URL = "https://api.vgnc.org/v1"
DEVICE_ID = "device001"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

command = {
    "command": "relay",
    "value": True  # Relay einschalten
}

response = requests.post(
    f"{BASE_URL}/api/device/{DEVICE_ID}/command", 
    headers=headers,
    data=json.dumps(command)
)

if response.status_code == 200:
    result = response.json()
    print(f"Befehl gesendet: {result['message']}")
else:
    print(f"Fehler: {response.status_code} - {response.text}")
""",

    "api_client": """
# Einfacher API-Client für SwissAirDry
import requests
import json

class SwissAirDryClient:
    def __init__(self, api_key, base_url="https://api.vgnc.org/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_devices(self, skip=0, limit=100):
        """Gibt eine Liste aller Geräte zurück."""
        params = {"skip": skip, "limit": limit}
        response = requests.get(
            f"{self.base_url}/api/devices", 
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def get_device(self, device_id):
        """Gibt ein Gerät anhand seiner ID zurück."""
        response = requests.get(
            f"{self.base_url}/api/devices/{device_id}", 
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_device(self, device_data):
        """Erstellt ein neues Gerät."""
        response = requests.post(
            f"{self.base_url}/api/devices", 
            headers=self.headers,
            data=json.dumps(device_data)
        )
        response.raise_for_status()
        return response.json()
    
    def update_device(self, device_id, device_data):
        """Aktualisiert ein Gerät."""
        response = requests.put(
            f"{self.base_url}/api/devices/{device_id}", 
            headers=self.headers,
            data=json.dumps(device_data)
        )
        response.raise_for_status()
        return response.json()
    
    def delete_device(self, device_id):
        """Löscht ein Gerät."""
        response = requests.delete(
            f"{self.base_url}/api/devices/{device_id}", 
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_sensor_data(self, device_id, limit=100):
        """Gibt die Sensordaten eines Geräts zurück."""
        params = {"limit": limit}
        response = requests.get(
            f"{self.base_url}/api/device/{device_id}/data", 
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def send_sensor_data(self, device_id, sensor_data):
        """Sendet Sensordaten für ein Gerät."""
        response = requests.post(
            f"{self.base_url}/api/device/{device_id}/data", 
            headers=self.headers,
            data=json.dumps(sensor_data)
        )
        response.raise_for_status()
        return response.json()
    
    def send_command(self, device_id, command, value):
        """Sendet einen Befehl an ein Gerät."""
        command_data = {
            "command": command,
            "value": value
        }
        response = requests.post(
            f"{self.base_url}/api/device/{device_id}/command", 
            headers=self.headers,
            data=json.dumps(command_data)
        )
        response.raise_for_status()
        return response.json()

# Beispielverwendung:
if __name__ == "__main__":
    client = SwissAirDryClient(api_key="ihr_api_schlüssel")
    
    # Alle Geräte abrufen
    devices = client.get_devices()
    for device in devices:
        print(f"Gerät: {device['name']} (ID: {device['device_id']})")
    
    # Befehle an ein Gerät senden
    client.send_command("device001", "relay", True)
    
    # Sensordaten abrufen
    data = client.get_sensor_data("device001", limit=5)
    for entry in data:
        print(f"Temperatur: {entry['temperature']}°C, Luftfeuchtigkeit: {entry['humidity']}%")
""",
}

# JavaScript/Node.js-Beispiele
javascript_examples = {
    "device_list": """
// Geräteliste abrufen mit JavaScript/Node.js und Axios
const axios = require('axios');

const API_KEY = 'ihr_api_schlüssel';
const BASE_URL = 'https://api.vgnc.org/v1';

async function getDevices() {
  try {
    const response = await axios.get(`${BASE_URL}/api/devices`, {
      headers: {
        'X-API-Key': API_KEY
      }
    });
    
    const devices = response.data;
    devices.forEach(device => {
      console.log(`Gerät: ${device.name} (ID: ${device.device_id}) - Status: ${device.status}`);
    });
  } catch (error) {
    console.error(`Fehler: ${error.response ? error.response.status : error.message}`);
    if (error.response) {
      console.error(error.response.data);
    }
  }
}

getDevices();
""",

    "sensor_data_send": """
// Sensordaten senden mit JavaScript/Node.js und Axios
const axios = require('axios');

const API_KEY = 'ihr_api_schlüssel';
const BASE_URL = 'https://api.vgnc.org/v1';
const DEVICE_ID = 'device001';

async function sendSensorData() {
  try {
    const data = {
      temperature: 22.5,
      humidity: 65.8,
      power: 450.0,
      energy: 12.5,
      relay_state: true,
      runtime: 3600
    };
    
    const response = await axios.post(
      `${BASE_URL}/api/device/${DEVICE_ID}/data`, 
      data,
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const result = response.data;
    console.log(`Daten erfolgreich gesendet. Status: ${result.status}`);
    if (result.relay_control !== undefined) {
      console.log(`Relay-Steuerungsbefehl empfangen: ${result.relay_control}`);
    }
  } catch (error) {
    console.error(`Fehler: ${error.response ? error.response.status : error.message}`);
    if (error.response) {
      console.error(error.response.data);
    }
  }
}

sendSensorData();
""",

    "send_command": """
// Befehl an ein Gerät senden mit JavaScript/Node.js und Axios
const axios = require('axios');

const API_KEY = 'ihr_api_schlüssel';
const BASE_URL = 'https://api.vgnc.org/v1';
const DEVICE_ID = 'device001';

async function sendCommand() {
  try {
    const command = {
      command: 'relay',
      value: true  // Relay einschalten
    };
    
    const response = await axios.post(
      `${BASE_URL}/api/device/${DEVICE_ID}/command`, 
      command,
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const result = response.data;
    console.log(`Befehl gesendet: ${result.message}`);
  } catch (error) {
    console.error(`Fehler: ${error.response ? error.response.status : error.message}`);
    if (error.response) {
      console.error(error.response.data);
    }
  }
}

sendCommand();
""",

    "api_client": """
// SwissAirDry API-Client für JavaScript/Node.js
const axios = require('axios');

class SwissAirDryClient {
  constructor(apiKey, baseUrl = 'https://api.vgnc.org/v1') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json'
    };
  }
  
  async getDevices(skip = 0, limit = 100) {
    try {
      const response = await axios.get(`${this.baseUrl}/api/devices`, {
        params: { skip, limit },
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getDevice(deviceId) {
    try {
      const response = await axios.get(`${this.baseUrl}/api/devices/${deviceId}`, {
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async createDevice(deviceData) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/devices`, deviceData, {
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async updateDevice(deviceId, deviceData) {
    try {
      const response = await axios.put(`${this.baseUrl}/api/devices/${deviceId}`, deviceData, {
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async deleteDevice(deviceId) {
    try {
      const response = await axios.delete(`${this.baseUrl}/api/devices/${deviceId}`, {
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async getSensorData(deviceId, limit = 100) {
    try {
      const response = await axios.get(`${this.baseUrl}/api/device/${deviceId}/data`, {
        params: { limit },
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async sendSensorData(deviceId, sensorData) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/device/${deviceId}/data`, sensorData, {
        headers: this.defaultHeaders
      });
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  async sendCommand(deviceId, command, value) {
    try {
      const commandData = {
        command,
        value
      };
      const response = await axios.post(
        `${this.baseUrl}/api/device/${deviceId}/command`, 
        commandData,
        {
          headers: this.defaultHeaders
        }
      );
      return response.data;
    } catch (error) {
      this._handleError(error);
    }
  }
  
  _handleError(error) {
    if (error.response) {
      throw new Error(`API Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      throw new Error('Request Error: No response received from API');
    } else {
      throw new Error(`Error: ${error.message}`);
    }
  }
}

// Beispielverwendung:
async function example() {
  const client = new SwissAirDryClient('ihr_api_schlüssel');
  
  // Alle Geräte abrufen
  const devices = await client.getDevices();
  devices.forEach(device => {
    console.log(`Gerät: ${device.name} (ID: ${device.device_id})`);
  });
  
  // Befehle an ein Gerät senden
  await client.sendCommand('device001', 'relay', true);
  
  // Sensordaten abrufen
  const data = await client.getSensorData('device001', 5);
  data.forEach(entry => {
    console.log(`Temperatur: ${entry.temperature}°C, Luftfeuchtigkeit: ${entry.humidity}%`);
  });
}

// example().catch(console.error);
""",
}

# ESP8266/Arduino-Beispiele
arduino_examples = {
    "send_sensor_data": """
/**
 * SwissAirDry API - ESP8266/Arduino-Beispiel für Sensordatenübermittlung
 * 
 * Dieses Beispiel zeigt, wie ein ESP8266/ESP32 Sensordaten an die SwissAirDry API senden kann.
 * 
 * Benötigte Bibliotheken:
 * - ESP8266WiFi/WiFi (je nach Board)
 * - ESP8266HTTPClient/HTTPClient
 * - ArduinoJson
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// WLAN-Konfiguration
const char* WIFI_SSID = "IhrWLANNetzwerk";
const char* WIFI_PASSWORD = "IhrWLANPasswort";

// API-Konfiguration
const char* API_KEY = "ihr_api_schlüssel";
const char* API_HOST = "api.vgnc.org";
const int API_PORT = 443;
const char* API_PATH = "/v1/api/device/%s/data";
const char* DEVICE_ID = "device001";

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("SwissAirDry ESP8266/Arduino Beispiel");
  
  // Mit WLAN verbinden
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Verbindung zum WLAN herstellen");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.print("Verbunden mit IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Sensordaten sammeln (hier als Beispiel simulierte Daten)
    float temperature = 22.5;  // In °C
    float humidity = 65.8;     // In %
    float power = 450.0;       // In Watt
    float energy = 12.5;       // In kWh
    bool relayState = true;    // Relais-Status
    unsigned long runtime = 3600; // Laufzeit in Sekunden
    
    // Sensordaten an API senden
    if (sendSensorData(temperature, humidity, power, energy, relayState, runtime)) {
      Serial.println("Daten erfolgreich gesendet");
    } else {
      Serial.println("Fehler beim Senden der Daten");
    }
  }
  
  // 5 Minuten warten bis zum nächsten Senden
  delay(300000);
}

/**
 * Sendet Sensordaten an die SwissAirDry API
 */
bool sendSensorData(float temperature, float humidity, float power, float energy, bool relayState, unsigned long runtime) {
  WiFiClientSecure client;
  client.setInsecure(); // In der Produktion besser mit Zertifikat arbeiten
  
  // HTTP-Client initialisieren
  HTTPClient http;
  
  char url[128];
  snprintf(url, sizeof(url), API_PATH, DEVICE_ID);
  
  Serial.print("URL: ");
  Serial.println(url);
  
  // HTTP-Anfrage starten
  http.begin(client, API_HOST, API_PORT, url, true);
  
  // Header hinzufügen
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);
  
  // JSON-Daten erstellen
  StaticJsonDocument<256> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["power"] = power;
  doc["energy"] = energy;
  doc["relay_state"] = relayState;
  doc["runtime"] = runtime;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  Serial.print("Sende Daten: ");
  Serial.println(requestBody);
  
  // POST-Anfrage senden
  int httpCode = http.POST(requestBody);
  
  Serial.print("HTTP-Statuscode: ");
  Serial.println(httpCode);
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.print("Antwort: ");
    Serial.println(response);
    
    // JSON-Antwort verarbeiten
    StaticJsonDocument<128> responseDoc;
    DeserializationError error = deserializeJson(responseDoc, response);
    
    if (!error) {
      // Prüfen, ob ein Relay-Steuerungsbefehl erhalten wurde
      if (responseDoc.containsKey("relay_control")) {
        bool newRelayState = responseDoc["relay_control"];
        Serial.print("Neuer Relay-Status empfangen: ");
        Serial.println(newRelayState ? "EIN" : "AUS");
        
        // Hier den Relay-Status aktualisieren
        // digitalWrite(RELAY_PIN, newRelayState ? HIGH : LOW);
      }
      
      http.end();
      return true;
    }
  }
  
  http.end();
  return false;
}
""",

    "mqtt_client": """
/**
 * SwissAirDry API - ESP8266/Arduino-Beispiel für MQTT-Kommunikation
 * 
 * Dieses Beispiel zeigt, wie ein ESP8266/ESP32 mit dem SwissAirDry MQTT-Broker kommunizieren kann.
 * 
 * Benötigte Bibliotheken:
 * - ESP8266WiFi/WiFi (je nach Board)
 * - PubSubClient
 * - ArduinoJson
 */

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WLAN-Konfiguration
const char* WIFI_SSID = "IhrWLANNetzwerk";
const char* WIFI_PASSWORD = "IhrWLANPasswort";

// MQTT-Konfiguration
const char* MQTT_HOST = "mqtt.swissairdry.com";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "mqtt_user";  // Falls Authentifizierung erforderlich
const char* MQTT_PASSWORD = "mqtt_password";  // Falls Authentifizierung erforderlich
const char* MQTT_CLIENT_ID = "ESP8266_Client";  // Eindeutige Client-ID

// Gerätekonfiguration
const char* DEVICE_ID = "device001";
const char* MQTT_TOPIC_DATA = "swissairdry/%s/data";      // Für Sensordaten
const char* MQTT_TOPIC_STATUS = "swissairdry/%s/status";  // Für Statusmeldungen
const char* MQTT_TOPIC_CMD = "swissairdry/%s/cmd/#";      // Für Befehle
const char* MQTT_TOPIC_CMD_RELAY = "swissairdry/%s/cmd/relay";  // Für Relay-Befehle

// GPIO-Konfiguration
const int RELAY_PIN = D1;  // Relais am Pin D1

// Globale Variablen
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
unsigned long lastMsgTime = 0;
const long msgInterval = 60000;  // Messintervall in Millisekunden (60 Sekunden)

void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("SwissAirDry MQTT-Client Beispiel");
  
  // GPIO initialisieren
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // Relay initial ausschalten
  
  // Mit WLAN verbinden
  setupWifi();
  
  // MQTT-Client konfigurieren
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  // MQTT-Verbindung überprüfen und ggf. wiederherstellen
  if (!mqttClient.connected()) {
    reconnectMqtt();
  }
  mqttClient.loop();
  
  // Regelmäßiges Senden von Sensordaten
  unsigned long now = millis();
  if (now - lastMsgTime > msgInterval) {
    lastMsgTime = now;
    sendSensorData();
  }
}

/**
 * Stellt die WLAN-Verbindung her
 */
void setupWifi() {
  delay(10);
  Serial.println();
  Serial.print("Verbindung zu WLAN herstellen: ");
  Serial.println(WIFI_SSID);
  
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WLAN verbunden");
  Serial.print("IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

/**
 * Stellt die MQTT-Verbindung her
 */
void reconnectMqtt() {
  while (!mqttClient.connected()) {
    Serial.print("Verbindung zum MQTT-Broker herstellen...");
    
    // Verbindung mit Authentifizierung
    if (mqttClient.connect(MQTT_CLIENT_ID, MQTT_USER, MQTT_PASSWORD)) {
      Serial.println("verbunden");
      
      // Status veröffentlichen
      publishStatus("online");
      
      // Befehlsthemen abonnieren
      char cmdTopic[50];
      snprintf(cmdTopic, sizeof(cmdTopic), MQTT_TOPIC_CMD, DEVICE_ID);
      mqttClient.subscribe(cmdTopic);
      
      Serial.print("Abonniert: ");
      Serial.println(cmdTopic);
    } else {
      Serial.print("fehlgeschlagen, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" Wiederholung in 5 Sekunden");
      delay(5000);
    }
  }
}

/**
 * MQTT-Callback-Funktion für eingehende Nachrichten
 */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Nachricht empfangen [");
  Serial.print(topic);
  Serial.print("] ");
  
  // Nachricht in String umwandeln
  char message[length + 1];
  memcpy(message, payload, length);
  message[length] = '\\0';
  
  Serial.println(message);
  
  // Relay-Befehl verarbeiten
  char relayTopic[50];
  snprintf(relayTopic, sizeof(relayTopic), MQTT_TOPIC_CMD_RELAY, DEVICE_ID);
  
  if (strcmp(topic, relayTopic) == 0) {
    if (strcmp(message, "true") == 0 || strcmp(message, "1") == 0) {
      digitalWrite(RELAY_PIN, HIGH);
      Serial.println("Relay eingeschaltet");
    } else if (strcmp(message, "false") == 0 || strcmp(message, "0") == 0) {
      digitalWrite(RELAY_PIN, LOW);
      Serial.println("Relay ausgeschaltet");
    }
  }
}

/**
 * Sendet den Gerätestatus an den MQTT-Broker
 */
void publishStatus(const char* status) {
  char topic[50];
  snprintf(topic, sizeof(topic), MQTT_TOPIC_STATUS, DEVICE_ID);
  
  StaticJsonDocument<128> doc;
  doc["status"] = status;
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  
  char buffer[128];
  size_t n = serializeJson(doc, buffer);
  
  mqttClient.publish(topic, buffer, true);  // Mit retained-Flag
  Serial.print("Status veröffentlicht: ");
  Serial.println(buffer);
}

/**
 * Sendet Sensordaten an den MQTT-Broker
 */
void sendSensorData() {
  // Sensordaten sammeln (hier als Beispiel simulierte Daten)
  float temperature = 22.5;  // In °C
  float humidity = 65.8;     // In %
  float power = 450.0;       // In Watt
  float energy = 12.5;       // In kWh
  bool relayState = digitalRead(RELAY_PIN) == HIGH;  // Aktueller Relay-Status
  unsigned long runtime = millis() / 1000;  // Laufzeit in Sekunden
  
  // JSON-Daten erstellen
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = millis();
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["power"] = power;
  doc["energy"] = energy;
  doc["relay_state"] = relayState;
  doc["runtime"] = runtime;
  
  char buffer[256];
  size_t n = serializeJson(doc, buffer);
  
  // Thema erstellen und veröffentlichen
  char topic[50];
  snprintf(topic, sizeof(topic), MQTT_TOPIC_DATA, DEVICE_ID);
  
  mqttClient.publish(topic, buffer);
  Serial.print("Sensordaten veröffentlicht: ");
  Serial.println(buffer);
}
""",
}

# Beispiele für die Verwendung der Dokumentation
"""
Um die Code-Beispiele aus dieser Datei in der API-Dokumentation zu verwenden,
können Sie den folgenden Code verwenden:

```python
from swissairdry.api.docs.code_examples import python_examples, javascript_examples, arduino_examples

# Python-Beispiel für das Abrufen von Geräten in der Dokumentation anzeigen
print(python_examples["device_list"])

# JavaScript-Beispiel für das Senden von Sensordaten anzeigen
print(javascript_examples["sensor_data_send"])

# Arduino/ESP8266-Beispiel für MQTT-Kommunikation anzeigen
print(arduino_examples["mqtt_client"])
```
"""