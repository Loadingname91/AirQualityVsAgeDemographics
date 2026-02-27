/**
 * ZIP Exposure Tool - client-side PM2.5 exposure by ZIP code
 * Uses IDW interpolation from PurpleAir sensors or EPA stations.
 */
(function () {
  'use strict';

  const ZIP_RE = /^\d{5}$/;
  const IDW_POWER = 2;
  const BUFFER_SAMPLES = 9; // center + 8 ring points

  let zipCentroids = null;
  let purpleAirPoints = null;
  let epaPoints = null;
  let map = null;
  let markers = [];
  let circles = [];

  function getBaseUrl() {
    const el = document.querySelector('.zip-exposure-tool');
    return (el && el.dataset.baseurl) || '';
  }

  function parseZips(input) {
    const tokens = input
      .split(/[\s,;\n]+/)
      .map((t) => t.trim().replace(/\D/g, '').slice(0, 5))
      .filter((t) => t.length === 5 && ZIP_RE.test(t));
    return [...new Set(tokens)];
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
      const dKm = Math.max(d * 1000, 10);
      const w = 1 / Math.pow(dKm, IDW_POWER);
      sumW += w;
      sumWv += w * p.pm25;
    }
    return sumW > 0 ? sumWv / sumW : null;
  }

  function bufferSamples(lat, lon, radiusM) {
    const samples = [{ lat, lon }];
    const degPerM = 1 / 111320;
    const step = radiusM * degPerM * 0.707;
    for (let i = 0; i < 8; i++) {
      const angle = (i * Math.PI * 2) / 8;
      samples.push({
        lat: lat + step * Math.cos(angle),
        lon: lon + step * Math.sin(angle) / Math.cos((lat * Math.PI) / 180)
      });
    }
    return samples;
  }

  function bufferMean(lat, lon, radiusM, points) {
    const samples = bufferSamples(lat, lon, radiusM);
    let sum = 0;
    let count = 0;
    for (const s of samples) {
      const v = idwAt(s.lat, s.lon, points);
      if (v != null) {
        sum += v;
        count++;
      }
    }
    return count > 0 ? sum / count : null;
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
      headers.forEach((h, i) => (row[h.trim()] = vals[i] ? vals[i].trim() : ''));
      return row;
    });
  }

  async function ensureData() {
    if (!zipCentroids) {
      zipCentroids = await loadCsv('/assets/data/ut_zip_centroids.csv');
    }
    const source = document.querySelector('input[name="zip-tool-source"]:checked')?.value || 'purpleair';
    if (source === 'purpleair' && !purpleAirPoints) {
      const rows = await loadCsv('/assets/data/purpleair_sensor_means_2026-01-01_2026-01-25.csv');
      purpleAirPoints = rows.map((r) => ({
        lat: parseFloat(r.lat),
        lon: parseFloat(r.lon),
        pm25: parseFloat(r.pm25)
      })).filter((p) => !isNaN(p.lat) && !isNaN(p.lon) && !isNaN(p.pm25));
    }
    if (source === 'epa' && !epaPoints) {
      const rows = await loadCsv('/assets/data/epa_station_means_2025-01-01_2025-01-30.csv');
      epaPoints = rows.map((r) => ({
        lat: parseFloat(r.lat),
        lon: parseFloat(r.lon),
        pm25: parseFloat(r.pm25)
      })).filter((p) => !isNaN(p.lat) && !isNaN(p.lon) && !isNaN(p.pm25));
    }
  }

  function zipLookup(zip) {
    if (!zipCentroids) return null;
    const z = String(zip).padStart(5, '0');
    return zipCentroids.find((r) => r.zip === z) || null;
  }

  function getPm25Color(v) {
    if (v < 12) return '#2ecc71';
    if (v < 35) return '#e67e22';
    return '#e74c3c';
  }

  function clearMap() {
    markers.forEach((m) => m.remove());
    markers = [];
    circles.forEach((c) => c.remove());
    circles = [];
  }

  function renderMap(results, bufferM) {
    const container = document.getElementById('zip-tool-map');
    if (!container) return;
    clearMap();
    if (!map) {
      map = L.map('zip-tool-map').setView([40.76, -111.89], 10);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap'
      }).addTo(map);
    }
    const bounds = [];
    for (const r of results) {
      const m = L.circleMarker([r.lat, r.lon], {
        radius: 10,
        fillColor: getPm25Color(r.pm25Point),
        color: '#333',
        weight: 2,
        fillOpacity: 0.8
      }).addTo(map);
      m.bindPopup(
        `<b>ZIP ${r.zip}</b><br>PM2.5: ${r.pm25Point != null ? r.pm25Point.toFixed(1) : 'N/A'} µg/m³` +
        (bufferM > 0 && r.pm25Buffer != null
          ? `<br>Buffer (${bufferM}m) mean: ${r.pm25Buffer.toFixed(1)} µg/m³`
          : '')
      );
      markers.push(m);
      bounds.push([r.lat, r.lon]);
      if (bufferM > 0 && r.pm25Buffer != null) {
        const circle = L.circle([r.lat, r.lon], {
          radius: bufferM,
          color: getPm25Color(r.pm25Buffer),
          fillOpacity: 0.1,
          weight: 1
        }).addTo(map);
        circles.push(circle);
      }
    }
    if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [30, 30] });
    } else if (bounds.length === 1) {
      map.setView(bounds[0], 14);
    }
  }

  function renderTable(results, bufferM) {
    const tbody = document.getElementById('zip-tool-table')?.querySelector('tbody');
    const table = document.getElementById('zip-tool-table');
    if (!tbody || !table) return;
    tbody.innerHTML = '';
    const showBuffer = bufferM > 0;
    for (const r of results) {
      const tr = document.createElement('tr');
      tr.innerHTML =
        `<td>${r.zip}</td><td>${r.lat.toFixed(4)}</td><td>${r.lon.toFixed(4)}</td>` +
        `<td>${r.pm25Point != null ? r.pm25Point.toFixed(2) : '—'}</td>` +
        `<td>${showBuffer && r.pm25Buffer != null ? r.pm25Buffer.toFixed(2) : '—'}</td>`;
      tbody.appendChild(tr);
    }
    table.hidden = false;
  }

  async function compute() {
    const input = document.getElementById('zip-tool-input');
    const bufferSel = document.getElementById('zip-tool-buffer');
    const status = document.getElementById('zip-tool-status');
    if (!input || !bufferSel || !status) return;
    const zips = parseZips(input.value);
    if (zips.length === 0) {
      status.textContent = 'Enter one or more 5-digit ZIP codes.';
      return;
    }
    status.textContent = 'Loading data...';
    try {
      await ensureData();
      const source = document.querySelector('input[name="zip-tool-source"]:checked')?.value || 'purpleair';
      const points = source === 'purpleair' ? purpleAirPoints : epaPoints;
      const bufferM = parseInt(bufferSel.value, 10) || 0;
      const results = [];
      const notFound = [];
      for (const zip of zips) {
        const row = zipLookup(zip);
        if (!row) {
          notFound.push(zip);
          continue;
        }
        const lat = parseFloat(row.lat);
        const lon = parseFloat(row.lon);
        if (isNaN(lat) || isNaN(lon)) continue;
        const pm25Point = idwAt(lat, lon, points);
        const pm25Buffer = bufferM > 0 ? bufferMean(lat, lon, bufferM, points) : null;
        results.push({
          zip,
          lat,
          lon,
          pm25Point,
          pm25Buffer
        });
      }
      if (notFound.length > 0) {
        status.textContent = `ZIP(s) not found: ${notFound.join(', ')}. Showing ${results.length} result(s).`;
      } else {
        status.textContent = `Found ${results.length} ZIP(s).`;
      }
      renderMap(results, bufferM);
      renderTable(results, bufferM);
    } catch (e) {
      status.textContent = 'Error: ' + (e.message || 'Could not load data.');
      console.error(e);
    }
  }

  function init() {
    const tool = document.querySelector('.zip-exposure-tool');
    if (!tool) return;
    const btn = document.getElementById('zip-tool-compute');
    if (btn) btn.addEventListener('click', compute);
    document.querySelectorAll('input[name="zip-tool-source"]').forEach((radio) => {
      radio.addEventListener('change', () => {
        purpleAirPoints = null;
        epaPoints = null;
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
