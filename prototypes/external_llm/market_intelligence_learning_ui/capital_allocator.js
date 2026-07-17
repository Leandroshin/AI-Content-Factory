/* Market Intelligence — Capital Allocator v1.0 */
/* Alocacao de orcamento MOCK. Nenhum dinheiro real. */
const CapitalAllocator = (function() {
  var VERSION = 'capital-allocation-v1.0';
  var PROFILES = {
    conservative: { maxExposurePct: 20, minConfidence: 0.7, reservePct: 60 },
    moderate: { maxExposurePct: 40, minConfidence: 0.5, reservePct: 40 },
    exploratory: { maxExposurePct: 60, minConfidence: 0.3, reservePct: 20 }
  };
  function allocate(budget, experiments, profile) {
    if (!budget || budget <= 0) return { error: 'Orcamento invalido', allocations: [], reserve: 0, totalAllocated: 0 };
    var p = PROFILES[profile] || PROFILES.conservative;
    var allocations = [];
    var available = budget;
    experiments.forEach(function(exp) {
      if (available <= 0) return;
      var cost = exp.max_cost || 0;
      if (cost <= 0) return;
      if (cost > available) cost = available;
      var confidence = exp.confidence || 0.5;
      if (confidence < p.minConfidence) {
        allocations.push({ experiment_id: exp.experiment_id, title: exp.hypothesis || 'Sem nome', requested: exp.max_cost, allocated: 0, reason: 'Confianca abaixo do minimo (' + p.minConfidence + ')' });
        return;
      }
      var maxExposure = budget * p.maxExposurePct / 100;
      if (cost > maxExposure) cost = maxExposure;
      allocations.push({ experiment_id: exp.experiment_id, title: exp.hypothesis || 'Sem nome', requested: exp.max_cost, allocated: Math.round(cost), reason: 'Aprovado' });
      available -= cost;
    });
    var reserve = budget * p.reservePct / 100;
    var totalAllocated = budget - Math.round(available) - Math.round(reserve);
    var conclusion = '';
    if (totalAllocated === 0) {
      conclusion = 'Nenhum experimento atendeu aos criterios minimos. Nao utilizar o orcamento agora.';
    } else if (reserve > totalAllocated) {
      conclusion = 'As evidencias atuais nao justificam utilizar todo o orcamento. Mantenha ' + Math.round(reserve) + ' de reserva.';
    } else {
      conclusion = 'Carteira diversificada com ' + allocations.length + ' experimentos e ' + Math.round(reserve) + ' de reserva.';
    }
    return {
      budget: budget,
      profile: profile,
      allocations: allocations.filter(function(a) { return a.allocated > 0; }),
      rejected: allocations.filter(function(a) { return a.allocated === 0; }),
      reserve: Math.round(reserve),
      totalAllocated: totalAllocated,
      conclusion: conclusion,
      version: VERSION
    };
  }
  return { allocate: allocate, VERSION: VERSION, PROFILES: PROFILES };
})();
