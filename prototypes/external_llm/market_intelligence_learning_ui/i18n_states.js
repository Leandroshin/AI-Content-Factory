/* Market Intelligence — Central de Traducao de Estados v1.0 */
/* Mapeamento de identificadores internos (ingles) para portugues brasileiro. */
const I18n = (function() {
  var stateMap = {
    /* Estados de fonte */
    transcript_needed: 'Aguardando transcricao',
    transcript_available: 'Transcricao disponivel',
    /* Estados de Knowledge Card */
    promoted: 'Promovido',
    candidate: 'Candidato',
    review: 'Em revisao',
    rejected: 'Rejeitado',
    archived: 'Arquivado',
    /* Estados de claim/auditoria */
    verified: 'Verificada',
    partially_supported: 'Parcialmente sustentada',
    unverified: 'Nao verificada',
    promotional_claim: 'Alegacao promocional',
    contradicted: 'Contradita',
    outdated: 'Desatualizada',
    inconclusive: 'Inconclusivo',
    /* Estados de experimento */
    active: 'Ativo',
    proposed: 'Proposto',
    paused: 'Pausado',
    completed: 'Concluido',
    failed: 'Falhou',
    cancelled: 'Cancelado',
    /* Estados de aprovacao */
    approved: 'Aprovado',
    not_approved: 'Nao aprovado',
    pending_approval: 'Pendente de aprovacao',
    /* Estados gerais */
    learning: 'Aprendizado',
    observation: 'Observacao',
    comprovado: 'Comprovado',
    provavel: 'Provavel',
    especulativo: 'Especulativo',
    /* Classification */
    tool_mention: 'Mencao de ferramenta',
    revenue_claim: 'Alegacao de receita',
    strategy_pattern: 'Padrao de estrategia',
    metric_claim: 'Alegacao de metrica',
    cost_claim: 'Alegacao de custo',
    market_data: 'Dado de mercado',
    /* Prioridades */
    high: 'Alta',
    medium: 'Media',
    low: 'Baixa',
    emergency: 'Emergencia'
  };

  function t(key, fallback) {
    if (!key) return fallback || 'Nao informado';
    if (stateMap[key]) return stateMap[key];
    var upper = key.charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ');
    return upper;
  }

  function mapEnumList(items, field) {
    return (items || []).map(function(item) {
      var obj = {};
      obj[field || 'status'] = item;
      obj.label = t(item);
      return obj;
    });
  }

  return {
    t: t,
    mapEnumList: mapEnumList
  };
})();
