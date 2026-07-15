/**
 * Alerts Console & Threshold Breaches Management View
 */
class AlertsView {
  static async render(container) {
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Central Predictive Alert Management Console</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Status:</label>
            <select id="alerts-filter-status" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="AlertsView.loadData()">
              <option value="">All Statuses</option>
              <option value="ACTIVE" selected>ACTIVE Only</option>
              <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
              <option value="RESOLVED">RESOLVED</option>
            </select>
            <label style="font-size:11px; color:var(--text-secondary); margin-left:8px;">Severity:</label>
            <select id="alerts-filter-severity" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="AlertsView.loadData()">
              <option value="">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="WARNING">WARNING</option>
            </select>
            <button class="btn btn-sm" onclick="AlertsView.loadData()">Refresh Alerts</button>
          </div>
        </div>
      </div>

      <!-- Alert Console Table -->
      <div class="panel">
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Time Logged</th>
                <th>Turbine</th>
                <th>Parameter</th>
                <th>Current</th>
                <th>Predicted</th>
                <th>Threshold</th>
                <th>Breach In</th>
                <th>Message</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="alerts-full-tbody">
              <tr><td colspan="11" style="color:var(--text-muted); text-align:center;">Loading alert records...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await AlertsView.loadData();
  }

  static async loadData() {
    const status = document.getElementById('alerts-filter-status')?.value;
    const severity = document.getElementById('alerts-filter-severity')?.value;

    const params = {};
    if (status) params.status = status;
    if (severity) params.severity = severity;

    try {
      const res = await ApiClient.getAlerts(params);
      const tbody = document.getElementById('alerts-full-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      if (!res.alerts || res.alerts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:var(--text-muted); padding:20px;">No alerts matching current filters.</td></tr>`;
        return;
      }

      res.alerts.forEach(a => {
        const sevClass = a.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning';
        const etaText = a.expected_breach_time ? `${new Date(a.expected_breach_time).toLocaleTimeString()}` : 'None';
        const tr = document.createElement('tr');

        let actionBtns = '--';
        if (a.status === 'ACTIVE') {
          actionBtns = `
            <button class="btn btn-sm" onclick="AlertsView.acknowledge(${a.id})">Acknowledge</button>
            <button class="btn btn-sm btn-primary" onclick="AlertsView.resolve(${a.id})">Resolve</button>
          `;
        } else if (a.status === 'ACKNOWLEDGED') {
          actionBtns = `<button class="btn btn-sm btn-primary" onclick="AlertsView.resolve(${a.id})">Resolve</button>`;
        }

        tr.innerHTML = `
          <td><span class="badge ${sevClass}">${a.severity}</span></td>
          <td class="mono" style="font-size:11px;">${new Date(a.created_at).toLocaleTimeString()}</td>
          <td class="mono"><strong>${a.unit_code || '--'}</strong></td>
          <td>${a.parameter_name || '--'}</td>
          <td class="mono">${a.current_value}</td>
          <td class="mono" style="color:#fbbf24; font-weight:700;">${a.predicted_value || '--'}</td>
          <td class="mono">${a.threshold}</td>
          <td class="mono">${etaText}</td>
          <td style="font-size:11px; max-width:260px; white-space:normal;">${a.message}</td>
          <td><span class="badge badge-normal">${a.status}</span></td>
          <td>${actionBtns}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
    }
  }

  static async acknowledge(alertId) {
    try {
      await ApiClient.acknowledgeAlert(alertId);
      await AlertsView.loadData();
    } catch (e) {
      alert(e.message);
    }
  }

  static async resolve(alertId) {
    try {
      await ApiClient.resolveAlert(alertId);
      await AlertsView.loadData();
    } catch (e) {
      alert(e.message);
    }
  }
}

window.AlertsView = AlertsView;
