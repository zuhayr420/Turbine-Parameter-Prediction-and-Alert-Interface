/**
 * Turbine Detail View Component
 */
class UnitDetailView {
  static async render(container, params = {}) {
    const unitId = params.unitId || 1;
    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
          <h2 id="ud-title" style="font-size:16px;">Turbine Unit Details</h2>
          <div id="ud-subtitle" style="font-size:11px; color:var(--text-muted);">Loading...</div>
        </div>
        <div class="toolbar">
          <button class="btn btn-sm" onclick="App.navigate('telemetry_input', { unitId: ${unitId} })">Update Telemetry</button>
          <button class="btn btn-primary btn-sm" onclick="UnitDetailView.runPredictions(${unitId})">Run 3H Forecast</button>
          <button class="btn btn-sm" onclick="App.navigate('dashboard')">Back to Plant</button>
        </div>
      </div>

      <!-- Interactive P&ID SVG Panel -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Interactive P&ID Schematic</span>
          <span class="text-secondary" style="font-size:11px;">Live telemetry overlay</span>
        </div>
        <div class="panel-body" style="text-align:center; background:#0f172a; padding: 20px;">
          <!-- SVG Mock of a turbine with data overlay points -->
          <svg width="600" height="200" viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg">
            <!-- Turbine Body -->
            <rect x="150" y="75" width="300" height="50" rx="2" fill="#334155" stroke="#475569" stroke-width="2"/>
            <!-- Rotor shaft -->
            <rect x="50" y="95" width="500" height="10" fill="#64748b"/>
            <!-- Bearings -->
            <rect x="100" y="85" width="20" height="30" fill="#94a3b8"/>
            <rect x="480" y="85" width="20" height="30" fill="#94a3b8"/>
            <!-- Labels -->
            <text x="300" y="60" fill="#94a3b8" font-size="12" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">HP/IP TURBINE CASING</text>
            <text x="110" y="135" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">BRG-1</text>
            <text x="490" y="135" fill="#94a3b8" font-size="11" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">BRG-2</text>
            <!-- Telemetry Overlays -->
            <rect x="100" y="40" width="80" height="20" rx="2" fill="#1e293b" stroke="#3b82f6"/>
            <text id="pid-brg1-vib" x="140" y="54" fill="#60a5fa" font-size="11" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">Vib: --</text>

            <rect x="420" y="40" width="80" height="20" rx="2" fill="#1e293b" stroke="#3b82f6"/>
            <text id="pid-brg2-vib" x="460" y="54" fill="#60a5fa" font-size="11" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">Vib: --</text>
            
            <rect x="260" y="140" width="80" height="20" rx="2" fill="#1e293b" stroke="#ef4444"/>
            <text id="pid-case-temp" x="300" y="154" fill="#fca5a5" font-size="11" font-weight="bold" text-anchor="middle" font-family="'Times New Roman', Times, serif">Tmp: --</text>
          </svg>
        </div>
      </div>

      <!-- Unit Operational Stats Panel -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Operational Status</span>
          <span id="ud-status-badge" class="badge">--</span>
        </div>
        <div class="panel-body" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px;">
          <div>
            <div class="form-label">Plant & Bay</div>
            <div id="ud-location" class="mono">--</div>
          </div>
          <div>
            <div class="form-label">Rated Capacity</div>
            <div id="ud-capacity" class="mono">--</div>
          </div>
          <div>
            <div class="form-label">Turbine Model / OEM</div>
            <div id="ud-model" class="mono">--</div>
          </div>
          <div>
            <div class="form-label">Recorded Downtime</div>
            <div id="ud-downtime" class="mono">--</div>
          </div>
        </div>
      </div>

      <!-- Monitored Parameters Table -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Current Operating Parameters</span>
          <span class="text-secondary" style="font-size:11px;">Latest telemetry vs safety thresholds</span>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Parameter Name</th>
                <th>Current Reading</th>
                <th>Warning Limit</th>
                <th>Critical Limit</th>
                <th>Timestamp</th>
                <th>Data Source</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="ud-parameters-tbody">
              <tr><td colspan="7" style="color:var(--text-muted);">Loading telemetry parameters...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Forecast Visualization Panel -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title" id="ud-chart-title">3-Hour Predictive Trajectory (XGBoost)</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Select Parameter:</label>
            <select id="ud-param-selector" class="form-control" style="padding:2px 6px; font-size:11px;" onchange="UnitDetailView.onParamSelect(${unitId})"></select>
          </div>
        </div>
        <div class="panel-body">
          <div class="chart-panel">
            <canvas id="ud-forecast-canvas"></canvas>
          </div>
        </div>
      </div>
    `;

    await UnitDetailView.loadData(unitId);
  }

  static async loadData(unitId) {
    try {
      const unitRes = await ApiClient.getUnit(unitId);
      if (!unitRes) return;
      const u = unitRes.unit;

      document.getElementById('ud-title').innerText = `${u.unit_code} — ${u.unit_name}`;
      document.getElementById('ud-subtitle').innerText = `${u.plant_name} | Location: ${u.location || 'Bay 1'}`;

      let badgeClass = 'badge-normal';
      if (u.status === 'WARNING') badgeClass = 'badge-warning';
      if (u.status === 'CRITICAL') badgeClass = 'badge-critical';
      if (u.status === 'OFFLINE' || !u.active) badgeClass = 'badge-offline';

      const sBadge = document.getElementById('ud-status-badge');
      sBadge.className = `badge ${badgeClass}`;
      sBadge.innerText = u.status;

      document.getElementById('ud-location').innerText = `${u.plant_name} (${u.location || 'Bay 1'})`;
      document.getElementById('ud-capacity').innerText = `${u.capacity_mw} MW`;
      document.getElementById('ud-model').innerText = `${u.model || '--'} (${u.manufacturer || '--'})`;
      document.getElementById('ud-downtime').innerText = `${u.downtime_hours} Hours`;

      // Load parameters and current readings
      const readingsRes = await ApiClient.getCurrentReadings(unitId);
      const readings = readingsRes.current_readings;
      const tbody = document.getElementById('ud-parameters-tbody');
      tbody.innerHTML = '';

      const selector = document.getElementById('ud-param-selector');
      selector.innerHTML = '';

      readings.forEach((r, idx) => {
        // Add to selector
        const opt = document.createElement('option');
        opt.value = r.parameter_id;
        opt.text = `${r.parameter} (${r.unit})`;
        selector.appendChild(opt);

        const tr = document.createElement('tr');
        const valText = r.value !== null ? `${r.value} ${r.unit}` : '<span style="color:var(--text-muted);">No reading</span>';
        const tsText = r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : '--';
        const sourceBadge = r.data_source ? `<span class="badge badge-normal">${r.data_source}</span>` : '--';

        tr.innerHTML = `
          <td><strong>${r.parameter}</strong></td>
          <td class="mono" style="font-size:13px; font-weight:700;">${valText}</td>
          <td class="mono" style="color:#fbbf24;">${r.warning_threshold} ${r.unit}</td>
          <td class="mono" style="color:#f87171;">${r.critical_threshold} ${r.unit}</td>
          <td class="mono">${tsText}</td>
          <td>${sourceBadge}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="UnitDetailView.forecastSingle(${unitId}, ${r.parameter_id})">Forecast</button>
          </td>
        `;
        tbody.appendChild(tr);
      });

      // Render chart for first parameter
      if (readings.length > 0) {
        await UnitDetailView.renderChart(unitId, readings[0].parameter_id);
      }

      // Real-time telemetry bindings for SVG
      window.addEventListener('telemetry_update', (e) => {
        const data = e.detail;
        if (data && data.unit_id == unitId) {
          const dict = data.readings || {};
          const elBrg1 = document.getElementById('pid-brg1-vib');
          const elBrg2 = document.getElementById('pid-brg2-vib');
          const elCase = document.getElementById('pid-case-temp');
          if (elBrg1 && dict['Bearing 1 Vibration'] !== undefined) elBrg1.textContent = 'Vib: ' + Number(dict['Bearing 1 Vibration']).toFixed(2);
          if (elBrg2 && dict['Bearing 2 Vibration'] !== undefined) elBrg2.textContent = 'Vib: ' + Number(dict['Bearing 2 Vibration']).toFixed(2);
          if (elCase && dict['Casing Temperature'] !== undefined) elCase.textContent = 'Tmp: ' + Number(dict['Casing Temperature']).toFixed(1);
        }
      });
    } catch (e) {
      console.error(e);
    }
  }

  static async onParamSelect(unitId) {
    const selector = document.getElementById('ud-param-selector');
    const paramId = selector.value;
    await UnitDetailView.renderChart(unitId, paramId);
  }

  static async renderChart(unitId, parameterId) {
    try {
      // 1. Get historical readings
      let history = [];
      try {
        const histRes = await ApiClient.getParameterHistory(unitId, parameterId, 30);
        history = histRes ? histRes.history : [];
      } catch (hErr) {
        console.warn("Could not load history for chart:", hErr);
      }

      // Fetch parameter metadata for threshold
      let paramName = 'Parameter';
      let paramUnit = '';
      let warnTh = null;
      let critTh = null;

      try {
        const paramsRes = await ApiClient.getUnitParameters(unitId);
        if (paramsRes && paramsRes.parameters) {
          const pObj = paramsRes.parameters.find(p => p.id == parameterId);
          if (pObj) {
            paramName = pObj.name;
            paramUnit = pObj.measurement_unit;
            warnTh = pObj.warning_threshold;
            critTh = pObj.critical_threshold;
          }
        }
      } catch (metaErr) {
        console.warn("Could not load parameter metadata:", metaErr);
      }

      // 2. Trigger or fetch predictions
      let forecastPoints = [];
      try {
        const predRes = await ApiClient.predictParameter(unitId, parameterId);
        if (predRes && predRes.status === 'success') {
          forecastPoints = predRes.predictions || [];
          if (predRes.parameter) {
            paramName = predRes.parameter.name || paramName;
            paramUnit = predRes.parameter.unit || paramUnit;
          }
          if (predRes.alert) {
            warnTh = predRes.alert.threshold || warnTh;
          }
        }
      } catch (predErr) {
        console.warn("Forecast execution notice (rendering history & limits):", predErr.message);
      }

      const titleEl = document.getElementById('ud-chart-title');
      if (titleEl) titleEl.innerText = `3-Hour Predictive Trajectory: ${paramName}`;

      ScadaCharts.renderDualZoneForecast(
        'ud-forecast-canvas',
        paramName,
        paramUnit,
        history,
        forecastPoints,
        warnTh,
        critTh
      );
    } catch (err) {
      console.warn("Forecast render warning:", err);
    }
  }

  static async runPredictions(unitId) {
    try {
      alert("Running 3-Hour XGBoost Forecast across all configured parameters...");
      await ApiClient.predictUnit(unitId);
      await UnitDetailView.loadData(unitId);
    } catch (e) {
      alert(`Forecast error: ${e.message}`);
    }
  }

  static async forecastSingle(unitId, parameterId) {
    document.getElementById('ud-param-selector').value = parameterId;
    await UnitDetailView.renderChart(unitId, parameterId);
  }
}

window.UnitDetailView = UnitDetailView;
