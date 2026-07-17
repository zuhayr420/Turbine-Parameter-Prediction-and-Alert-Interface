/**
 * Reports View Component
 */
class ReportsView {
  static async render(container) {
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Turbine Operational & Predictive Summary Reports</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Select Turbine:</label>
            <select id="report-unit-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="ReportsView.loadReport()"></select>
            <button class="btn btn-primary btn-sm" onclick="window.print()">Print / Export PDF</button>
            <button class="btn btn-sm" onclick="ReportsView.exportFullCsv()">Export Full Telemetry CSV</button>
          </div>
        </div>
        <div class="panel-body" id="report-content-area">
          <div style="color:var(--text-muted);">Generating report...</div>
        </div>
      </div>
    `;

    await ReportsView.populateUnits();
  }

  static async populateUnits() {
    try {
      const unitsRes = await ApiClient.getUnits();
      const select = document.getElementById('report-unit-select');
      select.innerHTML = '';
      unitsRes.units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.text = `${u.unit_code} (${u.unit_name})`;
        select.appendChild(opt);
      });
      await ReportsView.loadReport();
    } catch (e) {
      console.error(e);
    }
  }

  static async loadReport() {
    const unitId = document.getElementById('report-unit-select').value;
    const area = document.getElementById('report-content-area');
    try {
      const res = await ApiClient.getUnitReport(unitId);
      const rep = res.report;
      const u = rep.unit;

      let html = `
        <div style="border-bottom:1px solid var(--border-subtle); padding-bottom:12px; margin-bottom:14px; display:flex; justify-content:space-between;">
          <div>
            <h2 style="font-size:16px;">${u.unit_code} — Technical Audit & Predictive Health Report</h2>
            <div style="font-size:11px; color:var(--text-muted);">
              Facility: ${u.plant_name} | Commissioned: ${u.commissioning_date || '--'} | Status: ${u.status}
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:11px; font-weight:700; color:var(--text-primary); letter-spacing:0.04em;">THERMAL POWER STATION SCADA</div>
            <div style="font-size:10px; color:var(--text-muted);">Generated: ${new Date(rep.generated_at).toLocaleString()}</div>
          </div>
        </div>

        <h3 style="font-size:12px; text-transform:uppercase; color:var(--text-secondary); margin-bottom:8px;">1. Parameter Telemetry & Forecast Summary</h3>
        <table class="scada-table" style="margin-bottom:18px;">
          <thead>
            <tr>
              <th>Parameter</th>
              <th>Latest Measured Value</th>
              <th>Warning Limit</th>
              <th>Critical Limit</th>
              <th>Active Alerts</th>
              <th>3-Hour Expected Trajectory</th>
            </tr>
          </thead>
          <tbody>
      `;

      rep.parameters.forEach(p => {
        const lr = p.latest_reading;
        const valText = lr ? `${lr.value} ${p.parameter.measurement_unit}` : '--';
        const alertCount = p.active_alerts.length;
        const alertBadge = alertCount > 0 
          ? `<span class="badge badge-critical">${alertCount} Active Alert(s)</span>` 
          : `<span class="badge badge-normal">Normal</span>`;
        
        const fPoints = p.forecast.map(f => f.predicted_value);
        const fEnd = fPoints.length > 0 ? `${fPoints[fPoints.length - 1]} ${p.parameter.measurement_unit}` : '--';

        html += `
          <tr>
            <td><strong>${p.parameter.name}</strong></td>
            <td class="mono" style="font-weight:700;">${valText}</td>
            <td class="mono" style="color:#fbbf24;">${p.parameter.warning_threshold}</td>
            <td class="mono" style="color:#f87171;">${p.parameter.critical_threshold}</td>
            <td>${alertBadge}</td>
            <td class="mono" style="color:#38bdf8;">Forecast 3H: ${fEnd}</td>
          </tr>
        `;
      });

      html += `
          </tbody>
        </table>
      `;

      area.innerHTML = html;
    } catch (e) {
      console.error(e);
      area.innerHTML = `<div style="color:var(--status-critical);">Failed generating report: ${e.message}</div>`;
    }
  }

  static async exportFullCsv() {
    const unitId = document.getElementById('report-unit-select').value;
    try {
      const csvStr = await ApiClient.exportCsv(unitId);
      const blob = new Blob([csvStr], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `unit_${unitId}_telemetry_audit.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export error: ${e.message}`);
    }
  }
}

window.ReportsView = ReportsView;
