/* Offer Intelligence — Score deterministico v1.0 */
/* Formula: offer-score-v1.0 */
/* A IA (futura) apenas explica o resultado, nunca modifica a nota. */

function calculateScore(offer) {
  const components = [];
  let total = 0;
  let maxTotal = 100;
  let penalties = 0;
  let missingData = [];

  /* 1. Crescimento (weight 20) */
  let growthScore = 0;
  if (offer.growth_90d >= 100) growthScore = 20;
  else if (offer.growth_90d >= 50) growthScore = 17;
  else if (offer.growth_90d >= 20) growthScore = 13;
  else if (offer.growth_90d >= 5) growthScore = 8;
  else if (offer.growth_90d >= -5) growthScore = 5;
  else growthScore = 1;
  components.push({
    name: "crescimento", weight: 20, value: growthScore, weighted: growthScore,
    data_available: true, source: "trends", confidence: 0.8,
    note: offer.growth_90d >= 20 ? "Crescimento forte em 90 dias" : offer.growth_90d >= 0 ? "Crescimento moderado" : "Declinio detectado"
  });
  total += growthScore;

  /* 2. Volume absoluto (weight 10) */
  let volScore = 0;
  const vol = offer.search_volume;
  if (vol >= 20000) volScore = 10;
  else if (vol >= 10000) volScore = 8;
  else if (vol >= 5000) volScore = 6;
  else if (vol >= 2000) volScore = 4;
  else if (vol >= 500) volScore = 2;
  else volScore = 1;
  components.push({
    name: "volume_absoluto", weight: 10, value: volScore, weighted: volScore,
    data_available: true, source: "trends", confidence: 0.75,
    note: vol >= 5000 ? "Volume de busca alto" : vol >= 2000 ? "Volume moderado" : "Volume baixo"
  });
  total += volScore;

  /* 3. Comissao (weight 18) */
  let commScore = 0;
  const comm = offer.commission_percent;
  const price = offer.current_price;
  const commValue = price * (comm / 100);
  if (comm >= 60 || commValue >= 100) commScore = 18;
  else if (comm >= 40 || commValue >= 50) commScore = 14;
  else if (comm >= 20 || commValue >= 20) commScore = 10;
  else if (comm >= 5) commScore = 6;
  else commScore = 2;
  components.push({
    name: "comissao", weight: 18, value: commScore, weighted: commScore,
    data_available: true, source: "affiliate_network", confidence: 0.85,
    note: comm >= 40 ? "Comissao alta" : comm >= 20 ? "Comissao moderada" : "Comissao baixa"
  });
  total += commScore;

  /* 4. Persistencia da tendencia (weight 8) */
  let persistScore = 0;
  const p = offer.trend_persistence;
  if (p === "sustained_12m") persistScore = 8;
  else if (p === "sustained_6m") persistScore = 7;
  else if (p === "sustained_3m") persistScore = 5;
  else if (p === "emerging_3m") persistScore = 4;
  else if (p === "stable_12m") persistScore = 5;
  else if (p === "stable_6m") persistScore = 4;
  else if (p === "stable_3m") persistScore = 3;
  else if (p === "declining_3m") persistScore = 2;
  else if (p === "declining_6m") persistScore = 1;
  else persistScore = 3;
  components.push({
    name: "persistencia_tendencia", weight: 8, value: persistScore, weighted: persistScore,
    data_available: true, source: "trends", confidence: 0.7,
    note: p.includes("sustained") ? "Tendencia sustentada" : p.includes("stable") ? "Estabilidade" : "Sinal de declinio"
  });
  total += persistScore;

  /* 5. Presenca de anuncios (weight 12) */
  let adScore = 0;
  const ads = offer.active_ads || 0;
  const advs = offer.advertiser_count || 0;
  if (ads >= 20 && advs >= 5) adScore = 12;
  else if (ads >= 10 && advs >= 3) adScore = 9;
  else if (ads >= 5 && advs >= 2) adScore = 6;
  else if (ads >= 1) adScore = 3;
  else adScore = 0;
  if (ads === 0 && offer.risk_flags.includes("sem_anuncios")) {
    missingData.push("anuncios");
  }
  components.push({
    name: "presenca_anuncios", weight: 12, value: adScore, weighted: adScore,
    data_available: ads > 0, source: "meta_ad_library", confidence: ads > 0 ? 0.75 : 0,
    note: ads >= 10 ? "Presenca publicitaria significativa" : ads > 0 ? "Anuncios detectados" : "Nenhum anuncio encontrado"
  });
  total += adScore;

  /* 6. Qualidade da oferta (weight 12) */
  let qualityScore = 0;
  const trust = offer.marketplace_trust || 0.5;
  const rating = offer.reviews_avg || 0;
  const reviews = offer.review_count || 0;
  qualityScore += trust >= 0.85 ? 4 : trust >= 0.7 ? 3 : 2;
  qualityScore += rating >= 4.5 ? 4 : rating >= 4.0 ? 3 : rating >= 3.5 ? 2 : 1;
  qualityScore += reviews >= 500 ? 4 : reviews >= 100 ? 3 : reviews >= 20 ? 2 : 1;
  qualityScore = Math.min(12, qualityScore);
  components.push({
    name: "qualidade_oferta", weight: 12, value: qualityScore, weighted: qualityScore,
    data_available: true, source: "marketplace", confidence: 0.9,
    note: qualityScore >= 9 ? "Oferta de alta qualidade" : qualityScore >= 6 ? "Qualidade media" : "Qualidade abaixo da media"
  });
  total += qualityScore;

  /* 7. Disponibilidade de afiliacao (weight 8) */
  let affScore = 0;
  if (offer.affiliate_available && offer.affiliate_program) {
    if (offer.cookie_days >= 30) affScore = 8;
    else if (offer.cookie_days >= 7) affScore = 6;
    else affScore = 4;
  } else {
    affScore = 0;
    missingData.push("afiliacao");
  }
  components.push({
    name: "disponibilidade_afiliacao", weight: 8, value: affScore, weighted: affScore,
    data_available: offer.affiliate_available, source: "manual", confidence: 0.9,
    note: offer.affiliate_available ? (offer.cookie_days >= 30 ? "Programa de afiliados com cookie longo" : "Afiliacao disponivel") : "Sem programa de afiliados"
  });
  total += affScore;

  /* 8. Atualidade das evidencias (weight 5) */
  let freshScore = 0;
  const days = offer.evidence_freshness_days || 30;
  if (days <= 1) freshScore = 5;
  else if (days <= 3) freshScore = 4;
  else if (days <= 7) freshScore = 3;
  else if (days <= 15) freshScore = 2;
  else freshScore = 1;
  components.push({
    name: "atualidade_evidencias", weight: 5, value: freshScore, weighted: freshScore,
    data_available: true, source: "sistema", confidence: 1.0,
    note: days <= 3 ? "Dados recentes" : days <= 7 ? "Dados da ultima semana" : "Dados desatualizados"
  });
  total += freshScore;

  /* 9. Confianca das evidencias (weight 5) */
  let confScore = Math.round(offer.evidence_confidence * 5);
  confScore = Math.max(1, Math.min(5, confScore));
  components.push({
    name: "confianca_evidencias", weight: 5, value: confScore, weighted: confScore,
    data_available: true, source: "calculada", confidence: offer.evidence_confidence,
    note: offer.evidence_confidence >= 0.8 ? "Fontes confiaveis" : offer.evidence_confidence >= 0.6 ? "Confianca media" : "Confianca baixa"
  });
  total += confScore;

  /* 10. Risco de saturacao (penalty 0 to -8) */
  let satPenalty = 0;
  if (offer.saturation_level === "alto") satPenalty = 8;
  else if (offer.saturation_level === "medio") satPenalty = 4;
  else satPenalty = 0;
  if (offer.competition_level === "alto") satPenalty += 3;
  else if (offer.competition_level === "medio") satPenalty += 1;
  satPenalty = Math.min(8, satPenalty);
  penalties += satPenalty;
  components.push({
    name: "risco_saturacao", weight: 8, value: -satPenalty, weighted: -satPenalty,
    data_available: true, source: "inferido", confidence: 0.6,
    note: satPenalty > 0 ? "Mercado com concorrencia" : "Baixa saturacao"
  });

  /* 11. Risco de politica publicitaria (penalty 0 to -10) */
  let policyPenalty = 0;
  if (offer.policy_risk === "alto") policyPenalty = 10;
  else if (offer.policy_risk === "medio") policyPenalty = 5;
  else policyPenalty = 0;
  if (offer.risk_flags.includes("saude_sem_comprovacao")) policyPenalty += 5;
  policyPenalty = Math.min(10, policyPenalty);
  penalties += policyPenalty;
  components.push({
    name: "risco_politica", weight: 10, value: -policyPenalty, weighted: -policyPenalty,
    data_available: true, source: "inferido", confidence: 0.65,
    note: policyPenalty > 0 ? "Restricoes de politica publicitaria" : "Sem restricoes"
  });

  total -= penalties;
  total = Math.max(0, Math.min(100, Math.round(total)));

  /* Confianca geral */
  let confidenceLevel = "alta";
  if (offer.evidence_confidence < 0.5 || missingData.length > 2) confidenceLevel = "baixa";
  else if (offer.evidence_confidence < 0.7 || missingData.length > 1) confidenceLevel = "media";

  /* Classificacao */
  let classification, classificationLabel;
  if (total >= 80) { classification = "strong_test"; classificationLabel = "Teste Forte"; }
  else if (total >= 60) { classification = "promising"; classificationLabel = "Promissora"; }
  else if (total >= 40) { classification = "needs_review"; classificationLabel = "Revisao Necessaria"; }
  else if (total >= 20) { classification = "weak"; classificationLabel = "Fraca"; }
  else { classification = "skip"; classificationLabel = "Pular"; }

  return {
    score_total: total,
    max_total: maxTotal,
    formula_version: "offer-score-v1.0",
    classification: classification,
    classification_label: classificationLabel,
    confidence: confidenceLevel,
    evidence_confidence: offer.evidence_confidence,
    data_missing: missingData,
    components: components,
    penalties: penalties,
    penalties_detail: {
      saturacao: satPenalty,
      politica: policyPenalty
    },
    offer_id: offer.id,
    product_name: offer.product_name
  };
}

function getScoreColor(score) {
  if (score >= 80) return "#4ade80";
  if (score >= 60) return "#60a5fa";
  if (score >= 40) return "#fbbf24";
  if (score >= 20) return "#fb923c";
  return "#f87171";
}

function getScoreBg(score) {
  if (score >= 80) return "rgba(74,222,128,0.15)";
  if (score >= 60) return "rgba(96,165,250,0.15)";
  if (score >= 40) return "rgba(251,191,36,0.15)";
  if (score >= 20) return "rgba(251,146,60,0.15)";
  return "rgba(248,113,113,0.15)";
}
