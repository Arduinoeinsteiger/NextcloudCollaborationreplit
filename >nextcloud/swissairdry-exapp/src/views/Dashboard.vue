<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <div class="last-updated">
        Zuletzt aktualisiert: {{ lastUpdated }}
      </div>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner">
        <i class="icon-loading"></i>
      </div>
      <div class="loading-text">Daten werden geladen...</div>
    </div>
    
    <div v-else-if="error" class="error-state">
      <div class="error-icon">
        <i class="icon-error"></i>
      </div>
      <div class="error-title">Fehler</div>
      <div class="error-message">{{ error }}</div>
      <button @click="$emit('refresh')" class="retry-btn">
        <i class="icon-refresh"></i> Erneut versuchen
      </button>
    </div>
    
    <div v-else class="dashboard-grid">
      <!-- Geräteübersicht -->
      <div class="card device-overview">
        <div class="card-header">
          <h2>Geräteübersicht</h2>
          <router-link to="/devices" class="card-link">Alle anzeigen</router-link>
        </div>
        <div class="card-content">
          <div class="status-boxes">
            <div class="status-box status-active">
              <div class="status-value">{{ deviceStatusCounts.active }}</div>
              <div class="status-label">Aktiv</div>
            </div>
            <div class="status-box status-inactive">
              <div class="status-value">{{ deviceStatusCounts.inactive }}</div>
              <div class="status-label">Inaktiv</div>
            </div>
            <div class="status-box status-warning">
              <div class="status-value">{{ deviceStatusCounts.warning }}</div>
              <div class="status-label">Warnung</div>
            </div>
            <div class="status-box status-alarm">
              <div class="status-value">{{ deviceStatusCounts.alarm }}</div>
              <div class="status-label">Alarm</div>
            </div>
          </div>
          
          <div class="device-list-preview">
            <h3>Neueste Geräte</h3>
            <ul v-if="topDevices.length > 0">
              <li v-for="device in topDevices" :key="device.id" class="device-item" :class="'status-' + device.status">
                <div class="device-icon">
                  <i class="icon-category-monitoring"></i>
                </div>
                <div class="device-info">
                  <div class="device-name">{{ device.name }}</div>
                  <div class="device-details">
                    <span class="device-type">{{ device.type }}</span>
                    <span v-if="device.telemetry?.temperature" class="device-temperature">{{ device.telemetry.temperature }}°C</span>
                    <span v-if="device.telemetry?.humidity" class="device-humidity">{{ device.telemetry.humidity }}%</span>
                  </div>
                </div>
                <div class="device-status">
                  <span class="status-indicator" :class="'status-' + device.status"></span>
                </div>
              </li>
            </ul>
            <div v-else class="empty-state">
              <i class="icon-category-monitoring"></i>
              <p>Keine Geräte verfügbar</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Alarme -->
      <div class="card alarms-overview">
        <div class="card-header">
          <h2>Neueste Alarme</h2>
          <router-link to="/alarms" class="card-link">Alle anzeigen</router-link>
        </div>
        <div class="card-content">
          <ul v-if="topAlarms.length > 0" class="alarm-list-preview">
            <li v-for="alarm in topAlarms" :key="alarm.id" class="alarm-item" :class="'severity-' + alarm.severity">
              <div class="alarm-icon">
                <i class="icon-alert"></i>
              </div>
              <div class="alarm-info">
                <div class="alarm-title">{{ alarm.title }}</div>
                <div class="alarm-description">{{ alarm.description }}</div>
                <div class="alarm-details">
                  <span class="alarm-device">Gerät: {{ alarm.device_id }}</span>
                  <span class="alarm-timestamp">{{ formatDate(alarm.timestamp) }}</span>
                </div>
              </div>
            </li>
          </ul>
          <div v-else class="empty-state">
            <i class="icon-checkmark"></i>
            <p>Keine Alarme vorhanden</p>
          </div>
        </div>
      </div>
      
      <!-- Systemstatus -->
      <div class="card system-status">
        <div class="card-header">
          <h2>Systemstatus</h2>
        </div>
        <div class="card-content">
          <div class="status-details">
            <div class="status-detail-item" :class="status.api ? 'status-ok' : 'status-error'">
              <div class="status-icon">
                <i :class="status.api ? 'icon-checkmark' : 'icon-error'"></i>
              </div>
              <div class="status-text">
                <div class="status-title">API</div>
                <div class="status-value">{{ status.api ? 'Verbunden' : 'Fehler' }}</div>
              </div>
            </div>
            
            <div class="status-detail-item" :class="status.mqtt ? 'status-ok' : 'status-error'">
              <div class="status-icon">
                <i :class="status.mqtt ? 'icon-checkmark' : 'icon-error'"></i>
              </div>
              <div class="status-text">
                <div class="status-title">MQTT</div>
                <div class="status-value">{{ status.mqtt ? 'Verbunden' : 'Fehler' }}</div>
              </div>
            </div>
            
            <div class="status-detail-item" :class="status.deck ? 'status-ok' : 'status-warning'">
              <div class="status-icon">
                <i :class="status.deck ? 'icon-checkmark' : 'icon-warning'"></i>
              </div>
              <div class="status-text">
                <div class="status-title">Deck Integration</div>
                <div class="status-value">{{ status.deck ? 'Aktiv' : 'Inaktiv' }}</div>
              </div>
            </div>
          </div>
          
          <!-- Nextcloud Integration Actions -->
          <div v-if="status.deck" class="nextcloud-actions">
            <h3>Nextcloud Integration</h3>
            <div class="action-buttons">
              <button class="btn btn-primary create-board-btn" @click="createBoard" :disabled="creatingBoard">
                <i :class="creatingBoard ? 'icon-loading' : 'icon-add'"></i> 
                {{ creatingBoardStatus ? creatingBoardStatus : 'SwissAirDry Board erstellen' }}
              </button>
              <button class="btn btn-warning create-alarm-board-btn" @click="createAlarmBoard" :disabled="creatingAlarmBoard">
                <i :class="creatingAlarmBoard ? 'icon-loading' : 'icon-add'"></i> 
                {{ creatingAlarmBoardStatus ? creatingAlarmBoardStatus : 'Alarm-Board erstellen' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { apiService } from '../api/apiService';

export default {
  name: 'Dashboard',
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    error: {
      type: String,
      default: null
    },
    devices: {
      type: Array,
      default: () => []
    },
    alarms: {
      type: Array,
      default: () => []
    },
    status: {
      type: Object,
      default: () => ({
        api: false,
        mqtt: false,
        deck: false
      })
    }
  },
  
  setup(props, { emit }) {
    // Status für Board-Erstellung
    const creatingBoard = ref(false);
    const creatingBoardStatus = ref('');
    const creatingAlarmBoard = ref(false);
    const creatingAlarmBoardStatus = ref('');
    
    // Aktuelles Datum für "Zuletzt aktualisiert"
    const lastUpdated = ref(new Date().toLocaleTimeString());
    
    // Geräte nach Status zählen
    const deviceStatusCounts = computed(() => {
      const counts = {
        active: 0,
        inactive: 0,
        warning: 0,
        alarm: 0
      };
      
      props.devices.forEach(device => {
        if (counts[device.status] !== undefined) {
          counts[device.status]++;
        }
      });
      
      return counts;
    });
    
    // Top 5 Geräte für die Vorschau
    const topDevices = computed(() => {
      return props.devices.slice(0, 5);
    });
    
    // Top 5 Alarme für die Vorschau
    const topAlarms = computed(() => {
      // Nach Zeitstempel sortieren, neueste zuerst
      return [...props.alarms]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 5);
    });
    
    // Datum formatieren
    const formatDate = (dateString) => {
      try {
        const date = new Date(dateString);
        return date.toLocaleString();
      } catch (error) {
        return dateString;
      }
    };
    
    // Board in Deck erstellen
    const createBoard = async () => {
      if (creatingBoard.value) return;
      
      creatingBoard.value = true;
      creatingBoardStatus.value = 'Wird erstellt...';
      
      try {
        await apiService.createDeckBoard();
        creatingBoardStatus.value = 'Board erstellt';
        
        // Nach 3 Sekunden zurücksetzen
        setTimeout(() => {
          creatingBoard.value = false;
          creatingBoardStatus.value = '';
          emit('refresh');
        }, 3000);
      } catch (error) {
        console.error('Fehler beim Erstellen des Boards:', error);
        creatingBoardStatus.value = 'Fehler';
        
        // Nach 3 Sekunden zurücksetzen
        setTimeout(() => {
          creatingBoard.value = false;
          creatingBoardStatus.value = '';
        }, 3000);
      }
    };
    
    // Alarm-Board in Deck erstellen
    const createAlarmBoard = async () => {
      if (creatingAlarmBoard.value) return;
      
      creatingAlarmBoard.value = true;
      creatingAlarmBoardStatus.value = 'Wird erstellt...';
      
      try {
        await apiService.createDeckBoard('alarm');
        creatingAlarmBoardStatus.value = 'Board erstellt';
        
        // Nach 3 Sekunden zurücksetzen
        setTimeout(() => {
          creatingAlarmBoard.value = false;
          creatingAlarmBoardStatus.value = '';
          emit('refresh');
        }, 3000);
      } catch (error) {
        console.error('Fehler beim Erstellen des Alarm-Boards:', error);
        creatingAlarmBoardStatus.value = 'Fehler';
        
        // Nach 3 Sekunden zurücksetzen
        setTimeout(() => {
          creatingAlarmBoard.value = false;
          creatingAlarmBoardStatus.value = '';
        }, 3000);
      }
    };
    
    // "Zuletzt aktualisiert" regelmäßig aktualisieren
    onMounted(() => {
      setInterval(() => {
        if (!props.loading) {
          lastUpdated.value = new Date().toLocaleTimeString();
        }
      }, 60000);
    });
    
    return {
      lastUpdated,
      deviceStatusCounts,
      topDevices,
      topAlarms,
      formatDate,
      createBoard,
      createAlarmBoard,
      creatingBoard,
      creatingBoardStatus,
      creatingAlarmBoard,
      creatingAlarmBoardStatus
    };
  }
};
</script>

<style scoped>
/* Dashboard Layout */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.dark-mode .dashboard-header h1 {
  color: #f5f5f5;
}

.last-updated {
  color: #999;
  font-size: 12px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

/* Cards */
.card {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  overflow: hidden;
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.dark-mode .card {
  background-color: #333;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  transition: border-color 0.3s ease;
}

.dark-mode .card-header {
  border-bottom-color: #444;
}

.card-header h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.dark-mode .card-header h2 {
  color: #f5f5f5;
}

.card-link {
  color: #0082c9;
  text-decoration: none;
  font-size: 13px;
}

.card-link:hover {
  text-decoration: underline;
}

.card-content {
  padding: 20px;
}

/* Status Boxes */
.status-boxes {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.status-box {
  padding: 15px;
  border-radius: 4px;
  text-align: center;
  background-color: #f9f9f9;
  transition: background-color 0.3s ease;
}

.dark-mode .status-box {
  background-color: #444;
}

.status-box.status-active {
  background-color: rgba(70, 186, 97, 0.2);
}

.status-box.status-inactive {
  background-color: rgba(153, 153, 153, 0.2);
}

.status-box.status-warning {
  background-color: rgba(233, 168, 70, 0.2);
}

.status-box.status-alarm {
  background-color: rgba(233, 66, 75, 0.2);
}

.dark-mode .status-box.status-active {
  background-color: rgba(70, 186, 97, 0.3);
}

.dark-mode .status-box.status-inactive {
  background-color: rgba(153, 153, 153, 0.3);
}

.dark-mode .status-box.status-warning {
  background-color: rgba(233, 168, 70, 0.3);
}

.dark-mode .status-box.status-alarm {
  background-color: rgba(233, 66, 75, 0.3);
}

.status-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.status-label {
  font-size: 12px;
  color: #666;
}

.dark-mode .status-label {
  color: #ccc;
}

/* Device List */
.device-list-preview h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.dark-mode .device-list-preview h3 {
  color: #ccc;
}

.device-list-preview ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.device-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 5px;
  background-color: #f9f9f9;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.dark-mode .device-item {
  background-color: #444;
}

.device-item:hover {
  transform: translateX(5px);
}

.device-item.status-active {
  border-left: 3px solid #46ba61;
}

.device-item.status-inactive {
  border-left: 3px solid #999;
}

.device-item.status-warning {
  border-left: 3px solid #e9a846;
}

.device-item.status-alarm {
  border-left: 3px solid #e9424b;
}

.device-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background-color: rgba(0, 130, 201, 0.1);
  color: #0082c9;
  margin-right: 10px;
}

.dark-mode .device-icon {
  background-color: rgba(0, 130, 201, 0.3);
}

.device-icon i {
  font-size: 18px;
}

.device-info {
  flex: 1;
}

.device-name {
  font-weight: 600;
  margin-bottom: 3px;
}

.device-details {
  display: flex;
  font-size: 12px;
  color: #666;
}

.dark-mode .device-details {
  color: #ccc;
}

.device-details span {
  margin-right: 10px;
}

.device-status {
  display: flex;
  align-items: center;
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 5px;
}

.status-indicator.status-active {
  background-color: #46ba61;
}

.status-indicator.status-inactive {
  background-color: #999;
}

.status-indicator.status-warning {
  background-color: #e9a846;
}

.status-indicator.status-alarm {
  background-color: #e9424b;
}

/* Alarm List */
.alarm-list-preview {
  list-style: none;
  margin: 0;
  padding: 0;
}

.alarm-item {
  display: flex;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  background-color: #f9f9f9;
  transition: background-color 0.3s ease, transform 0.2s ease;
}

.dark-mode .alarm-item {
  background-color: #444;
}

.alarm-item:hover {
  transform: translateX(5px);
}

.alarm-item.severity-critical {
  border-left: 3px solid #e9424b;
}

.alarm-item.severity-high {
  border-left: 3px solid #e9634b;
}

.alarm-item.severity-medium {
  border-left: 3px solid #e9a846;
}

.alarm-item.severity-low {
  border-left: 3px solid #46ba61;
}

.alarm-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background-color: rgba(233, 66, 75, 0.1);
  color: #e9424b;
  margin-right: 10px;
  flex-shrink: 0;
}

.dark-mode .alarm-icon {
  background-color: rgba(233, 66, 75, 0.3);
}

.alarm-icon i {
  font-size: 18px;
}

.alarm-info {
  flex: 1;
}

.alarm-title {
  font-weight: 600;
  margin-bottom: 5px;
}

.alarm-description {
  font-size: 13px;
  margin-bottom: 5px;
  color: #666;
}

.dark-mode .alarm-description {
  color: #ccc;
}

.alarm-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

/* System Status Details */
.status-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  margin-bottom: 20px;
}

@media (max-width: 400px) {
  .status-details {
    grid-template-columns: 1fr;
  }
}

.status-detail-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #f9f9f9;
  transition: background-color 0.3s ease;
}

.dark-mode .status-detail-item {
  background-color: #444;
}

.status-detail-item.status-ok {
  border-left: 3px solid #46ba61;
}

.status-detail-item.status-warning {
  border-left: 3px solid #e9a846;
}

.status-detail-item.status-error {
  border-left: 3px solid #e9424b;
}

.status-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.05);
  margin-right: 10px;
  flex-shrink: 0;
}

.dark-mode .status-icon {
  background-color: rgba(255, 255, 255, 0.1);
}

.status-icon i {
  font-size: 18px;
}

.status-detail-item.status-ok .status-icon {
  color: #46ba61;
  background-color: rgba(70, 186, 97, 0.1);
}

.status-detail-item.status-warning .status-icon {
  color: #e9a846;
  background-color: rgba(233, 168, 70, 0.1);
}

.status-detail-item.status-error .status-icon {
  color: #e9424b;
  background-color: rgba(233, 66, 75, 0.1);
}

.dark-mode .status-detail-item.status-ok .status-icon {
  background-color: rgba(70, 186, 97, 0.3);
}

.dark-mode .status-detail-item.status-warning .status-icon {
  background-color: rgba(233, 168, 70, 0.3);
}

.dark-mode .status-detail-item.status-error .status-icon {
  background-color: rgba(233, 66, 75, 0.3);
}

.status-text {
  flex: 1;
}

.status-title {
  font-weight: 600;
  margin-bottom: 3px;
}

.status-value {
  font-size: 13px;
  color: #666;
}

.dark-mode .status-value {
  color: #ccc;
}

/* Nextcloud Integration */
.nextcloud-actions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  transition: border-color 0.3s ease;
}

.dark-mode .nextcloud-actions {
  border-top-color: #444;
}

.nextcloud-actions h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.dark-mode .nextcloud-actions h3 {
  color: #ccc;
}

.action-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* Empty States */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px;
  text-align: center;
  color: #999;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ddd;
}

.dark-mode .empty-state i {
  color: #555;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  text-align: center;
}

.loading-spinner {
  font-size: 48px;
  color: #0082c9;
  margin-bottom: 20px;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 16px;
  color: #666;
}

.dark-mode .loading-text {
  color: #ccc;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 50px 20px;
  text-align: center;
}

.error-icon {
  font-size: 48px;
  color: #e9424b;
  margin-bottom: 10px;
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: #e9424b;
  margin-bottom: 10px;
}

.error-message {
  font-size: 16px;
  color: #666;
  margin-bottom: 20px;
  max-width: 600px;
}

.dark-mode .error-message {
  color: #ccc;
}

.retry-btn {
  padding: 8px 16px;
  background-color: #0082c9;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.retry-btn i {
  margin-right: 8px;
}

.retry-btn:hover {
  background-color: #006ca8;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.btn i {
  margin-right: 8px;
}

.btn-primary {
  background-color: #0082c9;
  color: white;
  border: none;
}

.btn-primary:hover {
  background-color: #006ca8;
}

.btn-warning {
  background-color: #e9a846;
  color: white;
  border: none;
}

.btn-warning:hover {
  background-color: #d89932;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>