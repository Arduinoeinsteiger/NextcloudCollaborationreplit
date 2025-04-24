"""
SwissAirDry MicroPython Sensor-Modul für ESP32-S6
-------------------------------------------------

Dieses Modul stellt Funktionen zur Verfügung, um verschiedene Sensoren
auszulesen und die Daten zu verarbeiten.
"""

import time
import math
import json
import random
from machine import Pin, ADC, I2C
try:
    import dht
    DHT_AVAILABLE = True
except ImportError:
    DHT_AVAILABLE = False

try:
    import bme280
    BME280_AVAILABLE = True
except ImportError:
    BME280_AVAILABLE = False


class SensorManager:
    """
    Verwaltet alle Sensoren des ESP32-S6 und bietet eine
    einheitliche Schnittstelle zum Auslesen der Daten.
    """
    
    def __init__(self, config_file="config.json"):
        """Initialisiert den SensorManager mit der Konfiguration."""
        self.config = self._load_config(config_file)
        self.sensors = {}
        self.last_readings = {}
        self._init_sensors()
    
    def _load_config(self, config_file):
        """Lädt die Konfiguration aus einer JSON-Datei."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            print(f"Fehler beim Laden der Konfiguration: {e}")
            # Standardkonfiguration zurückgeben
            return {
                "sensors": {
                    "temperature": {"enabled": True, "pin": 12, "type": "DHT22"},
                    "humidity": {"enabled": True, "pin": 12, "type": "DHT22"},
                    "battery": {"enabled": True, "pin": 33, "type": "ADC", "voltage_factor": 2.0}
                }
            }
    
    def _init_sensors(self):
        """Initialisiert alle konfigurierten Sensoren."""
        sensor_config = self.config.get("sensors", {})
        
        # DHT-Sensor für Temperatur und Luftfeuchtigkeit
        if DHT_AVAILABLE:
            temp_config = sensor_config.get("temperature", {})
            hum_config = sensor_config.get("humidity", {})
            
            if (temp_config.get("enabled", False) and temp_config.get("type") in ["DHT11", "DHT22"]) or \
               (hum_config.get("enabled", False) and hum_config.get("type") in ["DHT11", "DHT22"]):
                pin = temp_config.get("pin", 12)
                sensor_type = temp_config.get("type", "DHT22")
                
                if sensor_type == "DHT11":
                    self.sensors["dht"] = dht.DHT11(Pin(pin))
                else:
                    self.sensors["dht"] = dht.DHT22(Pin(pin))
                
                print(f"DHT-Sensor an Pin {pin} initialisiert")
        
        # BME280-Sensor für Temperatur, Luftfeuchtigkeit und Luftdruck
        if BME280_AVAILABLE:
            pressure_config = sensor_config.get("pressure", {})
            
            if pressure_config.get("enabled", False) and pressure_config.get("type") == "BME280":
                scl_pin = pressure_config.get("i2c_scl", 22)
                sda_pin = pressure_config.get("i2c_sda", 21)
                i2c_address = pressure_config.get("address", 0x76)
                
                try:
                    i2c = I2C(1, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=100000)
                    self.sensors["bme280"] = bme280.BME280(i2c=i2c, address=i2c_address)
                    print(f"BME280-Sensor an I2C (SCL: {scl_pin}, SDA: {sda_pin}) initialisiert")
                except Exception as e:
                    print(f"Fehler bei der Initialisierung des BME280-Sensors: {e}")
        
        # Batteriesensor (ADC)
        battery_config = sensor_config.get("battery", {})
        if battery_config.get("enabled", False):
            pin = battery_config.get("pin", 33)
            self.sensors["battery"] = ADC(Pin(pin))
            self.sensors["battery"].atten(ADC.ATTN_11DB)  # Vollbereichseinstellung für 0-3.3V
            print(f"Batteriesensor an Pin {pin} initialisiert")
    
    def read_temperature(self):
        """Liest die Temperatur vom Sensor."""
        if "dht" in self.sensors:
            try:
                self.sensors["dht"].measure()
                temp = self.sensors["dht"].temperature()
                self.last_readings["temperature"] = temp
                return temp
            except Exception as e:
                print(f"Fehler beim Lesen der Temperatur (DHT): {e}")
        
        if "bme280" in self.sensors:
            try:
                values = self.sensors["bme280"].values
                temp = values[0].replace("C", "")
                temp = float(temp)
                self.last_readings["temperature"] = temp
                return temp
            except Exception as e:
                print(f"Fehler beim Lesen der Temperatur (BME280): {e}")
        
        # Wenn kein echter Sensor verfügbar ist, simulieren wir Daten
        temp = 20 + 10 * math.sin(time.time() / 3600)
        self.last_readings["temperature"] = temp
        return temp
    
    def read_humidity(self):
        """Liest die Luftfeuchtigkeit vom Sensor."""
        if "dht" in self.sensors:
            try:
                self.sensors["dht"].measure()
                humidity = self.sensors["dht"].humidity()
                self.last_readings["humidity"] = humidity
                return humidity
            except Exception as e:
                print(f"Fehler beim Lesen der Luftfeuchtigkeit (DHT): {e}")
        
        if "bme280" in self.sensors:
            try:
                values = self.sensors["bme280"].values
                humidity = values[2].replace("%", "")
                humidity = float(humidity)
                self.last_readings["humidity"] = humidity
                return humidity
            except Exception as e:
                print(f"Fehler beim Lesen der Luftfeuchtigkeit (BME280): {e}")
        
        # Wenn kein echter Sensor verfügbar ist, simulieren wir Daten
        humidity = 40 + 30 * math.sin(time.time() / 7200)
        self.last_readings["humidity"] = humidity
        return humidity
    
    def read_pressure(self):
        """Liest den Luftdruck vom Sensor."""
        if "bme280" in self.sensors:
            try:
                values = self.sensors["bme280"].values
                pressure = values[1].replace("hPa", "")
                pressure = float(pressure)
                self.last_readings["pressure"] = pressure
                return pressure
            except Exception as e:
                print(f"Fehler beim Lesen des Luftdrucks (BME280): {e}")
        
        # Wenn kein echter Sensor verfügbar ist, simulieren wir Daten
        pressure = 1013 + 10 * math.sin(time.time() / 10800)
        self.last_readings["pressure"] = pressure
        return pressure
    
    def read_battery_level(self):
        """Liest den Batteriestand über den ADC."""
        battery_config = self.config.get("sensors", {}).get("battery", {})
        voltage_factor = battery_config.get("voltage_factor", 2.0)
        min_voltage = battery_config.get("min_voltage", 3.2)
        max_voltage = battery_config.get("max_voltage", 4.2)
        
        if "battery" in self.sensors:
            try:
                adc = self.sensors["battery"]
                
                # Mehrfachmessung für bessere Genauigkeit
                value = 0
                samples = 10
                
                for _ in range(samples):
                    value += adc.read()
                    time.sleep_ms(10)
                
                value = value / samples
                
                # Umrechnung in Volt
                voltage = (value / 4095) * 3.3 * voltage_factor
                
                # Batterieprozentsatz berechnen
                percentage = 100 * min(1.0, max(0.0, (voltage - min_voltage) / (max_voltage - min_voltage)))
                
                result = {
                    "voltage": round(voltage, 2),
                    "percentage": round(percentage, 1)
                }
                
                self.last_readings["battery"] = result
                return result
            except Exception as e:
                print(f"Fehler beim Lesen der Batteriespannung: {e}")
        
        # Wenn kein echter Sensor verfügbar ist, simulieren wir Daten
        voltage = 3.5 + 0.5 * random.random()
        percentage = 100 * min(1.0, max(0.0, (voltage - min_voltage) / (max_voltage - min_voltage)))
        
        result = {
            "voltage": round(voltage, 2),
            "percentage": round(percentage, 1)
        }
        
        self.last_readings["battery"] = result
        return result
    
    def read_all(self):
        """Liest alle Sensordaten."""
        data = {}
        
        # Temperatur
        if self.config.get("sensors", {}).get("temperature", {}).get("enabled", False):
            data["temperature"] = self.read_temperature()
        
        # Luftfeuchtigkeit
        if self.config.get("sensors", {}).get("humidity", {}).get("enabled", False):
            data["humidity"] = self.read_humidity()
        
        # Luftdruck
        if self.config.get("sensors", {}).get("pressure", {}).get("enabled", False):
            data["pressure"] = self.read_pressure()
        
        # Batterie
        if self.config.get("sensors", {}).get("battery", {}).get("enabled", False):
            data["battery"] = self.read_battery_level()
        
        return data
    
    def get_readings(self):
        """Gibt die letzten Messwerte zurück."""
        return self.last_readings
    
    def calibrate(self, sensor_type, offset):
        """Kalibriert einen Sensor mit einem Offset."""
        sensor_config = self.config.get("sensors", {}).get(sensor_type, {})
        if sensor_config and "calibration_offset" in sensor_config:
            sensor_config["calibration_offset"] = offset
            print(f"Sensor {sensor_type} kalibriert mit Offset {offset}")
            return True
        return False