/* Offer Intelligence — Comparador deterministico */
/* Compara 2 a 4 ofertas lado a lado e produz ranking. */

function compareOffers(offerIds) {
  const selected = OFFERS.filter(o => offerIds.includes(o.id));
  if (selected.length < 2 || selected.length > 4) {
    return { error: "Selecione 2 a 4 ofertas para comparar.", offers: [] };
  }

  const scores = {};
  selected.forEach(o => { scores[o.id] = calculateScore(o); });

  const fields = [
    { key: "score_total", label: "Score Total", unit: "", higher_better: true, icon: "mdi-score" },
    { key: "confidence_label", label: "Confianca", unit: "", higher_better: true, icon: "mdi-shield" },
    { key: "growth_90d", label: "Crescimento 90d", unit: "%", higher_better: true, icon: "mdi-trending-up" },
    { key: "search_volume", label: "Volume Busca", unit: "", higher_better: true, icon: "mdi-magnify" },
    { key: "commission_percent", label: "Comissao", unit: "%", higher_better: true, icon: "mdi-percent" },
    { key: "cookie_days", label: "Cookie", unit: "dias", higher_better: true, icon: "mdi-cookie" },
    { key: "active_ads", label: "Anuncios", unit: "", higher_better: true, icon: "mdi-bullhorn" },
    { key: "evidence_confidence", label: "Conf. Evidencias", unit: "", higher_better: true, icon: "mdi-file-check" },
    { key: "saturation_risk", label: "Risco Saturacao", unit: "", higher_better: false, icon: "mdi-alert" },
    { key: "policy_risk", label: "Risco Politica", unit: "", higher_better: false, icon: "mdi-gavel" },
    { key: "evidence_freshness_days", label: "Desatualizacao", unit: "dias", higher_better: false, icon: "mdi-clock" }
  ];

  /* Ranking */
  const ranked = [...selected].sort((a, b) => scores[b.id].score_total - scores[a.id].score_total);
  const bestOverall = ranked[0].id;

  const bestCommission = [...selected].sort((a, b) => b.commission_percent - a.commission_percent)[0].id;
  const bestGrowth = [...selected].sort((a, b) => b.growth_90d - a.growth_90d)[0].id;
  const bestConfidence = [...selected].sort((a, b) => b.evidence_confidence - a.evidence_confidence)[0].id;
  const lowestRisk = [...selected].sort((a, b) => {
    const riskA = (scores[a.id].penalties_detail.saturacao + scores[a.id].penalties_detail.politica);
    const riskB = (scores[b.id].penalties_detail.saturacao + scores[b.id].penalties_detail.politica);
    return riskA - riskB;
  })[0].id;

  const highlights = {
    best_overall: bestOverall,
    best_commission: bestCommission,
    best_growth: bestGrowth,
    best_confidence: bestConfidence,
    lowest_risk: lowestRisk
  };

  /* Conclusao */
  let conclusion;
  const best = scores[bestOverall];
  if (best.score_total >= 80) {
    conclusion = "Melhor candidata para teste limitado. Forneca aprovacao para iniciar producao controlada.";
  } else if (best.score_total >= 60) {
    conclusion = "Candidata promissora. Recomenda-se coleta de evidencias adicionais antes do teste.";
  } else {
    conclusion = "Nenhuma oferta apresenta sinais fortes. Considere buscar novas opcoes ou revisar criterios.";
  }

  return {
    offers: selected.map(o => ({ offer: o, score: scores[o.id] })),
    fields: fields,
    highlights: highlights,
    conclusion: conclusion,
    generated_at: new Date().toISOString()
  };
}

function generateAIAnalysis(offerId) {
  const offer = OFFERS.find(o => o.id === offerId);
  if (!offer) return null;
  const score = calculateScore(offer);

  const strengths = [];
  const weaknesses = [];
  const risks = [];
  const missingData = [];

  score.components.forEach(c => {
    if (c.weighted >= c.weight * 0.7 && c.weight > 5) strengths.push(c.note);
    if (c.weighted < c.weight * 0.3 && c.data_available && c.weight > 5) weaknesses.push(c.note);
    if (!c.data_available) missingData.push(c.name);
  });

  score.components.filter(c => c.value < 0).forEach(c => risks.push(c.note));

  let recAction, stopCondition, questions;

  if (score.score_total >= 80) {
    recAction = "Iniciar producao de criativo e preparar campanha de teste com orcamento controlado.";
    stopCondition = "Se o CPC ultrapassar 2x o estimado ou a taxa de conversao ficar abaixo de 0,5% apos 50 cliques.";
    questions = ["O publico-alvo corresponde ao perfil do produto?", "Ha sazonalidade que pode afetar o lancamento?"];
  } else if (score.score_total >= 60) {
    recAction = "Coletar mais evidencias de demanda e anuncios antes de iniciar producao.";
    stopCondition = "Se apos 7 dias de coleta o score permanecer abaixo de 60.";
    questions = ["Por que os dados de anuncios estao ausentes?", "Ha concorrentes de baixo custo no mesmo nicho?"];
  } else {
    recAction = "Revisar a oferta. Considere buscar alternativa com sinais mais fortes.";
    stopCondition = "Nao iniciar campanha ate que pelo menos 7 componentes tenham dados disponiveis.";
    questions = ["A oferta realmente atende a demanda do publico?", "Ha outra plataforma onde esta oferta tem melhor desempenho?"];
  }

  return {
    mock: true,
    disclaimer: "ANALISE MOCK - NENHUM LLM FOI CHAMADO. Esta analise e gerada localmente por regras JavaScript.",
    offer_name: offer.product_name,
    executive_summary: `${offer.product_name} obteve ${score.score_total}/100 (${score.classification_label}). ${score.confidence === "alta" ? "Confianca alta nos dados." : score.confidence === "media" ? "Confianca media - alguns dados podem estar desatualizados." : "Confianca baixa - dados insuficientes para conclusao robusta."}`,
    score_explanation: `O score foi calculado pela formula offer-score-v1.0 com ${score.components.length} componentes. O componente mais forte foi "${score.components.reduce((a, b) => a.weighted > b.weighted ? a : b).name}" e o mais fraco foi "${score.components.reduce((a, b) => a.weighted < b.weighted ? a : b).name}".`,
    strengths: strengths.length > 0 ? strengths : ["Nenhum ponto forte destacavel com os dados atuais."],
    weaknesses: weaknesses.length > 0 ? weaknesses : ["Nenhum ponto fraco critico identificado."],
    risks: risks.length > 0 ? risks : ["Riscos dentro do aceitavel para esta categoria."],
    missing_data: missingData.length > 0 ? missingData : ["Todos os componentes principais possuem dados."],
    sources_used: [offer.evidence_source],
    suggested_test_plan: recAction,
    stop_conditions: stopCondition,
    open_questions: questions,
    generated_at: new Date().toISOString(),
    model: "mock-rule-based-v1.0"
  };
}
