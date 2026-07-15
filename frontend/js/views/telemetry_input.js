/**
 * Operator Parameter Input & Telemetry Ingestion View
 */
class TelemetryInputView {
  static async render(container, params = {}) {
    const unitId = params.unitId || 1;
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Operator Telemetry Ingestion Console</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Select Turbine:</label>
            <select id="telemetry-unit-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="TelemetryInputView.onUnitChange()"></select>
          </div>
        </div>
        <div class="panel-body">
          <p style="color:var(--text-secondary); font-size:12px; margin-bottom:14px;">
            Enter instantaneous operating values measured at the turbine sensors or local gauges. Entered values are logged to historical readings with <code>MANUAL</code> tag and appended to the 30-observation sliding window.
          </p>

          <form id="telemetry-form" onsubmit="TelemetryInputView.handleSubmit(event)">
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:14px;" id="param-inputs-grid">
              <div style="color:var(--text-muted);">Loading parameters...</div>
            </div>

            <div style="margin-top:18px; display:flex; gap:10px;">
              <button type="submit" class="btn btn-primary">Update Parameters &amp; Trigger Forecast</button>
              <button type="button" class="btn" onclick="TelemetryInputView.resetForm()">Reset Fields</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Past Readings History Table -->
      <div class="panel" id="telemetry-history-panel" style="display:none;">
        <div class="panel-header">
          <span class="panel-title">Past Telemetry Readings</span>
          <span style="font-size:11px; color:var(--text-secondary);">Last 10 readings per parameter</span>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Parameter</th>
                <th>Value</th>
                <th>Unit</th>
                <th>Source</th>
                <th>Recorded At</th>
              </tr>
            </thead>
            <tbody id="telemetry-history-tbody">
              <tr><td colspan="5" style="color:var(--text-muted); text-align:center; padding:16px;">Loading history...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await TelemetryInputView.loadUnits(unitId);
  }

  static async loadUnits(selectedUnitId) {
    try {
      const unitsRes = await ApiClient.getUnits();
      const select = document.getElementById('telemetry-unit-select');
      select.innerHTML = '';
      unitsRes.units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.text = `${u.unit_code} — ${u.unit_name}`;
        if (u.id == selectedUnitId) opt.selected = true;
        select.appendChild(opt);
      });
      await TelemetryInputView.loadParameters();
    } catch (e) {
      console.error(e);
    }
  }

  static async onUnitChange() {
    await TelemetryInputView.loadParameters();
  }

  static async loadParameters() {
    const unitId = document.getElementById('telemetry-unit-select').value;
    const grid = document.getElementById('param-inputs-grid');
    grid.innerHTML = '<div style="color:var(--text-muted);">Loading...</div>';

    try {
      const currentReadingsRes = await ApiClient.getCurrentReadings(unitId);
      const readings = currentReadingsRes.current_readings;
      grid.innerHTML = '';

      readings.forEach(r => {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
          <label class="form-label">${r.parameter} (${r.unit})</label>
          <div style="display:flex; align-items:center; gap:8px;">
            <input type="number" step="any" class="form-control" name="param_${r.parameter_id}" value="${r.value !== null ? r.value : ''}" placeholder="Safe range < ${r.warning_threshold}" required style="flex:1;">
            <span class="mono" style="font-size:11px; color:var(--text-muted); min-width:40px;">${r.unit}</span>
          </div>
          <span style="font-size:10px; color:var(--text-muted);">Warn: ${r.warning_threshold} | Crit: ${r.critical_threshold}</span>
        `;
        grid.appendChild(div);
      });

      await TelemetryInputView.loadHistory();
    } catch (e) {
      console.error(e);
    }
  }

  static async loadHistory() {
    const unitId = document.getElementById('telemetry-unit-select').value;
    const panel = document.getElementById('telemetry-history-panel');
    const tbody = document.getElementById('telemetry-history-tbody');
    if (!panel || !tbody) return;

    try {
      // Get current readings to know which parameters exist
      const currentReadingsRes = await ApiClient.getCurrentReadings(unitId);
      const readings = currentReadingsRes.current_readings;

      if (!readings || readings.length === 0) {
        panel.style.display = 'none';
        return;
      }

      panel.style.display = 'flex';
      tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted); text-align:center; padding:12px;">Loading...</td></tr>';

      // Fetch history for each parameter
      const allRows = [];
      for (const r of readings) {
        try {
          const histRes = await ApiClient.request(`/api/units/${unitId}/parameters/${r.parameter_id}/history?limit=10`);
          const entries = histRes.history || histRes.readings || [];
          entries.forEach(entry => {
            allRows.push({
              parameter: r.parameter,
              unit: r.unit,
              value: entry.value,
              source: entry.data_source || entry.source || 'SENSOR',
              timestamp: entry.timestamp || entry.created_at
            });
          });
        } catch (err) {
          console.warn(`No history for parameter ${r.parameter_id}:`, err.message);
        }
      }

      // Sort newest first
      allRows.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

      if (allRows.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="color:var(--text-muted); text-align:center; padding:12px;">No historical readings recorded yet.</td></tr>';
        return;
      }

      tbody.innerHTML = '';
      allRows.forEach(row => {
        const tr = document.createElement('tr');
        const srcBadge = row.source === 'MANUAL'
          ? '<span class="badge badge-warning">MANUAL</span>'
          : '<span class="badge badge-normal">SENSOR</span>';
        tr.innerHTML = `
          <td><strong>${row.parameter}</strong></td>
          <td class="mono">${parseFloat(row.value).toFixed(3)}</td>
          <td class="mono">${row.unit}</td>
          <td>${srcBadge}</td>
          <td class="mono" style="font-size:10px;">${new Date(row.timestamp).toLocaleString()}</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error('Failed to load telemetry history:', e);
      if (panel) panel.style.display = 'none';
    }
  }

  static async handleSubmit(e) {
    e.preventDefault();
    const unitId = document.getElementById('telemetry-unit-select').value;
    const form = document.getElementById('telemetry-form');
    const formData = new FormData(form);

    const inputs = [];
    for (const [key, val] of formData.entries()) {
      if (key.startsWith('param_')) {
        const paramId = parseInt(key.replace('param_', ''));
        const numVal = parseFloat(val);
        if (!isNaN(numVal)) {
          inputs.push({ parameter_id: paramId, value: numVal });
        }
      }
    }

    try {
      for (const item of inputs) {
        await ApiClient.addReading(unitId, {
          parameter_id: item.parameter_id,
          value: item.value,
          data_source: 'MANUAL'
        });
      }

      alert("Parameters successfully updated. Now triggering 3-Hour forecast...");
      await ApiClient.predictUnit(unitId);
      // Refresh history table to show the new readings before navigating
      await TelemetryInputView.loadHistory();
      App.navigate('unit_detail', { unitId });
    } catch (err) {
      alert(`Error submitting readings: ${err.message}`);
    }
  }

  static resetForm() {
    document.getElementById('telemetry-form').reset();
  }
}

window.TelemetryInputView = TelemetryInputView;

