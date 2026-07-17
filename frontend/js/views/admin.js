/**
 * Administration & Management View Component
 * Clean White Engineering Theme with Full In-App Plant & Parameter Provisioning
 */
class AdminView {
  static async render(container) {
    if (!Auth.isAdmin()) {
      container.innerHTML = `
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title" style="color:var(--status-critical);">Access Restricted</span>
          </div>
          <div class="panel-body">
            <p style="color:var(--text-secondary);">Administrator role is required to manage plant units, configure operating parameters, and manage user accounts.</p>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">SCADA Plant & Parameter Administration</span>
          <div class="toolbar">
            <button class="btn btn-primary btn-sm" onclick="AdminView.openCreateUnitModal()">+ Provision Turbine Unit</button>
            <button class="btn btn-sm" onclick="AdminView.openCreateUserModal()">+ Add User Account</button>
          </div>
        </div>
      </div>

      <!-- Turbine Units Provisioning Table -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Turbines & Power Plant Units</span>
          <span style="font-size:11px; color:var(--text-secondary);">Add, edit parameters, deactivate or remove turbines</span>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Unit Code</th>
                <th>Turbine Name</th>
                <th>Station / Bay</th>
                <th>Capacity</th>
                <th>Status</th>
                <th>Active</th>
                <th>Parameters</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="admin-units-tbody">
              <tr><td colspan="8" style="color:var(--text-muted); text-align:center; padding:16px;">Loading turbines...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Parameter Configuration Panel for Selected Unit -->
      <div class="panel" id="admin-param-panel" style="display:none;">
        <div class="panel-header">
          <span class="panel-title" id="admin-param-panel-title">Configured Operating Parameters</span>
          <div class="toolbar">
            <button class="btn btn-primary btn-sm" id="admin-add-param-btn">+ Add Parameter to Turbine</button>
          </div>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Parameter Name</th>
                <th>Key</th>
                <th>Unit</th>
                <th>Warning Threshold</th>
                <th>Critical Threshold</th>
                <th>Min Value</th>
                <th>Max Value</th>
                <th>Alerts</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="admin-params-tbody">
              <tr><td colspan="9" style="color:var(--text-muted);">Select a unit above to inspect and configure parameters.</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      
      <!-- Stations Table -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Stations</span>
          <button class="btn btn-sm btn-primary" onclick="AdminView.openCreateStationModal()">+ Add Station</button>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Station Name</th>
                <th>Location</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="admin-stations-tbody">
              <tr><td colspan="4" style="color:var(--text-muted);">Loading stations...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- User Accounts Table -->
      <div class="panel">
        <div class="panel-header">
          <span class="panel-title">Authorized Terminal Users</span>
        </div>
        <div class="table-container">
          <table class="scada-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email Address</th>
                <th>Role</th>
                <th>Active</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="admin-users-tbody">
              <tr><td colspan="6" style="color:var(--text-muted);">Loading users...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Modal Container -->
      <div id="admin-modal-container"></div>
    `;

    await AdminView.loadData();
  }

  static async loadData() {
    try {
      const unitsRes = await ApiClient.getUnits(true);
      const utbody = document.getElementById('admin-units-tbody');
      utbody.innerHTML = '';

      if (!unitsRes.units || unitsRes.units.length === 0) {
        utbody.innerHTML = `<tr><td colspan="8" style="color:var(--text-muted); text-align:center; padding:20px;">No turbines provisioned. Click '+ Provision Turbine Unit' to add your first plant turbine.</td></tr>`;
      } else {
        unitsRes.units.forEach(u => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td class="mono"><strong>${u.unit_code}</strong></td>
            <td><strong>${u.unit_name}</strong></td>
            <td>${u.station_name || "Unknown Station"} (${u.location || 'Bay 1'})</td>
            <td class="mono">${u.capacity_mw} MW</td>
            <td><span class="badge ${u.status === 'CRITICAL' ? 'badge-critical' : (u.status === 'WARNING' ? 'badge-warning' : 'badge-normal')}">${u.status}</span></td>
            <td>${u.active ? '<span class="badge badge-normal">Active</span>' : '<span class="badge badge-offline">Deactivated</span>'}</td>
            <td>
              <button class="btn btn-sm btn-primary" onclick="AdminView.inspectParameters(${u.id}, '${u.unit_code}')">Manage Parameters</button>
            </td>
            <td>
              <button class="btn btn-sm" onclick="AdminView.toggleUnitStatus(${u.id}, ${!u.active})">${u.active ? 'Deactivate' : 'Reactivate'}</button>
              <button class="btn btn-sm btn-danger" onclick="AdminView.deleteUnitPermanent(${u.id}, '${u.unit_code}')">Delete</button>
            </td>
          `;
          utbody.appendChild(tr);
        });
      }

      // Load Users
      
      // Load Stations
      const stationsRes = await ApiClient.request('/api/stations');
      const stbody = document.getElementById('admin-stations-tbody');
      stbody.innerHTML = '';
      if (!stationsRes.stations || stationsRes.stations.length === 0) {
        stbody.innerHTML = `<tr><td colspan="4" style="color:var(--text-muted);">No stations configured.</td></tr>`;
      } else {
        stationsRes.stations.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><strong>${s.name}</strong></td>
              <td>${s.location || '--'}</td>
              <td>${s.active ? '<span class="badge badge-normal">Active</span>' : '<span class="badge badge-offline">Inactive</span>'}</td>
              <td>
                <button class="btn btn-sm btn-primary" onclick="AdminView.openEditStationModal(${s.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="AdminView.deleteStation(${s.id}, '${s.name}')">Delete</button>
              </td>
            `;
          stbody.appendChild(tr);
        });
      }

      const usersRes = await ApiClient.getUsers();
    
      const usertbody = document.getElementById('admin-users-tbody');
      usertbody.innerHTML = '';
      usersRes.users.forEach(usr => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${usr.username}</strong></td>
          <td class="mono">${usr.email}</td>
          <td><span class="badge badge-normal">${usr.role}</span></td>
          <td>${usr.active ? '<span class="badge badge-normal">Active</span>' : '<span class="badge badge-offline">Inactive</span>'}</td>
          <td class="mono" style="font-size:10px;">${new Date(usr.created_at).toLocaleDateString()}</td>
          <td>
            <button class="btn btn-sm btn-primary" onclick="AdminView.openEditUserModal(${usr.id}, '${usr.username}', '${usr.role}', '${usr.email}', ${usr.active})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="AdminView.deleteUser(${usr.id}, '${usr.username}')" ${usr.role === 'admin' ? 'disabled' : ''}>Delete</button>
          </td>
        `;
        usertbody.appendChild(tr);
      });

    } catch (e) {
      console.error(e);
    }
  }

  static async inspectParameters(unitId, unitCode) {
    const panel = document.getElementById('admin-param-panel');
    panel.style.display = 'flex';
    document.getElementById('admin-param-panel-title').innerText = `Parameters Configured for Turbine: ${unitCode}`;
    document.getElementById('admin-add-param-btn').onclick = () => AdminView.openCreateParamModal(unitId, unitCode);

    try {
      const res = await ApiClient.getUnitParameters(unitId);
      const tbody = document.getElementById('admin-params-tbody');
      tbody.innerHTML = '';

      if (!res.parameters || res.parameters.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" style="color:var(--text-muted); text-align:center; padding:16px;">No parameters configured for this turbine. Click '+ Add Parameter to Turbine' to create operating limits.</td></tr>`;
        return;
      }

      res.parameters.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${p.name}</strong></td>
          <td class="mono">${p.parameter_key}</td>
          <td class="mono">${p.measurement_unit}</td>
          <td class="mono" style="color:#b45309; font-weight:700;">${p.warning_threshold}</td>
          <td class="mono" style="color:#b91c1c; font-weight:700;">${p.critical_threshold}</td>
          <td class="mono">${p.minimum_value !== null ? p.minimum_value : '--'}</td>
          <td class="mono">${p.maximum_value !== null ? p.maximum_value : '--'}</td>
          <td>${p.alert_enabled ? '<span class="badge badge-normal">Enabled</span>' : '<span class="badge badge-offline">Disabled</span>'}</td>
          <td>
            <button class="btn btn-sm btn-danger" onclick="AdminView.deleteParameter(${p.id}, ${unitId}, '${unitCode}')">Remove</button>
          </td>
        `;
        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error(e);
    }
  }

  // Provisioning Modals
  static openCreateUnitModal() {
    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Provision New Turbine Unit</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitCreateUnit(event)">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Turbine Unit Code (Unique Identifier)</label>
                <input type="text" id="m-unit-code" class="form-control" placeholder="e.g. UNIT-01" required>
              </div>
              <div class="form-group">
                <label class="form-label">Turbine Unit Name / Designation</label>
                <input type="text" id="m-unit-name" class="form-control" placeholder="e.g. Turbine Unit 01 (Steam Turbo-Generator)" required>
              </div>
              <div class="form-group">
                <label class="form-label">Thermal Power Plant Name</label>
                <input type="text" id="m-plant-name" class="form-control" value="Thermal Power Station Alpha" required>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Station Bay / Location</label>
                  <input type="text" id="m-location" class="form-control" placeholder="e.g. Turbine Hall Bay 1">
                </div>
                <div class="form-group">
                  <label class="form-label">Rated Capacity (MW)</label>
                  <input type="number" id="m-capacity" class="form-control" value="210.0" step="any" required>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Manufacturer / OEM</label>
                  <input type="text" id="m-manufacturer" class="form-control" placeholder="e.g. Siemens / GE / BHEL">
                </div>
                <div class="form-group">
                  <label class="form-label">Turbine Model</label>
                  <input type="text" id="m-model" class="form-control" placeholder="e.g. SST-800 Series">
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Provision Turbine</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateUnit(e) {
    e.preventDefault();
    const payload = {
      unit_code: document.getElementById('m-unit-code').value.trim(),
      unit_name: document.getElementById('m-unit-name').value.trim(),
      plant_name: document.getElementById('m-plant-name').value.trim(),
      location: document.getElementById('m-location').value.trim(),
      capacity_mw: parseFloat(document.getElementById('m-capacity').value) || 210.0,
      manufacturer: document.getElementById('m-manufacturer').value.trim(),
      model: document.getElementById('m-model').value.trim(),
      status: 'RUNNING'
    };

    try {
      await ApiClient.createUnit(payload);
      AdminView.closeModal();
      alert("Turbine unit provisioned successfully.");
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed creating unit: ${err.message}`);
    }
  }

  static openCreateParamModal(unitId, unitCode) {
    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Add Parameter to ${unitCode}</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitCreateParam(event, ${unitId}, '${unitCode}')">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Parameter Name</label>
                <select id="m-param-name" class="form-control" onchange="document.getElementById('m-param-key').value = event.target.value.toLowerCase().replace(/ /g, '_')" required>
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
                  <input type="text" id="m-param-key" class="form-control" placeholder="e.g. vibration" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Measurement Unit</label>
                  <select id="m-param-unit" class="form-control" required>
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
                  <input type="number" step="any" id="m-param-warn" class="form-control" placeholder="e.g. 4.0" required>
                </div>
                <div class="form-group">
                  <label class="form-label">Critical Threshold</label>
                  <input type="number" step="any" id="m-param-crit" class="form-control" placeholder="e.g. 5.0" required>
                </div>
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
                <div class="form-group">
                  <label class="form-label">Minimum Expected Value</label>
                  <input type="number" step="any" id="m-param-min" class="form-control" placeholder="e.g. 0.0">
                </div>
                <div class="form-group">
                  <label class="form-label">Maximum Expected Value</label>
                  <input type="number" step="any" id="m-param-max" class="form-control" placeholder="e.g. 15.0">
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">Description</label>
                <input type="text" id="m-param-desc" class="form-control" placeholder="e.g. Journal bearing vibration sensor (horizontal axis)">
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Save Parameter</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateParam(e, unitId, unitCode) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('m-param-name').value.trim(),
      parameter_key: document.getElementById('m-param-key').value.trim(),
      measurement_unit: document.getElementById('m-param-unit').value.trim(),
      warning_threshold: parseFloat(document.getElementById('m-param-warn').value),
      critical_threshold: parseFloat(document.getElementById('m-param-crit').value),
      minimum_value: document.getElementById('m-param-min').value ? parseFloat(document.getElementById('m-param-min').value) : null,
      maximum_value: document.getElementById('m-param-max').value ? parseFloat(document.getElementById('m-param-max').value) : null,
      description: document.getElementById('m-param-desc').value.trim(),
      enabled: true,
      alert_enabled: true
    };

    try {
      await ApiClient.createParameter(unitId, payload);
      AdminView.closeModal();
      alert("Parameter configured successfully.");
      await AdminView.inspectParameters(unitId, unitCode);
    } catch (err) {
      alert(`Failed configuring parameter: ${err.message}`);
    }
  }

  static async deleteParameter(paramId, unitId, unitCode) {
    if (!confirm("Are you sure you want to delete this parameter and all its historical readings?")) return;
    try {
      await ApiClient.request(`/api/parameters/${paramId}`, { method: 'DELETE' });
      await AdminView.inspectParameters(unitId, unitCode);
    } catch (e) {
      alert(e.message);
    }
  }

  static async toggleUnitStatus(unitId, makeActive) {
    try {
      await ApiClient.updateUnit(unitId, { active: makeActive, status: makeActive ? 'RUNNING' : 'OFFLINE' });
      await AdminView.loadData();
    } catch (e) {
      alert(e.message);
    }
  }

  static async deleteUnitPermanent(unitId, unitCode) {
    if (!confirm(`Are you sure you want to permanently delete turbine '${unitCode}'?`)) return;
    try {
      await ApiClient.request(`/api/units/${unitId}?hard=true`, { method: 'DELETE' });
      document.getElementById('admin-param-panel').style.display = 'none';
      await AdminView.loadData();
    } catch (e) {
      alert(e.message);
    }
  }

  
  static openEditUserModal(userId, username, role, email, active) {
    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Edit User: ${username}</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitEditUser(event, ${userId})">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">New Password (leave blank to keep current)</label>
                <input type="password" id="e-user-pass" class="form-control">
              </div>
              <div class="form-group">
                <label class="form-label">Role</label>
                <select id="e-user-role" class="form-control" ${role === 'admin' ? 'disabled' : ''}>
                  <option value="operator" ${role === 'operator' ? 'selected' : ''}>Operator</option>
                  <option value="engineer" ${role === 'engineer' ? 'selected' : ''}>Engineer</option>
                  <option value="admin" ${role === 'admin' ? 'selected' : ''}>Administrator</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">Status</label>
                <select id="e-user-active" class="form-control" ${role === 'admin' ? 'disabled' : ''}>
                  <option value="true" ${active ? 'selected' : ''}>Active</option>
                  <option value="false" ${!active ? 'selected' : ''}>Inactive</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitEditUser(e, userId) {
    e.preventDefault();
    const payload = {};
    const pass = document.getElementById('e-user-pass').value;
    if (pass) payload.password = pass;
    
    const roleEl = document.getElementById('e-user-role');
    if (!roleEl.disabled) payload.role = roleEl.value;
    
    const activeEl = document.getElementById('e-user-active');
    if (!activeEl.disabled) payload.active = activeEl.value === 'true';

    try {
      await ApiClient.request(`/api/users/${userId}`, { method: 'PUT', body: JSON.stringify(payload) });
      AdminView.closeModal();
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed updating user: ${err.message}`);
    }
  }

  static async deleteUser(userId, username) {
    if (!confirm(`Are you sure you want to permanently delete user '${username}'?`)) return;
    try {
      await ApiClient.request(`/api/users/${userId}`, { method: 'DELETE' });
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed deleting user: ${err.message}`);
    }
  }


  
  static openCreateStationModal() {
    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Add Station</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitCreateStation(event)">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Station Name</label>
                <input type="text" id="m-station-name" class="form-control" required>
              </div>
              <div class="form-group">
                <label class="form-label">Location</label>
                <input type="text" id="m-station-loc" class="form-control">
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Create Station</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateStation(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('m-station-name').value.trim(),
      location: document.getElementById('m-station-loc').value.trim()
    };
    try {
      await ApiClient.request('/api/stations', { method: 'POST', body: JSON.stringify(payload) });
      AdminView.closeModal();
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed creating station: ${err.message}`);
    }
  }

  static async deleteStation(stationId, stationName) {
    if (!confirm(`Delete station '${stationName}'? This may fail if units are attached.`)) return;
    try {
      await ApiClient.request(`/api/stations/${stationId}`, { method: 'DELETE' });
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed deleting station: ${err.message}`);
    }
  }

  static async openEditStationModal(stationId) {
    // Fetch current station data
    let station;
    try {
      const res = await ApiClient.request(`/api/stations/${stationId}`);
      station = res.station || res;
    } catch (err) {
      alert(`Could not load station data: ${err.message}`);
      return;
    }

    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Edit Station</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitEditStation(event, ${stationId})">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Station Name</label>
                <input type="text" id="e-station-name" class="form-control" value="${station.name || ''}" required>
              </div>
              <div class="form-group">
                <label class="form-label">Location</label>
                <input type="text" id="e-station-loc" class="form-control" value="${station.location || ''}">
              </div>
              <div class="form-group">
                <label class="form-label">Status</label>
                <select id="e-station-active" class="form-control">
                  <option value="true" ${station.active ? 'selected' : ''}>Active</option>
                  <option value="false" ${!station.active ? 'selected' : ''}>Inactive</option>
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Save Changes</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitEditStation(e, stationId) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('e-station-name').value.trim(),
      location: document.getElementById('e-station-loc').value.trim(),
      active: document.getElementById('e-station-active').value === 'true'
    };
    try {
      await ApiClient.request(`/api/stations/${stationId}`, { method: 'PUT', body: JSON.stringify(payload) });
      AdminView.closeModal();
      await AdminView.loadData();
    } catch (err) {
      alert(`Failed updating station: ${err.message}`);
    }
  }


  static openCreateUserModal() {
    const container = document.getElementById('admin-modal-container');
    container.innerHTML = `
      <div class="modal-backdrop">
        <div class="modal-dialog">
          <div class="modal-header">
            <strong style="font-size:13px; text-transform:uppercase;">Add User Account</strong>
            <button class="btn btn-sm" onclick="AdminView.closeModal()">Close</button>
          </div>
          <form onsubmit="AdminView.submitCreateUser(event)">
            <div class="modal-body">
              <div class="form-group">
                <label class="form-label">Username</label>
                <input type="text" id="m-user-name" class="form-control" required>
              </div>
              <div class="form-group">
                <label class="form-label">Email Address</label>
                <input type="email" id="m-user-email" class="form-control" required>
              </div>
              <div class="form-group">
                <label class="form-label">Temporary Password</label>
                <input type="password" id="m-user-pass" class="form-control" required>
              </div>
              <div class="form-group">
                <label class="form-label">Role</label>
                <select id="m-user-role" class="form-control">
                  <option value="operator">Operator</option>
                  <option value="engineer">Engineer</option>
                  
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn" onclick="AdminView.closeModal()">Cancel</button>
              <button type="submit" class="btn btn-primary">Create User</button>
            </div>
          </form>
        </div>
      </div>
    `;
  }

  static async submitCreateUser(e) {
    e.preventDefault();
    const payload = {
      username: document.getElementById('m-user-name').value.trim(),
      email: document.getElementById('m-user-email').value.trim(),
      password: document.getElementById('m-user-pass').value,
      role: document.getElementById('m-user-role').value
    };

    try {
      await ApiClient.createUser(payload);
      AdminView.closeModal();
      alert("User account created successfully.");
      await AdminView.loadData();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  }

  static closeModal() {
    const container = document.getElementById('admin-modal-container');
    if (container) container.innerHTML = '';
  }
}

window.AdminView = AdminView;
