/* Market Intelligence — Security v1.0 */
/* Protecao basica contra XSS e URLs maliciosas. Sem dependencias. */
const Security = (function() {
  function sanitizeHTML(str) {
    if (typeof str !== 'string') return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }
  function validateURL(url) {
    if (typeof url !== 'string') return false;
    url = url.trim();
    if (url.startsWith('javascript:')) return false;
    if (url.startsWith('data:')) return false;
    if (url.startsWith('file:')) return false;
    if (url.includes('@') && url.includes('://')) return false;
    if (!url.startsWith('https://')) return false;
    return true;
  }
  function getDomain(url) {
    try {
      var u = new URL(url);
      return u.hostname;
    } catch(e) { return ''; }
  }
  function safeExternalLink(url, text) {
    if (!validateURL(url)) return '<span class="text-muted">Link invalido</span>';
    return '<a href="' + sanitizeHTML(url) + '" target="_blank" rel="noopener noreferrer" class="external-link">' + sanitizeHTML(text || getDomain(url)) + '</a>';
  }
  function validateJSON(str) {
    try {
      var d = JSON.parse(str);
      if (d && typeof d === 'object' && !Array.isArray(d) && d.version) return true;
      return !!d;
    } catch(e) { return false; }
  }
  function sanitizeText(str) { return sanitizeHTML(str); }
  function sanitizeUrl(url) {
    if (typeof url !== 'string') return '';
    url = url.trim();
    if (!url.startsWith('https://')) return '';
    return url;
  }
  return { sanitizeHTML, sanitizeText, sanitizeUrl, validateURL, getDomain, safeExternalLink, validateJSON };
})();
