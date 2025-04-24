/**
 * SwissAirDry - Web App
 * 
 * Hauptskript für die SwissAirDry-Webanwendung
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialisierung
  initApp();
  
  // Event-Listener registrieren
  registerEventListeners();
  
  // API-Status prüfen
  checkApiStatus();
  
  // Beispieldaten laden
  loadDashboardData();
  
  // Tutorial überprüfen
  checkAndStartTutorial();
});

/**
 * App initialisieren
 */
function initApp() {
  // Login-Status prüfen
  const token = localStorage.getItem('api_token');
  
  if (!token) {
    // Nicht eingeloggt, zur Login-Seite weiterleiten
    console.log('Nicht eingeloggt, Weiterleitung zur Login-Seite...');
    // In einer echten App: window.location.href = 'login.html';
  }
  
  // Aktuelle Seite aus URL-Hash ermitteln und anzeigen
  const hash = window.location.hash || '#dashboard';
  showSection(hash.substring(1));
}

/**
 * Event-Listener registrieren
 */
function registerEventListeners() {
  // Navigation
  document.querySelectorAll('nav a').forEach(link => {
    link.addEventListener('click', function(e) {
      const section = this.getAttribute('href').substring(1);
      showSection(section);
    });
  });
  
  // Logout-Button
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
      localStorage.removeItem('api_token');
      console.log('Abgemeldet, Weiterleitung zur Login-Seite...');
      // In einer echten App: window.location.href = 'login.html';
    });
  }
  
  // Tutorial-Button
  const tutorialBtn = document.getElementById('tutorial-btn');
  if (tutorialBtn) {
    tutorialBtn.addEventListener('click', function() {
      startTutorial();
    });
  }
  
  // Tutorial-Close-Button
  const tutorialCloseBtn = document.getElementById('tutorial-close');
  if (tutorialCloseBtn) {
    tutorialCloseBtn.addEventListener('click', function() {
      closeTutorial();
    });
  }
  
  // Tutorial-Prev-Button
  const tutorialPrevBtn = document.getElementById('tutorial-prev');
  if (tutorialPrevBtn) {
    tutorialPrevBtn.addEventListener('click', function() {
      navigateTutorial('prev');
    });
  }
  
  // Tutorial-Next-Button
  const tutorialNextBtn = document.getElementById('tutorial-next');
  if (tutorialNextBtn) {
    tutorialNextBtn.addEventListener('click', function() {
      navigateTutorial('next');
    });
  }
  
  // Tastatur-Navigation für Tutorial
  document.addEventListener('keydown', function(e) {
    const tutorialOverlay = document.getElementById('tutorial-overlay');
    
    if (tutorialOverlay && !tutorialOverlay.classList.contains('hidden')) {
      if (e.key === 'Escape') {
        closeTutorial();
      } else if (e.key === 'ArrowRight') {
        navigateTutorial('next');
      } else if (e.key === 'ArrowLeft') {
        navigateTutorial('prev');
      }
    }
  });
}

/**
 * Abschnitt anzeigen
 */
function showSection(sectionId) {
  // Alle Abschnitte ausblenden
  document.querySelectorAll('main section').forEach(section => {
    section.classList.remove('active-section');
  });
  
  // Gewählten Abschnitt einblenden
  const activeSection = document.getElementById(sectionId);
  if (activeSection) {
    activeSection.classList.add('active-section');
  }
  
  // URL-Hash aktualisieren
  window.location.hash = '#' + sectionId;
}

/**
 * API-Status prüfen
 */
function checkApiStatus() {
  // Beispiel für API-Status-Prüfung
  fetch('/api/health')
    .then(response => {
      if (response.ok) {
        updateApiStatus('online');
      } else {
        updateApiStatus('offline');
      }
    })
    .catch(error => {
      console.error('API-Status-Prüfung fehlgeschlagen:', error);
      updateApiStatus('offline');
    });
  
  // Status alle 60 Sekunden aktualisieren
  setTimeout(checkApiStatus, 60000);
}

/**
 * API-Status aktualisieren
 */
function updateApiStatus(status) {
  const statusIndicator = document.querySelector('.status-indicator');
  
  if (statusIndicator) {
    statusIndicator.className = 'status-indicator ' + status;
    statusIndicator.textContent = status === 'online' ? 'Online' : 'Offline';
  }
}

/**
 * Dashboard-Daten laden
 */
function loadDashboardData() {
  // In einer echten App würden hier Daten von der API geladen werden
  console.log('Dashboard-Daten werden geladen...');
}

/**
 * Überprüfen, ob Tutorial gestartet werden soll
 */
function checkAndStartTutorial() {
  // Prüfen, ob der Benutzer die App zum ersten Mal verwendet
  const hasSeenTutorial = localStorage.getItem('tutorial_completed');
  
  if (!hasSeenTutorial) {
    // Tutorial nach kurzer Verzögerung starten
    setTimeout(startTutorial, 1000);
  }
}

/**
 * Tutorial starten
 */
function startTutorial() {
  const tutorialOverlay = document.getElementById('tutorial-overlay');
  if (tutorialOverlay) {
    tutorialOverlay.classList.remove('hidden');
    showTutorialStep(1);
  }
}

/**
 * Tutorial schließen
 */
function closeTutorial() {
  const tutorialOverlay = document.getElementById('tutorial-overlay');
  if (tutorialOverlay) {
    tutorialOverlay.classList.add('hidden');
    
    // Alle Highlights entfernen
    removeAllHighlights();
    
    // Alle Tooltips entfernen
    removeAllTooltips();
    
    // Tutorial als gesehen markieren
    localStorage.setItem('tutorial_completed', 'true');
  }
}

/**
 * Tutorial-Navigation
 * @param {string} direction - "prev" oder "next"
 */
function navigateTutorial(direction) {
  const currentStepEl = document.querySelector('.tutorial-step.active');
  if (!currentStepEl) return;
  
  const currentStep = parseInt(currentStepEl.getAttribute('data-step'));
  const totalSteps = document.querySelectorAll('.tutorial-step').length;
  
  // Nächsten oder vorherigen Schritt berechnen
  let nextStep = currentStep;
  if (direction === 'next' && currentStep < totalSteps) {
    nextStep = currentStep + 1;
  } else if (direction === 'prev' && currentStep > 1) {
    nextStep = currentStep - 1;
  }
  
  // Zum nächsten Schritt wechseln
  if (nextStep !== currentStep) {
    showTutorialStep(nextStep);
  }
  
  // Wenn letzter Schritt, "Weiter"-Button in "Fertig" umbenennen
  const nextButton = document.getElementById('tutorial-next');
  if (nextButton) {
    if (nextStep === totalSteps) {
      nextButton.textContent = 'Fertig';
      nextButton.addEventListener('click', closeTutorial, { once: true });
    } else {
      nextButton.textContent = 'Weiter';
      nextButton.removeEventListener('click', closeTutorial);
    }
  }
}

/**
 * Zeigt einen bestimmten Tutorial-Schritt an
 * @param {number} stepNumber - Nummer des anzuzeigenden Schritts
 */
function showTutorialStep(stepNumber) {
  // Alle Schritte ausblenden
  document.querySelectorAll('.tutorial-step').forEach(step => {
    step.classList.remove('active');
  });
  
  // Gewählten Schritt einblenden
  const activeStep = document.querySelector(`.tutorial-step[data-step="${stepNumber}"]`);
  if (activeStep) {
    activeStep.classList.add('active');
  }
  
  // Fortschrittsanzeige aktualisieren
  const currentStepEl = document.getElementById('current-step');
  if (currentStepEl) {
    currentStepEl.textContent = stepNumber;
  }
  
  // Zurück-Button aktivieren/deaktivieren
  const prevButton = document.getElementById('tutorial-prev');
  if (prevButton) {
    prevButton.disabled = stepNumber === 1;
  }
  
  // Alle Highlights entfernen
  removeAllHighlights();
  
  // Alle Tooltips entfernen
  removeAllTooltips();
  
  // Element für diesen Schritt hervorheben
  highlightElementForStep(stepNumber);
}

/**
 * Hebt ein Element basierend auf dem aktuellen Tutorial-Schritt hervor
 * @param {number} stepNumber - Aktuelle Schrittnummer
 */
function highlightElementForStep(stepNumber) {
  let selector;
  
  switch (stepNumber) {
    case 2: // Dashboard
      selector = 'nav a[data-tutorial="dashboard"]';
      break;
    case 3: // Statistik-Karten
      selector = '[data-tutorial="stat-card"]';
      break;
    case 4: // Diagramme
      selector = '[data-tutorial="chart"]';
      break;
    case 5: // Meldungen
      selector = '[data-tutorial="alerts"]';
      break;
    case 6: // Geräte
      selector = 'nav a[data-tutorial="devices"]';
      break;
    case 7: // Aufträge
      selector = 'nav a[data-tutorial="jobs"]';
      break;
    case 8: // Berichte
      selector = 'nav a[data-tutorial="reports"]';
      break;
    case 9: // Einstellungen
      selector = 'nav a[data-tutorial="settings"]';
      break;
    case 10: // API-Status
      selector = '[data-tutorial="api-status"]';
      break;
    case 11: // Hilfe-Button
      selector = '[data-tutorial="help"]';
      break;
    default:
      selector = null;
  }
  
  if (selector) {
    const element = document.querySelector(selector);
    if (element) {
      element.classList.add('tutorial-highlight');
      
      // Tooltip hinzufügen
      addTooltipToElement(element, getTutorialTextForStep(stepNumber));
      
      // Zu dem Element scrollen
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }
}

/**
 * Entfernt alle Highlight-Klassen
 */
function removeAllHighlights() {
  document.querySelectorAll('.tutorial-highlight').forEach(el => {
    el.classList.remove('tutorial-highlight');
  });
}

/**
 * Fügt einem Element ein Tooltip hinzu
 * @param {HTMLElement} element - Element, an das der Tooltip angehängt werden soll
 * @param {string} text - Text des Tooltips
 */
function addTooltipToElement(element, text) {
  // Tooltip erstellen
  const tooltip = document.createElement('div');
  tooltip.className = 'tutorial-tooltip';
  tooltip.textContent = text;
  
  // Position und Richtung bestimmen
  const rect = element.getBoundingClientRect();
  const windowHeight = window.innerHeight;
  const windowWidth = window.innerWidth;
  
  let direction = 'top';
  
  // Bestimmen, in welche Richtung der Tooltip zeigen soll
  if (rect.top < 100) {
    direction = 'bottom';
  } else if (rect.left < 150) {
    direction = 'right';
  } else if (windowWidth - rect.right < 150) {
    direction = 'left';
  }
  
  tooltip.classList.add(direction);
  
  // Tooltip positionieren
  let top, left;
  
  switch (direction) {
    case 'bottom':
      top = rect.bottom + 10;
      left = rect.left + rect.width / 2 - 125;
      break;
    case 'top':
      top = rect.top - 60;
      left = rect.left + rect.width / 2 - 125;
      break;
    case 'left':
      top = rect.top + rect.height / 2 - 25;
      left = rect.left - 260;
      break;
    case 'right':
      top = rect.top + rect.height / 2 - 25;
      left = rect.right + 10;
      break;
  }
  
  // Sicherstellen, dass der Tooltip im Viewport bleibt
  top = Math.max(10, Math.min(windowHeight - 70, top));
  left = Math.max(10, Math.min(windowWidth - 260, left));
  
  tooltip.style.top = `${top}px`;
  tooltip.style.left = `${left}px`;
  
  // Tooltip zum DOM hinzufügen
  document.body.appendChild(tooltip);
}

/**
 * Entfernt alle Tooltips
 */
function removeAllTooltips() {
  document.querySelectorAll('.tutorial-tooltip').forEach(tooltip => {
    tooltip.remove();
  });
}

/**
 * Gibt den Tooltip-Text für einen bestimmten Schritt zurück
 * @param {number} stepNumber - Nummer des Tutorial-Schritts
 * @returns {string} - Tooltip-Text
 */
function getTutorialTextForStep(stepNumber) {
  switch (stepNumber) {
    case 2:
      return "Im Dashboard sehen Sie eine Übersicht Ihrer Geräte und Sensordaten.";
    case 3:
      return "Statistik-Karten zeigen wichtige Kennzahlen auf einen Blick.";
    case 4:
      return "Diagramme visualisieren den Verlauf Ihrer Sensordaten.";
    case 5:
      return "Hier werden aktuelle Meldungen und Warnungen angezeigt.";
    case 6:
      return "Unter 'Geräte' sehen Sie alle Ihre Trocknungsgeräte.";
    case 7:
      return "Verwalten Sie hier Ihre Trocknungsaufträge.";
    case 8:
      return "Erstellen Sie detaillierte Berichte über abgeschlossene Trocknungsprojekte.";
    case 9:
      return "Passen Sie die App an Ihre Bedürfnisse an.";
    case 10:
      return "Hier sehen Sie den aktuellen Status der API-Verbindung.";
    case 11:
      return "Klicken Sie auf diesen Button, um das Tutorial erneut anzuzeigen.";
    default:
      return "";
  }
}