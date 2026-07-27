/**
 * 3-Hour Predictions & Forecasting Dedicated Screen
 * Powered by XGBoost Recursive Multi-Step Regressor & SHAP Explainability
 */
class PredictionsView {
  static async render(container) {
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">XGBoost 3-Hour Predictive Forecasting Console</span>
          <div class="toolbar">
            <label style="font-size:11px; color:var(--text-secondary);">Turbine Unit:</label>
            <select id="pred-unit-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="PredictionsView.onUnitChange()"></select>
            <label style="font-size:11px; color:var(--text-secondary); margin-left:8px;">Parameter:</label>
            <select id="pred-param-select" class="form-control" style="font-size:11px; padding:3px 8px;" onchange="PredictionsView.onParamChange()"></select>
            <button class="btn btn-primary btn-sm" onclick="PredictionsView.runForecast()">Execute Prediction</button>
          </div>
        </div>
      </div>

      <!-- Forecast Summary KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <span class="kpi-label">Current Observed Value</span>
          <span class="kpi-val" id="pred-kpi-current">--</span>
          <span class="kpi-subtext" id="pred-kpi-cur-ts">Last sensor update</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Predicted 3-Hour Horizon</span>
          <span class="kpi-val" id="pred-kpi-3h">--</span>
          <span class="kpi-subtext" id="pred-kpi-diff">Expected Change: --</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Trajectory Trend</span>
          <span class="kpi-val" id="pred-kpi-trend">--</span>
          <span class="kpi-subtext" id="pred-kpi-roc">Rate of Change: --</span>
        </div>
        <div class="kpi-card">
          <span class="kpi-label">Predictive Safety Evaluation</span>
          <span class="kpi-val" id="pred-kpi-alert-status">--</span>
          <span class="kpi-subtext" id="pred-kpi-breach-eta">ETA to threshold breach: --</span>
        </div>
      </div>

      <!-- Interactive Inputs Console for XGBoost -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">XGBoost Input Observations (30-Reading Sliding Window)</span>
          <div class="toolbar">
            <button class="btn btn-sm" onclick="PredictionsView.loadLiveHistory()">Reload Live Sensor Readings</button>
            <button class="btn btn-sm" onclick="PredictionsView.loadSampleInputs()">Load Sample Calibration Pattern</button>
            <button class="btn btn-primary btn-sm" onclick="PredictionsView.runForecastWithCustomInputs()">Forecast with Custom Inputs</button>
          </div>
        </div>
        <div class="panel-body" style="padding:12px 16px;">
          <div style="font-size:11px; color:var(--text-secondary); margin-bottom:8px;">
            The XGBoost model reads 30 chronological observations [t-29 ... t] and extracts 17 statistical time-series features (rolling averages, volatility, rate of change, slope) to forecast the next 3 hours ahead (12 steps of 15 minutes).
          </div>
          <div style="display:flex; gap:10px; align-items:center;">
            <textarea id="pred-custom-inputs" class="form-control mono" rows="2" style="font-size:11px; width:100%; resize:vertical;" placeholder="30 comma-separated numeric readings, e.g. 3.4, 3.5, 3.6, ..."></textarea>
          </div>
        </div>
      </div>

      <!-- Main Dual-Zone Chart Panel -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title" id="pred-chart-header">Time-Series Forecast (30 Input Observations → 12 Forecast Steps)</span>
          <span style="font-size:10px; font-weight:700; color:var(--text-muted); letter-spacing:0.04em;" id="pred-model-badge">MODEL: XGBOOST REGRESSOR</span>
        </div>
        <div class="panel-body">
          <div class="chart-panel">
            <canvas id="pred-main-canvas"></canvas>
          </div>
        </div>
      </div>

      <!-- Multi-step Forecast Points Data Table -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">15-Minute Recursive Forecast Points (Next 3 Hours)</span>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Horizon Step</th>
                <th>Future Offset</th>
                <th>Predicted Value</th>
                <th>Warning Limit</th>
                <th>Critical Limit</th>
                <th>Safety Margin</th>
                <th>Top Driving Features (SHAP Explainability)</th>
              </tr>
            </thead>
            <tbody id="pred-table-tbody">
              <tr><td colspan="7" style="color:var(--text-muted); text-align:center;">Select parameter and click Execute Prediction.</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    `;

    await PredictionsView.populateUnits();
  }

  static async populateUnits() {
    try {
      const unitsRes = await ApiClient.getUnits();
      const unitSelect = document.getElementById('pred-unit-select');
      if (!unitSelect) return;
      unitSelect.innerHTML = '';
      unitsRes.units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.text = `${u.unit_code} (${u.unit_name})`;
        unitSelect.appendChild(opt);
      });

      if (unitsRes.units.length > 0) {
        await PredictionsView.onUnitChange();
      }
    } catch (e) {
      console.error("Error populating units:", e);
    }
  }

  static async onUnitChange() {
    const unitSelect = document.getElementById('pred-unit-select');
    if (!unitSelect) return;
    const unitId = unitSelect.value;
    const paramsRes = await ApiClient.getUnitParameters(unitId);
    const paramSelect = document.getElementById('pred-param-select');
    if (!paramSelect) return;
    paramSelect.innerHTML = '';

    if (!paramsRes || !paramsRes.parameters) return;

    paramsRes.parameters.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.text = `${p.name} (${p.measurement_unit})`;
      paramSelect.appendChild(opt);
    });

    if (paramsRes.parameters.length > 0) {
      await PredictionsView.loadLiveHistory();
    }
  }

  static async onParamChange() {
    await PredictionsView.loadLiveHistory();
  }

  static async loadLiveHistory() {
    const unitSelect = document.getElementById('pred-unit-select');
    const paramSelect = document.getElementById('pred-param-select');
    if (!unitSelect || !paramSelect) return;
    const unitId = unitSelect.value;
    const paramId = paramSelect.value;
    if (!unitId || !paramId) return;

    try {
      const histRes = await ApiClient.getParameterHistory(unitId, paramId, 30);
      const history = histRes ? histRes.history : [];
      const values = history.map(h => typeof h === 'object' && h !== null ? h.value : h);
      
      const inputEl = document.getElementById('pred-custom-inputs');
      if (inputEl && values.length > 0) {
        inputEl.value = values.map(v => Number(v).toFixed(2)).join(', ');
      }
      await PredictionsView.runForecast();
    } catch (e) {
      console.warn("Could not load history for parameter:", e);
      await PredictionsView.runForecast();
    }
  }

  static async loadSampleInputs() {
    try {
      const sample = await ApiClient.getSampleForecastInputs();
      if (sample && sample.inputs) {
        const inputEl = document.getElementById('pred-custom-inputs');
        if (inputEl) inputEl.value = sample.inputs.join(', ');
        await PredictionsView.runForecastWithCustomInputs();
      }
    } catch (e) {
      console.error("Error loading sample inputs:", e);
    }
  }

  static parseCustomInputs() {
    const inputEl = document.getElementById('pred-custom-inputs');
    if (!inputEl || !inputEl.value.trim()) return null;

    const raw = inputEl.value.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
    return raw.length > 0 ? raw : null;
  }

  static async runForecastWithCustomInputs() {
    const custom = PredictionsView.parseCustomInputs();
    if (!custom || custom.length === 0) {
      alert("Please provide at least one valid numeric input observation in the input box.");
      return;
    }
    await PredictionsView.runForecast(custom);
  }

  static async runForecast(customInputs = null) {
    const unitSelect = document.getElementById('pred-unit-select');
    const paramSelect = document.getElementById('pred-param-select');
    if (!unitSelect || !paramSelect) return;

    const unitId = unitSelect.value;
    const paramId = paramSelect.value;
    if (!unitId || !paramId) return;

    try {
      // 1. Fetch historical observations for chart base
      let history = [];
      try {
        const histRes = await ApiClient.getParameterHistory(unitId, paramId, 30);
        history = histRes ? histRes.history : [];
      } catch (hErr) {
        console.warn("Could not fetch parameter history:", hErr);
      }

      // If customInputs not explicitly passed, check if custom inputs box has numbers
      if (!customInputs) {
        const parsed = PredictionsView.parseCustomInputs();
        if (parsed && parsed.length > 0) {
          customInputs = parsed;
        }
      }

      // 2. Predict parameter with XGBoost
      let res = null;
      try {
        res = await ApiClient.predictParameter(unitId, paramId, customInputs);
      } catch (apiErr) {
        console.warn("predictParameter notice:", apiErr);
      }

      // Fetch parameter metadata for threshold
      let pObj = null;
      try {
        const pData = await ApiClient.getUnitParameters(unitId);
        pObj = pData?.parameters?.find(p => p.id == paramId);
      } catch (pErr) {
        console.warn("Could not load parameter config:", pErr);
      }

      const paramName = res?.parameter?.name || pObj?.name || 'Turbine Parameter';
      const paramUnit = res?.parameter?.unit || pObj?.measurement_unit || '';
      const warnTh = pObj?.warning_threshold;
      const critTh = pObj?.critical_threshold;

      if (res && res.status === 'success') {
        // If custom inputs were passed, update history array for chart visualization
        if (res.inputs_read && res.inputs_read.length > 0) {
          history = res.inputs_read;
          const inputEl = document.getElementById('pred-custom-inputs');
          if (inputEl && !inputEl.value) {
            inputEl.value = res.inputs_read.map(v => Number(v).toFixed(2)).join(', ');
          }
        }

        // Update KPI panels
        const curEl = document.getElementById('pred-kpi-current');
        if (curEl) curEl.innerText = `${res.current_value} ${paramUnit}`;

        const p3h = res.predictions && res.predictions.length > 0 
          ? res.predictions[res.predictions.length - 1].value 
          : res.current_value;
        const p3hEl = document.getElementById('pred-kpi-3h');
        if (p3hEl) p3hEl.innerText = `${p3h} ${paramUnit}`;

        const diff = (p3h - res.current_value).toFixed(2);
        const diffEl = document.getElementById('pred-kpi-diff');
        if (diffEl) diffEl.innerText = `Expected Change: ${diff >= 0 ? '+' : ''}${diff} ${paramUnit}`;

        // Trend tag
        let trendClass = 'trend-stable';
        if (res.trend === 'INCREASING') trendClass = 'trend-up';
        if (res.trend === 'RAPIDLY_INCREASING') trendClass = 'trend-rapid-up';
        if (res.trend === 'DECREASING') trendClass = 'trend-down';
        if (res.trend === 'RAPIDLY_DECREASING') trendClass = 'trend-rapid-down';
        const trendEl = document.getElementById('pred-kpi-trend');
        if (trendEl) trendEl.innerHTML = `<span class="trend-tag ${trendClass}">${res.trend}</span>`;

        const rocEl = document.getElementById('pred-kpi-roc');
        if (rocEl) rocEl.innerText = `Rate of Change: ${(res.rate_of_change * 100).toFixed(2)}%`;

        // Safety status
        const sev = res.alert?.severity || 'NORMAL';
        const sBadge = sev === 'CRITICAL' ? 'badge-critical' : (sev === 'WARNING' ? 'badge-warning' : 'badge-normal');
        const alertEl = document.getElementById('pred-kpi-alert-status');
        if (alertEl) alertEl.innerHTML = `<span class="badge ${sBadge}">${sev}</span>`;

        const eta = res.alert?.expected_breach_minutes ? `${res.alert.expected_breach_minutes} Minutes` : 'None within 3 hours';
        const etaEl = document.getElementById('pred-kpi-breach-eta');
        if (etaEl) etaEl.innerText = `Breach ETA: ${eta}`;

        // Populate multi-step forecast table
        const tbody = document.getElementById('pred-table-tbody');
        if (tbody) {
          tbody.innerHTML = '';
          res.predictions.forEach((pt, idx) => {
            const wTh = warnTh !== undefined && warnTh !== null ? warnTh : '--';
            const cTh = critTh !== undefined && critTh !== null ? critTh : '--';
            const margin = warnTh !== undefined && warnTh !== null ? (warnTh - pt.value).toFixed(2) : '--';
            
            let shapStr = '--';
            if (pt.shap && pt.shap.length > 0) {
              shapStr = pt.shap.map(s => `<span style="background:var(--bg-panel-header); border:1px solid var(--border-subtle); color:var(--text-secondary); padding:2px 6px; border-radius:2px; margin-right:4px;">${s.feature} (${s.impact > 0 ? '+' : ''}${s.impact})</span>`).join('');
            }

            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><strong>Step +${idx + 1}</strong></td>
              <td class="mono">+${pt.minutes} Minutes</td>
              <td class="mono" style="font-weight:700; color:var(--status-warning);">${pt.value} ${paramUnit}</td>
              <td class="mono">${wTh} ${paramUnit}</td>
              <td class="mono">${cTh} ${paramUnit}</td>
              <td class="mono" style="font-weight:700; color:${margin < 0 ? 'var(--status-critical)' : 'var(--status-normal)'};">${margin} ${paramUnit}</td>
              <td style="font-size:11px;">${shapStr}</td>
            `;
            tbody.appendChild(tr);
          });
        }
      }

      // Render dual-zone chart
      ScadaCharts.renderDualZoneForecast(
        'pred-main-canvas',
        paramName,
        paramUnit,
        history,
        res?.predictions || [],
        warnTh,
        critTh
      );
    } catch (err) {
      console.error("Forecast execution notice:", err);
    }
  }
}

window.PredictionsView = PredictionsView;
