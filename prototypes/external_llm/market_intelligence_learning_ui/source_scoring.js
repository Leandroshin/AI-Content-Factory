/* Market Intelligence — Source Scoring v1.0 */
/* Score deterministico de confianca e risco de fonte. */
const SourceScoring = (function() {
  var VERSION = 'source-learning-score-v1.0';
  function score(source) {
    if (!source) return { total: 0, components: [], version: VERSION };
    var components = [];
    /* 1. Credibilidade do criador */
    var credibilityMap = { expert: 20, practitioner: 18, educator: 16, journalist: 14, influencer: 10, unknown: 6 };
    var credMax = 20;
    var credScore = credibilityMap[source.creator_type] || 6;
    components.push({ name: 'credibilidade_criador', weighted: credScore, weight: credMax, pct: Math.round(credScore / credMax * 100) });
    /* 2. Tipo de fonte */
    var typeMap = { documentation: 15, report: 14, case_study: 13, interview: 12, podcast: 10, video: 10, class: 11, manual_transcript: 8 };
    var typeMax = 15;
    var typeScore = typeMap[source.source_type] || 8;
    components.push({ name: 'tipo_fonte', weighted: typeScore, weight: typeMax, pct: Math.round(typeScore / typeMax * 100) });
    /* 3. Atualidade */
    var ageMax = 15;
    var daysOld = source.days_old || 365;
    var ageScore = Math.max(0, ageMax - Math.floor(daysOld / 30));
    components.push({ name: 'atualidade', weighted: ageScore, weight: ageMax, pct: Math.round(ageScore / ageMax * 100) });
    /* 4. Evidencia visual */
    var visMax = 10;
    var visScore = source.has_visual_evidence ? 10 : source.visual_cue_count > 0 ? 5 : 2;
    components.push({ name: 'evidencia_visual', weighted: visScore, weight: visMax, pct: Math.round(visScore / visMax * 100) });
    /* 5. Risco promocional */
    var riskMax = 15;
    var riskScore = source.promotional_risk === 'baixo' ? 15 : source.promotional_risk === 'medio' ? 10 : 3;
    components.push({ name: 'risco_promocional', weighted: riskScore, weight: riskMax, pct: Math.round(riskScore / riskMax * 100) });
    /* 6. Compliance */
    var compMax = 10;
    var compScore = source.compliance_risk === 'baixo' ? 10 : source.compliance_risk === 'medio' ? 6 : 2;
    components.push({ name: 'risco_compliance', weighted: compScore, weight: compMax, pct: Math.round(compScore / compMax * 100) });
    /* 7. Quantidade de dados */
    var dataMax = 15;
    var dataScore = Math.min(15, (source.segment_count || 0) * 0.5 + (source.tool_mentions || 0) * 2 + (source.claim_count || 0) * 1);
    components.push({ name: 'densidade_dados', weighted: Math.round(dataScore), weight: dataMax, pct: Math.round(dataScore / dataMax * 100) });
    var total = Math.max(0, Math.min(100, Math.round(components.reduce(function(s, c) { return s + c.weighted; }, 0))));
    var classification = total >= 80 ? 'confiavel' : total >= 60 ? 'provavel' : total >= 40 ? 'revisar' : total >= 20 ? 'cautela' : 'desconfiar';
    return { total: total, components: components, classification: classification, version: VERSION };
  }
  return { score: score, VERSION: VERSION };
})();
