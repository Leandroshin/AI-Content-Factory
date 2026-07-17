/* Market Intelligence — Extraction Engine v1.0 */
/* Extracao deterministica por regras. */
const ExtractionEngine = (function() {
  var VERSION = 'extraction-engine-v1.0';
  var TOOL_WORDS = ['usamos', 'ferramenta', 'plataforma', 'software', 'crm', 'checkout', 'dashboard', 'app', 'analytics', 'builder', 'sistema', 'automacao'];
  var CLAIM_WORDS = ['r$', 'us$', 'dolar', 'faturamento', 'lucro', 'vendas', 'milhao', 'milhoes', 'roi', 'retorno', 'margem', 'comissao', 'sete digitos', 'oito digitos', 'receita', 'faturou'];
  var STRATEGY_WORDS = ['nossa estrategia', 'o que fazemos', 'o processo e', 'primeiro', 'depois', 'funil', 'trafego', 'upsell', 'backend', 'recorrencia', 'coproducao'];
  function extractFromSegment(seg, sourceId) {
    if (!seg || !seg.text) return [];
    var result = [];
    var t = seg.text.toLowerCase();
    /* Tool mentions */
    TOOL_WORDS.forEach(function(w) {
      if (t.includes(w)) {
        result.push({ type: 'ToolMention', title: 'Ferramenta mencionada: ' + w, text: seg.text, timestamp: seg.start_time, speaker: seg.speaker, source_id: sourceId, segment_id: seg.segment_id, confidence: 0.5, nature: 'observed', tags: [w] });
      }
    });
    /* Financial claims */
    CLAIM_WORDS.forEach(function(w) {
      if (t.includes(w)) {
        result.push({ type: 'RevenueClaim', title: 'Alegacao financeira: ' + w, text: seg.text, timestamp: seg.start_time, speaker: seg.speaker, source_id: sourceId, segment_id: seg.segment_id, confidence: 0.3, nature: 'stated_claim', tags: [w, 'alegacao'] });
      }
    });
    /* Strategy patterns */
    STRATEGY_WORDS.forEach(function(w) {
      if (t.includes(w)) {
        result.push({ type: 'StrategyPattern', title: 'Padrao de estrategia: ' + w, text: seg.text, timestamp: seg.start_time, speaker: seg.speaker, source_id: sourceId, segment_id: seg.segment_id, confidence: 0.4, nature: 'observed', tags: [w, 'estrategia'] });
      }
    });
    return result;
  }
  function extractAll(segments, sourceId) {
    var all = [];
    segments.forEach(function(seg) {
      var ex = extractFromSegment(seg, sourceId);
      all = all.concat(ex);
    });
    return all;
  }
  function detectDomain(text) {
    var m = text.match(/https?:\/\/([a-zA-Z0-9.-]+)/);
    return m ? m[1] : null;
  }
  return { extractFromSegment: extractFromSegment, extractAll: extractAll, VERSION: VERSION };
})();
