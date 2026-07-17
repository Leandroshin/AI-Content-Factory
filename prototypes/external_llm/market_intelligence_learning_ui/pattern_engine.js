/* Market Intelligence — Pattern Engine v1.0 */
/* Agrupamento e score de padroes. */
const PatternEngine = (function() {
  var VERSION = 'pattern-strength-v1.0';
  function groupExtractions(extractions) {
    var groups = {};
    extractions.forEach(function(ex) {
      if (!ex.tags) return;
      ex.tags.forEach(function(tag) {
        if (!groups[tag]) groups[tag] = [];
        groups[tag].push(ex);
      });
    });
    return groups;
  }
  function scorePattern(tag, extractions, sources) {
    var ex = extractions || [];
    var src = sources || [];
    var uniqueSources = {};
    ex.forEach(function(e) { if (e.source_id) uniqueSources[e.source_id] = true; });
    var uniqueCount = Object.keys(uniqueSources).length;
    var components = [];
    var freqScore = Math.min(25, ex.length * 4);
    components.push({ name: 'frequencia', weighted: freqScore, weight: 25, pct: Math.round(freqScore / 25 * 100) });
    var indepScore = Math.min(25, uniqueCount * 8);
    components.push({ name: 'fontes_independentes', weighted: indepScore, weight: 25, pct: Math.round(indepScore / 25 * 100) });
    var recency = 10;
    components.push({ name: 'atualidade', weighted: recency, weight: 10, pct: 100 });
    var consistencyScore = Math.min(20, ex.length * 3);
    components.push({ name: 'consistencia', weighted: consistencyScore, weight: 20, pct: Math.round(consistencyScore / 20 * 100) });
    var total = Math.max(0, Math.min(100, Math.round(components.reduce(function(s, c) { return s + c.weighted; }, 0))));
    var warning = ex.length >= 3 && uniqueCount < 2 ? 'Mesma tag aparece em varias extracoes mas de poucas fontes independentes' : '';
    return { tag: tag, total: total, components: components, occurrences: ex.length, uniqueSources: uniqueCount, warning: warning, version: VERSION };
  }
  return { groupExtractions: groupExtractions, scorePattern: scorePattern, VERSION: VERSION };
})();
