/**
 * SwissAirDry Nextcloud ExApp
 * 
 * Dies ist die Hauptdatei der SwissAirDry ExApp, die die JavaScript-Funktionalität bereitstellt.
 */

(function() {
  'use strict';

  /**
   * Konfiguration
   */
  const CONFIG = {
    apiUrl: window.location.protocol + '//' + window.location.hostname + ':8081', // ExApp Daemon API
    refreshInterval: 30000, // Aktualisierungsintervall in ms (30 Sekunden)
    defaultView: 'dashboard',
    availableViews: ['dashboard', 'devices', 'alarms', 'settings'],
    icons: {
      dashboard: 'icon-dashboard',
      devices: 'icon-category-monitoring',
      alarms: 'icon-alert',
      settings: 'icon-settings'
    }
  };

  /**
   * Hauptfunktion, die beim Laden der Seite ausgeführt wird
   */
  function init() {
    console.log('SwissAirDry ExApp wird initialisiert...');
    
    // Baue die UI auf
    buildUI();
    
    // Event-Listener registrieren
    registerEventListeners();
    
    // Prüfe den API-Status
    checkApiStatus();
    
    // Lade die Startansicht
    loadView(CONFIG.defaultView);
    
    // Starte den Aktualisierungstimer
    startRefreshTimer();
    
    console.log('SwissAirDry ExApp initialisiert');
  }

  /**
   * Erstellt die Benutzeroberfläche
   */
  function buildUI() {
    const appContainer = document.getElementById('swissairdry-app');
    if (!appContainer) {
      console.error('App-Container nicht gefunden!');
      return;
    }
    
    // Lösche bestehenden Inhalt
    appContainer.innerHTML = '';
    
    // Erstelle UI-Framework
    appContainer.innerHTML = `
      <div class="sard-app-container">
        <div class="sard-sidebar">
          <div class="sard-logo">
            <img src="./img/swissairdry-logo.svg" alt="SwissAirDry">
          </div>
          <nav class="sard-navigation">
            <ul>
              ${CONFIG.availableViews.map(view => 
                `<li>
                  <a href="#" class="sard-nav-link" data-view="${view}">
                    <span class="${CONFIG.icons[view] || 'icon-app'}"></span>
                    <span>${capitalizeFirstLetter(view)}</span>
                  </a>
                </li>`
              ).join('')}
            </ul>
          </nav>
          <div class="sard-api-status">
            <span class="sard-status-indicator offline"></span>
            <span class="sard-status-text">API: Nicht verbunden</span>
          </div>
        </div>
        <div class="sard-content">
          <header class="sard-header">
            <h1 class="sard-view-title">Dashboard</h1>
            <div class="sard-actions">
              <button class="sard-refresh-btn">
                <span class="icon-refresh"></span>
              </button>
            </div>
          </header>
          <main class="sard-view-container">
            <div class="sard-loading">
              <span class="icon-loading"></span>
              <span>Lade Daten...</span>
            </div>
          </main>
        </div>
      </div>
    `;
  }

  /**
   * Registriert Event-Listener für die UI-Elemente
   */
  function registerEventListeners() {
    // Navigation
    document.querySelectorAll('.sard-nav-link').forEach(link => {
      link.addEventListener('click', function(e) {
        e.preventDefault();
        const view = this.getAttribute('data-view');
        loadView(view);
      });
    });
    
    // Aktualisierungs-Button
    document.querySelector('.sard-refresh-btn').addEventListener('click', function() {
      refreshCurrentView();
    });
  }

  /**
   * Prüft den Status der API
   */
  function checkApiStatus() {
    fetch(`${CONFIG.apiUrl}/status`)
      .then(response => response.json())
      .then(data => {
        updateApiStatus(data.status === 'ok');
      })
      .catch(error => {
        console.error('API-Status-Fehler:', error);
        updateApiStatus(false);
      });
  }

  /**
   * Aktualisiert die API-Status-Anzeige
   * @param {boolean} isOnline - Ob die API online ist
   */
  function updateApiStatus(isOnline) {
    const statusIndicator = document.querySelector('.sard-status-indicator');
    const statusText = document.querySelector('.sard-status-text');
    
    if (isOnline) {
      statusIndicator.classList.remove('offline');
      statusIndicator.classList.add('online');
      statusText.textContent = 'API: Verbunden';
    } else {
      statusIndicator.classList.remove('online');
      statusIndicator.classList.add('offline');
      statusText.textContent = 'API: Nicht verbunden';
    }
  }

  /**
   * Lädt eine bestimmte Ansicht
   * @param {string} viewName - Name der zu ladenden Ansicht
   */
  function loadView(viewName) {
    if (!CONFIG.availableViews.includes(viewName)) {
      console.error(`Ungültige Ansicht: ${viewName}`);
      return;
    }
    
    // Aktualisiere aktive Navigation
    document.querySelectorAll('.sard-nav-link').forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('data-view') === viewName) {
        link.classList.add('active');
      }
    });
    
    // Aktualisiere Titel
    document.querySelector('.sard-view-title').textContent = capitalizeFirstLetter(viewName);
    
    // Zeige Ladeindikator
    const viewContainer = document.querySelector('.sard-view-container');
    viewContainer.innerHTML = `
      <div class="sard-loading">
        <span class="icon-loading"></span>
        <span>Lade ${capitalizeFirstLetter(viewName)}...</span>
      </div>
    `;
    
    // Lade Daten für die Ansicht
    loadViewData(viewName);
  }

  /**
   * Lädt Daten für eine bestimmte Ansicht
   * @param {string} viewName - Name der Ansicht
   */
  function loadViewData(viewName) {
    let endpoint = '';
    
    switch(viewName) {
      case 'dashboard':
        endpoint = '/api/proxy?path=dashboard';
        break;
      case 'devices':
        endpoint = '/api/proxy?path=devices';
        break;
      case 'alarms':
        endpoint = '/deck/alarms';
        break;
      case 'settings':
        endpoint = '/status';
        break;
      default:
        endpoint = '/status';
    }
    
    fetch(`${CONFIG.apiUrl}${endpoint}`)
      .then(response => response.json())
      .then(data => {
        renderView(viewName, data);
      })
      .catch(error => {
        console.error(`Fehler beim Laden der ${viewName}-Daten:`, error);
        showErrorInView(viewName, error);
      });
  }

  /**
   * Rendert eine Ansicht mit Daten
   * @param {string} viewName - Name der Ansicht
   * @param {object} data - Daten für die Ansicht
   */
  function renderView(viewName, data) {
    const viewContainer = document.querySelector('.sard-view-container');
    
    switch(viewName) {
      case 'dashboard':
        renderDashboard(viewContainer, data);
        break;
      case 'devices':
        renderDevices(viewContainer, data);
        break;
      case 'alarms':
        renderAlarms(viewContainer, data);
        break;
      case 'settings':
        renderSettings(viewContainer, data);
        break;
      default:
        viewContainer.innerHTML = `<div class="sard-error">Unbekannte Ansicht: ${viewName}</div>`;
    }
  }

  /**
   * Rendert die Dashboard-Ansicht
   * @param {HTMLElement} container - Container-Element
   * @param {object} data - Dashboard-Daten
   */
  function renderDashboard(container, data) {
    let deviceCount = 0;
    let activeDevices = 0;
    let alarmsCount = 0;
    
    if (data && data.devices) {
      deviceCount = data.devices.length;
      activeDevices = data.devices.filter(d => d.status === 'active').length;
    }
    
    if (data && data.alarms) {
      alarmsCount = data.alarms.length;
    }
    
    container.innerHTML = `
      <div class="sard-dashboard">
        <div class="sard-dashboard-overview">
          <div class="sard-card">
            <div class="sard-card-header">
              <h2>Geräteübersicht</h2>
            </div>
            <div class="sard-card-content">
              <div class="sard-stat-box">
                <span class="sard-stat-value">${deviceCount}</span>
                <span class="sard-stat-label">Geräte gesamt</span>
              </div>
              <div class="sard-stat-box">
                <span class="sard-stat-value">${activeDevices}</span>
                <span class="sard-stat-label">Aktive Geräte</span>
              </div>
              <div class="sard-stat-box">
                <span class="sard-stat-value">${alarmsCount}</span>
                <span class="sard-stat-label">Aktive Alarme</span>
              </div>
            </div>
          </div>
          
          <div class="sard-card">
            <div class="sard-card-header">
              <h2>Statusübersicht</h2>
            </div>
            <div class="sard-card-content">
              <div class="sard-api-connections">
                <div class="sard-connection-item">
                  <span class="sard-connection-label">API:</span>
                  <span class="sard-connection-status ${data.api_status ? 'online' : 'offline'}">
                    ${data.api_status ? 'Verbunden' : 'Nicht verbunden'}
                  </span>
                </div>
                <div class="sard-connection-item">
                  <span class="sard-connection-label">MQTT:</span>
                  <span class="sard-connection-status ${data.mqtt_status ? 'online' : 'offline'}">
                    ${data.mqtt_status ? 'Verbunden' : 'Nicht verbunden'}
                  </span>
                </div>
                <div class="sard-connection-item">
                  <span class="sard-connection-label">Deck:</span>
                  <span class="sard-connection-status ${data.deck_status ? 'online' : 'offline'}">
                    ${data.deck_status ? 'Verbunden' : 'Nicht verbunden'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="sard-dashboard-recent">
          <div class="sard-card">
            <div class="sard-card-header">
              <h2>Neueste Alarme</h2>
            </div>
            <div class="sard-card-content">
              ${renderRecentAlarms(data.recentAlarms || [])}
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Rendert neueste Alarme
   * @param {Array} alarms - Liste der Alarme
   * @returns {string} HTML für die Alarmliste
   */
  function renderRecentAlarms(alarms) {
    if (!alarms || alarms.length === 0) {
      return '<div class="sard-empty-state">Keine Alarme vorhanden</div>';
    }
    
    return `
      <ul class="sard-alarm-list">
        ${alarms.slice(0, 5).map(alarm => `
          <li class="sard-alarm-item">
            <div class="sard-alarm-icon ${getAlarmTypeClass(alarm.type)}">
              <span class="icon-alert"></span>
            </div>
            <div class="sard-alarm-details">
              <div class="sard-alarm-title">${alarm.title || alarm.type}</div>
              <div class="sard-alarm-device">${alarm.device_id}</div>
              <div class="sard-alarm-time">${formatDateTime(alarm.timestamp)}</div>
            </div>
          </li>
        `).join('')}
      </ul>
      <div class="sard-see-all">
        <a href="#" class="sard-nav-link" data-view="alarms">Alle Alarme anzeigen</a>
      </div>
    `;
  }

  /**
   * Rendert die Geräteansicht
   * @param {HTMLElement} container - Container-Element
   * @param {object} data - Gerätedaten
   */
  function renderDevices(container, data) {
    if (!data || !data.devices || data.devices.length === 0) {
      container.innerHTML = '<div class="sard-empty-state">Keine Geräte gefunden</div>';
      return;
    }
    
    const devices = data.devices;
    
    container.innerHTML = `
      <div class="sard-devices">
        <div class="sard-device-filters">
          <input type="text" class="sard-search-input" placeholder="Geräte suchen...">
          <div class="sard-filter-group">
            <label>Status:</label>
            <select class="sard-filter-select">
              <option value="all">Alle</option>
              <option value="active">Aktiv</option>
              <option value="inactive">Inaktiv</option>
              <option value="alarm">Alarm</option>
            </select>
          </div>
        </div>
        
        <div class="sard-device-grid">
          ${devices.map(device => `
            <div class="sard-device-card">
              <div class="sard-device-header ${getDeviceStatusClass(device.status)}">
                <h3 class="sard-device-name">${device.name || 'Unbenanntes Gerät'}</h3>
                <span class="sard-device-id">${device.id}</span>
              </div>
              <div class="sard-device-content">
                <div class="sard-device-status">
                  <span class="sard-status-dot ${getDeviceStatusClass(device.status)}"></span>
                  <span class="sard-status-text">${getDeviceStatusText(device.status)}</span>
                </div>
                <div class="sard-device-metrics">
                  ${renderDeviceMetrics(device)}
                </div>
                <div class="sard-device-last-seen">
                  Zuletzt gesehen: ${formatDateTime(device.last_seen)}
                </div>
              </div>
              <div class="sard-device-actions">
                <button class="sard-btn sard-btn-primary" data-device-id="${device.id}">Details</button>
                <button class="sard-btn" data-device-id="${device.id}">Steuerung</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    
    // Event-Listener für Details-Buttons
    document.querySelectorAll('.sard-device-actions .sard-btn-primary').forEach(btn => {
      btn.addEventListener('click', function() {
        const deviceId = this.getAttribute('data-device-id');
        openDeviceDetails(deviceId);
      });
    });
  }

  /**
   * Rendert Geräte-Metrikdaten
   * @param {object} device - Gerätedaten
   * @returns {string} HTML für die Metrikanzeige
   */
  function renderDeviceMetrics(device) {
    const metrics = [];
    
    if (device.temperature !== undefined) {
      metrics.push(`
        <div class="sard-metric">
          <span class="sard-metric-icon icon-temperature"></span>
          <span class="sard-metric-value">${device.temperature}°C</span>
        </div>
      `);
    }
    
    if (device.humidity !== undefined) {
      metrics.push(`
        <div class="sard-metric">
          <span class="sard-metric-icon icon-humidity"></span>
          <span class="sard-metric-value">${device.humidity}%</span>
        </div>
      `);
    }
    
    if (device.battery !== undefined) {
      metrics.push(`
        <div class="sard-metric">
          <span class="sard-metric-icon icon-battery"></span>
          <span class="sard-metric-value">${device.battery}%</span>
        </div>
      `);
    }
    
    if (metrics.length === 0) {
      return '<div class="sard-no-metrics">Keine Metrikdaten verfügbar</div>';
    }
    
    return metrics.join('');
  }

  /**
   * Rendert die Alarm-Ansicht
   * @param {HTMLElement} container - Container-Element
   * @param {object} data - Alarmdaten
   */
  function renderAlarms(container, data) {
    if (!data || !data.alarms || data.alarms.length === 0) {
      container.innerHTML = '<div class="sard-empty-state">Keine Alarme gefunden</div>';
      return;
    }
    
    const alarms = data.alarms;
    
    container.innerHTML = `
      <div class="sard-alarms">
        <div class="sard-alarm-filters">
          <input type="text" class="sard-search-input" placeholder="Alarme suchen...">
          <div class="sard-filter-group">
            <label>Typ:</label>
            <select class="sard-filter-select">
              <option value="all">Alle</option>
              <option value="temperature">Temperatur</option>
              <option value="humidity">Luftfeuchtigkeit</option>
              <option value="connectivity">Verbindung</option>
              <option value="battery">Batterie</option>
            </select>
          </div>
        </div>
        
        <div class="sard-alarm-list">
          ${alarms.map(alarm => `
            <div class="sard-alarm-card ${getAlarmSeverityClass(alarm.severity)}">
              <div class="sard-alarm-icon">
                <span class="${getAlarmIconClass(alarm.type)}"></span>
              </div>
              <div class="sard-alarm-info">
                <h3 class="sard-alarm-title">${alarm.title || alarm.type}</h3>
                <div class="sard-alarm-description">${alarm.description || 'Keine Beschreibung verfügbar'}</div>
                <div class="sard-alarm-device">Gerät: ${alarm.device_id}</div>
                <div class="sard-alarm-time">Zeit: ${formatDateTime(alarm.timestamp)}</div>
              </div>
              <div class="sard-alarm-actions">
                <button class="sard-btn sard-btn-primary" data-alarm-id="${alarm.id}">Details</button>
                <button class="sard-btn" data-alarm-id="${alarm.id}">Bestätigen</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Rendert die Einstellungsansicht
   * @param {HTMLElement} container - Container-Element
   * @param {object} data - Einstellungsdaten
   */
  function renderSettings(container, data) {
    container.innerHTML = `
      <div class="sard-settings">
        <div class="sard-card">
          <div class="sard-card-header">
            <h2>API-Einstellungen</h2>
          </div>
          <div class="sard-card-content">
            <form class="sard-settings-form">
              <div class="sard-form-group">
                <label for="api_url">API-URL</label>
                <input type="text" id="api_url" value="${CONFIG.apiUrl}" class="sard-input">
              </div>
              <div class="sard-form-actions">
                <button type="button" class="sard-btn sard-btn-primary" id="save-api-settings">Speichern</button>
                <button type="button" class="sard-btn" id="test-api-connection">Verbindung testen</button>
              </div>
            </form>
          </div>
        </div>
        
        <div class="sard-card">
          <div class="sard-card-header">
            <h2>Deck-Integration</h2>
          </div>
          <div class="sard-card-content">
            <div class="sard-integration-status">
              <span class="sard-status-label">Status:</span>
              <span class="sard-status-value ${data.deck?.initialized ? 'online' : 'offline'}">
                ${data.deck?.initialized ? 'Aktiviert' : 'Deaktiviert'}
              </span>
            </div>
            
            <div class="sard-form-actions">
              <button type="button" class="sard-btn" id="configure-deck">Deck konfigurieren</button>
            </div>
          </div>
        </div>
        
        <div class="sard-card">
          <div class="sard-card-header">
            <h2>Über</h2>
          </div>
          <div class="sard-card-content">
            <div class="sard-about">
              <p><strong>SwissAirDry ExApp</strong></p>
              <p>Version: ${data.version || '1.0.0'}</p>
              <p>Entwickelt von: Swiss Air Dry Team</p>
              <p><a href="https://swissairdry.com" target="_blank">https://swissairdry.com</a></p>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Event-Listener für Settings
    document.getElementById('save-api-settings').addEventListener('click', function() {
      const apiUrl = document.getElementById('api_url').value;
      if (apiUrl) {
        CONFIG.apiUrl = apiUrl;
        // Speichere in localStorage
        window.localStorage.setItem('sard_api_url', apiUrl);
        showNotification('API-URL gespeichert', 'success');
      }
    });
    
    document.getElementById('test-api-connection').addEventListener('click', function() {
      checkApiStatus();
    });
  }

  /**
   * Zeigt einen Fehler in einer Ansicht an
   * @param {string} viewName - Name der Ansicht
   * @param {Error} error - Fehlerobjekt
   */
  function showErrorInView(viewName, error) {
    const viewContainer = document.querySelector('.sard-view-container');
    viewContainer.innerHTML = `
      <div class="sard-error">
        <h2>Fehler beim Laden der ${capitalizeFirstLetter(viewName)}-Ansicht</h2>
        <p>${error.message}</p>
        <button class="sard-btn sard-btn-primary sard-retry-btn">Erneut versuchen</button>
      </div>
    `;
    
    document.querySelector('.sard-retry-btn').addEventListener('click', function() {
      loadView(viewName);
    });
  }

  /**
   * Öffnet die Detailansicht eines Geräts
   * @param {string} deviceId - ID des Geräts
   */
  function openDeviceDetails(deviceId) {
    fetch(`${CONFIG.apiUrl}/api/proxy?path=devices/${deviceId}`)
      .then(response => response.json())
      .then(data => {
        showDeviceModal(data);
      })
      .catch(error => {
        console.error(`Fehler beim Laden der Gerätedetails:`, error);
        showNotification(`Fehler beim Laden der Gerätedetails: ${error.message}`, 'error');
      });
  }

  /**
   * Zeigt ein Modal mit Gerätedetails an
   * @param {object} device - Gerätedaten
   */
  function showDeviceModal(device) {
    // Modal-Element erstellen
    const modal = document.createElement('div');
    modal.className = 'sard-modal';
    
    modal.innerHTML = `
      <div class="sard-modal-content">
        <div class="sard-modal-header">
          <h2>Gerät: ${device.name || 'Unbenanntes Gerät'}</h2>
          <button class="sard-modal-close">&times;</button>
        </div>
        <div class="sard-modal-body">
          <div class="sard-device-details">
            <div class="sard-detail-section">
              <h3>Grundinformationen</h3>
              <table class="sard-detail-table">
                <tr>
                  <th>ID:</th>
                  <td>${device.id}</td>
                </tr>
                <tr>
                  <th>Typ:</th>
                  <td>${device.type || 'Unbekannt'}</td>
                </tr>
                <tr>
                  <th>Status:</th>
                  <td class="${getDeviceStatusClass(device.status)}">${getDeviceStatusText(device.status)}</td>
                </tr>
                <tr>
                  <th>Letzter Kontakt:</th>
                  <td>${formatDateTime(device.last_seen)}</td>
                </tr>
              </table>
            </div>
            
            <div class="sard-detail-section">
              <h3>Sensorwerte</h3>
              <div class="sard-sensor-grid">
                ${renderSensorValues(device)}
              </div>
            </div>
            
            <div class="sard-detail-section">
              <h3>Standort</h3>
              <div class="sard-location-info">
                ${device.location ? `
                  <p>${device.location.address || 'Kein Adresse verfügbar'}</p>
                  <p>Koordinaten: ${device.location.latitude}, ${device.location.longitude}</p>
                ` : '<p>Kein Standort verfügbar</p>'}
              </div>
            </div>
          </div>
        </div>
        <div class="sard-modal-footer">
          <button class="sard-btn">Schließen</button>
          <button class="sard-btn sard-btn-primary">Steuerung</button>
        </div>
      </div>
    `;
    
    // Zum Dokument hinzufügen
    document.body.appendChild(modal);
    
    // Event-Listener zum Schließen
    modal.querySelector('.sard-modal-close').addEventListener('click', function() {
      document.body.removeChild(modal);
    });
    
    modal.querySelector('.sard-modal-footer .sard-btn').addEventListener('click', function() {
      document.body.removeChild(modal);
    });
    
    // Verhindere Klick-Durchleitung
    modal.querySelector('.sard-modal-content').addEventListener('click', function(e) {
      e.stopPropagation();
    });
    
    // Klick außerhalb schließt Modal
    modal.addEventListener('click', function() {
      document.body.removeChild(modal);
    });
  }

  /**
   * Rendert Sensorwerte eines Geräts
   * @param {object} device - Gerätedaten
   * @returns {string} HTML für die Sensorwerte
   */
  function renderSensorValues(device) {
    const sensors = [];
    
    if (device.temperature !== undefined) {
      sensors.push(`
        <div class="sard-sensor-card">
          <div class="sard-sensor-icon">
            <span class="icon-temperature"></span>
          </div>
          <div class="sard-sensor-value">${device.temperature}°C</div>
          <div class="sard-sensor-label">Temperatur</div>
        </div>
      `);
    }
    
    if (device.humidity !== undefined) {
      sensors.push(`
        <div class="sard-sensor-card">
          <div class="sard-sensor-icon">
            <span class="icon-humidity"></span>
          </div>
          <div class="sard-sensor-value">${device.humidity}%</div>
          <div class="sard-sensor-label">Luftfeuchtigkeit</div>
        </div>
      `);
    }
    
    if (device.battery !== undefined) {
      sensors.push(`
        <div class="sard-sensor-card">
          <div class="sard-sensor-icon">
            <span class="icon-battery"></span>
          </div>
          <div class="sard-sensor-value">${device.battery}%</div>
          <div class="sard-sensor-label">Batterie</div>
        </div>
      `);
    }
    
    if (device.pressure !== undefined) {
      sensors.push(`
        <div class="sard-sensor-card">
          <div class="sard-sensor-icon">
            <span class="icon-pressure"></span>
          </div>
          <div class="sard-sensor-value">${device.pressure} hPa</div>
          <div class="sard-sensor-label">Luftdruck</div>
        </div>
      `);
    }
    
    if (sensors.length === 0) {
      return '<div class="sard-empty-state">Keine Sensorwerte verfügbar</div>';
    }
    
    return sensors.join('');
  }

  /**
   * Zeigt eine Benachrichtigung an
   * @param {string} message - Nachrichtentext
   * @param {string} type - Typ der Nachricht ('success', 'error', 'warning', 'info')
   */
  function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `sard-notification sard-notification-${type}`;
    
    notification.innerHTML = `
      <div class="sard-notification-content">
        <div class="sard-notification-icon">
          <span class="${getNotificationIconClass(type)}"></span>
        </div>
        <div class="sard-notification-message">${message}</div>
        <div class="sard-notification-close">&times;</div>
      </div>
    `;
    
    // Zum Dokument hinzufügen
    document.body.appendChild(notification);
    
    // Animation zum Einblenden
    setTimeout(() => {
      notification.classList.add('show');
    }, 10);
    
    // Event-Listener zum Schließen
    notification.querySelector('.sard-notification-close').addEventListener('click', function() {
      closeNotification(notification);
    });
    
    // Automatisch schließen nach 5 Sekunden
    setTimeout(() => {
      closeNotification(notification);
    }, 5000);
  }

  /**
   * Schließt eine Benachrichtigung
   * @param {HTMLElement} notification - Benachrichtigungselement
   */
  function closeNotification(notification) {
    notification.classList.remove('show');
    notification.classList.add('hide');
    
    // Nach Animation entfernen
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 300);
  }

  /**
   * Aktualisiert die aktuelle Ansicht
   */
  function refreshCurrentView() {
    const activeNav = document.querySelector('.sard-nav-link.active');
    if (activeNav) {
      const viewName = activeNav.getAttribute('data-view');
      loadView(viewName);
    }
  }

  /**
   * Startet einen Timer zur regelmäßigen Aktualisierung
   */
  function startRefreshTimer() {
    setInterval(() => {
      checkApiStatus();
      // Automatische Aktualisierung der aktuellen Ansicht
      refreshCurrentView();
    }, CONFIG.refreshInterval);
  }

  // Hilfsfunktionen

  /**
   * Macht den ersten Buchstaben eines Textes groß
   * @param {string} text - Text
   * @returns {string} Text mit großem Anfangsbuchstaben
   */
  function capitalizeFirstLetter(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  /**
   * Formatiert ein Datum/Zeit
   * @param {string} dateStr - Datum als String oder ISO-String
   * @returns {string} Formatiertes Datum
   */
  function formatDateTime(dateStr) {
    if (!dateStr) return 'Unbekannt';
    
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return dateStr;
    }
  }

  /**
   * Gibt die CSS-Klasse für einen Alarmtyp zurück
   * @param {string} type - Alarmtyp
   * @returns {string} CSS-Klasse
   */
  function getAlarmTypeClass(type) {
    switch (type?.toLowerCase()) {
      case 'temperature':
        return 'temperature';
      case 'humidity':
        return 'humidity';
      case 'connectivity':
        return 'connectivity';
      case 'battery':
        return 'battery';
      default:
        return 'default';
    }
  }

  /**
   * Gibt die CSS-Klasse für einen Gerätestatus zurück
   * @param {string} status - Gerätestatus
   * @returns {string} CSS-Klasse
   */
  function getDeviceStatusClass(status) {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'online':
        return 'status-online';
      case 'inactive':
      case 'offline':
        return 'status-offline';
      case 'warning':
        return 'status-warning';
      case 'alarm':
      case 'error':
        return 'status-error';
      default:
        return 'status-unknown';
    }
  }

  /**
   * Gibt den Text für einen Gerätestatus zurück
   * @param {string} status - Gerätestatus
   * @returns {string} Lesbarer Status
   */
  function getDeviceStatusText(status) {
    switch (status?.toLowerCase()) {
      case 'active':
      case 'online':
        return 'Online';
      case 'inactive':
      case 'offline':
        return 'Offline';
      case 'warning':
        return 'Warnung';
      case 'alarm':
      case 'error':
        return 'Alarm';
      default:
        return 'Unbekannt';
    }
  }

  /**
   * Gibt die CSS-Klasse für eine Alarmpriorität zurück
   * @param {string} severity - Alarmschwere
   * @returns {string} CSS-Klasse
   */
  function getAlarmSeverityClass(severity) {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'severity-critical';
      case 'high':
        return 'severity-high';
      case 'medium':
        return 'severity-medium';
      case 'low':
        return 'severity-low';
      default:
        return 'severity-default';
    }
  }

  /**
   * Gibt die Icon-Klasse für einen Alarmtyp zurück
   * @param {string} type - Alarmtyp
   * @returns {string} Icon-Klasse
   */
  function getAlarmIconClass(type) {
    switch (type?.toLowerCase()) {
      case 'temperature':
        return 'icon-temperature';
      case 'humidity':
        return 'icon-humidity';
      case 'connectivity':
        return 'icon-connection-error';
      case 'battery':
        return 'icon-battery-low';
      default:
        return 'icon-alert';
    }
  }

  /**
   * Gibt die Icon-Klasse für einen Benachrichtigungstyp zurück
   * @param {string} type - Benachrichtigungstyp
   * @returns {string} Icon-Klasse
   */
  function getNotificationIconClass(type) {
    switch (type) {
      case 'success':
        return 'icon-checkmark';
      case 'error':
        return 'icon-error';
      case 'warning':
        return 'icon-warning';
      case 'info':
      default:
        return 'icon-info';
    }
  }

  // Initialisierung beim Laden der Seite
  document.addEventListener('DOMContentLoaded', init);

})();