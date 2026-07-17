/* Market Intelligence — Claim Auditor v1.0 */
/* Auditoria cetica de alegacoes. Score deterministico. */
const ClaimAuditor = (function() {
  var VERSION = 'claim-audit-v1.0';
  function audit(claimText) {
    if (!claimText) return { total: 0, classification: 'not_applicable', components: [], version: VERSION };
    var t = claimText.toLowerCase();
    var components = [];
    /* 1. Especificidade */
    var specScore = _hasPattern(t, ['r$', 'us$', '%', 'x', 'em ', 'por ']) ? 15 : 3;
    components.push({ name: 'especificidade', weighted: specScore, weight: 15, pct: Math.round(specScore / 15 * 100) });
    /* 2. Periodo informado */
    var periodScore = _hasPattern(t, ['mes', 'ano', 'semana', 'dia', 'diario', 'mensal', 'anual', 'semanal']) ? 12 : 3;
    components.push({ name: 'periodo_informado', weighted: periodScore, weight: 12, pct: Math.round(periodScore / 12 * 100) });
    /* 3. Custo informado */
    var costScore = _hasPattern(t, ['gastei', 'gasto', 'investi', 'investimento', 'custo', 'custeou']) ? 12 : 3;
    components.push({ name: 'custo_informado', weighted: costScore, weight: 12, pct: Math.round(costScore / 12 * 100) });
    /* 4. Receita vs lucro */
    var rvlScore = (_hasPattern(t, ['lucro', 'liquido']) && _hasPattern(t, ['faturamento', 'receita', 'vendas'])) ? 12 : _hasPattern(t, ['lucro', 'liquido']) ? 8 : _hasPattern(t, ['faturamento', 'receita', 'vendas']) ? 4 : 2;
    components.push({ name: 'receita_vs_lucro', weighted: rvlScore, weight: 12, pct: Math.round(rvlScore / 12 * 100) });
    /* 5. Evidencia apresentada */
    var evScore = _hasPattern(t, ['fonte', 'dados', 'print', 'screenshot', 'link', 'url', 'mostrar', 'prova']) ? 12 : 2;
    components.push({ name: 'evidencia_apresentada', weighted: evScore, weight: 12, pct: Math.round(evScore / 12 * 100) });
    /* 6. Verificabilidade */
    var verScore = _hasPattern(t, ['pode ver', 'confira', 'acesse', 'acessar', 'link', 'site', 'plataforma']) ? 10 : 3;
    components.push({ name: 'verificabilidade', weighted: verScore, weight: 10, pct: Math.round(verScore / 10 * 100) });
    /* 7. Conflito de interesse */
    var coiScore = (_hasPattern(t, ['curso', 'mentoria', 'programa', 'vendo', 'afiliado', 'comissao', 'link']) && _hasPattern(t, ['ganhei', 'faturei', 'lucro', 'receita'])) ? 2 : 8;
    components.push({ name: 'conflito_interesse', weighted: coiScore, weight: 10, pct: Math.round(coiScore / 10 * 100) });
    /* 8. Contexto */
    var ctxScore = claimText.length > 100 ? 10 : claimText.length > 50 ? 6 : 3;
    components.push({ name: 'contexto', weighted: ctxScore, weight: 10, pct: Math.round(ctxScore / 10 * 100) });
    /* 9. Replicabilidade */
    var repScore = _hasPattern(t, ['passo', 'etapa', 'processo', 'metodo', 'sistema', 'framework']) ? 7 : 2;
    components.push({ name: 'replicabilidade', weighted: repScore, weight: 7, pct: Math.round(repScore / 7 * 100) });
    var total = Math.max(0, Math.min(100, Math.round(components.reduce(function(s, c) { return s + c.weighted; }, 0))));
    var classification = total >= 70 ? 'verified' : total >= 50 ? 'partially_supported' : total >= 30 ? 'unverified' : total >= 15 ? 'promotional_claim' : 'contradicted';
    var missing = [];
    if (periodScore <= 3) missing.push('periodo');
    if (costScore <= 3) missing.push('custo');
    if (rvlScore <= 4) missing.push('separacao receita/lucro');
    if (evScore <= 2) missing.push('evidencia');
    if (coiScore >= 8) missing.push('possivel conflito de interesse');
    return { total: total, classification: classification, components: components, missing: missing, version: VERSION };
  }
  function _hasPattern(text, patterns) {
    for (var i = 0; i < patterns.length; i++) { if (text.includes(patterns[i])) return true; }
    return false;
  }
  return { audit: audit, VERSION: VERSION };
})();
