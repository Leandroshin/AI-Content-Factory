/* Market Intelligence — Charts v1.0 */
/* SVG graficos sem dependencias. */
const Charts = (function() {
  function create(containerId, config) {
    var c = document.getElementById(containerId); if (!c) return;
    var dark = document.body.classList.contains('light') === false;
    var ct = { text: dark ? '#8b949e' : '#656d76', axis: dark ? '#30363d' : '#d0d7de', grid: dark ? '#21262d' : '#e5e7eb' };
    var w = config.w || c.clientWidth || 400, h = config.h || 200;
    var html = '<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + (config.label || 'Grafico') + '" style="width:100%;height:auto;max-width:' + w + 'px">';
    html += '<desc>' + (config.desc || '') + '</desc>';
    if (config.type === 'funnel') html += _funnel(config, w, h, ct);
    else if (config.type === 'bar') html += _bar(config, w, h, ct);
    else if (config.type === 'donut') html += _donut(config, w, h, ct, dark);
    else if (config.type === 'scatter') html += _scatter(config, w, h, ct);
    else if (config.type === 'sparkline') html += _sparkline(config, w, h, ct);
    else if (config.type === 'timeline') html += _timeline(config, w, h, ct);
    html += '</svg>';
    c.innerHTML = html;
  }
  function _funnel(config, w, h, ct) {
    var data = config.data || []; var html = '';
    var maxVal = Math.max.apply(null, data.map(function(d) { return d.value; })) || 1;
    var stepH = Math.min((h - 40) / data.length, 50);
    var startW = w - 80;
    data.forEach(function(d, i) {
      var sw = (d.value / maxVal) * startW;
      var x = (w - sw) / 2; var y = 10 + i * stepH;
      html += '<polygon points="' + x + ',' + y + ' ' + (x + sw) + ',' + y + ' ' + (x + sw * 0.85) + ',' + (y + stepH * 0.8) + ' ' + (x + sw * 0.15) + ',' + (y + stepH * 0.8) + '" fill="' + (d.color || '#58a6ff') + '" opacity="0.8"><title>' + d.label + ': ' + d.value + '</title></polygon>';
      html += '<text x="' + (w / 2) + '" y="' + (y + stepH * 0.4) + '" text-anchor="middle" fill="#fff" font-size="11" font-weight="600">' + d.label + ' (' + d.value + ')</text>';
    });
    return html;
  }
  function _bar(config, w, h, ct) {
    var data = config.data || []; var html = '';
    var maxVal = Math.max.apply(null, data.map(function(d) { return d.value; })) || 1;
    var barW = Math.min((w - 60) / data.length * 0.7, 30);
    var gap = ((w - 60) - barW * data.length) / (data.length + 1);
    html += '<line x1="50" y1="' + (h - 20) + '" x2="' + (w - 10) + '" y2="' + (h - 20) + '" stroke="' + ct.axis + '" stroke-width="1"/>';
    data.forEach(function(d, i) {
      var x = 50 + gap + i * (barW + gap);
      var bh = (d.value / maxVal) * (h - 40);
      var y = h - 20 - bh;
      html += '<rect x="' + x + '" y="' + y + '" width="' + barW + '" height="' + bh + '" fill="' + (d.color || '#58a6ff') + '" rx="2" opacity="0.85"><title>' + d.label + ': ' + d.value + '</title></rect>';
      html += '<text x="' + (x + barW / 2) + '" y="' + (h - 6) + '" text-anchor="middle" fill="' + ct.text + '" font-size="9">' + _trunc(d.label, 10) + '</text>';
    });
    return html;
  }
  function _donut(config, w, h, ct, dark) {
    var data = config.data || []; var cx = w / 2, cy = h / 2, r = Math.min(w, h) / 2 - 30;
    var total = data.reduce(function(s, d) { return s + d.value; }, 0) || 1;
    var html = '', cum = 0;
    data.forEach(function(d) {
      var pct = d.value / total; var angle = pct * 360; if (angle === 0) return;
      var sr = (cum - 90) * Math.PI / 180, er = (cum + angle - 90) * Math.PI / 180;
      var x1 = cx + r * Math.cos(sr), y1 = cy + r * Math.sin(sr);
      var x2 = cx + r * Math.cos(er), y2 = cy + r * Math.sin(er);
      var large = angle > 180 ? 1 : 0;
      html += '<path d="M' + cx + ',' + cy + ' L' + x1 + ',' + y1 + ' A' + r + ',' + r + ' 0 ' + large + ',1 ' + x2 + ',' + y2 + ' Z" fill="' + d.color + '" opacity="0.85"><title>' + d.label + ': ' + d.value + '</title></path>';
      cum += angle;
    });
    html += '<circle cx="' + cx + '" cy="' + cy + '" r="' + (r * 0.55) + '" fill="' + (dark ? '#1c2129' : '#fff') + '"/>';
    html += '<text x="' + cx + '" y="' + (cy + 4) + '" text-anchor="middle" fill="' + ct.text + '" font-size="12" font-weight="600">' + total + '</text>';
    return html;
  }
  function _scatter(config, w, h, ct) {
    var data = config.data || []; var html = '';
    var xMin = Math.min.apply(null, data.map(function(d) { return d.x; })) * 0.8 || 0;
    var xMax = Math.max.apply(null, data.map(function(d) { return d.x; })) * 1.2 || 1;
    var yMin = Math.min.apply(null, data.map(function(d) { return d.y; })) * 0.8 || 0;
    var yMax = Math.max.apply(null, data.map(function(d) { return d.y; })) * 1.2 || 1;
    data.forEach(function(d) {
      var px = 50 + ((d.x - xMin) / (xMax - xMin)) * (w - 70);
      var py = h - 20 - ((d.y - yMin) / (yMax - yMin)) * (h - 40);
      html += '<circle cx="' + px + '" cy="' + py + '" r="6" fill="' + (d.color || '#58a6ff') + '" opacity="0.7"><title>' + d.label + '</title></circle>';
    });
    return html;
  }
  function _sparkline(config, w, h, ct) {
    var data = config.data || []; if (data.length < 2) return '';
    var min = Math.min.apply(null, data), max = Math.max.apply(null, data), rng = max - min || 1;
    var pts = data.map(function(v, i) { return ((i / (data.length - 1)) * (w - 4) + 2) + ',' + (h - 3 - ((v - min) / rng) * (h - 6)); }).join(' ');
    var col = data[data.length - 1] > data[0] ? '#4ade80' : '#f87171';
    return '<polyline points="' + pts + '" fill="none" stroke="' + col + '" stroke-width="1.5"/>';
  }
  function _timeline(config, w, h, ct) {
    var data = config.data || []; if (data.length < 2) return '';
    var min = Math.min.apply(null, data), max = Math.max.apply(null, data), rng = max - min || 1;
    var pts = data.map(function(v, i) { return (50 + (i / (data.length - 1)) * (w - 70)) + ',' + (h - 20 - ((v - min) / rng) * (h - 40)); }).join(' ');
    html = '<polyline points="' + pts + '" fill="none" stroke="#58a6ff" stroke-width="2"/>';
    data.forEach(function(v, i) {
      var x = 50 + (i / (data.length - 1)) * (w - 70);
      var y = h - 20 - ((v - min) / rng) * (h - 40);
      html += '<circle cx="' + x + '" cy="' + y + '" r="3" fill="#58a6ff"><title>' + v + '</title></circle>';
    });
    return html;
  }
  function _trunc(s, n) { return s.length > n ? s.slice(0, n - 1) + '...' : s; }
  return { create };
})();
