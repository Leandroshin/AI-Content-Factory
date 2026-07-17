/* Offer Intelligence — Charts v1.0 */
/* SVG graficos. Sem CDN, sem dependencias. */

function createChart(containerId, config) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const isDark = document.body.classList.contains('light') === false;
  const colors = {
    text: isDark ? '#8b949e' : '#656d76',
    axis: isDark ? '#30363d' : '#d0d7de',
    grid: isDark ? '#21262d' : '#e5e7eb',
    bg: 'transparent'
  };
  const w = config.width || container.clientWidth || 400;
  const h = config.height || 200;
  const pad = config.pad || { top: 20, right: 20, bottom: 30, left: 50 };
  const plotW = w - pad.left - pad.right;
  const plotH = h - pad.top - pad.bottom;

  let svg = '<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + (config.ariaLabel || 'Grafico') + '" style="width:100%;height:auto;max-width:' + w + 'px">';
  svg += '<desc>' + (config.desc || '') + '</desc>';

  if (config.type === 'donut') {
    svg += _donut(config, w, h, colors, isDark);
  } else if (config.type === 'scatter') {
    svg += _scatter(config, w, h, pad, plotW, plotH, colors);
  } else if (config.type === 'bar') {
    svg += _barChart(config, w, h, pad, plotW, plotH, colors);
  } else if (config.type === 'sparkline') {
    svg += _sparkline(config, w, h, colors);
  } else if (config.type === 'comparison_bars') {
    svg += _comparisonBars(config, w, h, pad, plotW, plotH, colors);
  } else if (config.type === 'trend_detail') {
    svg += _trendDetail(config, w, h, pad, plotW, plotH, colors, isDark);
  }

  svg += '</svg>';
  container.innerHTML = svg;
}

function _donut(config, w, h, colors, isDark) {
  const cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 30;
  const total = config.data.reduce((s, d) => s + d.value, 0) || 1;
  let html = '';
  let cumulative = 0;
  config.data.forEach((d, i) => {
    const pct = d.value / total;
    const angle = pct * 360;
    if (angle === 0) return;
    const startRad = (cumulative - 90) * Math.PI / 180;
    const endRad = (cumulative + angle - 90) * Math.PI / 180;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);
    const large = angle > 180 ? 1 : 0;
    html += '<path d="M' + cx + ',' + cy + ' L' + x1 + ',' + y1 + ' A' + r + ',' + r + ' 0 ' + large + ',1 ' + x2 + ',' + y2 + ' Z" fill="' + d.color + '" opacity="0.85"><title>' + d.label + ': ' + d.value + ' (' + Math.round(pct * 100) + '%)</title></path>';
    cumulative += angle;
  });
  html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + (r * 0.55) + '" fill="' + (isDark ? '#1c2129' : '#ffffff') + '"/>';
  html += '<text x="' + cx + '" y="' + (cy + 4) + '" text-anchor="middle" fill="' + colors.text + '" font-size="12" font-weight="600">' + total + '</text>';

  /* Legend */
  let ly = h - 16;
  let lx = 10;
  config.data.forEach((d, i) => {
    if (lx + 120 > w) { lx = 10; ly -= 16; }
    html += '<rect x="' + lx + '" y="' + (ly - 8) + '" width="8" height="8" fill="' + d.color + '" rx="2"/>';
    html += '<text x="' + (lx + 12) + '" y="' + ly + '" fill="' + colors.text + '" font-size="10">' + d.label + ' (' + d.value + ')</text>';
    lx += 100;
  });
  return html;
}

function _scatter(config, w, h, pad, plotW, plotH, colors) {
  let html = '';
  const data = config.data;
  const xMin = Math.min(...data.map(d => d.x)) * 0.8 || 0;
  const xMax = Math.max(...data.map(d => d.x)) * 1.2 || 1;
  const yMin = Math.min(...data.map(d => d.y)) * 0.8 || 0;
  const yMax = Math.max(...data.map(d => d.y)) * 1.2 || 1;
  const sizeScale = config.sizeScale || 30;

  /* Axes */
  html += '<line x1="' + pad.left + '" y1="' + (pad.top + plotH) + '" x2="' + (pad.left + plotW) + '" y2="' + (pad.top + plotH) + '" stroke="' + colors.axis + '" stroke-width="1"/>';
  html += '<line x1="' + pad.left + '" y1="' + pad.top + '" x2="' + pad.left + '" y2="' + (pad.top + plotH) + '" stroke="' + colors.axis + '" stroke-width="1"/>';
  html += '<text x="' + (pad.left + plotW / 2) + '" y="' + (h - 4) + '" text-anchor="middle" fill="' + colors.text + '" font-size="10">Volume de Busca</text>';
  html += '<text x="8" y="' + (pad.top + plotH / 2) + '" text-anchor="middle" fill="' + colors.text + '" font-size="10" transform="rotate(-90,8,' + (pad.top + plotH / 2) + ')">Crescimento 90d</text>';

  /* Grid lines */
  for (let i = 0; i <= 4; i++) {
    const x = pad.left + (plotW * i / 4);
    const y = pad.top + (plotH * i / 4);
    html += '<line x1="' + pad.left + '" y1="' + y + '" x2="' + (pad.left + plotW) + '" y2="' + y + '" stroke="' + colors.grid + '" stroke-width="0.5"/>';
    html += '<line x1="' + x + '" y1="' + pad.top + '" x2="' + x + '" y2="' + (pad.top + plotH) + '" stroke="' + colors.grid + '" stroke-width="0.5"/>';
  }

  /* Points */
  data.forEach(d => {
    const px = pad.left + ((d.x - xMin) / (xMax - xMin)) * plotW;
    const py = pad.top + plotH - ((d.y - yMin) / (yMax - yMin)) * plotH;
    const r = Math.max(4, Math.min(20, Math.sqrt(Math.abs(d.size || 10)) * sizeScale / 20));
    html += '<circle cx="' + px + '" cy="' + py + '" r="' + r + '" fill="' + (d.color || '#58a6ff') + '" opacity="0.7" cursor="pointer"><title>' + d.label + ': Vol ' + d.x + ', Cresc ' + d.y + '%, Comissao ' + (d.size || 0) + '%</title></circle>';
  });
  return html;
}

function _barChart(config, w, h, pad, plotW, plotH, colors) {
  let html = '';
  const data = config.data;
  const maxVal = Math.max(...data.map(d => d.value), 1);
  const barW = Math.min(plotW / data.length * 0.7, 40);
  const gap = (plotW - barW * data.length) / (data.length + 1);

  /* Axes */
  html += '<line x1="' + pad.left + '" y1="' + (pad.top + plotH) + '" x2="' + (pad.left + plotW) + '" y2="' + (pad.top + plotH) + '" stroke="' + colors.axis + '" stroke-width="1"/>';

  /* Grid */
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH * i / 4);
    html += '<line x1="' + pad.left + '" y1="' + y + '" x2="' + (pad.left + plotW) + '" y2="' + y + '" stroke="' + colors.grid + '" stroke-width="0.5"/>';
  }

  data.forEach((d, i) => {
    const x = pad.left + gap + i * (barW + gap);
    const bh = (d.value / maxVal) * plotH;
    const y = pad.top + plotH - bh;
    html += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" fill="' + (d.color || '#58a6ff') + '" rx="2" opacity="0.85"><title>' + d.label + ': ' + d.value + '</title></rect>';
    html += '<text x="' + (x + barW / 2) + '" y="' + (pad.top + plotH + 14) + '" text-anchor="end" fill="' + colors.text + '" font-size="9" transform="rotate(-30,' + (x + barW / 2) + ',' + (pad.top + plotH + 14) + ')">' + _truncate(d.label, 10) + '</text>';
  });
  return html;
}

function _sparkline(config, w, h, colors) {
  const data = config.data;
  if (!data || data.length < 2) return '<text x="' + (w / 2) + '" y="' + (h / 2) + '" text-anchor="middle" fill="' + colors.text + '" font-size="10">Sem dados</text>';
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * (w - 4) + 2;
    const y = h - 3 - ((v - min) / range) * (h - 6);
    return x + ',' + y;
  }).join(' ');
  const trendColor = data[data.length - 1] > data[0] ? '#4ade80' : data[data.length - 1] < data[0] ? '#f87171' : '#58a6ff';
  return '<polyline points="' + points + '" fill="none" stroke="' + trendColor + '" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>';
}

function _comparisonBars(config, w, h, pad, plotW, plotH, colors) {
  let html = '';
  const groups = config.data;
  const maxVal = Math.max(...groups.flatMap(g => g.values.map(v => v.value)), 1);
  const groupW = plotW / groups.length;
  const barW = Math.min(groupW * 0.2, 20);
  const gap = (groupW - barW * Math.max(...groups.map(g => g.values.length))) / 2;

  html += '<line x1="' + pad.left + '" y1="' + (pad.top + plotH) + '" x2="' + (pad.left + plotW) + '" y2="' + (pad.top + plotH) + '" stroke="' + colors.axis + '" stroke-width="1"/>';

  groups.forEach((g, gi) => {
    const gx = pad.left + gi * groupW;
    g.values.forEach((v, vi) => {
      const x = gx + gap + vi * (barW + 2);
      const bh = (v.value / maxVal) * plotH;
      const y = pad.top + plotH - bh;
      html += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" fill="' + (v.color || '#58a6ff') + '" rx="1" opacity="0.85"><title>' + g.label + ' - ' + v.label + ': ' + v.value + '</title></rect>';
    });
    html += '<text x="' + (gx + groupW / 2) + '" y="' + (h - 4) + '" text-anchor="middle" fill="' + colors.text + '" font-size="9">' + _truncate(g.label, 8) + '</text>';
  });
  return html;
}

function _trendDetail(config, w, h, pad, plotW, plotH, colors, isDark) {
  const data = config.data;
  if (!data || data.length < 2) return '';
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  let html = '';

  /* Grid */
  for (let i = 0; i <= 4; i++) {
    const y = pad.top + (plotH * i / 4);
    html += '<line x1="' + pad.left + '" y1="' + y + '" x2="' + (pad.left + plotW) + '" y2="' + y + '" stroke="' + colors.grid + '" stroke-width="0.5"/>';
    const val = max - (range * i / 4);
    html += '<text x="' + (pad.left - 5) + '" y="' + (y + 4) + '" text-anchor="end" fill="' + colors.text + '" font-size="9">' + Math.round(val) + '</text>';
  }

  /* Area fill */
  const areaPoints = data.map((v, i) => {
    const x = pad.left + (i / (data.length - 1)) * plotW;
    const y = pad.top + plotH - ((v - min) / range) * plotH;
    return x + ',' + y;
  });
  html += '<polygon points="' + pad.left + ',' + (pad.top + plotH) + ' ' + areaPoints.join(' ') + ' ' + (pad.left + plotW) + ',' + (pad.top + plotH) + '" fill="' + (isDark ? 'rgba(88,166,255,0.15)' : 'rgba(88,166,255,0.1)') + '"/>';

  /* Line */
  html += '<polyline points="' + areaPoints.join(' ') + '" fill="none" stroke="#58a6ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';

  /* Markers */
  data.forEach((v, i) => {
    const x = pad.left + (i / (data.length - 1)) * plotW;
    const y = pad.top + plotH - ((v - min) / range) * plotH;
    html += '<circle cx="' + x + '" cy="' + y + '" r="3" fill="#58a6ff" opacity="0.8"><title>Dia ' + i + ': ' + Math.round(v) + '</title></circle>';
  });

  /* Mark config markers */
  if (config.markers) {
    config.markers.forEach(m => {
      const idx = Math.min(Math.max(0, Math.round(m.position * data.length)), data.length - 1);
      const x = pad.left + (idx / (data.length - 1)) * plotW;
      const y = pad.top + plotH - ((data[idx] - min) / range) * plotH;
      html += '<circle cx="' + x + '" cy="' + y + '" r="6" fill="none" stroke="' + m.color + '" stroke-width="2" opacity="0.9"><title>' + m.label + '</title></circle>';
      html += '<text x="' + (x + 8) + '" y="' + (y - 8) + '" fill="' + m.color + '" font-size="9">' + m.label + '</text>';
    });
  }

  return html;
}

function _truncate(s, n) {
  return s.length > n ? s.slice(0, n - 1) + '\u2026' : s;
}
