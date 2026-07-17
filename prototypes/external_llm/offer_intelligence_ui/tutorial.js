/* Offer Intelligence — Tutorial v1.0 */
/* Tour guiado sem dependencias. */

const Tutorial = (function() {
  'use strict';

  const STEPS = [
    {
      target: '#view-title',
      title: 'Visao Geral',
      text: 'Esta e a tela inicial. Aqui voce ve um resumo rapido de todas as ofertas disponiveis: quantas sao, a nota media, as melhores oportunidades e os alertas importantes.',
      view: 'dashboard'
    },
    {
      target: '#stats-summary',
      title: 'Indicadores',
      text: 'Estes numeros mostram o panorama geral: total de ofertas, nota media, quantas sao fortes e quantas estao crescendo. E um termometro rapido do estado atual.'
    },
    {
      target: '#top-offers-card',
      title: 'Melhores Ofertas',
      text: 'Aqui estao as ofertas com as notas mais altas. Clique em qualquer uma para ver os detalhes completos.'
    },
    {
      target: '#alerts-card',
      title: 'Alertas',
      text: 'Alertas importantes sobre mudancas nas ofertas: crescimento, declinio ou dados insuficientes. Fique de olho aqui.'
    },
    {
      target: '#trends-card',
      title: 'Tendencias',
      text: 'Ofertas que estao crescendo em procura. Uma seta para cima significa que mais pessoas estao procurando.'
    },
    {
      target: '.nav-item[data-view="radar"]',
      title: 'Radar de Ofertas',
      text: 'No Radar voce ve uma tabela completa com todas as ofertas. Pode filtrar por nicho, plataforma, status e nota. Clique em uma oferta para ver detalhes.',
      view: 'radar',
      pad: 10
    },
    {
      target: '#radar-table',
      title: 'Tabela de Ofertas',
      text: 'Cada linha e uma oferta. A coluna Score mostra a nota (0 a 100). Cores verdes sao notas altas, vermelhas sao notas baixas. Clique em qualquer linha para ver os detalhes.'
    },
    {
      target: '.score-cell',
      title: 'Score',
      text: 'O Score e a nota da oferta, de 0 a 100. Quanto maior, melhor. A cor ajuda a identificar rapidamente: verde e bom, amarelo e medio, vermelho e baixo.',
      pad: 8
    },
    {
      target: '.nav-item[data-view="detail"]',
      title: 'Detalhes',
      text: 'No Detalhe voce ve informacoes completas de uma oferta: preco, comissao, crescimento, riscos e o detalhamento do score.',
      view: 'detail'
    },
    {
      target: '.detail-score',
      title: 'Nota da Oferta',
      text: 'A nota principal aparece no topo. Abaixo dela, a classificacao (Teste Forte, Promissora, etc.) e a confianca nos dados.',
      pad: 10
    },
    {
      target: '.comp-list',
      title: 'Componentes do Score',
      text: 'Cada parte da nota e explicada aqui: crescimento, volume, comissao, etc. Barras mais cheias significam que aquele componente contribuiu bem para a nota.'
    },
    {
      target: '.nav-item[data-view="comparator"]',
      title: 'Comparador',
      text: 'No Comparador voce pode selecionar de 2 a 4 ofertas e ve-las lado a lado. Assim fica mais facil escolher a melhor.',
      view: 'comparator'
    },
    {
      target: '.comp-selector',
      title: 'Selecionar Ofertas',
      text: 'Escolha duas ou mais ofertas nos menus. O sistema mostra uma comparacao com score, crescimento, comissao e riscos lado a lado.'
    },
    {
      target: '.nav-item[data-view="analysis"]',
      title: 'Analise IA',
      text: 'A Analise IA explica os motivos da nota de uma oferta. Importante: esta e uma analise MOCK, nenhuma inteligencia artificial real foi chamada.',
      view: 'analysis'
    },
    {
      target: '#analysis-content',
      title: 'Resultado da Analise',
      text: 'A analise mostra pontos fortes, fracos, riscos e dados ausentes. Use isso para entender se vale a pena investir tempo em uma oferta.'
    },
    {
      target: '.nav-item[data-view="sources"]',
      title: 'Fontes',
      text: 'Em Fontes voce ve de onde vieram os dados de cada oferta. Cada informacao tem origem, data e nivel de confianca registrados.',
      view: 'sources'
    },
    {
      target: '.nav-item[data-view="monitoring"]',
      title: 'Monitoramento',
      text: 'No Monitoramento ficam todos os alertas: crescimento repentino, declinio, dados insuficientes. Filtre por severidade.',
      view: 'monitoring'
    },
    {
      target: '.nav-item[data-view="settings"]',
      title: 'Configuracoes',
      text: 'Nas Configuracoes voce pode alternar entre Modo Aprender e Modo Profissional, mudar o tema, a moeda e outras preferencias. Tudo fica salvo automaticamente.',
      view: 'settings'
    },
    {
      target: '.nav-item[data-view="academia"]',
      title: 'Academia Offer Intelligence',
      text: 'A Academia e um curso completo com 26 aulas para aprender a interpretar ofertas, graficos, riscos e decisoes passo a passo. Cada aula tem narracao, exercicios e correcao.',
      view: 'academia'
    }
  ];

  /* 19 steps total */

  let currentStep = 0;
  let isActive = false;
  let overlayEl = null;
  let popupEl = null;
  let onFinishCallback = null;

  function start(options) {
    if (overlayEl) return;
    onFinishCallback = options && options.onFinish ? options.onFinish : null;

    isActive = true;
    currentStep = 0;

    overlayEl = document.createElement('div');
    overlayEl.className = 'tutorial-overlay';
    overlayEl.setAttribute('role', 'dialog');
    overlayEl.setAttribute('aria-label', 'Tour guiado');
    document.body.appendChild(overlayEl);

    popupEl = document.createElement('div');
    popupEl.className = 'tutorial-popup';
    popupEl.innerHTML = _buildStepHTML();
    document.body.appendChild(popupEl);

    _highlightStep();
    _bindPopupEvents();

    overlayEl.addEventListener('click', _end);
    document.addEventListener('keydown', _keyHandler);
  }

  function _buildStepHTML() {
    const step = STEPS[currentStep];
    const total = STEPS.length;
    const pct = Math.round(((currentStep + 1) / total) * 100);
    return `
      <div class="tutorial-progress">
        <div class="tutorial-progress-bar" style="width:${pct}%"></div>
      </div>
      <div class="tutorial-step-info">Passo ${currentStep + 1} de ${total}</div>
      <h3 class="tutorial-title">${step.title}</h3>
      <p class="tutorial-text">${step.text}</p>
      <div class="tutorial-actions">
        <button class="tutorial-btn tutorial-btn-skip" data-action="skip">Pular</button>
        <div>
          ${currentStep > 0 ? '<button class="tutorial-btn" data-action="prev">Voltar</button>' : ''}
          <button class="tutorial-btn tutorial-btn-primary" data-action="${currentStep < total - 1 ? 'next' : 'finish'}">
            ${currentStep < total - 1 ? 'Proximo' : 'Concluir'}
          </button>
        </div>
      </div>
    `;
  }

  function _highlightStep() {
    const step = STEPS[currentStep];
    const el = document.querySelector(step.target);
    if (!el) return;

    /* Navigate to correct view if specified */
    if (step.view && typeof navigate === 'function') {
      navigate(step.view);
    }

    /* Remove previous highlights */
    document.querySelectorAll('.tutorial-highlight').forEach(e => e.classList.remove('tutorial-highlight'));

    /* Re-query after navigation */
    setTimeout(function() {
      const target = document.querySelector(step.target);
      if (!target) return;
      target.classList.add('tutorial-highlight');
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });

      if (popupEl) {
        popupEl.innerHTML = _buildStepHTML();
        _bindPopupEvents();
      }
    }, 100);
  }

  function _bindPopupEvents() {
    if (!popupEl) return;
    popupEl.querySelectorAll('[data-action]').forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const action = this.dataset.action;
        if (action === 'next') _next();
        else if (action === 'prev') _prev();
        else if (action === 'skip' || action === 'finish') _end();
      });
    });
  }

  function _next() {
    if (currentStep < STEPS.length - 1) {
      currentStep++;
      _highlightStep();
    } else {
      _end();
    }
  }

  function _prev() {
    if (currentStep > 0) {
      currentStep--;
      _highlightStep();
    }
  }

  function _keyHandler(e) {
    if (!isActive) return;
    if (e.key === 'Escape') _end();
    if (e.key === 'ArrowRight') _next();
    if (e.key === 'ArrowLeft') _prev();
  }

  function _end() {
    isActive = false;
    document.querySelectorAll('.tutorial-highlight').forEach(e => e.classList.remove('tutorial-highlight'));
    if (overlayEl) { overlayEl.remove(); overlayEl = null; }
    if (popupEl) { popupEl.remove(); popupEl = null; }
    document.removeEventListener('keydown', _keyHandler);
    try { localStorage.setItem('offer_intel_tutorial_done', 'true'); } catch(e) {}
    if (onFinishCallback) onFinishCallback();
  }

  function isDone() {
    try { return localStorage.getItem('offer_intel_tutorial_done') === 'true'; } catch(e) { return false; }
  }

  function resetDone() {
    try { localStorage.removeItem('offer_intel_tutorial_done'); } catch(e) {}
  }

  return { start, isDone, resetDone };
})();
