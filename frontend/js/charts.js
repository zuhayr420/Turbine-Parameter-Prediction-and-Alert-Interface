/**
 * SCADA Industrial Chart Component (Chart.js wrapper)
 * Clean White Engineering Theme with Dual-Zone Time-Series Visualization
 */
class ScadaCharts {
  static renderDualZoneForecast(canvasId, parameterName, unit, historicalData, forecastData, warningTh, criticalTh) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    if (typeof Chart === 'undefined') {
      console.error("Chart.js library is not loaded.");
      const parent = ctx.parentElement;
      if (parent) {
        parent.innerHTML = `<div style="padding:24px; text-align:center; color:#dc2626; font-size:12px;">Chart.js library not loaded. Please ensure js/chart.umd.min.js is accessible.</div>`;
      }
      return null;
    }

    // Chart.js 4.x canvas reuse: safely destroy existing chart instance
    try {
      const existing = Chart.getChart(ctx);
      if (existing) {
        existing.destroy();
      }
    } catch (e) {
      console.debug("Existing chart cleanup notice:", e);
    }

    if (ctx._chartInstance) {
      try {
        ctx._chartInstance.destroy();
      } catch (e) {}
    }

    const hist = Array.isArray(historicalData) ? historicalData : [];
    const fore = Array.isArray(forecastData) ? forecastData : [];

    const labels = [];
    const histPoints = [];
    const forecastPoints = [];

    // 1. Process Historical Observations (Solid Technical Blue)
    hist.forEach((pt, idx) => {
      const offset = hist.length - 1 - idx;
      labels.push(offset === 0 ? 'Current (t)' : `t-${offset}`);
      const val = typeof pt === 'object' && pt !== null ? pt.value : pt;
      histPoints.push(val !== undefined && val !== null ? Number(val) : null);
      forecastPoints.push(null);
    });

    // Bridge point: connect historical endpoint to the start of forecast
    if (histPoints.length > 0 && fore.length > 0) {
      forecastPoints[histPoints.length - 1] = histPoints[histPoints.length - 1];
    }

    // 2. Process Multi-Step Recursive Forecast Points (Dashed Amber)
    fore.forEach(pt => {
      const mins = typeof pt === 'object' && pt !== null ? (pt.minutes || pt.step * 15) : 15;
      labels.push(`+${mins}m`);
      histPoints.push(null);
      const val = typeof pt === 'object' && pt !== null ? pt.value : pt;
      forecastPoints.push(val !== undefined && val !== null ? Number(val) : null);
    });

    // If both historical and forecast are currently empty, provide empty time axes
    if (labels.length === 0) {
      for (let i = 1; i <= 12; i++) {
        labels.push(`+${i * 15}m`);
        forecastPoints.push(null);
        histPoints.push(null);
      }
    }

    const datasets = [
      {
        label: `Historical (${unit || ''})`,
        data: histPoints,
        borderColor: '#0284c7', // Professional technical blue
        backgroundColor: 'rgba(2, 132, 199, 0.05)',
        borderWidth: 2,
        fill: false,
        pointRadius: 2,
        pointHoverRadius: 5,
        tension: 0.1
      },
      {
        label: `Predicted 3H Forecast (${unit || ''})`,
        data: forecastPoints,
        borderColor: '#d97706', // Amber dashed
        borderDash: [6, 4],
        borderWidth: 2,
        fill: false,
        pointRadius: 3,
        pointHoverRadius: 6,
        tension: 0.1
      }
    ];

    // Warning Threshold boundary
    if (warningTh !== undefined && warningTh !== null && !isNaN(Number(warningTh))) {
      const wVal = Number(warningTh);
      datasets.push({
        label: `Warning Threshold (${wVal} ${unit || ''})`,
        data: labels.map(() => wVal),
        borderColor: '#f59e0b',
        borderDash: [3, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false
      });
    }

    // Critical Threshold boundary
    if (criticalTh !== undefined && criticalTh !== null && !isNaN(Number(criticalTh))) {
      const cVal = Number(criticalTh);
      datasets.push({
        label: `Critical Threshold (${cVal} ${unit || ''})`,
        data: labels.map(() => cVal),
        borderColor: '#dc2626',
        borderDash: [3, 3],
        borderWidth: 1.5,
        pointRadius: 0,
        fill: false
      });
    }

    if (typeof Chart !== 'undefined' && Chart.defaults) {
      Chart.defaults.font.family = "'Times New Roman', Times, serif";
    }

    const chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 250 },
        scales: {
          x: {
            grid: { color: '#e2e8f0' },
            ticks: { color: '#475569', font: { family: "'Times New Roman', Times, serif", size: 11 } }
          },
          y: {
            grid: { color: '#e2e8f0' },
            ticks: { color: '#475569', font: { family: "'Times New Roman', Times, serif", size: 11 } },
            title: {
              display: true,
              text: `${parameterName} (${unit || ''})`,
              color: '#1e293b',
              font: { family: "'Times New Roman', Times, serif", size: 12, weight: 'bold' }
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              color: '#334155',
              font: { size: 12, family: "'Times New Roman', Times, serif" },
              boxWidth: 14
            }
          },
          tooltip: {
            backgroundColor: '#ffffff',
            borderColor: '#cbd5e1',
            borderWidth: 1,
            titleColor: '#0f172a',
            bodyColor: '#334155',
            titleFont: { family: "'Times New Roman', Times, serif", size: 12, weight: 'bold' },
            bodyFont: { family: "'Times New Roman', Times, serif", size: 12 },
            callbacks: {
              label: function(context) {
                return `${context.dataset.label}: ${context.parsed.y} ${unit || ''}`;
              }
            }
          }
        }
      }
    });

    ctx._chartInstance = chart;
    return chart;
  }
}

window.ScadaCharts = ScadaCharts;
