/**
 * Historical Data View Component
 */
class HistoricalView {
  static async render(container) {
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Historical Time-Series Telemetry Query</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Turbine:</label>
            <select id="hist-unit-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="HistoricalView.onUnitChange()"></select>
            <label style="font-size:11px; color:var(--text-secondary); margin-left:8px;">Parameter:</label>
            <select id="hist-param-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="HistoricalView.loadHistory()"></select>
            <button class="btn btn-sm" onclick="HistoricalView.loadHistory()">Query</button>
            <button class="btn btn-primary btn-sm" onclick="HistoricalView.exportCsv()">Export CSV</button>
          </div>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Reading ID</th>
                <th>Timestamp</th>
                <th>Parameter</th>
                <th>Value</th>
                <th>Unit</th>
                <th>Data Source</th>
              </tr>
            </thead>
            <tbody id="hist-table-tbody">
              <tr><td colspan="6" style="color:var(--text-muted); text-align:center;">Loading historical data...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await HistoricalView.populateUnits();
  }

  static async populateUnits() {
    try {
      const unitsRes = await ApiClient.getUnits();
      const select = document.getElementById('hist-unit-select');
      select.innerHTML = '';
      unitsRes.units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.text = `${u.unit_code} (${u.unit_name})`;
        select.appendChild(opt);
      });
      await HistoricalView.onUnitChange();
    } catch (e) {
      console.error(e);
    }
  }

  static async onUnitChange() {
    const unitId = document.getElementById('hist-unit-select').value;
    const paramsRes = await ApiClient.getUnitParameters(unitId);
    const select = document.getElementById('hist-param-select');
    select.innerHTML = '';

    paramsRes.parameters.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.text = `${p.name} (${p.measurement_unit})`;
      select.appendChild(opt);
    });

    await HistoricalView.loadHistory();
  }

  static async loadHistory() {
    const unitId = document.getElementById('hist-unit-select').value;
    const paramId = document.getElementById('hist-param-select').value;
    if (!unitId || !paramId) return;

    try {
      const res = await ApiClient.getParameterHistory(unitId, paramId, 100);
      const tbody = document.getElementById('hist-table-tbody');
      tbody.innerHTML = '';

      if (!res.history || res.history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No records found.</td></tr>`;
        return;
      }

      // Display in reverse order (most recent first)
      const reversed = [...res.history].reverse();
      reversed.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td class="mono">${r.id}</td>
          <td class="mono">${new Date(r.timestamp).toLocaleString()}</td>
          <td>Parameter #${r.parameter_id}</td>
          <td class="mono" style="font-weight:700;">${r.value}</td>
          <td class="mono">--</td>
          <td><span class="badge badge-normal">${r.data_source}</span></td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
    }
  }

  static async exportCsv() {
    const unitId = document.getElementById('hist-unit-select').value;
    const paramId = document.getElementById('hist-param-select').value;
    try {
      const csvStr = await ApiClient.exportCsv(unitId, paramId);
      const blob = new Blob([csvStr], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `unit_${unitId}_readings.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export failed: ${e.message}`);
    }
  }
}

window.HistoricalView = HistoricalView;
