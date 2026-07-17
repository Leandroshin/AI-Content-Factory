/* Market Intelligence — Software Opportunity Engine v1.0 */
/* Score de oportunidades de software. */
const SoftwareOpportunityEngine = (function() {
  var VERSION = 'software-opportunity-v1.0';
  function score(opp) {
    if (!opp) return { total: 0, components: [], version: VERSION };
    var components = [];
    var freqScore = Math.min(20, (opp.frequency || 0) * 5);
    components.push({ name: 'frequencia_do_problema', weighted: freqScore, weight: 20, pct: Math.round(freqScore / 20 * 100) });
    var intScore = Math.min(15, (opp.intensity || 5) * 2);
    components.push({ name: 'intensidade', weighted: intScore, weight: 15, pct: Math.round(intScore / 15 * 100) });
    var srcScore = Math.min(15, (opp.source_count || 0) * 4);
    components.push({ name: 'quantidade_fontes', weighted: srcScore, weight: 15, pct: Math.round(srcScore / 15 * 100) });
    var payScore = opp.payment_willingness === 'alta' ? 12 : opp.payment_willingness === 'media' ? 7 : 3;
    components.push({ name: 'disposicao_pagar', weighted: payScore, weight: 12, pct: Math.round(payScore / 12 * 100) });
    var altScore = !opp.alternatives_exist ? 10 : opp.alternatives_exist === 'poucas' ? 6 : 2;
    components.push({ name: 'falta_alternativas', weighted: altScore, weight: 10, pct: Math.round(altScore / 10 * 100) });
    var compScore = Math.min(10, opp.complexity === 'baixa' ? 10 : opp.complexity === 'media' ? 6 : 3);
    components.push({ name: 'complexidade', weighted: compScore, weight: 10, pct: Math.round(compScore / 10 * 100) });
    var synScore = opp.synergy_with_factory ? 10 : 3;
    components.push({ name: 'sinergia_fabrica', weighted: synScore, weight: 10, pct: Math.round(synScore / 10 * 100) });
    var riskScore = opp.risk === 'baixo' ? 8 : opp.risk === 'medio' ? 5 : 2;
    components.push({ name: 'risco', weighted: riskScore, weight: 8, pct: Math.round(riskScore / 8 * 100) });
    var total = Math.max(0, Math.min(100, Math.round(components.reduce(function(s, c) { return s + c.weighted; }, 0))));
    return { total: total, components: components, version: VERSION };
  }
  return { score: score, VERSION: VERSION };
})();
