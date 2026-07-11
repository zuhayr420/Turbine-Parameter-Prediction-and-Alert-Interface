/**
 * Turbine Units Management View
 * Allows viewing all turbines and directly provisioning new units with parameters
 */
class UnitsView {
  static async loadStationOptions() {
    let options = '';
    try {
      const res = await ApiClient.request('/api/stations');
      res.stations.forEach(s => {
        options += `<option value="${s.id}">${s.name}${s.location ? ' (' + s.location + ')' : ''}</option>`;
      });
    } catch (e) {
      console.error('Failed loading stations', e);
    }
    return options;
  }

  static async render(container) {
    const isAdmin = Auth.isAdmin();
    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Turbine Units Directory</span>
          <div class="toolbar">
            ${isAdmin ? `<button class="btn btn-primary btn-sm" onclick="UnitsView.openAddUnitModal()">+ Add Turbine Unit</button>` : ''}
            <button class="btn btn-sm" onclick="UnitsView.loadUnits()">Refresh</button>
          </div>
        </div>
        <div class="panel-body">
          <div id="units-list-container" class="unit-grid">
            <div style="color:var(--text-muted);">Loading turbines...</div>
          </div>
        </div>
      </div>

      <!-- Modal container for adding unit -->
      <div id="unit-modal-slot"></div>
    `;

    await UnitsView.loadUnits();
  }

  static async loadUnits() {
    const container = document.getElementById('units-list-container');
    try {
      const res = await ApiClient.getUnits();
      container.innerHTML = '';

      if (!res.units || res.units.length === 0) {
        container.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 30px; text-align: center; background: #ffffff; border: 1px dashed var(--border-subtle); border-radius: 2px;">
            <div style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Turbine Units Registered</div>
            <p style="color: var(--text-secondary); font-size: 12px; margin-bottom: 16px;">
              Get started by provisioning the first turbine unit for your thermal power station.
            </p>
            ${Auth.isAdmin() ? `<button class="btn btn-primary" onclick="UnitsView.openAddUnitModal()">+ Provision First Turbine</button>` : ''}
          </div>
        `;
        return;
      }

      res.units.forEach(u => {
        let badgeClass = 'badge-normal';
        if (u.status === 'WARNING') badgeClass = 'badge-warning';
        if (u.status === 'CRITICAL') badgeClass = 'badge-critical';
        if (u.status === 'OFFLINE' || !u.active) badgeClass = 'badge-offline';

        const card = document.createElement('div');
        card.className = 'unit-card';
        card.innerHTML = `
          <div class="unit-card-header">
            <div>
              <strong style="font-size:14px; color:var(--text-primary);">${u.unit_code}</strong>
              <div style="font-size:11px; color:var(--text-muted);">${u.location || 'Turbine Hall'}</div>
            </div>
            <span class="badge ${badgeClass}">${u.status}</span>
          </div>
          <div class="unit-card-body">
            <div style="font-size:12px; font-weight:600; color:var(--text-primary);">${u.unit_name}</div>
            <div class="telemetry-row">
              <span class="telemetry-param">Power Plant:</span>
              <span class="telemetry-val">${u.station_name || "Unknown Station"}</span>
            </div>
            <div class="telemetry-row">
              <span class="telemetry-param">Rated Capacity:</span>
              <span class="telemetry-val">${u.capacity_mw} MW</span>
            </div>
            <div class="telemetry-row">
              <span class="telemetry-param">OEM / Model:</span>
              <span class="telemetry-val">${u.manufacturer || '--'} ${u.model || ''}</span>
            </div>
            <div class="telemetry-row">
              <span class="telemetry-param">Downtime:</span>
              <span class="telemetry-val">${u.downtime_hours} hrs</span>
            </div>
            <div style="margin-top:8px; display:flex; justify-content:space-between; gap:6px;">
              <button class="btn btn-sm btn-primary" onclick="App.navigate('unit_detail', { unitId: ${u.id} })">Inspect Parameters & Forecast →</button>
              ${Auth.isAdmin() ? `<button class="btn btn-sm" onclick="UnitsView.openAddParamModal(${u.id}, '${u.unit_code}')">+ Param</button>` : ''}
            </div>
          </div>
        `;
        container.appendChild(card);
      });
    } catch (e) {
      console.error(e);
      container.innerHTML = `<div style="color:var(--status-critical);">Failed loading turbines: ${e.message}</div>`;
    }
  }

  static async openAddUnitModal() {
    let stationsHtml = '<option value="">Select a Station...</option>';
    try {
      const res = await ApiClient.request('/api/stations');
      if (res && res.stations) {
        res.stations.forEach(s => {
          stationsHtml += `<option value="${s.id}">${s.name}${s.location ? ' (' + s.location + ')' : ''}</option>`;
        });
      }
    } catch(e) {
      console.error(e);
    }

    const slot = document.getElementById('unit-modal-slot');
    slot.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Provision Turbine Unit</strong>
            <button class="btn btn-sm" onclick="UnitsView.closeModal()">Close</button>
          </div>
          <form onsubmit="UnitsView.submitCreateUnit(event)">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Turbine Unit Code (Required)</label>
                <input type="text" id="unit-code-input" class="form-control" placeholder="e.g. UNIT-01, TG-1, TURBINE-A" required autofocus>
              </div>
              <div class="form-group">
                <label class="form-label">Turbine Designation / Name (Required)</label>
                <input type="text" id="unit-name-input" class="form-control" placeholder="e.g. Turbine Unit 01 (Steam Turbo-Generator)" required>
              </div>
                <div class="form-group">
                  <label class="form-label">Station</label>
                  <select id="station-id-input" class="form-control" required>
                    ${stationsHtml}
                  </select>
                </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Location / Station Bay</label>
                  <input type="text" id="location-input" class="form-control" placeholder="e.g. Turbine Hall Bay 1">
                </div>
                <div class="form-group">
                  <label class="form-label">Rated Capacity (MW)</label>
                  <input type="number" step="any" id="capacity-input" class="form-control" value="210.0" required>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Manufacturer / OEM</label>
                  <input type="text" id="manufacturer-input" class="form-control" placeholder="e.g. Siemens, GE, BHEL, Mitsubishi">
                </div>
                <div class="form-group">
                  <label class="form-label">Turbine Model</label>
                  <input type="text" id="model-input" class="form-control" placeholder="e.g. SST-800 Series">
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="UnitsView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">+ Provision Turbine</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateUnit(e) {
    e.preventDefault();
    const payload = {
      unit_code: document.getElementById('unit-code-input').value.trim(),
      unit_name: document.getElementById('unit-name-input').value.trim(),
      station_id: parseInt(document.getElementById('station-id-input').value),
      location: document.getElementById('location-input').value.trim(),
      capacity_mw: parseFloat(document.getElementById('capacity-input').value) || 210.0,
      manufacturer: document.getElementById('manufacturer-input').value.trim(),
      model: document.getElementById('model-input').value.trim(),
      status: 'RUNNING'
    };

    try {
      const res = await ApiClient.createUnit(payload);
      UnitsView.closeModal();
      alert(`Turbine '${payload.unit_code}' provisioned successfully! Now add operating parameters for monitoring.`);
      await UnitsView.loadUnits();
    } catch (err) {
      alert(`Error creating unit: ${err.message}`);
    }
  }

  static openAddParamModal(unitId, unitCode) {
    const slot = document.getElementById('unit-modal-slot');
    slot.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Add Parameter to ${unitCode}</strong>
            <button class="btn btn-sm" onclick="UnitsView.closeModal()">Close</button>
          </div>
          <form onsubmit="UnitsView.submitCreateParam(event, ${unitId})">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Parameter Name</label>
                <select id="param-name-input" class="form-control" onchange="document.getElementById('param-key-input').value = event.target.value.toLowerCase().replace(/ /g, '_')" required autofocus>
                    <option value="">Select an O&M Parameter...</option>
                    <option value="Bearing Vibration">Bearing Vibration</option>
                    <option value="Lube Oil Pressure">Lube Oil Pressure</option>
                    <option value="Lube Oil Temperature">Lube Oil Temperature</option>
                    <option value="Coolant Pressure">Coolant Pressure</option>
                    <option value="Coolant Temperature">Coolant Temperature</option>
                    <option value="Exhaust Gas Temperature">Exhaust Gas Temperature</option>
                    <option value="Rotor Speed">Rotor Speed</option>
                    <option value="Power Output">Power Output</option>
                    <option value="Steam Pressure">Steam Pressure</option>
                    <option value="Steam Temperature">Steam Temperature</option>
                    <option value="Casing Expansion">Casing Expansion</option>
                    <option value="Differential Expansion">Differential Expansion</option>
</select>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Parameter Key (snake_case)</label>
                  <input type="text" id="param-key-input" class="form-control" placeholder="e.g. vibration, pressure" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Measurement Unit</label>
                  <select id="param-unit-input" class="form-control" required>
                    <option value="">Select a unit...</option>
                    <option value="°C">°C (Temperature)</option>
                    <option value="°F">°F (Temperature)</option>
                    <option value="mm/s">mm/s (Velocity/Vibration)</option>
                    <option value="MPa">MPa (Pressure)</option>
                    <option value="bar">bar (Pressure)</option>
                    <option value="RPM">RPM (Speed)</option>
                    <option value="Hz">Hz (Frequency)</option>
                    <option value="MW">MW (Power)</option>
                    <option value="kW">kW (Power)</option>
                    <option value="V">V (Voltage)</option>
                    <option value="A">A (Current)</option>
                    <option value="%">% (Percentage)</option>
                  </select>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Warning Threshold</label>
                  <input type="number" step="any" id="param-warn-input" class="form-control" placeholder="e.g. 4.0" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Critical Threshold</label>
                  <input type="number" step="any" id="param-crit-input" class="form-control" placeholder="e.g. 5.0" required>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Min Expected Value</label>
                  <input type="number" step="any" id="param-min-input" class="form-control" placeholder="e.g. 0.0">
                </div>
                <div class="form-group">
                  <label class="form-label">Max Expected Value</label>
                  <input type="number" step="any" id="param-max-input" class="form-control" placeholder="e.g. 15.0">
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="UnitsView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Save Parameter</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateParam(e, unitId) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('param-name-input').value.trim(),
      parameter_key: document.getElementById('param-key-input').value.trim(),
      measurement_unit: document.getElementById('param-unit-input').value.trim(),
      warning_threshold: parseFloat(document.getElementById('param-warn-input').value),
      critical_threshold: parseFloat(document.getElementById('param-crit-input').value),
      minimum_value: document.getElementById('param-min-input').value ? parseFloat(document.getElementById('param-min-input').value) : null,
      maximum_value: document.getElementById('param-max-input').value ? parseFloat(document.getElementById('param-max-input').value) : null,
      enabled: true,
      alert_enabled: true
    };

    try {
      await ApiClient.createParameter(unitId, payload);
      UnitsView.closeModal();
      alert("Parameter successfully added!");
    } catch (err) {
      alert(`Failed adding parameter: ${err.message}`);
    }
  }

  static closeModal() {
    const slot = document.getElementById('unit-modal-slot');
    if (slot) slot.innerHTML = '';
  }
}

window.UnitsView = UnitsView;
