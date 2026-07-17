/* Offer Intelligence — Beginner Mode v1.0 */
/* Modo Aprender vs Profissional. Explicacoes simples e diagnosticos. */

const BeginnerMode = (function() {
  'use strict';

  function isBeginner() {
    try {
      const s = localStorage.getItem('offer_intel_beginner_mode');
      return s !== 'false';
    } catch(e) { return true; }
  }

  function setMode(beginner) {
    try { localStorage.setItem('offer_intel_beginner_mode', beginner ? 'true' : 'false'); } catch(e) {}
    document.body.classList.toggle('beginner-mode', beginner);
    document.body.classList.toggle('professional-mode', !beginner);
    const toggle = document.getElementById('mode-toggle');
    if (toggle) {
      toggle.textContent = beginner ? 'Modo Profissional' : 'Modo Aprender';
      toggle.title = beginner ? 'Alternar para o modo profissional' : 'Alternar para o modo aprender';
    }
  }

  function toggle() {
    setMode(!isBeginner());
  }

  function init() {
    setMode(isBeginner());
  }

  /* Tooltip helper: adds data-tooltip to elements */
  function addTooltip(el, text) {
    if (!el) return;
    el.setAttribute('data-tooltip', text);
    el.classList.add('has-tooltip');
  }

  /* Simple explanation block */
  function createExplanationBlock(field, value, extra) {
    const text = getSimpleExplanation(field);
    if (!text) return '';
    return '<div class="simple-explanation"><span class="explanation-icon">?</span><span class="explanation-text">' + text + '</span></div>';
  }

  /* One-liner offer summary */
  function oneLiner(offer) {
    const s = calculateScore(offer);
    const parts = [];
    if (s.score_total >= 80) parts.push('Esta oferta tem uma nota excelente');
    else if (s.score_total >= 60) parts.push('Esta oferta e promissora');
    else if (s.score_total >= 40) parts.push('Esta oferta precisa de revisao');
    else parts.push('Esta oferta nao apresenta sinais fortes');

    if (offer.growth_90d >= 50) parts.push('esta crescendo rapido');
    else if (offer.growth_90d >= 20) parts.push('esta crescendo moderadamente');

    if (offer.commission_percent >= 50) parts.push('paga uma comissao alta');
    else if (offer.commission_percent >= 30) parts.push('paga uma comissao boa');

    if (offer.search_volume >= 10000) parts.push('e tem um publico grande');
    else if (offer.search_volume >= 2000) parts.push('e tem um publico moderado');
    else parts.push('mas o publico ainda e pequeno');

    if (offer.evidence_confidence < 0.6) parts.push('(atencao: dados com confianca baixa)');

    return parts.join(', ') + '.';
  }

  /* Why this score */
  function scoreReasons(offer) {
    const score = calculateScore(offer);
    const positives = [];
    const negatives = [];
    let biggestPositive = '';
    let biggestNegative = '';
    let maxPosWeight = 0;
    let maxNegWeight = 0;

    score.components.forEach(c => {
      const pct = c.weight > 0 ? Math.round((c.weighted / c.weight) * 100) : 0;
      if (pct >= 70 && c.weighted > 0) {
        positives.push(c.note);
        if (c.weighted > maxPosWeight) {
          maxPosWeight = c.weighted;
          biggestPositive = c.note;
        }
      } else if (pct < 40 && c.data_available && c.weight > 0) {
        negatives.push(c.note);
        const loss = c.weight - c.weighted;
        if (loss > maxNegWeight) {
          maxNegWeight = loss;
          biggestNegative = c.note;
        }
      }
    });

    const missingData = score.data_missing;
    const mainRisk = score.penalties_detail.saturacao >= score.penalties_detail.politica
      ? 'Saturacao: perdeu ' + score.penalties_detail.saturacao + ' pontos'
      : 'Politica: perdeu ' + score.penalties_detail.politica + ' pontos';

    const needsConfirm = missingData.length > 0 ? missingData[0] : 'Nenhum dado critico faltando';

    return {
      positives: positives.slice(0, 3),
      negatives: negatives.slice(0, 3),
      biggestPositive: biggestPositive,
      biggestNegative: biggestNegative,
      mainRisk: mainRisk,
      needsConfirm: needsConfirm,
      componentCount: score.components.length,
      totalScore: score.score_total,
      missingData: missingData
    };
  }

  function askModeAfterAcademia() {
    if (!confirm('Deseja continuar no Modo Aprender ou voltar ao Modo Profissional?')) {
      setMode(false);
    }
  }

  function enableBeginnerForAcademia() {
    if (!isBeginner()) {
      setMode(true);
    }
  }

  return {
    isBeginner,
    setMode,
    toggle,
    init,
    addTooltip,
    createExplanationBlock,
    oneLiner,
    scoreReasons,
    askModeAfterAcademia,
    enableBeginnerForAcademia
  };
})();
