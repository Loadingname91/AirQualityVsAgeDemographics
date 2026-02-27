/**
 * Move history timeline tool.
 * Parses residential history, estimates PM2.5 with IDW, renders timeline map and step chart.
 */
(function () {
  'use strict';

  const ZIP_RE = /^\d{5}$/;
  const IDW_POWER = 2;
  const ERA_COLORS = {
    '1980s': '#1f77b4',
    '1990s': '#2ca02c',
    '2000s': '#ff7f0e',
    '2010s': '#9467bd',
    '2020s': '#d62728',
    other: '#7f8c8d'
  };

  let zipCentroids = null;
  let purpleAirPoints = null;
  let epaPoints = null;
  let map = null;
  let layerGroup = null;
  let chart = null;

  function getBaseUrl() {
    const el = document.querySelector('.move-history-tool');
    return (el && el.dataset.baseurl) || '';
  }

  async function loadCsv(url) {
    const base = getBaseUrl();
    const path = url.startsWith('/') ? url.slice(1) : url;
    const full = base ? (base.endsWith('/') ? base : base + '/') + path : url;
    const r = await fetch(full);
    if (!r.ok) throw new Error('Failed to load: ' + url);
    const text = await r.text();
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',');
    return lines.slice(1).map((line) => {
      const vals = line.split(',');
      const row = {};
      headers.forEach((h, i) => {
        row[h.trim()] = vals[i] ? vals[i].trim() : '';
      });
      return row;
    });
  }

  async function ensureData(source) {
    if (!zipCentroids) {
      zipCentroids = await loadCsv('/assets/data/ut_zip_centroids.csv');
    }
    if (source === 'purpleair' && !purpleAirPoints) {
      const rows = await loadCsv('/assets/data/purpleair_sensor_means_2026-01-01_2026-01-25.csv');
      purpleAirPoints = rows
        .map((r) => ({
          id: r.sensor_id,
          lat: parseFloat(r.lat),
          lon: parseFloat(r.lon),
          pm25: parseFloat(r.pm25)
        }))
        .filter((p) => !isNaN(p.lat) && !isNaN(p.lon) && !isNaN(p.pm25));
    }
    if (source === 'epa' && !epaPoints) {
      const rows = await loadCsv('/assets/data/epa_station_means_2025-01-01_2025-01-30.csv');
      epaPoints = rows
        .map((r) => ({
          id: r.local_site_name || r.site_number,
          lat: parseFloat(r.lat),
          lon: parseFloat(r.lon),
          pm25: parseFloat(r.pm25)
        }))
        .filter((p) => !isNaN(p.lat) && !isNaN(p.lon) && !isNaN(p.pm25));
    }
  }

  function getActiveSource() {
    return document.querySelector('input[name="mh-source"]:checked')?.value || 'purpleair';
  }

  function getColorMode() {
    return document.querySelector('input[name="mh-color-mode"]:checked')?.value || 'era';
  }

  function zipLookup(zip) {
    if (!zipCentroids) return null;
    const normalized = String(zip).padStart(5, '0');
    return zipCentroids.find((z) => z.zip === normalized) || null;
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function idwAt(lat, lon, points) {
    if (!points || points.length === 0) return null;
    let sumW = 0;
    let sumWv = 0;
    for (const p of points) {
      const d = haversineKm(lat, lon, p.lat, p.lon);
      const dM = Math.max(d * 1000, 10);
      const w = 1 / Math.pow(dM, IDW_POWER);
      sumW += w;
      sumWv += w * p.pm25;
    }
    return sumW > 0 ? sumWv / sumW : null;
  }

  function getPm25Color(v) {
    if (v < 12) return '#2ecc71';
    if (v < 35) return '#e67e22';
    return '#e74c3c';
  }

  function normalizeDateStr(raw, fallbackEnd) {
    const s = String(raw || '').trim();
    if (!s) {
      return fallbackEnd ? new Date().toISOString().slice(0, 10) : null;
    }
    if (/^\d{4}$/.test(s)) return s + '-01-01';
    if (/^\d{4}-\d{2}$/.test(s)) return s + '-01';
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
    return null;
  }

  function parseCsvRecords(text) {
    const lines = text
      .split('\n')
      .map((l) => l.trim())
      .filter((l) => l);
    if (lines.length < 2) return [];
    const header = lines[0].toLowerCase();
    if (!header.includes('zip')) return [];
    return lines.slice(1).map((line) => {
      const parts = line.split(',').map((p) => p.trim());
      return {
        zip: parts[0] || '',
        start: parts[1] || '',
        end: parts[2] || ''
      };
    });
  }

  function parseInput(text) {
    const trimmed = text.trim();
    if (!trimmed) return [];

    if (trimmed.startsWith('[')) {
      const parsed = JSON.parse(trimmed);
      if (!Array.isArray(parsed)) throw new Error('JSON input must be an array.');
      return parsed.map((item) => ({
        zip: String(item.zip || '').trim(),
        start: String(item.start || item.start_date || '').trim(),
        end: String(item.end || item.end_date || '').trim()
      }));
    }
    return parseCsvRecords(trimmed);
  }

  function decadeLabel(isoDate) {
    if (!isoDate) return 'other';
    const year = Number(isoDate.slice(0, 4));
    if (isNaN(year)) return 'other';
    const decade = Math.floor(year / 10) * 10;
    return decade + 's';
  }

  function renderMap(records, colorMode) {
    const mapEl = document.getElementById('mh-map');
    if (!mapEl) return;

    if (!map) {
      map = L.map('mh-map').setView([40.76, -111.89], 10);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
      }).addTo(map);
    }
    if (layerGroup) layerGroup.remove();
    layerGroup = L.layerGroup().addTo(map);

    const latLngs = [];
    records.forEach((r, i) => {
      latLngs.push([r.lat, r.lon]);
      const markerColor = colorMode === 'pm25' ? getPm25Color(r.pm25) : (ERA_COLORS[decadeLabel(r.startISO)] || ERA_COLORS.other);
      const marker = L.circleMarker([r.lat, r.lon], {
        radius: 9,
        fillColor: markerColor,
        color: '#2c3e50',
        weight: 2,
        fillOpacity: 0.85
      }).addTo(layerGroup);

      const deltaText = i === 0 ? 'Initial residence.' : `Move impact: ${(r.delta >= 0 ? '+' : '') + r.delta.toFixed(2)} µg/m³`;
      marker.bindPopup(
        `<b>${i + 1}. ZIP ${r.zip}</b><br>` +
        `${r.startLabel} to ${r.endLabel}<br>` +
        `Estimated PM2.5: ${r.pm25.toFixed(2)} µg/m³<br>` +
        deltaText
      );
      marker.bindTooltip(`#${i + 1}`, { permanent: true, direction: 'top', offset: [0, -10] });
    });

    if (latLngs.length > 1) {
      const line = L.polyline(latLngs, { color: '#34495e', weight: 3, opacity: 0.85 }).addTo(layerGroup);
      map.fitBounds(line.getBounds(), { padding: [30, 30] });
    } else if (latLngs.length === 1) {
      map.setView(latLngs[0], 12);
    }
  }

  function renderMoveDeltas(records) {
    const root = document.getElementById('mh-move-deltas');
    if (!root) return;
    if (records.length < 2) {
      root.innerHTML = '<p>No move transitions to summarize yet.</p>';
      return;
    }
    const items = records.slice(1).map((r, idx) => {
      const direction = r.delta >= 0 ? 'increased' : 'decreased';
      return `<li>Move ${idx + 1} to ZIP ${r.zip} ${direction} estimated exposure by <strong>${Math.abs(r.delta).toFixed(2)} µg/m³</strong>.</li>`;
    });
    root.innerHTML = `<ul>${items.join('')}</ul>`;
  }

  function renderChart(records) {
    const canvas = document.getElementById('mh-chart');
    if (!canvas || typeof Chart === 'undefined') return;
    if (chart) chart.destroy();

    const labels = [];
    const values = [];
    records.forEach((r) => {
      labels.push(r.startLabel);
      values.push(Number(r.pm25.toFixed(2)));
    });
    labels.push(records[records.length - 1].endLabel);
    values.push(Number(records[records.length - 1].pm25.toFixed(2)));

    chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Estimated PM2.5 at residence (µg/m³)',
            data: values,
            stepped: 'after',
            borderColor: '#2c3e50',
            backgroundColor: 'rgba(52, 73, 94, 0.15)',
            pointBackgroundColor: '#2c3e50',
            pointRadius: 4,
            fill: false,
            tension: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: true },
          tooltip: { mode: 'index', intersect: false }
        },
        scales: {
          y: {
            title: { display: true, text: 'PM2.5 (µg/m³)' },
            beginAtZero: true
          },
          x: {
            title: { display: true, text: 'Residence timeline' }
          }
        }
      }
    });
  }

  async function buildTimeline() {
    const input = document.getElementById('mh-history-input');
    const status = document.getElementById('mh-status');
    if (!input || !status) return;

    try {
      const rawRecords = parseInput(input.value);
      if (rawRecords.length === 0) {
        status.textContent = 'Enter at least one residence row in CSV or JSON format.';
        return;
      }

      status.textContent = 'Loading PM2.5 and ZIP data...';
      const source = getActiveSource();
      await ensureData(source);
      const points = source === 'purpleair' ? purpleAirPoints : epaPoints;

      const normalized = rawRecords
        .map((r) => ({
          zip: String(r.zip || '').replace(/\D/g, '').slice(0, 5),
          startISO: normalizeDateStr(r.start, false),
          endISO: normalizeDateStr(r.end, true)
        }))
        .filter((r) => ZIP_RE.test(r.zip) && r.startISO);

      if (normalized.length === 0) {
        status.textContent = 'No valid rows found. Ensure each row has ZIP and start date.';
        return;
      }

      normalized.sort((a, b) => new Date(a.startISO) - new Date(b.startISO));
      const enriched = [];
      const missing = [];
      for (const r of normalized) {
        const centroid = zipLookup(r.zip);
        if (!centroid) {
          missing.push(r.zip);
          continue;
        }
        const lat = parseFloat(centroid.lat);
        const lon = parseFloat(centroid.lon);
        if (isNaN(lat) || isNaN(lon)) continue;

        const pm25 = idwAt(lat, lon, points);
        if (pm25 == null) continue;
        enriched.push({
          zip: r.zip,
          startISO: r.startISO,
          endISO: r.endISO || new Date().toISOString().slice(0, 10),
          startLabel: r.startISO,
          endLabel: r.endISO || 'present',
          lat,
          lon,
          pm25
        });
      }

      if (enriched.length === 0) {
        status.textContent = 'None of the input ZIPs could be resolved.';
        return;
      }

      enriched.forEach((r, idx) => {
        if (idx === 0) {
          r.delta = 0;
        } else {
          r.delta = r.pm25 - enriched[idx - 1].pm25;
        }
      });

      renderMap(enriched, getColorMode());
      renderChart(enriched);
      renderMoveDeltas(enriched);

      status.textContent =
        `Built timeline for ${enriched.length} residence(s)` +
        (missing.length ? `. ZIP(s) not found: ${missing.join(', ')}` : '.');
    } catch (err) {
      status.textContent = 'Error: ' + (err.message || 'Could not build timeline.');
      console.error(err);
    }
  }

  function demoInput() {
    const input = document.getElementById('mh-history-input');
    if (!input) return;
    input.value = [
      'zip,start_date,end_date',
      '84102,2010-01,2014-12',
      '84101,2015-01,2020-12',
      '84003,2021-01,'
    ].join('\n');
  }

  function init() {
    if (!document.querySelector('.move-history-tool')) return;
    const buildBtn = document.getElementById('mh-build-btn');
    const demoBtn = document.getElementById('mh-demo-btn');
    if (buildBtn) buildBtn.addEventListener('click', buildTimeline);
    if (demoBtn) demoBtn.addEventListener('click', demoInput);
    document.querySelectorAll('input[name="mh-color-mode"]').forEach((el) => {
      el.addEventListener('change', buildTimeline);
    });
    document.querySelectorAll('input[name="mh-source"]').forEach((el) => {
      el.addEventListener('change', buildTimeline);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
