<template>
  <div id="swissairdry-app" :class="{ 'dark-mode': darkMode }">
    <header class="app-header">
      <div class="logo">
        <img src="./assets/swissairdry-logo.svg" alt="SwissAirDry Logo">
        <h1>Swiss Air Dry</h1>
      </div>
      <nav class="main-nav">
        <router-link to="/" class="nav-item" exact>
          <span class="icon"><i class="icon-dashboard"></i></span>
          <span class="label">Dashboard</span>
        </router-link>
        <router-link to="/devices" class="nav-item">
          <span class="icon"><i class="icon-category-monitoring"></i></span>
          <span class="label">Geräte</span>
        </router-link>
        <router-link to="/alarms" class="nav-item">
          <span class="icon"><i class="icon-alert"></i></span>
          <span class="label">Alarme</span>
        </router-link>
        <router-link to="/settings" class="nav-item">
          <span class="icon"><i class="icon-settings"></i></span>
          <span class="label">Einstellungen</span>
        </router-link>
      </nav>
      <div class="app-controls">
        <button @click="refreshData" class="refresh-btn" :class="{ 'rotating': isRefreshing }">
          <i class="icon-refresh"></i>
        </button>
        <button @click="toggleDarkMode" class="dark-mode-btn">
          <i :class="darkMode ? 'icon-sun' : 'icon-moon'"></i>
        </button>
      </div>
    </header>

    <main class="app-content">
      <router-view 
        :loading="loading"
        :error="error"
        :devices="devices"
        :alarms="alarms"
        :status="apiStatus"
        @refresh="refreshData"
      />
    </main>

    <footer class="app-footer">
      <div class="status-bar">
        <div class="status-item" :class="{ 'status-ok': apiStatus.api, 'status-error': !apiStatus.api }">
          <i :class="apiStatus.api ? 'icon-checkmark' : 'icon-error'"></i>
          <span>API</span>
        </div>
        <div class="status-item" :class="{ 'status-ok': apiStatus.mqtt, 'status-error': !apiStatus.mqtt }">
          <i :class="apiStatus.mqtt ? 'icon-checkmark' : 'icon-error'"></i>
          <span>MQTT</span>
        </div>
        <div class="status-item" :class="{ 'status-ok': apiStatus.deck, 'status-warning': !apiStatus.deck }">
          <i :class="apiStatus.deck ? 'icon-checkmark' : 'icon-warning'"></i>
          <span>Deck</span>
        </div>
        <div class="version">v1.0.0</div>
      </div>
    </footer>

    <!-- Benachrichtigungen -->
    <div v-if="notification" class="notification" :class="notification.type">
      <div class="notification-icon">
        <i :class="getNotificationIcon()"></i>
      </div>
      <div class="notification-content">{{ notification.message }}</div>
      <button @click="notification = null" class="notification-close">&times;</button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { useRouter } from 'vue-router';
import { apiService } from './api/apiService';

export default {
  name: 'App',
  setup() {
    // Router
    const router = useRouter();
    
    // State
    const loading = ref(true);
    const error = ref(null);
    const devices = ref([]);
    const alarms = ref([]);
    const apiStatus = reactive({
      api: false,
      mqtt: false,
      deck: false
    });
    const isRefreshing = ref(false);
    const updateTimer = ref(null);
    const notification = ref(null);
    
    // Dark Mode aus dem lokalen Speicher laden oder auf false setzen
    const darkMode = ref(localStorage.getItem('swissairdry_dark_mode') === 'true');
    
    // Update-Interval aus dem lokalen Speicher laden oder Standardwert verwenden
    const updateInterval = ref(parseInt(localStorage.getItem('swissairdry_update_interval')) || 30000);
    
    // Daten laden
    const loadData = async () => {
      try {
        loading.value = true;
        error.value = null;
        
        // Status laden
        const statusData = await apiService.getStatus();
        apiStatus.api = statusData.api || false;
        apiStatus.mqtt = statusData.mqtt || false;
        apiStatus.deck = statusData.deck?.initialized || false;
        
        // Dashboard-Daten laden
        const dashboardData = await apiService.getDashboard();
        devices.value = dashboardData.devices || [];
        alarms.value = dashboardData.alarms || [];
        
        loading.value = false;
      } catch (err) {
        console.error('Fehler beim Laden der Daten:', err);
        error.value = 'Fehler beim Laden der Daten. Bitte versuchen Sie es später erneut.';
        loading.value = false;
      }
    };
    
    // Daten aktualisieren
    const refreshData = async () => {
      if (isRefreshing.value) return;
      
      isRefreshing.value = true;
      try {
        // Status aktualisieren
        const statusData = await apiService.getStatus();
        apiStatus.api = statusData.api || false;
        apiStatus.mqtt = statusData.mqtt || false;
        apiStatus.deck = statusData.deck?.initialized || false;
        
        // Daten je nach aktuellem Pfad aktualisieren
        const path = router.currentRoute.value.path;
        
        if (path === '/' || path === '/dashboard') {
          const dashboardData = await apiService.getDashboard();
          devices.value = dashboardData.devices || [];
          alarms.value = dashboardData.alarms || [];
        } else if (path.startsWith('/devices')) {
          const devicesData = await apiService.getDevices();
          devices.value = devicesData.devices || [];
        } else if (path.startsWith('/alarms')) {
          const alarmsData = await apiService.getAlarms();
          alarms.value = alarmsData.alarms || [];
        }
        
        isRefreshing.value = false;
      } catch (err) {
        console.error('Fehler beim Aktualisieren der Daten:', err);
        isRefreshing.value = false;
        showNotification('Aktualisierung fehlgeschlagen. Bitte versuchen Sie es später erneut.', 'error');
      }
    };
    
    // Auto-Update starten
    const startAutoUpdate = () => {
      // Bestehenden Timer löschen, falls vorhanden
      if (updateTimer.value) {
        clearInterval(updateTimer.value);
      }
      
      // Neuen Timer setzen
      updateTimer.value = setInterval(() => {
        refreshData();
      }, updateInterval.value);
    };
    
    // Dark Mode umschalten
    const toggleDarkMode = () => {
      darkMode.value = !darkMode.value;
      localStorage.setItem('swissairdry_dark_mode', darkMode.value);
    };
    
    // Benachrichtigung anzeigen
    const showNotification = (message, type = 'info') => {
      notification.value = { message, type };
      
      // Nach 5 Sekunden automatisch ausblenden
      setTimeout(() => {
        if (notification.value && notification.value.message === message) {
          notification.value = null;
        }
      }, 5000);
    };
    
    // Icon für die Benachrichtigung ermitteln
    const getNotificationIcon = () => {
      if (!notification.value) return '';
      
      switch (notification.value.type) {
        case 'success': return 'icon-checkmark';
        case 'error': return 'icon-error';
        case 'warning': return 'icon-warning';
        default: return 'icon-info';
      }
    };
    
    // Daten beim Mounten laden
    onMounted(() => {
      loadData().then(() => {
        startAutoUpdate();
      });
    });
    
    // Timer beim Unmounten löschen
    onBeforeUnmount(() => {
      if (updateTimer.value) {
        clearInterval(updateTimer.value);
      }
    });
    
    return {
      loading,
      error,
      devices,
      alarms,
      apiStatus,
      darkMode,
      isRefreshing,
      notification,
      refreshData,
      toggleDarkMode,
      showNotification,
      getNotificationIcon
    };
  }
};
</script>

<style scoped>
/* Container */
#swissairdry-app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #f5f5f5;
  color: #333;
  transition: background-color 0.3s ease, color 0.3s ease;
}

#swissairdry-app.dark-mode {
  background-color: #222;
  color: #f5f5f5;
}

/* Header */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background-color: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: background-color 0.3s ease;
}

.dark-mode .app-header {
  background-color: #333;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.logo {
  display: flex;
  align-items: center;
}

.logo img {
  height: 30px;
  margin-right: 10px;
}

.logo h1 {
  font-size: 18px;
  font-weight: bold;
  color: #0082c9;
  margin: 0;
}

/* Navigation */
.main-nav {
  display: flex;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 0 5px;
  color: #666;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.dark-mode .nav-item {
  color: #ccc;
}

.nav-item .icon {
  margin-right: 8px;
  font-size: 16px;
}

.nav-item:hover {
  background-color: rgba(0, 130, 201, 0.1);
  color: #0082c9;
}

.nav-item.router-link-active {
  background-color: rgba(0, 130, 201, 0.2);
  color: #0082c9;
  font-weight: bold;
}

.dark-mode .nav-item:hover,
.dark-mode .nav-item.router-link-active {
  background-color: rgba(0, 130, 201, 0.3);
}

/* App Controls */
.app-controls {
  display: flex;
  align-items: center;
}

.app-controls button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  margin-left: 10px;
  background-color: transparent;
  border: none;
  border-radius: 4px;
  color: #666;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.dark-mode .app-controls button {
  color: #ccc;
}

.app-controls button:hover {
  background-color: rgba(0, 130, 201, 0.1);
  color: #0082c9;
}

.app-controls button i {
  font-size: 18px;
}

/* Refresh Button Animation */
.refresh-btn.rotating i {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Main Content */
.app-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

/* Footer */
.app-footer {
  padding: 10px 20px;
  background-color: #fff;
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.1);
  font-size: 12px;
  transition: background-color 0.3s ease;
}

.dark-mode .app-footer {
  background-color: #333;
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.5);
}

.status-bar {
  display: flex;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  margin-right: 20px;
  color: #666;
}

.dark-mode .status-item {
  color: #ccc;
}

.status-item i {
  margin-right: 5px;
}

.status-item.status-ok {
  color: #46ba61;
}

.status-item.status-warning {
  color: #e9a846;
}

.status-item.status-error {
  color: #e9424b;
}

.version {
  margin-left: auto;
  color: #999;
}

/* Notifications */
.notification {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 300px;
  max-width: 90%;
  animation: notification-slide-up 0.3s ease;
}

.dark-mode .notification {
  background-color: #333;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

@keyframes notification-slide-up {
  from { transform: translate(-50%, 20px); opacity: 0; }
  to { transform: translate(-50%, 0); opacity: 1; }
}

.notification-icon {
  margin-right: 12px;
  font-size: 20px;
}

.notification-content {
  flex: 1;
  font-size: 14px;
}

.notification-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #999;
  cursor: pointer;
  margin-left: 12px;
}

.notification-close:hover {
  color: #333;
}

.dark-mode .notification-close:hover {
  color: #f5f5f5;
}

.notification.success .notification-icon {
  color: #46ba61;
}

.notification.error .notification-icon {
  color: #e9424b;
}

.notification.warning .notification-icon {
  color: #e9a846;
}

.notification.info .notification-icon {
  color: #0082c9;
}

/* Responsive Layout */
@media (max-width: 768px) {
  .main-nav .label {
    display: none;
  }
  
  .main-nav .icon {
    margin-right: 0;
    font-size: 20px;
  }
  
  .nav-item {
    padding: 8px;
  }
  
  .logo h1 {
    display: none;
  }
}
</style>