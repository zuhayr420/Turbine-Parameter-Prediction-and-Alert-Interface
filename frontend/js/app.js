/**
 * Master Application Router & Navigation Orchestrator
 */
class App {
  static init() {
    // Verify auth
    const user = Auth.checkAuth();
    if (!user) return;

    // Display user profile in sidebar
    document.getElementById('nav-user-name').innerText = user.username;
    document.getElementById('nav-user-role').innerText = user.role;

    // Setup health monitoring heartbeat
    App.pollHealth();
    setInterval(App.pollHealth, 15000);

    // Initial navigation
    App.navigate('dashboard');

    // Initialize Socket.io connection for real-time telemetry
    App.socket = io('http://localhost:5000');
    App.socket.on('connect', () => {
      console.log("WebSocket connected for real-time telemetry.");
    });
    App.socket.on('telemetry_update', (data) => {
      // Trigger a custom event that specific views (like UnitDetailView) can listen to
      const event = new CustomEvent('telemetry_update', { detail: data });
      window.dispatchEvent(event);
    });
  }

  static async pollHealth() {
    try {
      const h = await ApiClient.getHealth();
      const dot = document.getElementById('heartbeat-dot');
      const val = document.getElementById('heartbeat-val');
      if (h && h.status === 'ONLINE') {
        if (dot) dot.className = 'indicator-dot';
        if (val) val.innerText = 'ONLINE';
      } else {
        if (dot) dot.className = 'indicator-dot warning';
        if (val) val.innerText = h?.status || 'DEGRADED';
      }
      const clock = document.getElementById('clock-val');
      if (clock) clock.innerText = new Date().toLocaleTimeString();
    } catch {
      const dot = document.getElementById('heartbeat-dot');
      const val = document.getElementById('heartbeat-val');
      if (dot) dot.className = 'indicator-dot critical';
      if (val) val.innerText = 'OFFLINE';
    }
  }

  static navigate(viewName, params = {}) {
    // Update active class on navigation items
    document.querySelectorAll('.nav-item').forEach(el => {
      if (el.getAttribute('data-view') === viewName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    const contentArea = document.getElementById('app-content-area');
    contentArea.innerHTML = '';

    switch (viewName) {
      case 'dashboard':
        DashboardView.render(contentArea);
        break;
      case 'units':
        UnitsView.render(contentArea);
        break;
      case 'unit_detail':
        UnitDetailView.render(contentArea, params);
        break;
      case 'predictions':
        PredictionsView.render(contentArea);
        break;
      case 'alerts':
        AlertsView.render(contentArea);
        break;
      case 'telemetry_input':
        TelemetryInputView.render(contentArea, params);
        break;
      case 'historical':
        HistoricalView.render(contentArea);
        break;
      case 'reports':
        ReportsView.render(contentArea);
        break;
      case 'admin':
        AdminView.render(contentArea);
        break;
      default:
        DashboardView.render(contentArea);
    }
  }
}

window.App = App;
window.onload = App.init;
