/* Market Intelligence — Storage v1.0 */
/* localStorage persistence com validacao. */
const Storage = (function() {
  var PREFIX = 'mil_';
  function _key(k) { return PREFIX + k; }
  function get(key, def) {
    try { var v = localStorage.getItem(_key(key)); return v ? JSON.parse(v) : def; } catch(e) { return def; }
  }
  function set(key, val) {
    try { localStorage.setItem(_key(key), JSON.stringify(val)); } catch(e) {}
  }
  function remove(key) {
    try { localStorage.removeItem(_key(key)); } catch(e) {}
  }
  function generateId() { return 'mil-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 7); }
  function getAll(key) { return get(key, []); }
  function addItem(key, item) {
    var list = getAll(key);
    item.id = item.id || generateId();
    item.created_at = item.created_at || new Date().toISOString();
    list.push(item);
    set(key, list);
    return item;
  }
  function updateItem(key, id, updates) {
    var list = getAll(key);
    var idx = list.findIndex(function(x) { return x.id === id; });
    if (idx === -1) return null;
    list[idx] = Object.assign({}, list[idx], updates, { updated_at: new Date().toISOString() });
    set(key, list);
    return list[idx];
  }
  function removeItem(key, id) {
    var list = getAll(key);
    var filtered = list.filter(function(x) { return x.id !== id; });
    set(key, filtered);
    return filtered;
  }
  function getItem(key, id) {
    var list = getAll(key);
    return list.find(function(x) { return x.id === id; }) || null;
  }
  function clearAll() {
    var keys = Object.keys(localStorage);
    keys.forEach(function(k) { if (k.startsWith(PREFIX)) localStorage.removeItem(k); });
  }
  function exportData() {
    var result = {};
    var keys = Object.keys(localStorage);
    keys.forEach(function(k) {
      if (k.startsWith(PREFIX)) {
        try { result[k] = JSON.parse(localStorage.getItem(k)); } catch(e) { result[k] = localStorage.getItem(k); }
      }
    });
    result._exported_at = new Date().toISOString();
    result._version = '1.0';
    return JSON.stringify(result, null, 2);
  }
  function importData(jsonStr) {
    try {
      var data = JSON.parse(jsonStr);
      if (!data || typeof data !== 'object') return { success: false, error: 'Formato invalido' };
      var count = 0;
      Object.keys(data).forEach(function(k) {
        if (k.startsWith(PREFIX) && k !== PREFIX + 'history') {
          try { localStorage.setItem(k, JSON.stringify(data[k])); count++; } catch(e) {}
        }
      });
      return { success: true, imported: count };
    } catch(e) { return { success: false, error: 'JSON invalido: ' + e.message }; }
  }
  return { get, set, remove, generateId, getAll, addItem, updateItem, removeItem, getItem, clearAll, exportData, importData };
})();
