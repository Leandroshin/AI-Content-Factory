/* Market Intelligence — Knowledge Engine v1.0 */
/* Gerenciamento de Knowledge Cards e candidatos. */
const KnowledgeEngine = (function() {
  var VERSION = 'knowledge-promotion-score-v1.0';
  function createCandidate(title, summary, sourceId, segmentId, hypothesis) {
    return {
      card_id: Storage.generateId(),
      title: title || 'Candidato sem titulo',
      summary: summary || '',
      hypothesis: hypothesis || '',
      sources: sourceId ? [sourceId] : [],
      segments: segmentId ? [segmentId] : [],
      timestamps: [],
      screenshots: [],
      confidence: 0.5,
      applicability: 'unknown',
      departments: [],
      risks: [],
      cost_estimate: '',
      restrictions: [],
      created_at: new Date().toISOString(),
      valid_until: null,
      review_date: null,
      experiment_id: null,
      result: null,
      status: 'draft',
      version: 1,
      approved_by: '',
      approved_at: null
    };
  }
  function promotionScore(card) {
    if (!card) return { total: 0, components: [], version: VERSION };
    var components = [];
    var srcScore = Math.min(20, (card.sources || []).length * 8);
    components.push({ name: 'fontes_independentes', weighted: srcScore, weight: 20, pct: Math.round(srcScore / 20 * 100) });
    var confScore = Math.round((card.confidence || 0) * 15);
    components.push({ name: 'confianca', weighted: confScore, weight: 15, pct: Math.round(confScore / 15 * 100) });
    var appScore = card.applicability === 'alta' ? 15 : card.applicability === 'media' ? 10 : 4;
    components.push({ name: 'aplicabilidade', weighted: appScore, weight: 15, pct: Math.round(appScore / 15 * 100) });
    var riskPenalty = Math.min(15, (card.risks || []).length * 5);
    components.push({ name: 'risco', weighted: 15 - riskPenalty, weight: 15, pct: Math.round((15 - riskPenalty) / 15 * 100) });
    var expScore = card.experiment_id ? 10 : 0;
    components.push({ name: 'experimento_associado', weighted: expScore, weight: 10, pct: Math.round(expScore / 10 * 100) });
    var depScore = Math.min(10, (card.departments || []).length * 4);
    components.push({ name: 'departamentos_interessados', weighted: depScore, weight: 10, pct: Math.round(depScore / 10 * 100) });
    var total = Math.max(0, Math.min(100, Math.round(components.reduce(function(s, c) { return s + c.weighted; }, 0))));
    return { total: total, components: components, version: VERSION };
  }
  function validateCard(card) {
    var issues = [];
    if (!card.title || card.title === 'Candidato sem titulo') issues.push('titulo obrigatorio');
    if (!card.summary) issues.push('resumo obrigatorio');
    if (!card.sources || card.sources.length === 0) issues.push('ao menos uma fonte');
    if (!card.hypothesis) issues.push('hipotese obrigatoria');
    if (!card.departments || card.departments.length === 0) issues.push('departamento obrigatorio');
    if (!card.risks || card.risks.length === 0) issues.push('risco obrigatorio');
    return { valid: issues.length === 0, issues: issues };
  }
  return { createCandidate: createCandidate, promotionScore: promotionScore, validateCard: validateCard, VERSION: VERSION };
})();
