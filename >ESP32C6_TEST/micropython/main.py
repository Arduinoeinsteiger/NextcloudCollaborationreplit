"""
SwissAirDry MicroPython Client für ESP32-S6
-------------------------------------------

Dieses Skript ist die Hauptanwendung für den ESP32-S6 mit MicroPython.
Es nutzt die Module sensor.py und mqtt_client.py, um die Funktionalität 
des SwissAirDry-Sensor-Knotens zu implementieren.

Funktionen:
- Verbindung mit WLAN und MQTT-Broker
- Regelmäßige Übertragung von Sensordaten (Temperatur, Luftfeuchtigkeit, etc.)
- Empfang und Verarbeitung von Steuerungsbefehlen
- Automatische Wiederverbindung bei Verbindungsabbruch
- Stromsparfunktionen für längere Akkulaufzeit
"""

import time
import json
import network
import machine
from machine import Pin, deepsleep, Timer

# Importieren der eigenen Module
from sensor import SensorManager
from mqtt_client import SwissAirDryMQTTClient

# Standardkonfigurationsdatei
CONFIG_FILE = "config.json"

# Globale Variablen
led = None
mqtt_client = None
sensor_manager = None
timer = None
last_report_time = 0
device_config = {}

# LED für Status-Anzeigen einrichten
def setup_led():
    global led
    # LED-Pin aus Konfiguration laden oder Standardwert verwenden
    led_pin = device_config.get("display", {}).get("led_pin", 2)
    led = Pin(led_pin, Pin.OUT)
    led.off()

# LED-Blinkmuster für verschiedene Status
def blink_led(count, delay_ms=200):
    if led is None:
        return
    
    for i in range(count):
        led.on()
        time.sleep_ms(delay_ms)
        led.off()
        if i < count - 1:
            time.sleep_ms(delay_ms)

# Konfiguration aus Datei laden
def load_config(config_file=CONFIG_FILE):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"Konfiguration geladen aus {config_file}")
        return config
    except (OSError, ValueError) as e:
        print(f"Fehler beim Laden der Konfiguration: {e}")
        print("Verwende Standardkonfiguration")
        return {
            "device": {
                "id": "ESP32S6_001",
                "name": "SwissAirDry Sensor 1",
                "firmware_version": "1.0.0"
            },
            "wifi": {
                "ssid": "SwissAirDry-Network",
                "password": "SwissAirDry2025",
                "timeout": 20
            },
            "mqtt": {
                "broker": "192.168.1.100",
                "port": 1883,
                "topic_prefix": "swissairdry"
            },
            "reporting": {
                "interval": 60
            },
            "power": {
                "sleep_time": 300,
                "low_power_mode": False
            }
        }

# WiFi-Verbindung herstellen
def connect_wifi():
    wifi_config = device_config.get("wifi", {})
    ssid = wifi_config.get("ssid", "SwissAirDry-Network")
    password = wifi_config.get("password", "SwissAirDry2025")
    timeout = wifi_config.get("timeout", 20)
    
    print(f"Verbinde mit WLAN: {ssid}")
    # Status-LED schnell blinken während Verbindungsaufbau
    blink_led(3, 100)
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if not wlan.isconnected():
        wlan.connect(ssid, password)
        
        # Auf Verbindung warten
        max_attempts = timeout
        attempt = 0
        
        while not wlan.isconnected() and attempt < max_attempts:
            print(f"Warte auf WLAN-Verbindung... ({attempt+1}/{max_attempts})")
            attempt += 1
            # LED kurz blinken lassen
            led.on()
            time.sleep_ms(50)
            led.off()
            time.sleep_ms(950)  # Fast 1 Sekunde Pause
        
    if wlan.isconnected():
        print(f"WLAN verbunden. IP: {wlan.ifconfig()[0]}")
        # Bei erfolgreicher Verbindung zweimal blinken
        blink_led(2, 200)
        return True
    else:
        print("WLAN-Verbindung fehlgeschlagen")
        # Bei fehlgeschlagener Verbindung 5-mal schnell blinken
        blink_led(5, 100)
        return False

# Handler für empfangene MQTT-Nachrichten
def mqtt_message_handler(topic, msg):
    device_id = device_config.get("device", {}).get("id", "ESP32S6_001")
    topic_prefix = device_config.get("mqtt", {}).get("topic_prefix", "swissairdry")
    
    try:
        # JSON-Nachricht dekodieren
        message_data = json.loads(msg)
        
        # Kommando verarbeiten
        if topic == f"{topic_prefix}/{device_id}/command":
            handle_command(message_data)
        # Konfiguration verarbeiten
        elif topic == f"{topic_prefix}/{device_id}/config":
            handle_config(message_data)
    except Exception as e:
        print(f"Fehler bei der Verarbeitung der MQTT-Nachricht: {e}")

# Verarbeitung von Kommandos
def handle_command(command):
    if "action" not in command:
        print("Ungültiges Kommando: 'action' fehlt")
        return
    
    action = command["action"]
    
    try:
        if action == "restart":
            print("Neustart wird durchgeführt...")
            machine.reset()
        
        elif action == "sleep":
            sleep_time = device_config.get("power", {}).get("sleep_time", 300)
            duration = command.get("duration", sleep_time)
            print(f"Gehe in Deep-Sleep für {duration} Sekunden...")
            # MQTT-Verbindung ordnungsgemäß trennen
            if mqtt_client:
                mqtt_client.disconnect()
            deepsleep(duration * 1000)
        
        elif action == "led_on":
            if led:
                led.on()
                print("LED eingeschaltet")
        
        elif action == "led_off":
            if led:
                led.off()
                print("LED ausgeschaltet")
        
        elif action == "blink":
            count = command.get("count", 3)
            delay = command.get("delay", 200)
            blink_led(count, delay)
            print(f"LED blinkt {count} mal")
        
        elif action == "report_now":
            report_sensor_data()
            print("Sensordaten sofort gesendet")
        
        elif action == "calibrate":
            if sensor_manager and "sensor_type" in command and "offset" in command:
                sensor_type = command["sensor_type"]
                offset = command["offset"]
                result = sensor_manager.calibrate(sensor_type, offset)
                print(f"Kalibrierung von {sensor_type} mit Offset {offset}: {'Erfolgreich' if result else 'Fehlgeschlagen'}")
        
        else:
            print(f"Unbekannte Aktion: {action}")
    
    except Exception as e:
        print(f"Fehler bei der Verarbeitung des Kommandos: {e}")

# Verarbeitung von Konfigurationsänderungen
def handle_config(new_config):
    global device_config
    
    try:
        # Konfiguration aktualisieren
        if "reporting" in new_config:
            if "interval" in new_config["reporting"]:
                device_config["reporting"]["interval"] = new_config["reporting"]["interval"]
                print(f"Reporting-Intervall aktualisiert: {new_config['reporting']['interval']} Sekunden")
        
        if "power" in new_config:
            if "sleep_time" in new_config["power"]:
                device_config["power"]["sleep_time"] = new_config["power"]["sleep_time"]
                print(f"Sleep-Zeit aktualisiert: {new_config['power']['sleep_time']} Sekunden")
            
            if "low_power_mode" in new_config["power"]:
                device_config["power"]["low_power_mode"] = new_config["power"]["low_power_mode"]
                print(f"Low-Power-Modus: {'Aktiviert' if new_config['power']['low_power_mode'] else 'Deaktiviert'}")
        
        # Konfiguration speichern
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(device_config, f)
            print("Konfiguration gespeichert")
        except OSError as e:
            print(f"Fehler beim Speichern der Konfiguration: {e}")
        
        # Bestätigungsnachricht senden
        if mqtt_client:
            response = {
                "status": "updated",
                "config": device_config
            }
            device_id = device_config.get("device", {}).get("id", "ESP32S6_001")
            topic_prefix = device_config.get("mqtt", {}).get("topic_prefix", "swissairdry")
            topic = f"{topic_prefix}/{device_id}/config/response"
            mqtt_client.client.publish(topic, json.dumps(response))
    
    except Exception as e:
        print(f"Fehler bei der Verarbeitung der Konfiguration: {e}")

# Sensordaten melden
def report_sensor_data():
    global last_report_time
    
    if not mqtt_client or not sensor_manager:
        return
    
    try:
        # LED einschalten während der Datenübertragung
        if led:
            led.on()
        
        # Sensordaten lesen
        sensor_data = sensor_manager.read_all()
        
        # Daten über MQTT senden
        mqtt_client.publish_telemetry(sensor_data)
        
        # Letzte Meldezeit aktualisieren
        last_report_time = time.time()
        
        # LED ausschalten
        if led:
            led.off()
    
    except Exception as e:
        print(f"Fehler beim Melden der Sensordaten: {e}")

# Timer-Callback für regelmäßige Aktionen
def timer_callback(timer):
    try:
        # MQTT-Verbindung prüfen
        if mqtt_client:
            mqtt_client.check_messages()
        
        # Prüfen, ob es Zeit ist, Daten zu senden
        current_time = time.time()
        report_interval = device_config.get("reporting", {}).get("interval", 60)
        
        if current_time - last_report_time >= report_interval:
            report_sensor_data()
    
    except Exception as e:
        print(f"Fehler im Timer-Callback: {e}")

# Hauptprogramm
def main():
    global device_config, sensor_manager, mqtt_client, timer, last_report_time
    
    try:
        print("\n--- SwissAirDry MicroPython Client für ESP32-S6 ---")
        
        # Konfiguration laden
        device_config = load_config()
        device_id = device_config.get("device", {}).get("id", "ESP32S6_001")
        print(f"Geräte-ID: {device_id}")
        
        # LED einrichten
        setup_led()
        
        # Einmalig schnell blinken zum Anzeigen des Startvorgangs
        blink_led(5, 100)
        
        # Sensor-Manager initialisieren
        sensor_manager = SensorManager(CONFIG_FILE)
        
        # Mit WLAN verbinden
        if not connect_wifi():
            # Bei fehlgeschlagener Verbindung in den Deep-Sleep gehen und später neu versuchen
            sleep_time = device_config.get("power", {}).get("sleep_time", 300)
            print(f"Gehe für {sleep_time} Sekunden in Deep-Sleep und versuche erneut...")
            deepsleep(sleep_time * 1000)
        
        # MQTT-Client initialisieren und verbinden
        mqtt_client = SwissAirDryMQTTClient(device_config, mqtt_message_handler)
        
        if not mqtt_client.connect():
            print("MQTT-Verbindung fehlgeschlagen, versuche erneut in einer Minute...")
            time.sleep(60)
            if not mqtt_client.connect():
                print("MQTT-Verbindung erneut fehlgeschlagen, starte neu...")
                machine.reset()
        
        # Aktuelle Zeit für Reporting speichern
        last_report_time = time.time()
        
        # Timer für regelmäßige Aktionen einrichten (alle 5 Sekunden)
        timer = Timer(0)
        timer.init(period=5000, mode=Timer.PERIODIC, callback=timer_callback)
        
        # Initialer Datenbericht
        report_sensor_data()
        
        print("Setup abgeschlossen. Gerät läuft...")
        
        # Prüfen, ob Low-Power-Modus aktiviert ist
        if device_config.get("power", {}).get("low_power_mode", False):
            print("Low-Power-Modus aktiv, melde Daten und gehe in Deep-Sleep...")
            # Warten, damit die Daten gesendet werden können
            time.sleep(5)
            # MQTT-Verbindung trennen
            mqtt_client.disconnect()
            # Timer deaktivieren
            timer.deinit()
            # In Deep-Sleep gehen
            sleep_time = device_config.get("power", {}).get("sleep_time", 300)
            deepsleep(sleep_time * 1000)
        
        # Haupt-Loop
        while True:
            # Meiste Arbeit wird vom Timer erledigt
            # Hier können zusätzliche Aufgaben ausgeführt werden
            time.sleep(1)
        
    except Exception as e:
        print(f"Unbehandelter Fehler: {e}")
        # Bei kritischem Fehler neu starten
        machine.reset()

# Programm starten
if __name__ == "__main__":
    main()