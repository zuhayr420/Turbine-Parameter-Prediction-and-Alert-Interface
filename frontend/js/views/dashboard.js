/**
 * Dashboard View Component
 */
class DashboardView {
  static async render(container) {
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Station Summary</span>
          <span class="badge badge-normal" id="db-health-badge">SYSTEM HEALTH: ONLINE</span>
        </div>
      </div>

      <!-- KPI Grid -->
      <div class="kpi-grid" id="kpi-container">
        <div class="kpi-card accent">
          <span class="kpi-label">Active Turbines</span>
          <span class="kpi-val" id="kpi-active-units">--</span>
          <span class="kpi-subtext">Online generators</span>
        </div>
        <div class="kpi-card normal">
          <span class="kpi-label">Running Normal</span>
          <span class="kpi-val" id="kpi-running-units">--</span>
          <span class="kpi-subtext">Within safe limits</span>
        </div>
        <div class="kpi-card warning">
          <span class="kpi-label">Warning Units</span>
          <span class="kpi-val" id="kpi-warning-units">--</span>
          <span class="kpi-subtext">Approaching threshold</span>
        </div>
        <div class="kpi-card critical">
          <span class="kpi-label">Critical Units</span>
          <span class="kpi-val" id="kpi-critical-units">--</span>
          <span class="kpi-subtext">Immediate action req.</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Active Alerts</span>
          <span class="kpi-val" id="kpi-active-alerts">--</span>
          <span class="kpi-subtext" id="kpi-critical-alerts">-- Critical</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Parameters Monitored</span>
          <span class="kpi-val" id="kpi-parameters">--</span>
          <span class="kpi-subtext">Sensory telemetry</span>
        </div>
      </div>

      <!-- Turbines Overview Grid -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Turbine Units Overview</span>
          <div class="toolbar">
            <button class="btn btn-primary btn-sm" onclick="App.navigate('units')">+ Add / Manage Turbines</button>
          </div>
        </div>
        <div class="panel-body">
          <div class="unit-grid" id="units-grid">
            <div style="color:var(--text-muted);">Loading turbine units...</div>
          </div>
        </div>
      </div>

      <!-- Recent Predictive Alerts -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Active Predictive Alerts</span>
          <button class="btn btn-sm" onclick="App.navigate('alerts')">View Full Console</button>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Turbine</th>
                <th>Parameter</th>
                <th>Current Value</th>
                <th>Predicted Breach</th>
                <th>Breach In</th>
                <th>Alert Message</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody id="dashboard-alerts-tbody">
              <tr><td colspan="8" style="color:var(--text-muted);text-align:center;">No active alerts.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await DashboardView.loadData();
  }

  static async loadData() {
    try {
      const data = await ApiClient.getDashboard();
      if (!data) return;

      document.getElementById('kpi-active-units').innerText = `${data.running_units + data.warning_units + data.critical_units} / ${data.total_units}`;
      document.getElementById('kpi-running-units').innerText = data.running_units;
      document.getElementById('kpi-warning-units').innerText = data.warning_units;
      document.getElementById('kpi-critical-units').innerText = data.critical_units;
      document.getElementById('kpi-active-alerts').innerText = data.active_alerts;
      document.getElementById('kpi-critical-alerts').innerText = `${data.critical_alerts} Critical`;
      document.getElementById('kpi-parameters').innerText = data.parameters_monitored;

      // Render Units Grid
      const grid = document.getElementById('units-grid');
      grid.innerHTML = '';

      if (data.units.length === 0) {
        grid.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 24px; text-align: center; border: 1px dashed var(--border-subtle); border-radius: 2px;">
            <div style="font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Turbine Units Registered</div>
            <p style="color: var(--text-secondary); font-size: 12px; margin-bottom: 12px;">Get started by provisioning your thermal power station turbines.</p>
            <button class="btn btn-primary" onclick="App.navigate('units')">+ Provision First Turbine Unit</button>
          </div>
        `;
      } else {
        data.units.forEach(u => {
          let badgeClass = 'badge-normal';
          if (u.status === 'WARNING') badgeClass = 'badge-warning';
          if (u.status === 'CRITICAL') badgeClass = 'badge-critical';
          if (u.status === 'OFFLINE' || !u.active) badgeClass = 'badge-offline';

          const card = document.createElement('div');
          card.className = 'unit-card';
          card.onclick = () => App.navigate('unit_detail', { unitId: u.id });
          card.innerHTML = `
            <div class="unit-card-header">
              <div>
                <strong style="font-size:13px; color:var(--text-primary);">${u.unit_code}</strong>
                <div style="font-size:10px; color:var(--text-muted);">${u.location || 'Turbine Hall'}</div>
              </div>
              <span class="badge ${badgeClass}">${u.status}</span>
            </div>
            <div class="unit-card-body">
              <div style="font-size:12px; color:var(--text-secondary); font-weight:600;">${u.unit_name}</div>
              <div class="telemetry-row">
                <span class="telemetry-param">Capacity:</span>
                <span class="telemetry-val">${u.capacity_mw} MW</span>
              </div>
              <div class="telemetry-row">
                <span class="telemetry-param">Manufacturer:</span>
                <span class="telemetry-val">${u.manufacturer || '--'}</span>
              </div>
              <div class="telemetry-row">
                <span class="telemetry-param">Downtime:</span>
                <span class="telemetry-val">${u.downtime_hours} hrs</span>
              </div>
              <div style="margin-top:4px; display:flex; justify-content:flex-end;">
                <span style="font-size:11px; color:#38bdf8;">Inspect Telemetry & Forecast →</span>
              </div>
            </div>
          `;
          grid.appendChild(card);
        });
      }

      // Render Dashboard Alerts
      const alertsData = await ApiClient.getAlerts({ status: 'ACTIVE', limit: 5 });
      const tbody = document.getElementById('dashboard-alerts-tbody');
      tbody.innerHTML = '';

      if (alertsData && alertsData.alerts && alertsData.alerts.length > 0) {
        alertsData.alerts.forEach(a => {
          const sevClass = a.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning';
          const breachText = a.expected_breach_time ? `${new Date(a.expected_breach_time).toLocaleTimeString()}` : 'None';
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><span class="badge ${sevClass}">${a.severity}</span></td>
            <td class="mono"><strong>${a.unit_code || '--'}</strong></td>
            <td>${a.parameter_name || '--'}</td>
            <td class="mono">${a.current_value}</td>
            <td class="mono" style="color:#fbbf24;">${a.predicted_value || '--'}</td>
            <td class="mono">${breachText}</td>
            <td style="font-size:11px;">${a.message}</td>
            <td><span class="badge badge-normal">${a.status}</span></td>
          `;
          tbody.appendChild(tr);
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="8" style="color:var(--text-muted);text-align:center;padding:16px;">All turbines operating normally. No active predictive threshold breaches.</td></tr>`;
      }

    } catch (e) {
      console.error(e);
    }
  }
}

window.DashboardView = DashboardView;
