/**
 * SwissAirDry Dashboard mit Drag-and-Drop Funktionalität
 * 
 * Diese Datei enthält die JavaScript-Funktionen für das anpassbare Dashboard.
 * Es ermöglicht dem Benutzer, Widgets zu verschieben, zu entfernen und hinzuzufügen.
 * 
 * @author SwissAirDry Team
 * @copyright 2025 SwissAirDry
 */

// Dashboard-Konfiguration
let dashboardConfig = {
    widgets: [],
    layout: 'grid',
    theme: 'light',
    autoRefresh: true,
    refreshInterval: 60, // Sekunden
};

// Widget-Definitionen
const availableWidgets = [
    {
        id: 'device-status',
        title: 'Gerätestatus',
        type: 'status',
        size: 'medium',
        refreshInterval: 30,
        icon: 'device',
        description: 'Zeigt den Status aller verbundenen Geräte an'
    },
    {
        id: 'temperature-chart',
        title: 'Temperaturverlauf',
        type: 'chart',
        size: 'large',
        refreshInterval: 60,
        icon: 'temperature',
        description: 'Zeigt den Temperaturverlauf der ausgewählten Geräte an'
    },
    {
        id: 'humidity-chart',
        title: 'Feuchtigkeitsverlauf',
        type: 'chart',
        size: 'large',
        refreshInterval: 60,
        icon: 'humidity',
        description: 'Zeigt den Feuchtigkeitsverlauf der ausgewählten Geräte an'
    },
    {
        id: 'exapp-tasks',
        title: 'ExApp Aufgaben',
        type: 'list',
        size: 'medium',
        refreshInterval: 120,
        icon: 'tasks',
        description: 'Zeigt aktuelle Aufgaben aus der ExApp an'
    },
    {
        id: 'system-status',
        title: 'Systemstatus',
        type: 'status',
        size: 'small',
        refreshInterval: 30,
        icon: 'system',
        description: 'Zeigt den Status des SwissAirDry-Systems an'
    },
    {
        id: 'energy-chart',
        title: 'Energieverbrauch',
        type: 'chart',
        size: 'medium',
        refreshInterval: 3600,
        icon: 'energy',
        description: 'Zeigt den Energieverbrauch der Geräte an'
    }
];

// DOM-Elemente laden, wenn das Dokument fertig geladen ist
document.addEventListener('DOMContentLoaded', function() {
    // Dashboard-Container
    const dashboard = document.getElementById('dashboard');
    const widgetSelector = document.getElementById('widget-selector');
    const saveButton = document.getElementById('save-config');
    const resetButton = document.getElementById('reset-config');
    
    // Konfiguration vom Server laden
    loadDashboardConfig();
    
    // Widget-Auswahl anzeigen
    renderWidgetSelector();
    
    // Event-Listener für die Buttons
    if (saveButton) {
        saveButton.addEventListener('click', saveDashboardConfig);
    }
    if (resetButton) {
        resetButton.addEventListener('click', resetDashboardConfig);
    }
    
    // Drag-and-Drop-Funktionalität initialisieren
    initDragAndDrop();
});

/**
 * Lädt die Dashboard-Konfiguration vom Server
 */
async function loadDashboardConfig() {
    try {
        const response = await fetch('/api/dashboard/config');
        if (response.ok) {
            const data = await response.json();
            dashboardConfig = data;
            renderDashboard();
        } else {
            console.error('Fehler beim Laden der Dashboard-Konfiguration');
            // Standardkonfiguration verwenden
            setDefaultConfig();
            renderDashboard();
        }
    } catch (error) {
        console.error('Fehler beim Laden der Dashboard-Konfiguration:', error);
        // Standardkonfiguration verwenden
        setDefaultConfig();
        renderDashboard();
    }
}

/**
 * Setzt die Standard-Konfiguration
 */
function setDefaultConfig() {
    dashboardConfig = {
        widgets: [
            { id: 'device-status', position: 0, visible: true },
            { id: 'temperature-chart', position: 1, visible: true },
            { id: 'system-status', position: 2, visible: true }
        ],
        layout: 'grid',
        theme: 'light',
        autoRefresh: true,
        refreshInterval: 60
    };
}

/**
 * Speichert die Dashboard-Konfiguration auf dem Server
 */
async function saveDashboardConfig() {
    try {
        // Aktuelle Widget-Positionen und Konfiguration sammeln
        updateWidgetPositions();
        
        const response = await fetch('/api/dashboard/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dashboardConfig)
        });
        
        if (response.ok) {
            showNotification('Konfiguration gespeichert', 'success');
        } else {
            showNotification('Fehler beim Speichern der Konfiguration', 'error');
        }
    } catch (error) {
        console.error('Fehler beim Speichern der Konfiguration:', error);
        showNotification('Fehler beim Speichern der Konfiguration', 'error');
    }
}

/**
 * Setzt die Dashboard-Konfiguration zurück
 */
function resetDashboardConfig() {
    if (confirm('Möchten Sie die Dashboard-Konfiguration wirklich zurücksetzen?')) {
        setDefaultConfig();
        renderDashboard();
        showNotification('Konfiguration zurückgesetzt', 'info');
    }
}

/**
 * Aktualisiert die Widget-Positionen basierend auf der aktuellen DOM-Struktur
 */
function updateWidgetPositions() {
    const dashboardContainer = document.getElementById('dashboard');
    const widgetElements = dashboardContainer.querySelectorAll('.widget');
    
    // Array für die neuen Positionen
    const newWidgets = [];
    
    // Durch alle Widget-Elemente iterieren
    widgetElements.forEach((element, index) => {
        const widgetId = element.getAttribute('data-widget-id');
        
        // Widget-Konfiguration finden
        const existingWidget = dashboardConfig.widgets.find(w => w.id === widgetId);
        
        // Widget zur neuen Konfiguration hinzufügen
        if (existingWidget) {
            newWidgets.push({
                id: widgetId,
                position: index,
                visible: true,
                // Andere Eigenschaften beibehalten
                ...existingWidget,
                // Position immer aktualisieren
                position: index
            });
        } else {
            // Neues Widget
            newWidgets.push({
                id: widgetId,
                position: index,
                visible: true
            });
        }
    });
    
    // Konfiguration aktualisieren
    dashboardConfig.widgets = newWidgets;
}

/**
 * Rendert das Dashboard mit allen Widgets
 */
function renderDashboard() {
    const dashboardContainer = document.getElementById('dashboard');
    if (!dashboardContainer) return;
    
    // Dashboard leeren
    dashboardContainer.innerHTML = '';
    
    // Widgets sortiert nach Position
    const sortedWidgets = [...dashboardConfig.widgets]
        .filter(widget => widget.visible)
        .sort((a, b) => a.position - b.position);
    
    // Widgets rendern
    sortedWidgets.forEach(widget => {
        const widgetDef = availableWidgets.find(w => w.id === widget.id);
        if (widgetDef) {
            const widgetElement = createWidgetElement(widgetDef);
            dashboardContainer.appendChild(widgetElement);
            
            // Widget-Inhalt laden
            loadWidgetContent(widgetDef, widgetElement);
        }
    });
    
    // Nach dem Rendern Drag-and-Drop initialisieren
    initDragAndDrop();
}

/**
 * Erstellt ein Widget-Element
 */
function createWidgetElement(widget) {
    const widgetElement = document.createElement('div');
    widgetElement.className = `widget widget-${widget.size}`;
    widgetElement.setAttribute('data-widget-id', widget.id);
    widgetElement.setAttribute('draggable', 'true');
    
    // Widget-Header
    const header = document.createElement('div');
    header.className = 'widget-header';
    
    // Titel
    const title = document.createElement('h3');
    title.textContent = widget.title;
    header.appendChild(title);
    
    // Aktionen (Symbol-Buttons für Bearbeiten, Löschen, etc.)
    const actions = document.createElement('div');
    actions.className = 'widget-actions';
    
    // Refresh-Button
    const refreshBtn = document.createElement('button');
    refreshBtn.className = 'widget-action-btn refresh-btn';
    refreshBtn.innerHTML = '<i class="fa fa-refresh"></i>';
    refreshBtn.title = 'Aktualisieren';
    refreshBtn.addEventListener('click', function() {
        loadWidgetContent(widget, widgetElement);
    });
    actions.appendChild(refreshBtn);
    
    // Einstellungen-Button
    const settingsBtn = document.createElement('button');
    settingsBtn.className = 'widget-action-btn settings-btn';
    settingsBtn.innerHTML = '<i class="fa fa-cog"></i>';
    settingsBtn.title = 'Einstellungen';
    settingsBtn.addEventListener('click', function() {
        openWidgetSettings(widget);
    });
    actions.appendChild(settingsBtn);
    
    // Entfernen-Button
    const removeBtn = document.createElement('button');
    removeBtn.className = 'widget-action-btn remove-btn';
    removeBtn.innerHTML = '<i class="fa fa-times"></i>';
    removeBtn.title = 'Entfernen';
    removeBtn.addEventListener('click', function() {
        removeWidget(widget.id);
    });
    actions.appendChild(removeBtn);
    
    header.appendChild(actions);
    widgetElement.appendChild(header);
    
    // Widget-Inhalt
    const content = document.createElement('div');
    content.className = 'widget-content';
    content.innerHTML = '<div class="loading">Lädt...</div>';
    widgetElement.appendChild(content);
    
    return widgetElement;
}

/**
 * Lädt den Inhalt eines Widgets
 */
async function loadWidgetContent(widget, widgetElement) {
    const contentElement = widgetElement.querySelector('.widget-content');
    
    // Loading-Anzeige
    contentElement.innerHTML = '<div class="loading">Lädt...</div>';
    
    try {
        // Daten vom Server laden (je nach Widget-Typ unterschiedliche URL)
        let url = `/api/dashboard/widget/${widget.id}/data`;
        
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            
            // Widget-Inhalt rendern (abhängig vom Typ)
            switch (widget.type) {
                case 'status':
                    renderStatusWidget(data, contentElement, widget);
                    break;
                case 'chart':
                    renderChartWidget(data, contentElement, widget);
                    break;
                case 'list':
                    renderListWidget(data, contentElement, widget);
                    break;
                default:
                    contentElement.innerHTML = '<div class="error">Unbekannter Widget-Typ</div>';
            }
        } else {
            // Fehler beim Laden
            contentElement.innerHTML = '<div class="error">Fehler beim Laden der Daten</div>';
        }
    } catch (error) {
        console.error(`Fehler beim Laden des Widget-Inhalts (${widget.id}):`, error);
        contentElement.innerHTML = '<div class="error">Fehler beim Laden der Daten</div>';
    }
}

/**
 * Rendert ein Status-Widget
 */
function renderStatusWidget(data, contentElement, widget) {
    let html = '<div class="status-widget">';
    
    if (widget.id === 'device-status') {
        // Gerätestatus-Widget
        if (data.devices && data.devices.length > 0) {
            html += '<ul class="device-list">';
            data.devices.forEach(device => {
                html += `
                    <li class="device-item device-${device.status}">
                        <span class="device-name">${device.name}</span>
                        <span class="device-status">${device.status}</span>
                    </li>
                `;
            });
            html += '</ul>';
        } else {
            html += '<p>Keine Geräte gefunden</p>';
        }
    } else if (widget.id === 'system-status') {
        // Systemstatus-Widget
        html += `
            <div class="system-status-overview">
                <div class="status-item">
                    <span class="label">API</span>
                    <span class="status status-${data.api ? 'online' : 'offline'}">${data.api ? 'Online' : 'Offline'}</span>
                </div>
                <div class="status-item">
                    <span class="label">MQTT</span>
                    <span class="status status-${data.mqtt ? 'online' : 'offline'}">${data.mqtt ? 'Online' : 'Offline'}</span>
                </div>
                <div class="status-item">
                    <span class="label">ExApp</span>
                    <span class="status status-${data.exapp ? 'online' : 'offline'}">${data.exapp ? 'Online' : 'Offline'}</span>
                </div>
                <div class="status-item">
                    <span class="label">Datenbank</span>
                    <span class="status status-${data.database ? 'online' : 'offline'}">${data.database ? 'Online' : 'Offline'}</span>
                </div>
            </div>
            <div class="uptime">
                <span class="label">Uptime</span>
                <span class="value">${data.uptime || 'Unbekannt'}</span>
            </div>
        `;
    }
    
    html += '</div>';
    contentElement.innerHTML = html;
}

/**
 * Rendert ein Chart-Widget
 */
function renderChartWidget(data, contentElement, widget) {
    // Canvas für das Chart erstellen
    contentElement.innerHTML = `<canvas id="chart-${widget.id}"></canvas>`;
    const canvas = document.getElementById(`chart-${widget.id}`);
    
    // Chart erstellen (mit Chart.js)
    if (typeof Chart !== 'undefined') {
        let chartType = 'line';
        let chartTitle = widget.title;
        let chartData = {
            labels: data.labels || [],
            datasets: data.datasets || []
        };
        
        let options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: chartTitle
                }
            }
        };
        
        new Chart(canvas, {
            type: chartType,
            data: chartData,
            options: options
        });
    } else {
        // Fallback, wenn Chart.js nicht verfügbar ist
        contentElement.innerHTML = `
            <div class="chart-fallback">
                <p>Chart.js wird benötigt, um dieses Widget anzuzeigen</p>
            </div>
        `;
    }
}

/**
 * Rendert ein Listen-Widget
 */
function renderListWidget(data, contentElement, widget) {
    let html = '<div class="list-widget">';
    
    if (widget.id === 'exapp-tasks') {
        // ExApp-Aufgaben-Widget
        if (data.tasks && data.tasks.length > 0) {
            html += '<ul class="task-list">';
            data.tasks.forEach(task => {
                html += `
                    <li class="task-item priority-${task.priority}">
                        <span class="task-title">${task.title}</span>
                        <span class="task-due-date">${task.dueDate || ''}</span>
                    </li>
                `;
            });
            html += '</ul>';
        } else {
            html += '<p>Keine Aufgaben gefunden</p>';
        }
    }
    
    html += '</div>';
    contentElement.innerHTML = html;
}

/**
 * Rendert die Widget-Auswahl
 */
function renderWidgetSelector() {
    const widgetSelector = document.getElementById('widget-selector');
    if (!widgetSelector) return;
    
    // Widget-Auswahl leeren
    widgetSelector.innerHTML = '';
    
    // Titel
    const title = document.createElement('h3');
    title.textContent = 'Verfügbare Widgets';
    widgetSelector.appendChild(title);
    
    // Widget-Liste
    const widgetList = document.createElement('div');
    widgetList.className = 'widget-list';
    
    // Alle verfügbaren Widgets durchgehen
    availableWidgets.forEach(widget => {
        // Prüfen, ob das Widget bereits im Dashboard ist
        const isActive = dashboardConfig.widgets.some(w => w.id === widget.id && w.visible);
        
        const widgetItem = document.createElement('div');
        widgetItem.className = `widget-item ${isActive ? 'active' : ''}`;
        widgetItem.setAttribute('data-widget-id', widget.id);
        widgetItem.setAttribute('draggable', 'true');
        
        widgetItem.innerHTML = `
            <div class="widget-item-icon">
                <i class="fa fa-${widget.icon || 'chart-line'}"></i>
            </div>
            <div class="widget-item-details">
                <h4>${widget.title}</h4>
                <p>${widget.description}</p>
            </div>
        `;
        
        // Click-Event hinzufügen
        widgetItem.addEventListener('click', function() {
            if (!isActive) {
                addWidget(widget.id);
            }
        });
        
        widgetList.appendChild(widgetItem);
    });
    
    widgetSelector.appendChild(widgetList);
}

/**
 * Fügt ein Widget zum Dashboard hinzu
 */
function addWidget(widgetId) {
    // Prüfen, ob das Widget bereits vorhanden ist
    const existingIndex = dashboardConfig.widgets.findIndex(w => w.id === widgetId);
    
    if (existingIndex >= 0) {
        // Widget ist vorhanden, aber möglicherweise nicht sichtbar
        dashboardConfig.widgets[existingIndex].visible = true;
    } else {
        // Widget hinzufügen
        dashboardConfig.widgets.push({
            id: widgetId,
            position: dashboardConfig.widgets.length,
            visible: true
        });
    }
    
    // Dashboard aktualisieren
    renderDashboard();
    
    // Widget-Auswahl aktualisieren
    renderWidgetSelector();
    
    showNotification('Widget hinzugefügt', 'success');
}

/**
 * Entfernt ein Widget vom Dashboard
 */
function removeWidget(widgetId) {
    // Widget suchen
    const index = dashboardConfig.widgets.findIndex(w => w.id === widgetId);
    
    if (index >= 0) {
        // Widget entfernen
        dashboardConfig.widgets.splice(index, 1);
        
        // Positionen neu berechnen
        dashboardConfig.widgets.forEach((widget, i) => {
            widget.position = i;
        });
        
        // Dashboard aktualisieren
        renderDashboard();
        
        // Widget-Auswahl aktualisieren
        renderWidgetSelector();
        
        showNotification('Widget entfernt', 'info');
    }
}

/**
 * Öffnet die Einstellungen für ein Widget
 */
function openWidgetSettings(widget) {
    // TODO: Widget-Einstellungsmodal implementieren
    console.log('Widget-Einstellungen öffnen für:', widget);
    alert('Widget-Einstellungen werden noch implementiert');
}

/**
 * Initialisiert die Drag-and-Drop-Funktionalität
 */
function initDragAndDrop() {
    // Widgets aus dem Dashboard
    const widgetElements = document.querySelectorAll('#dashboard .widget');
    
    widgetElements.forEach(widget => {
        // Drag-Events
        widget.addEventListener('dragstart', handleDragStart);
        widget.addEventListener('dragend', handleDragEnd);
        
        // Drop-Events
        widget.addEventListener('dragover', handleDragOver);
        widget.addEventListener('dragenter', handleDragEnter);
        widget.addEventListener('dragleave', handleDragLeave);
        widget.addEventListener('drop', handleDrop);
    });
    
    // Widgets aus der Auswahl
    const widgetItems = document.querySelectorAll('#widget-selector .widget-item');
    
    widgetItems.forEach(item => {
        item.addEventListener('dragstart', handleSelectorDragStart);
        item.addEventListener('dragend', handleSelectorDragEnd);
    });
    
    // Dashboard als Drop-Target
    const dashboard = document.getElementById('dashboard');
    if (dashboard) {
        dashboard.addEventListener('dragover', handleDashboardDragOver);
        dashboard.addEventListener('drop', handleDashboardDrop);
    }
}

// Drag-Variablen
let draggedWidget = null;
let dragSource = null;

// Drag-Handler für Widgets
function handleDragStart(e) {
    draggedWidget = this;
    dragSource = 'dashboard';
    
    // Opacity ändern während des Drags
    this.style.opacity = '0.4';
    
    // Daten im dataTransfer speichern
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', this.getAttribute('data-widget-id'));
}

function handleDragEnd(e) {
    // Opacity zurücksetzen
    this.style.opacity = '1';
    
    // Alle Drag-Effekte zurücksetzen
    document.querySelectorAll('.widget').forEach(item => {
        item.classList.remove('over');
    });
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Erlaubt das Droppen
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(e) {
    // Highlight-Effekt für das Ziel
    this.classList.add('over');
}

function handleDragLeave(e) {
    // Highlight-Effekt entfernen
    this.classList.remove('over');
}

function handleDrop(e) {
    // Standard-Aktion verhindern
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    // Nur verarbeiten, wenn das gedroppte Element ein anderes ist
    if (draggedWidget && draggedWidget !== this && dragSource === 'dashboard') {
        // Widget-ID des Drag-Elements
        const draggedId = draggedWidget.getAttribute('data-widget-id');
        
        // Widget-ID des Ziel-Elements
        const targetId = this.getAttribute('data-widget-id');
        
        // Positionen in der Konfiguration finden
        const draggedIndex = dashboardConfig.widgets.findIndex(w => w.id === draggedId);
        const targetIndex = dashboardConfig.widgets.findIndex(w => w.id === targetId);
        
        if (draggedIndex >= 0 && targetIndex >= 0) {
            // Elemente in der Konfiguration tauschen
            const temp = dashboardConfig.widgets[draggedIndex].position;
            dashboardConfig.widgets[draggedIndex].position = dashboardConfig.widgets[targetIndex].position;
            dashboardConfig.widgets[targetIndex].position = temp;
            
            // Dashboard neu rendern
            renderDashboard();
        }
    }
    
    // Highlight-Effekt entfernen
    this.classList.remove('over');
    
    return false;
}

// Drag-Handler für Widget-Selector
function handleSelectorDragStart(e) {
    draggedWidget = this;
    dragSource = 'selector';
    
    // Opacity ändern während des Drags
    this.style.opacity = '0.4';
    
    // Daten im dataTransfer speichern
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('text/plain', this.getAttribute('data-widget-id'));
}

function handleSelectorDragEnd(e) {
    // Opacity zurücksetzen
    this.style.opacity = '1';
}

// Drag-Handler für das Dashboard
function handleDashboardDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault(); // Erlaubt das Droppen
    }
    e.dataTransfer.dropEffect = 'copy';
    return false;
}

function handleDashboardDrop(e) {
    // Standard-Aktion verhindern
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    // Wenn das gedroppte Element aus dem Selector kommt
    if (dragSource === 'selector') {
        // Widget-ID holen
        const widgetId = e.dataTransfer.getData('text/plain');
        
        // Widget hinzufügen
        addWidget(widgetId);
    }
    
    return false;
}

/**
 * Zeigt eine Benachrichtigung an
 */
function showNotification(message, type = 'info') {
    // Notification-Container erstellen, falls noch nicht vorhanden
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
    
    // Notification erstellen
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-message">${message}</span>
        <button class="notification-close">×</button>
    `;
    
    // Close-Button
    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', function() {
        container.removeChild(notification);
    });
    
    // Notification zum Container hinzufügen
    container.appendChild(notification);
    
    // Automatisch entfernen nach 5 Sekunden
    setTimeout(() => {
        if (notification.parentNode === container) {
            container.removeChild(notification);
        }
    }, 5000);
}