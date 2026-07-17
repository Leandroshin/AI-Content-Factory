/* Market Intelligence — Experiment Engine v1.0 */
/* Gerenciamento de experimentos com guardrails. */
const ExperimentEngine = (function() {
  function create(knowledgeCardId, hypothesis) {
    return {
      experiment_id: Storage.generateId(),
      knowledge_card_id: knowledgeCardId || '',
      hypothesis: hypothesis || '',
      baseline: '',
      variant: '',
      steps: [],
      max_cost: 0,
      duration_days: 30,
      primary_metric: '',
      secondary_metrics: [],
      success_condition: '',
      stop_condition: '',
      risk: 'medio',
      providers_needed: [],
      channel: '',
      published: false,
      approved: false,
      result: null,
      conclusion: '',
      status: 'proposed',
      created_at: new Date().toISOString()
    };
  }
  function isValid(exp) {
    if (!exp.hypothesis) return 'Hipotese obrigatoria';
    if (!exp.max_cost || exp.max_cost <= 0) return 'Custo maximo obrigatorio';
    if (!exp.duration_days || exp.duration_days <= 0) return 'Duracao obrigatoria';
    if (!exp.primary_metric) return 'Metrica principal obrigatoria';
    if (!exp.stop_condition) return 'Condicao de parada obrigatoria';
    return null;
  }
  return { create: create, isValid: isValid };
})();
