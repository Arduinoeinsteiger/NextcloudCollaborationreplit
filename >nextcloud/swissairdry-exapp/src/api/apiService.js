/**
 * API-Service für SwissAirDry ExApp
 * 
 * Dieser Service handhabt alle API-Anfragen an den SwissAirDry-Backend-Server und
 * stellt eine einheitliche Schnittstelle für die Vue-Komponenten bereit.
 */

import axios from 'axios';

// Konfiguration
const API_CONFIG = {
  // Base URL kann sich je nach Umgebung ändern
  baseURL: process.env.NODE_ENV === 'development' 
    ? 'http://localhost:5000/api' 
    : '/app-api/swissairdry/api',
  
  // Standard-Timeout (in Millisekunden)
  timeout: 10000,
  
  // Request-Header
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
};

// Axios-Instanz mit Konfiguration erstellen
const apiClient = axios.create(API_CONFIG);

// Interceptors für Fehlerbehandlung
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('API-Fehler:', error);
    
    // In Nextcloud-Umgebung OCS.message für Fehleranzeige verwenden
    if (window.OCS && window.OCS.message) {
      if (error.response) {
        window.OCS.message.error(
          error.response.data.message || 
          `Fehler ${error.response.status}: ${error.response.statusText}`
        );
      } else {
        window.OCS.message.error('Verbindungsfehler zum API-Server');
      }
    }
    
    return Promise.reject(error);
  }
);

/**
 * API-Service Objekt mit allen verfügbaren Endpunkten
 */
export const apiService = {
  /**
   * Prüft den Status des API-Servers
   * 
   * @returns {Promise<Object>} Status-Daten
   */
  async getStatus() {
    try {
      const response = await apiClient.get('/status');
      return response.data;
    } catch (error) {
      console.error('Fehler beim Abrufen des Status:', error);
      return {
        api: false,
        mqtt: false,
        deck: { available: false, initialized: false }
      };
    }
  },
  
  /**
   * Lädt Dashboard-Daten
   * 
   * @returns {Promise<Object>} Dashboard-Daten mit Geräten und Alarmen
   */
  async getDashboard() {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },
  
  /**
   * Lädt die Liste aller Geräte
   * 
   * @param {Object} params - Optionale Filter-Parameter
   * @returns {Promise<Object>} Liste der Geräte
   */
  async getDevices(params = {}) {
    const response = await apiClient.get('/devices', { params });
    return response.data;
  },
  
  /**
   * Lädt Details zu einem bestimmten Gerät
   * 
   * @param {string} id - Geräte-ID
   * @returns {Promise<Object>} Gerätedetails
   */
  async getDevice(id) {
    const response = await apiClient.get(`/devices/${id}`);
    return response.data;
  },
  
  /**
   * Ruft Telemetriedaten eines Geräts ab
   * 
   * @param {string} id - Geräte-ID
   * @param {Object} params - Optionale Parameter (Zeitraum, Aggregation, etc.)
   * @returns {Promise<Object>} Telemetriedaten
   */
  async getDeviceTelemetry(id, params = {}) {
    const response = await apiClient.get(`/devices/${id}/telemetry`, { params });
    return response.data;
  },
  
  /**
   * Aktualisiert die Konfiguration eines Geräts
   * 
   * @param {string} id - Geräte-ID
   * @param {Object} data - Aktualisierte Gerätekonfiguration
   * @returns {Promise<Object>} Aktualisiertes Gerät
   */
  async updateDevice(id, data) {
    const response = await apiClient.put(`/devices/${id}`, data);
    return response.data;
  },
  
  /**
   * Lädt die Liste aller Alarme
   * 
   * @param {Object} params - Optionale Filter-Parameter
   * @returns {Promise<Object>} Liste der Alarme
   */
  async getAlarms(params = {}) {
    const response = await apiClient.get('/alarms', { params });
    return response.data;
  },
  
  /**
   * Lädt Details zu einem bestimmten Alarm
   * 
   * @param {string} id - Alarm-ID
   * @returns {Promise<Object>} Alarmdetails
   */
  async getAlarm(id) {
    const response = await apiClient.get(`/alarms/${id}`);
    return response.data;
  },
  
  /**
   * Aktualisiert den Status eines Alarms (z.B. quittieren)
   * 
   * @param {string} id - Alarm-ID
   * @param {Object} data - Aktualisierte Alarmdaten
   * @returns {Promise<Object>} Aktualisierter Alarm
   */
  async updateAlarm(id, data) {
    const response = await apiClient.put(`/alarms/${id}`, data);
    return response.data;
  },
  
  /**
   * Sendet einen MQTT-Befehl an ein Gerät
   * 
   * @param {string} deviceId - Geräte-ID
   * @param {Object} command - Befehlsdaten
   * @returns {Promise<Object>} Befehlsstatus
   */
  async sendCommand(deviceId, command) {
    const response = await apiClient.post(`/devices/${deviceId}/command`, command);
    return response.data;
  },
  
  /**
   * Erstellt ein Board in Deck für SwissAirDry
   * 
   * @returns {Promise<Object>} Erstelltes Board
   */
  async createDeckBoard() {
    const response = await apiClient.post('/deck/create-board');
    return response.data;
  },
  
  /**
   * Erstellt eine Alarmkarte in Deck
   * 
   * @param {Object} alarmData - Alarmdaten
   * @returns {Promise<Object>} Erstellte Karte
   */
  async createDeckAlarmCard(alarmData) {
    const response = await apiClient.post('/deck/create-card', {
      type: 'alarm',
      data: alarmData
    });
    return response.data;
  },
  
  /**
   * Erstellt eine Gerätekarte in Deck
   * 
   * @param {Object} deviceData - Gerätedaten
   * @returns {Promise<Object>} Erstellte Karte
   */
  async createDeckDeviceCard(deviceData) {
    const response = await apiClient.post('/deck/create-card', {
      type: 'device',
      data: deviceData
    });
    return response.data;
  }
};

export default apiService;