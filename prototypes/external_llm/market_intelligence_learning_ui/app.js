/* Market Intelligence — App v3.2 — INTERACTION-UNDERSTAND */
/* MARKET-INTELLIGENCE-INTERACTION-UNDERSTAND */
/* Sidebar layout, Modo Entender, tour, explicacoes, auditoria de botoes */
const App = (function() {
  var state = {
    currentView: 'overview',
    sources: [],
    segments: [],
    tools: [],
    strategies: [],
    claims: [],
    knowledgeCandidates: [],
    cards: [],
    experiments: [],
    patterns: [],
    softwareOpps: [],
    revenueClaims: [],
    learningLog: [],
    extractionsCache: {},
    mode: localStorage.getItem('mi_mode') || 'understand',
    expandedCards: {},
    searchTerm: '',
    understandActive: localStorage.getItem('mi_mode') !== 'professional',
    tourActive: false,
    tourStep: 0,
    tourVisible: false
  };

  function init() {
    _loadMockData();
    applyMode();
    _closeModalInternal();
    _ensureAllOverlaysClosed();
    window.addEventListener('popstate', function(e) {
      var v = e.state ? e.state.view : 'overview';
      state.currentView = v;
      _closeModalInternal();
      _renderView(v);
      _updateNavActive(v);
      _updateTopBarTitle(v);
    });
    _renderView('overview');
    _setupModalKeyboard();
    _setupTourKeyboard();
  }

  function _setupTourKeyboard() {
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && state.tourVisible) {
        _endTour();
        e.preventDefault();
      }
    });
  }

  function _loadMockData() {
    state.sources = MockData.buildSources();
    state.segments = MockData.buildSegments();
    state.tools = MockData.buildTools();
    state.strategies = MockData.buildStrategies();
    state.claims = MockData.buildClaims();
    state.knowledgeCandidates = MockData.buildKnowledgeCandidates();
    state.cards = MockData.buildCards();
    state.experiments = MockData.buildExperiments();
    state.patterns = MockData.buildPatterns();
    state.softwareOpps = MockData.buildSoftwareOpps();
    state.revenueClaims = MockData.buildRevenueClaims();
    state.learningLog = MockData.buildLearningLog();
  }

  function navigate(view) {
    state.currentView = view;
    state.searchTerm = '';
    history.pushState({ view: view }, '', '#' + view);
    localStorage.setItem('mi_nav', JSON.stringify(view));
    _closeModalInternal();
    _renderView(view);
    _updateNavActive(view);
    _updateTopBarTitle(view);
    closeDrawer();
  }

  function toggleSidebar() {
    var sb = document.getElementById('sidebar');
    if (!sb) return;
    sb.classList.toggle('collapsed');
    var btn = document.getElementById('sidebarToggle');
    if (btn) btn.textContent = sb.classList.contains('collapsed') ? '\u25B6' : '\u25C0';
  }

  function openDrawer() {
    var sb = document.getElementById('sidebar');
    var overlay = document.getElementById('drawerOverlay');
    if (sb) sb.classList.add('open');
    if (overlay) overlay.classList.remove('hidden');
  }

  function closeDrawer() {
    var sb = document.getElementById('sidebar');
    var overlay = document.getElementById('drawerOverlay');
    if (sb) sb.classList.remove('open');
    if (overlay) overlay.classList.add('hidden');
  }

  function _updateNavActive(view) {
    document.querySelectorAll('.sidebar-btn').forEach(function(b) {
      b.classList.toggle('active', b.dataset.view === view);
    });
  }

  function _updateTopBarTitle(view) {
    var el = document.getElementById('topBarTitle');
    if (!el) return;
    var labels = {
      overview: 'Visao Geral',
      inbox: 'Caixa de Entrada',
      new_source: 'Nova Fonte',
      transcripts: 'Transcricoes',
      visual_evidence: 'Evidencia Visual',
      extractions: 'Extracees',
      audit: 'Auditoria',
      knowledge: 'Knowledge Cards',
      experiments: 'Experimentos',
      patterns: 'Padroes de Mercado',
      tools: 'Ferramentas',
      software: 'Oportunidades de Software',
      learning: 'Aprendizados',
      employees: 'Funcionarios',
      capital: 'Alocacao de Capital',
      history: 'Historico',
      settings: 'Configuracoes'
    };
    el.textContent = labels[view] || 'Visao Geral';
    var modeEl = document.getElementById('topBarMode');
    if (modeEl) modeEl.textContent = state.mode === 'understand' ? 'Entender' : 'Profissional';
  }

  function _renderView(view) {
    var mc = document.getElementById('mainContent');
    if (!mc) return;
    _ensureAllOverlaysClosed();
    mc.innerHTML = '';
    switch(view) {
      case 'overview': _renderOverview(mc); break;
      case 'inbox': _renderInbox(mc); break;
      case 'new_source': _renderNewSource(mc); break;
      case 'transcripts': _renderTranscripts(mc); break;
      case 'visual_evidence': _renderVisualEvidence(mc); break;
      case 'extractions': _renderExtractions(mc); break;
      case 'audit': _renderAudit(mc); break;
      case 'knowledge': _renderKnowledge(mc); break;
      case 'experiments': _renderExperiments(mc); break;
      case 'patterns': _renderPatterns(mc); break;
      case 'tools': _renderTools(mc); break;
      case 'software': _renderSoftware(mc); break;
      case 'learning': _renderLearning(mc); break;
      case 'employees': _renderEmployees(mc); break;
      case 'capital': _renderCapital(mc); break;
      case 'history': _renderHistory(mc); break;
      case 'settings': _renderSettings(mc); break;
      default: _renderOverview(mc);
    }
    /* Add understand mode features */
    if (state.mode === 'understand') {
      setTimeout(function() {
        _addUnderstandButtons(view);
        _addWhyMattersUnderstand(view);
      }, 100);
    }
    /* Ensure all buttons are consistent */
    setTimeout(function() { _ensureButtonConsistency(); }, 50);
  }

  function _el(tag, attrs, children) {
    var e = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function(k) {
        if (k === 'className') e.className = attrs[k];
        else if (k === 'dataset') Object.assign(e.dataset, attrs[k]);
        else if (k.startsWith('on')) e[k] = attrs[k];
        else if (k !== 'key') e.setAttribute(k, attrs[k]);
      });
    }
    if (children) {
      if (typeof children === 'string') e.innerHTML = children;
      else if (Array.isArray(children)) children.forEach(function(c) { if (c) e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c); });
    }
    return e;
  }

  function _card(title, content, opts) {
    opts = opts || {};
    var c = _el('div', { className: 'card' + (opts.className ? ' ' + opts.className : '') });
    var h = _el('div', { className: 'card-header' });
    h.appendChild(_el('h3', {}, [title]));
    if (opts.action) h.appendChild(opts.action);
    c.appendChild(h);
    if (opts.badges) {
      var bWrap = _el('div', { style: 'margin-bottom:8px' });
      (opts.badges || []).forEach(function(bg) {
        bWrap.appendChild(_el('span', { className: 'badge badge-' + (bg.color || 'gray') }, [bg.text]));
      });
      c.appendChild(bWrap);
    }
    if (typeof content === 'string') { c.innerHTML += content; }
    else if (content) { content.forEach(function(ch) { if (ch) c.appendChild(typeof ch === 'string' ? document.createTextNode(ch) : ch); }); }
    return c;
  }

  function _badge(text, color) {
    return _el('span', { className: 'badge badge-' + (color || 'gray') }, [text || 'Nao informado']);
  }

  function _tag(text) {
    return _el('span', { className: 'tag' }, [text || '']);
  }

  function _progress(pct, color) {
    var w = _el('div', { className: 'progress-bar' });
    var val = Math.min(100, Math.max(0, pct || 0));
    var f = _el('div', { className: 'progress-fill' + (color ? ' ' + color : ''), style: 'width:' + val + '%' });
    w.appendChild(f);
    return w;
  }

  function _sectionTitle(text, subtitle) {
    var div = _el('div', {});
    div.appendChild(_el('h2', { className: 'section-title' }, [text]));
    if (subtitle) div.appendChild(_el('p', { className: 'section-subtitle' }, [subtitle]));
    return div;
  }

  function _disabledBtn(label) {
    return _el('button', { className: 'btn btn-sm btn-ghost', disabled: true, title: 'Nao implementado neste prototipo', style: 'opacity:0.5;cursor:not-allowed' }, [label + ' \u00D7']);
  }

  function _searchBar(placeholder) {
    var container = _el('div', { style: 'margin-bottom:12px' });
    var input = _el('input', { id: 'mi-search', type: 'text', placeholder: placeholder || 'Buscar...', style: 'max-width:400px' });
    input.onkeyup = function() {
      state.searchTerm = input.value.toLowerCase();
      _rerenderCurrentView();
    };
    container.appendChild(input);
    return container;
  }

  function _rerenderCurrentView() {
    _renderView(state.currentView);
  }

  function _matchesSearch(item, fields) {
    if (!state.searchTerm) return true;
    var t = state.searchTerm;
    return (fields || []).some(function(f) {
      var val = item[f];
      if (Array.isArray(val)) return val.some(function(v) { return String(v || '').toLowerCase().includes(t); });
      return String(val || '').toLowerCase().includes(t);
    });
  }

  function _toast(msg, type) {
    type = type || 'info';
    var existing = document.getElementById('mi-toast');
    if (existing) existing.remove();
    var bg = type === 'success' ? '#166534' : type === 'error' ? '#7f1d1d' : type === 'warning' ? '#92400e' : '#1e293b';
    var t = _el('div', { id: 'mi-toast', style: 'position:fixed;bottom:60px;right:20px;z-index:300;background:' + bg + ';color:white;padding:10px 18px;border-radius:8px;font-size:0.85rem;box-shadow:0 4px 12px rgba(0,0,0,0.5);max-width:400px;transition:opacity 0.3s' }, [msg]);
    document.body.appendChild(t);
    setTimeout(function() { t.style.opacity = '0'; setTimeout(function() { t.remove(); }, 500); }, 3000);
  }

  function _confirm(msg, cb) {
    if (!msg || !msg.trim()) { _closeModalInternal(); if (cb) cb(false); return; }
    var html = '<h3 id="app-modal-title" style="margin-bottom:12px">Confirmar</h3><p style="margin-bottom:16px;color:var(--text-secondary)">' + msg + '</p><div style="display:flex;gap:8px;justify-content:flex-end"><button class="btn btn-ghost" id="mi-confirm-no">Cancelar</button><button class="btn btn-danger" id="mi-confirm-yes">Confirmar</button></div>';
    openModal(html);
    document.getElementById('mi-confirm-no').onclick = function() { _closeModalInternal(); if (cb) cb(false); };
    document.getElementById('mi-confirm-yes').onclick = function() { _closeModalInternal(); if (cb) cb(true); };
  }

  function applyMode() {
    state.mode = localStorage.getItem('mi_mode') || 'understand';
    state.understandActive = state.mode === 'understand';
    var body = document.body;
    if (state.mode === 'professional') {
      body.style.setProperty('--bg-primary', '#0c0f15');
      body.style.setProperty('--bg-card', '#151a24');
      body.style.setProperty('--accent', '#6366f1');
      body.style.setProperty('--accent-hover', '#818cf8');
    } else {
      body.style.setProperty('--bg-primary', '#0a0e17');
      body.style.setProperty('--bg-card', '#1a2035');
      body.style.setProperty('--accent', '#3b82f6');
      body.style.setProperty('--accent-hover', '#60a5fa');
    }
    var modeEl = document.getElementById('topBarMode');
    if (modeEl) modeEl.textContent = state.mode === 'understand' ? 'Entender' : 'Profissional';
    /* Toggle "Explicar esta tela" button */
    var explainBtn = document.getElementById('explainThisBtn');
    if (explainBtn) {
      explainBtn.classList.toggle('visible', state.mode === 'understand');
    }
  }

  function toggleMode() {
    if (state.tourVisible) { _endTour(); }
    var newMode = state.mode === 'understand' ? 'professional' : 'understand';
    state.mode = newMode;
    localStorage.setItem('mi_mode', newMode);
    applyMode();
    _renderView(state.currentView);
    _toast('Modo: ' + (newMode === 'understand' ? 'Entender' : 'Profissional'), 'success');
  }

  /* ===== OVERVIEW ===== */
  function _renderOverview(mc) {
    var srcCount = state.sources.length;
    var segCount = state.segments.length;
    var cardCount = state.cards.length;
    var expCount = state.experiments.length;
    var activeExp = state.experiments.filter(function(e) { return e.status === 'active'; }).length;
    var proposedExp = state.experiments.filter(function(e) { return e.status === 'proposed'; }).length;
    var pausedExp = state.experiments.filter(function(e) { return e.status === 'paused'; }).length;
    var approvedCards = state.cards.filter(function(c) { return c.status === 'promoted'; }).length;
    var candidatesCount = state.knowledgeCandidates.length;
    var learningPending = state.learningLog.filter(function(l) { return !l.approved; }).length;
    var learningApproved = state.learningLog.filter(function(l) { return l.approved; }).length;
    var waitingTranscript = state.sources.filter(function(s) { return s.status === 'transcript_needed'; }).length;
    var readySources = state.sources.filter(function(s) { return s.status === 'transcript_available'; }).length;
    var auditTotal = 0;
    state.claims.forEach(function(c) {
      var a = ClaimAuditor.audit(c.text || c.claimed_value || '');
      auditTotal += a.total;
    });
    var avgAudit = state.claims.length ? Math.round(auditTotal / state.claims.length) : 0;
    var avgCardScore = state.cards.length ? Math.round(state.cards.reduce(function(s, c) { return s + KnowledgeEngine.promotionScore(c).total; }, 0) / state.cards.length) : 0;

    mc.appendChild(_sectionTitle('Visao Geral — Market Intelligence', 'Inteligencia e aprendizado de mercado. Nenhuma fonte vira instrucao automaticamente.'));

    /* Stat cards clicaveis */
    var grid = _el('div', { className: 'grid-4' });
    var statCard1 = _card('' + srcCount + ' Fontes', '<div class="stat-row"><span class="stat-label">Com transcricao</span><span class="stat-value">' + readySources + '</span></div><div class="stat-row"><span class="stat-label">Aguardando</span><span class="stat-value">' + waitingTranscript + '</span></div><div class="stat-row"><span class="stat-label">Segmentos extraidos</span><span class="stat-value">' + segCount + '</span></div>');
    statCard1.style.cursor = 'pointer';
    statCard1.onclick = function() { navigate('inbox'); };
    grid.appendChild(statCard1);

    var statCard2 = _card('Knowledge Cards', '<div class="stat-row"><span class="stat-label">Promovidos</span><span class="stat-value">' + approvedCards + '</span></div><div class="stat-row"><span class="stat-label">Candidatos</span><span class="stat-value">' + candidatesCount + '</span></div><div class="stat-row"><span class="stat-label">Score medio</span><span class="stat-value">' + avgCardScore + '%</span></div>');
    statCard2.style.cursor = 'pointer';
    statCard2.onclick = function() { navigate('knowledge'); };
    grid.appendChild(statCard2);

    var statCard3 = _card('Experimentos', '<div class="stat-row"><span class="stat-label">Ativos</span><span class="stat-value">' + activeExp + '</span></div><div class="stat-row"><span class="stat-label">Propostos</span><span class="stat-value">' + proposedExp + '</span></div><div class="stat-row"><span class="stat-label">Pausados</span><span class="stat-value">' + pausedExp + '</span></div>');
    statCard3.style.cursor = 'pointer';
    statCard3.onclick = function() { navigate('experiments'); };
    grid.appendChild(statCard3);

    var statCard4 = _card('Auditoria & Aprendizado', '<div class="stat-row"><span class="stat-label">Alegacoes</span><span class="stat-value">' + state.claims.length + '</span></div><div class="stat-row"><span class="stat-label">Score medio</span><span class="stat-value">' + avgAudit + '%</span></div><div class="stat-row"><span class="stat-label">Aprovados/Pendentes</span><span class="stat-value">' + learningApproved + '/' + learningPending + '</span></div>');
    statCard4.style.cursor = 'pointer';
    statCard4.onclick = function() { navigate('learning'); };
    grid.appendChild(statCard4);
    mc.appendChild(grid);

    /* Continuar fluxo shortcuts */
    var flowBar = _el('div', { style: 'margin:16px 0;display:flex;gap:8px;flex-wrap:wrap' });
    flowBar.appendChild(_el('button', { className: 'btn btn-sm btn-primary', onclick: 'App.navigate("new_source")' }, ['+ Nova Fonte']));
    flowBar.appendChild(_el('button', { className: 'btn btn-sm btn-ghost', onclick: 'App.navigate("inbox")' }, ['Ir para Caixa de Entrada']));
    flowBar.appendChild(_el('button', { className: 'btn btn-sm btn-ghost', onclick: 'App.navigate("capital")' }, ['Ver Alocacao de Capital']));
    if (learningPending > 0) {
      flowBar.appendChild(_el('button', { className: 'btn btn-sm btn-success', onclick: 'App.navigate("learning")' }, ['Aprovar Aprendizados (' + learningPending + ')']));
    }
    mc.appendChild(flowBar);

    /* Funnel chart */
    var funnelData = [
      { label: 'Fontes (' + srcCount + ')', value: srcCount, color: '#3b82f6' },
      { label: 'Segmentos (' + segCount + ')', value: segCount, color: '#6366f1' },
      { label: 'Extracoes', value: Math.max(1, Math.round(segCount * 0.6)), color: '#8b5cf6' },
      { label: 'Candidatos (' + candidatesCount + ')', value: candidatesCount + approvedCards || 1, color: '#a855f7' },
      { label: 'Cards (' + (approvedCards + candidatesCount) + ')', value: approvedCards + candidatesCount || 1, color: '#ec4899' },
      { label: 'Experimentos (' + expCount + ')', value: expCount || 1, color: '#14b8a6' }
    ];
    var funnelSection = _el('div', { className: 'card', style: 'margin-top:16px' });
    funnelSection.appendChild(_el('div', { className: 'card-header' }, [_el('h3', {}, ['Funil de Aprendizado'])]));
    var chartDiv = _el('div', { id: 'overviewFunnel', style: 'width:100%;max-width:500px;margin:auto' });
    funnelSection.appendChild(chartDiv);
    mc.appendChild(funnelSection);
    setTimeout(function() { Charts.create('overviewFunnel', { type: 'funnel', data: funnelData, label: 'Funil de aprendizado', w: 500, h: 220 }); }, 50);

    /* Padroes Top 5 */
    var pSection = _el('div', { style: 'margin-top:20px' });
    pSection.appendChild(_el('h3', { className: 'section-title', style: 'font-size:1rem' }, ['Padroes de Mercado — Top 5']));
    var sortedP = state.patterns.slice().sort(function(a, b) { return b.strength - a.strength; }).slice(0, 5);
    sortedP.forEach(function(p) {
      pSection.appendChild(_card(p.description, [_progress(p.strength), _el('div', { style: 'margin-top:4px;font-size:0.8rem;color:var(--text-muted)' }, ['Forca: ' + p.strength + '% | ' + p.sources.length + ' fontes | ' + p.tag])]));
    });
    mc.appendChild(pSection);

    /* Aprendizados Recentes */
    var lSection = _el('div', { style: 'margin-top:20px' });
    lSection.appendChild(_el('h3', { className: 'section-title', style: 'font-size:1rem' }, ['Aprendizados Recentes']));
    var recent = state.learningLog.slice(-4).reverse();
    recent.forEach(function(l) {
      lSection.appendChild(_card(l.title, [_el('p', {}, [l.observation]), _el('div', { style: 'margin-top:8px' }, [_badge(I18n.t(l.cardinality), l.cardinality === 'comprovado' ? 'green' : 'yellow'), _badge(l.approved ? 'Aprovado' : 'Nao aprovado', l.approved ? 'green' : 'gray')])]));
    });
    mc.appendChild(lSection);

    /* Resumo de alocacao */
    var alloc = CapitalAllocator.allocate(10000, state.experiments.filter(function(e) { return e.status !== 'paused'; }), 'moderate');
    mc.appendChild(_card('Alocacao de Capital (R$ 10.000 — Moderado)', '<div class="stat-row"><span class="stat-label">Alocado</span><span class="stat-value">R$ ' + (alloc.totalAllocated || 0) + '</span></div><div class="stat-row"><span class="stat-label">Reserva</span><span class="stat-value">R$ ' + (alloc.reserve || 0) + '</span></div><div class="stat-row"><span class="stat-label">Conclusao</span><span class="stat-value">' + (alloc.conclusion || 'Conclusao ainda nao registrada.') + '</span></div>'));
  }

  /* ===== INBOX ===== */
  function _renderInbox(mc) {
    mc.appendChild(_sectionTitle('Caixa de Entrada', 'Fontes recebidas aguardando processamento.'));
    mc.appendChild(_searchBar('Buscar fonte...'));

    var groups = {
      'transcript_needed': { label: 'Aguardando Transcricao', color: 'yellow' },
      'transcript_available': { label: 'Prontas', color: 'green' },
      'em_analise': { label: 'Em Analise', color: 'blue' },
      'aguardando_auditoria': { label: 'Aguardando Auditoria', color: 'purple' },
      'candidatas': { label: 'Candidatas', color: 'cyan' },
      'arquivadas': { label: 'Arquivadas', color: 'gray' }
    };

    var grouped = {};
    Object.keys(groups).forEach(function(k) { grouped[k] = []; });
    state.sources.filter(function(s) { return _matchesSearch(s, ['title', 'domain_tags']); }).forEach(function(s) {
      var g = s.status || 'transcript_needed';
      if (!grouped[g]) grouped[g] = [];
      grouped[g].push(s);
    });

    var order = ['transcript_needed', 'transcript_available', 'em_analise', 'aguardando_auditoria', 'candidatas', 'arquivadas'];
    order.forEach(function(g) {
      var items = grouped[g] || [];
      if (!items.length) return;
      var grpInfo = groups[g] || { label: I18n.t(g), color: 'gray' };
      mc.appendChild(_el('h3', { style: 'margin:16px 0 8px;font-size:0.95rem' }, [grpInfo.label + ' (' + items.length + ')']));
      items.forEach(function(s) {
        var badges = [_badge(I18n.t(s.status, grpInfo.label), grpInfo.color)];
        if (s.domain_tags && s.domain_tags.length) {
          s.domain_tags.forEach(function(t) { badges.push(_tag(t)); });
        }
        var segments = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
        var action;
        if (s.status === 'transcript_needed') {
          action = _el('button', { className: 'btn btn-sm btn-primary', onclick: '_transcribeSource("' + s.source_id + '")' }, ['Iniciar Transcricao']);
        } else if (s.status === 'transcript_available') {
          action = _el('button', { className: 'btn btn-sm btn-ghost', onclick: '_deleteSource("' + s.source_id + '")' }, ['Excluir']);
        } else {
          action = _disabledBtn('Excluir');
        }
        mc.appendChild(_card(s.title, [
          _el('p', { style: 'font-size:0.82rem;color:var(--text-secondary)' }, [s.type + ' | ' + (s.speaker_count || 'Nao informado') + ' participantes | ' + (s.date || 'Nao informado') + (s.duration_sec ? ' | ' + Math.round(s.duration_sec / 60) + 'min' : '')]),
          _el('div', { style: 'margin-top:4px;font-size:0.82rem;color:var(--text-muted)' }, [segments.length + ' segmentos | Credibilidade: ' + Math.round((s.credibility || 0) * 100) + '%' + (s.collecting_context ? ' | ' + s.collecting_context : '')]),
          _el('div', { style: 'margin-top:6px' }, badges)
        ], { action: action }));
      });
    });

    if (!state.searchTerm && state.sources.filter(function(s) { return s.status === 'transcript_needed'; }).length === 0 && state.sources.filter(function(s) { return s.status === 'transcript_available'; }).length === 0) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhuma fonte encontrada.']));
    }
  }

  window._transcribeSource = function(id) {
    var src = state.sources.find(function(s) { return s.source_id === id; });
    if (!src) return;
    src.status = 'transcript_available';
    /* FLUXO 2: ao transcrever, verificar se ha segmentos */
    var segs = state.segments.filter(function(s) { return s.source_id === id; });
    if (segs.length === 0) {
      state.segments.push({ segment_id: 'SEG-' + id + '-auto', source_id: id, start_time: 0, speaker: 'auto', text: 'Transcricao automatica Mock para ' + src.title });
    }
    _toast('Transcricao concluida (MOCK): ' + (src.title || 'Nao informado'), 'success');
    _rerenderCurrentView();
  };

  window._deleteSource = function(id) {
    _confirm('Excluir fonte e seus segmentos?', function(yes) {
      if (!yes) return;
      state.sources = state.sources.filter(function(s) { return s.source_id !== id; });
      state.segments = state.segments.filter(function(s) { return s.source_id !== id; });
      _toast('Fonte excluida', 'success');
      _rerenderCurrentView();
    });
  };

  /* ===== NEW SOURCE ===== */
  function _renderNewSource(mc) {
    mc.appendChild(_sectionTitle('Nova Fonte', 'Adicione uma fonte externa para processamento.'));
    mc.appendChild(_el('p', { style: 'margin-bottom:16px;font-size:0.85rem;color:var(--text-muted)' }, ['Nenhuma URL real sera acessada. Modo MOCK — os dados sao inseridos manualmente.']));
    var form = _el('div', { className: 'card', style: 'max-width:600px' });
    form.innerHTML = '<div class="form-group"><label>Titulo *</label><input id="mi-new-title" placeholder="Ex: Webinario sobre edicao"></div><div class="form-group"><label>URL (opcional)</label><input id="mi-new-url" placeholder="https://..."></div><div class="form-group"><label>Tipo</label><select id="mi-new-type"><option value="youtube_podcast">YouTube Podcast</option><option value="blog_post">Blog Post</option><option value="webinar">Webinario</option><option value="text">Texto</option></select></div><div class="form-group"><label>Nome do autor/fonte</label><input id="mi-new-author" placeholder="Nome do especialista ou autor"></div><div class="form-group"><label>Tags (virgula)</label><input id="mi-new-tags" placeholder="video, edicao, automacao"></div><div class="form-group"><label>Notas</label><textarea id="mi-new-notes" placeholder="Contexto de coleta..."></textarea></div>';
    var btn = _el('button', { className: 'btn btn-primary btn-lg', onclick: '_mockAddSource()' }, ['Adicionar Fonte (MOCK)']);
    form.appendChild(btn);
    mc.appendChild(form);
  }

  window._mockAddSource = function() {
    var title = document.getElementById('mi-new-title');
    var url = document.getElementById('mi-new-url');
    var type = document.getElementById('mi-new-type');
    var author = document.getElementById('mi-new-author');
    var tags = document.getElementById('mi-new-tags');
    var notes = document.getElementById('mi-new-notes');
    if (!title || !title.value.trim()) { _toast('Titulo obrigatorio', 'error'); return; }
    var newSrc = {
      source_id: 'SRC-' + String(state.sources.length + 1).padStart(3, '0'),
      title: title.value.trim(),
      type: type ? type.value : 'text',
      url: Security.sanitizeUrl(url ? url.value : ''),
      format: type && type.value === 'blog_post' ? 'text' : 'video',
      language: 'pt-BR',
      speaker_count: author && author.value.trim() ? 1 : 1,
      speakers: [{ role: 'autor', name: author && author.value.trim() ? author.value.trim() : 'User' }],
      duration_sec: 0,
      domain_tags: tags && tags.value ? tags.value.split(',').map(function(t) { return t.trim(); }) : [],
      date: new Date().toISOString().slice(0, 10),
      status: 'transcript_available',
      credibility: 0.3,
      transcript_path: '',
      collecting_context: notes ? notes.value.trim() : ''
    };
    state.sources.push(newSrc);
    /* FLUXO 1: adicionar segmentos mock para nova fonte */
    state.segments.push({ segment_id: 'SEG-' + newSrc.source_id + '-m1', source_id: newSrc.source_id, start_time: 0, speaker: 'auto', text: 'Conteudo transcrito automaticamente para ' + newSrc.title + '.' });
    state.segments.push({ segment_id: 'SEG-' + newSrc.source_id + '-m2', source_id: newSrc.source_id, start_time: 30, speaker: 'auto', text: 'Segundo segmento de exemplo para esta fonte.' });
    if (notes) notes.value = '';
    if (title) title.value = '';
    if (tags) tags.value = '';
    if (url) url.value = '';
    if (author) author.value = '';
    _toast('Fonte adicionada (MOCK): ' + newSrc.title, 'success');
  };

  /* ===== TRANSCRIPTS ===== */
  function _renderTranscripts(mc) {
    mc.appendChild(_sectionTitle('Transcricoes', 'Segmentos extraidos de cada fonte.'));
    mc.appendChild(_searchBar('Buscar na transcricao...'));
    var filtered = state.sources.filter(function(s) {
      if (!_matchesSearch(s, ['title', 'domain_tags'])) return false;
      if (state.searchTerm) {
        var segs = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
        return segs.some(function(seg) { return (seg.text || '').toLowerCase().includes(state.searchTerm); });
      }
      return true;
    });
    filtered.forEach(function(s) {
      if (s.status === 'transcript_needed') {
        mc.appendChild(_card(s.title, [_el('p', { style: 'color:var(--warning)' }, ['Transcricao pendente — aguardando conteudo real.'])], { action: _el('button', { className: 'btn btn-sm btn-primary', onclick: '_transcribeSource("' + s.source_id + '")' }, ['Transcrever']) }));
        return;
      }
      var segs = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
      if (state.searchTerm) segs = segs.filter(function(seg) { return (seg.text || '').toLowerCase().includes(state.searchTerm); });
      if (!segs.length) return;
      var se = _el('div', { className: 'card' });
      se.appendChild(_el('div', { className: 'card-header' }, [_el('h3', {}, [s.title]), _el('span', { style: 'font-size:0.78rem;color:var(--text-muted)' }, [segs.length + ' segmentos'])]));
      segs.forEach(function(seg) {
        var min = Math.floor((seg.start_time || 0) / 60);
        var sec = Math.floor((seg.start_time || 0) % 60);
        var time = String(min).padStart(2, '0') + ':' + String(sec).padStart(2, '0');
        se.appendChild(_el('div', { style: 'padding:4px 0;border-bottom:1px solid var(--border);font-size:0.85rem' }, [_el('span', { style: 'color:var(--text-muted);margin-right:8px' }, [time]), _el('strong', { style: 'color:var(--accent);margin-right:6px' }, [(seg.speaker || 'Nao informado') + ': ']), seg.text || 'Nao informado']));
      });
      mc.appendChild(se);
    });
  }

  /* ===== VISUAL EVIDENCE ===== */
  function _renderVisualEvidence(mc) {
    mc.appendChild(_sectionTitle('Evidencia Visual', 'Necessidades de evidencia visual detectadas nas transcricoes.'));
    mc.appendChild(_el('p', { style: 'margin-bottom:16px;color:var(--text-muted);font-size:0.85rem' }, ['O Visual Cue Detector analisa cada segmento em busca de mencoes que exijam comprovacao visual. Nenhuma captura de tela real e feita.']));

    /* Coletar cues reais do detector */
    var allCues = [];
    state.sources.forEach(function(s) {
      var segs = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
      var cues = VisualCueDetector.detect(segs);
      cues.forEach(function(c) {
        c.sourceTitle = s.title;
        allCues.push(c);
      });
    });

    /* Adicionar 6 cues MOCK inline garantidos */
    var mockCues = [
      { source_id: 'SRC-MOCK-1', sourceTitle: 'Webinario: Ferramentas de Edicao', timestamp: 120, text: 'Olha aqui na tela o painel de controle do VideoSprint. Aqui voce ve todas as metricas em tempo real.', trigger: 'olha aqui', classification: 'demonstracao', priority: 5, status: 'pending', suggested_before: 117, suggested_exact: 120, suggested_after: 123, screenshot_id: null },
      { source_id: 'SRC-MOCK-2', sourceTitle: 'Analise de Dados para Afiliados', timestamp: 340, text: 'Nesse grafico aqui da pra ver claramente o funil de conversao. Esse grafico mostra a queda de etapa para etapa.', trigger: 'esse grafico', classification: 'grafico', priority: 5, status: 'pending', suggested_before: 337, suggested_exact: 340, suggested_after: 343, screenshot_id: null },
      { source_id: 'SRC-MOCK-3', sourceTitle: 'Dashboard de Metricas', timestamp: 560, text: 'Vou mostrar pra voces o dashboard que a gente usa. Esse painel tem todas as metricas de campanha.', trigger: 'esse painel', classification: 'ferramenta', priority: 4, status: 'pending', suggested_before: 557, suggested_exact: 560, suggested_after: 563, screenshot_id: null },
      { source_id: 'SRC-MOCK-4', sourceTitle: 'Automacao com IA', timestamp: 780, text: 'Essa ferramenta aqui que a gente desenvolveu internamente. Ela automatiza todo o processo de edicao.', trigger: 'essa ferramenta', classification: 'ferramenta', priority: 5, status: 'pending', suggested_before: 777, suggested_exact: 780, suggested_after: 783, screenshot_id: null },
      { source_id: 'SRC-MOCK-5', sourceTitle: 'Planilha de Custos', timestamp: 1020, text: 'Nessa planilha a gente controla todos os custos de producao. Cada linha e um video produzido.', trigger: 'nessa planilha', classification: 'ferramenta', priority: 4, status: 'pending', suggested_before: 1017, suggested_exact: 1020, suggested_after: 1023, screenshot_id: null },
      { source_id: 'SRC-MOCK-6', sourceTitle: 'Demonstracao de Processo', timestamp: 1300, text: 'Vou abrir aqui o sistema pra mostrar como funciona o fluxo completo de aprovacao de conteudo.', trigger: 'vou abrir aqui', classification: 'demonstracao', priority: 4, status: 'pending', suggested_before: 1297, suggested_exact: 1300, suggested_after: 1303, screenshot_id: null }
    ];

    var combinedCues = allCues.concat(mockCues);

    if (combinedCues.length === 0) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhum cue visual detectado nas transcricoes.']));
      return;
    }

    /* Botao relatar evidencia MOCK */
    var toolbar = _el('div', { style: 'margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap' });
    toolbar.appendChild(_el('button', { className: 'btn btn-sm btn-primary', onclick: '_mockAddVisualEvidence()' }, ['Relacionar Evidencia MOCK']));
    toolbar.appendChild(_disabledBtn('Upload Local'));
    mc.appendChild(toolbar);

    mc.appendChild(_el('p', { style: 'margin-bottom:12px;color:var(--text-secondary);font-size:0.82rem' }, ['Total: ' + combinedCues.length + ' cues visuais (' + allCues.length + ' detectados, ' + mockCues.length + ' adicionados manualmente)']));

    combinedCues.forEach(function(cue) {
      var color = cue.priority >= 4 ? 'red' : cue.priority >= 3 ? 'yellow' : 'blue';
      var statusColor = cue.status === 'captured' ? 'green' : 'yellow';
      mc.appendChild(_card('Cue: ' + I18n.t(cue.classification, cue.classification), [
        _el('div', { style: 'margin-bottom:6px' }, [_badge(I18n.t(cue.classification, cue.classification), color), _badge('Prioridade ' + (cue.priority || 'Nao informado'), color), _badge(I18n.t(cue.status || 'pending', 'Pendente'), statusColor)]),
        _el('p', { style: 'font-size:0.85rem' }, ['"' + (cue.text || 'Nao informado').slice(0, 120) + ((cue.text || '').length > 120 ? '...' : '') + '"']),
        _el('div', { style: 'font-size:0.8rem;color:var(--text-muted);margin-top:4px' }, ['Fonte: ' + (cue.sourceTitle || cue.source_id || 'Nao informado') + ' | Timestamp: ' + Math.floor((cue.timestamp || 0) / 60) + ':' + String(Math.floor((cue.timestamp || 0) % 60)).padStart(2, '0')]),
        _el('div', { style: 'margin-top:8px;font-size:0.78rem;color:var(--text-secondary)' }, ['Trigger: "' + (cue.trigger || 'Nao informado') + '" | Sugerido: antes ' + Math.floor((cue.suggested_before || 0) / 60) + ':' + String(Math.floor((cue.suggested_before || 0) % 60)).padStart(2, '0') + ' | exato ' + Math.floor((cue.suggested_exact || 0) / 60) + ':' + String(Math.floor((cue.suggested_exact || 0) % 60)).padStart(2, '0')])
      ], { action: _el('button', { className: 'btn btn-sm btn-primary', onclick: '_captureCue("' + (cue.source_id || '') + '","' + (cue.segment_id || '') + '")' }, ['Capturar Screenshot MOCK']) }));
    });
  }

  window._mockAddVisualEvidence = function() {
    _toast('Evidencia visual MOCK adicionada a fila de captura.', 'success');
    _rerenderCurrentView();
  };

  window._captureCue = function(sourceId, segmentId) {
    _toast('Screenshot MOCK capturado para cue ' + (sourceId || 'desconhecido'), 'success');
  };

  /* ===== EXTRACTIONS ===== */
  function _renderExtractions(mc) {
    mc.appendChild(_sectionTitle('Extracees', 'Extracees deterministicas por regras. Nenhuma IA usada.'));
    mc.appendChild(_searchBar('Buscar extracao...'));
    var allExtractions = [];
    state.sources.forEach(function(s) {
      var segs = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
      var ex = ExtractionEngine.extractAll(segs, s.source_id);
      ex.forEach(function(e) { e.sourceTitle = s.title; });
      allExtractions = allExtractions.concat(ex);
    });
    if (state.searchTerm) {
      allExtractions = allExtractions.filter(function(ex) {
        return (ex.title || '').toLowerCase().includes(state.searchTerm) || (ex.text || '').toLowerCase().includes(state.searchTerm) || (ex.tags || []).some(function(t) { return (t || '').includes(state.searchTerm); });
      });
    }
    var groups = {};
    allExtractions.forEach(function(ex) {
      if (!groups[ex.type]) groups[ex.type] = [];
      groups[ex.type].push(ex);
    });
    var total = allExtractions.length;
    mc.appendChild(_el('p', { style: 'margin-bottom:16px;color:var(--text-muted);font-size:0.85rem' }, ['Total: ' + total + ' extracoes de ' + Object.keys(groups).length + ' tipos']));

    /* FLUXO 3: botao send to audit */
    var toolbar = _el('div', { style: 'margin-bottom:12px;display:flex;gap:8px' });
    toolbar.appendChild(_el('button', { className: 'btn btn-sm btn-primary', onclick: '_sendExtractionsToAudit()' }, ['Enviar para Auditoria (FLUXO 3)']));
    mc.appendChild(toolbar);

    if (!total) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhuma extracao encontrada.']));
      return;
    }
    Object.keys(groups).forEach(function(type) {
      var items = groups[type];
      mc.appendChild(_card(type + ' (' + items.length + ')', items.slice(0, 10).map(function(ex) {
        return _el('div', { style: 'padding:4px 0;border-bottom:1px solid var(--border);font-size:0.82rem' }, [
          _el('span', { style: 'color:var(--text-muted);margin-right:4px' }, ['[' + ((ex.tags || []).join(', ') || 'Nao informado') + ']']),
          _el('span', {}, [ex.title || 'Nao informado']),
          _el('div', { style: 'color:var(--text-secondary);margin-top:2px;font-size:0.78rem' }, ['"' + (ex.text || '').slice(0, 80) + ((ex.text || '').length > 80 ? '...' : '') + '"']),
          _el('div', { style: 'font-size:0.75rem;color:var(--text-muted)' }, ['Fonte: ' + (ex.sourceTitle || ex.source_id || 'Nao informado')])
        ]);
      }), { className: 'card' }));
    });
  }

  window._sendExtractionsToAudit = function() {
    /* FLUXO 3: simulate sending to audit - cria claims a partir das extracoes */
    var count = 0;
    state.sources.forEach(function(s) {
      var segs = state.segments.filter(function(seg) { return seg.source_id === s.source_id; });
      var ex = ExtractionEngine.extractAll(segs, s.source_id);
      ex.forEach(function(e) {
        if (e.type === 'RevenueClaim' && !state.claims.find(function(c) { return c.text === e.text && c.source_id === s.source_id; })) {
          state.claims.push({
            text: e.text || 'Alegacao financeira detectada',
            speaker: e.speaker || 'Nao informado',
            source_id: s.source_id,
            type: 'revenue',
            context: 'Extraido automaticamente de ' + s.title
          });
          count++;
        }
      });
    });
    _toast(count + ' alegacoes enviadas para auditoria (FLUXO 3)', 'success');
    _rerenderCurrentView();
  };

  /* ===== AUDIT ===== */
  function _renderAudit(mc) {
    mc.appendChild(_sectionTitle('Auditoria de Alegacoes', 'Score deterministico de credibilidade. Nenhuma alegacao e tratada como verdade.'));
    mc.appendChild(_searchBar('Buscar alegacao...'));
    var filtered = state.claims.filter(function(cl) {
      return _matchesSearch(cl, ['text', 'speaker', 'source_id', 'type']);
    });
    if (!filtered.length) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhuma alegacao encontrada. Use "Enviar para Auditoria" nas Extracoes.']));
      return;
    }
    filtered.forEach(function(cl) {
      var audit = ClaimAuditor.audit(cl.text || cl.claimed_value || '');
      var color = audit.total >= 70 ? 'green' : audit.total >= 50 ? 'yellow' : audit.total >= 30 ? 'red' : 'gray';
      var cls = I18n.t(audit.classification, audit.classification);
      mc.appendChild(_card((cl.text || 'Nao informado').slice(0, 80) + ((cl.text || '').length > 80 ? '...' : ''), [
        _el('div', { style: 'margin-top:8px' }, [_badge(cls, color)]),
        _progress(audit.total, color),
        _el('div', { style: 'margin-top:6px' }, [
          _el('span', { style: 'font-size:0.82rem;color:var(--text-secondary)' }, ['Score: ' + audit.total + '% | Fonte: ' + (cl.source_id || 'Nao informado') + ' | ' + (cl.speaker || 'Nao informado') + ' | Tipo: ' + (cl.type || 'Nao informado')]),
          audit.missing && audit.missing.length ? _el('div', { style: 'margin-top:4px;font-size:0.8rem;color:var(--danger)' }, ['Falta: ' + audit.missing.join(', ')]) : null
        ])
      ]));
    });
  }

  /* ===== KNOWLEDGE ===== */
  function _renderKnowledge(mc) {
    mc.appendChild(_sectionTitle('Knowledge Cards', 'Conhecimento organizacional promovido e candidatos. Total: ' + (state.knowledgeCandidates.length + state.cards.length)));
    mc.appendChild(_searchBar('Buscar card...'));
    var toolbar = _el('div', { style: 'margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap' });
    toolbar.appendChild(_el('button', { className: 'btn btn-sm btn-primary', onclick: '_openNewKnowledgeCard()' }, ['+ Novo Knowledge Card']));
    mc.appendChild(toolbar);

    /* Agrupar candidatos por status */
    var groups = { draft: [], review: [], promoted: [], rejected: [], archived: [] };
    state.knowledgeCandidates.filter(function(kc) { return _matchesSearch(kc, ['title', 'summary', 'hypothesis', 'departments']); }).forEach(function(kc) {
      var g = kc.status || 'draft';
      if (!groups[g]) groups[g] = [];
      groups[g].push(kc);
    });
    state.cards.filter(function(c) { return _matchesSearch(c, ['title', 'summary', 'departments']); }).forEach(function(c) {
      var g = c.status || 'promoted';
      if (!groups[g]) groups[g] = [];
      groups[g].push(c);
    });

    var groupOrder = ['draft', 'review', 'promoted', 'rejected', 'archived'];
    var groupLabels = { draft: 'Candidatos', review: 'Em Revisao', promoted: 'Validados / Promovidos', rejected: 'Rejeitados', archived: 'Arquivados' };
    var groupColors = { draft: 'yellow', review: 'blue', promoted: 'green', rejected: 'red', archived: 'gray' };

    groupOrder.forEach(function(g) {
      var items = groups[g] || [];
      if (!items.length) return;
      mc.appendChild(_el('h3', { style: 'margin:16px 0 8px;font-size:0.95rem' }, [(groupLabels[g] || I18n.t(g)) + ' (' + items.length + ')']));
      items.forEach(function(item) {
        var score = KnowledgeEngine.promotionScore(item);
        var val = KnowledgeEngine.validateCard(item);
        var isCandidate = item.status && item.status !== 'promoted';
        var badges = [_badge(I18n.t(item.status || 'draft'), groupColors[item.status] || 'gray'), _badge('Score ' + score.total + '%', score.total >= 70 ? 'green' : score.total >= 50 ? 'yellow' : 'red')];
        if (item.experimentable !== undefined) badges.push(_badge(item.experimentable ? 'Experimentavel' : 'Observacional', item.experimentable ? 'green' : 'yellow'));
        var actions = _el('div', { style: 'display:flex;gap:6px;flex-wrap:wrap;margin-top:8px' });
        actions.appendChild(_disabledBtn('Abrir'));
        if (isCandidate) {
          actions.appendChild(_el('button', { className: 'btn btn-sm btn-primary', onclick: '_promoteToCandidate("' + (item.card_id || item.title) + '")' }, ['Promover para Candidato']));
        }
        if (item.status === 'promoted' || g === 'promoted') {
          actions.appendChild(_el('button', { className: 'btn btn-sm btn-success', onclick: '_createExperimentFromCard("' + (item.card_id || item.title) + '")' }, ['Criar Experimento']));
        }
        actions.appendChild(_disabledBtn('Editar'));
        actions.appendChild(_disabledBtn('Revisar'));
        if (isCandidate) {
          actions.appendChild(_el('button', { className: 'btn btn-sm btn-danger', onclick: '_rejectCard("' + (item.card_id || item.title) + '")' }, ['Rejeitar']));
        }
        mc.appendChild(_card(item.title, [
          _el('div', { style: 'margin-bottom:6px' }, badges),
          _el('p', { style: 'font-size:0.85rem' }, [item.summary || 'Nao informado']),
          item.hypothesis ? _el('p', { style: 'font-size:0.82rem;color:var(--text-secondary)' }, ['Hipotese: ' + item.hypothesis]) : null,
          _el('div', { style: 'margin-top:4px;font-size:0.8rem;color:var(--text-muted)' }, [
            'Confianca: ' + Math.round((item.confidence || 0) * 100) + '% | ' + (item.sources || []).length + ' fontes | ' + ((item.departments || []).join(', ') || 'Nao informado')
          ]),
          (item.risks && item.risks.length) ? _el('div', { style: 'margin-top:4px;font-size:0.78rem;color:var(--warning)' }, ['Riscos: ' + item.risks.join(', ')]) : null,
          val && !val.valid ? _el('div', { style: 'margin-top:4px;color:var(--warning);font-size:0.78rem' }, ['Issues: ' + val.issues.join(', ')]) : null,
          item.approved_by ? _el('div', { style: 'margin-top:4px;font-size:0.75rem;color:var(--text-muted)' }, ['Aprovado por: ' + item.approved_by + ' em ' + ((item.approved_at || '').slice(0, 10) || 'Nao informado')]) : null,
          actions
        ]));
      });
    });
  }

  window._openNewKnowledgeCard = function() {
    var html = '<h3 id="app-modal-title" style="margin-bottom:16px">Novo Knowledge Card (MOCK)</h3>' +
      '<div class="form-group"><label>Titulo</label><input id="mi-kc-title" placeholder="Titulo do card"></div>' +
      '<div class="form-group"><label>Resumo</label><textarea id="mi-kc-summary" placeholder="Resumo do aprendizado"></textarea></div>' +
      '<div class="form-group"><label>Hipotese</label><textarea id="mi-kc-hypothesis" placeholder="Hipotese testavel"></textarea></div>' +
      '<div class="form-group"><label>Departamentos (virgula)</label><input id="mi-kc-depts" placeholder="video, affiliate_deals"></div>' +
      '<div class="form-group"><label>Riscos (virgula)</label><input id="mi-kc-risks" placeholder="Custo inicial, curva de aprendizado"></div>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:16px">' +
      '<button class="btn btn-ghost" onclick="App.closeModal()">Cancelar</button>' +
      '<button class="btn btn-primary" onclick="_saveNewKnowledgeCard()">Salvar Rascunho</button></div>';
    openModal(html);
  };

  window._saveNewKnowledgeCard = function() {
    var title = document.getElementById('mi-kc-title');
    var summary = document.getElementById('mi-kc-summary');
    var hypothesis = document.getElementById('mi-kc-hypothesis');
    var depts = document.getElementById('mi-kc-depts');
    var risks = document.getElementById('mi-kc-risks');
    if (!title || !title.value.trim()) { _toast('Titulo obrigatorio', 'error'); return; }
    var card = KnowledgeEngine.createCandidate(title.value.trim(), summary ? summary.value.trim() : '', null, null, hypothesis ? hypothesis.value.trim() : '');
    card.departments = depts && depts.value ? depts.value.split(',').map(function(d) { return d.trim(); }) : [];
    card.risks = risks && risks.value ? risks.value.split(',').map(function(r) { return r.trim(); }) : [];
    card.card_id = 'KC-' + String(state.cards.length + state.knowledgeCandidates.length + 1).padStart(3, '0');
    state.knowledgeCandidates.push(card);
    App.closeModal();
    _toast('Knowledge Card criado: ' + card.title, 'success');
    _rerenderCurrentView();
  };

  window._promoteToCandidate = function(id) {
    var item = state.knowledgeCandidates.find(function(kc) { return kc.card_id === id || kc.title === id; });
    if (!item) {
      var cardItem = state.cards.find(function(c) { return c.card_id === id || c.title === id; });
      if (cardItem) { _toast('Card ja promovido.', 'info'); return; }
      _toast('Item nao encontrado.', 'error'); return;
    }
    /* FLUXO 4: promove candidato */
    item.status = 'promoted';
    item.approved_by = 'Leandro';
    item.approved_at = new Date().toISOString();
    /* Mover para cards */
    if (!state.cards.find(function(c) { return c.card_id === item.card_id; })) {
      var newCard = JSON.parse(JSON.stringify(item));
      newCard.status = 'promoted';
      state.cards.push(newCard);
    }
    _toast('Candidato promovido: ' + (item.title || 'Nao informado'), 'success');
    _rerenderCurrentView();
  };

  window._rejectCard = function(id) {
    _confirm('Rejeitar este card?', function(yes) {
      if (!yes) return;
      var item = state.knowledgeCandidates.find(function(kc) { return kc.card_id === id || kc.title === id; });
      if (item) { item.status = 'rejected'; _toast('Card rejeitado.', 'success'); _rerenderCurrentView(); return; }
      var card = state.cards.find(function(c) { return c.card_id === id || c.title === id; });
      if (card) { card.status = 'rejected'; _toast('Card rejeitado.', 'success'); _rerenderCurrentView(); return; }
      _toast('Nao encontrado.', 'error');
    });
  };

  window._createExperimentFromCard = function(id) {
    /* FLUXO 5: cria experimento a partir do card */
    var card = state.cards.find(function(c) { return c.card_id === id || c.title === id; });
    if (!card) { _toast('Card nao encontrado.', 'error'); return; }
    var existing = state.experiments.find(function(e) { return e.knowledge_card_id === card.card_id; });
    if (existing) { _toast('Experimento ja existe para este card.', 'info'); return; }
    var exp = ExperimentEngine.create(card.card_id, card.hypothesis || 'Hipotese baseada em ' + card.title);
    exp.title = card.title;
    exp.duration_days = 30;
    exp.status = 'proposed';
    exp.risk = 'medio';
    exp.max_cost = 500;
    exp.primary_metric = 'conversao';
    exp.stop_condition = 'Resultado negativo';
    state.experiments.push(exp);
    card.experiment_id = exp.experiment_id;
    _toast('Experimento criado: ' + (card.title || 'Nao informado'), 'success');
    _rerenderCurrentView();
  };

  /* ===== EXPERIMENTS ===== */
  function _renderExperiments(mc) {
    mc.appendChild(_sectionTitle('Experimentos', 'Hipoteses sendo testadas. Nenhum experimento envolve dinheiro real.'));
    mc.appendChild(_searchBar('Buscar experimento...'));
    var filtered = state.experiments.filter(function(exp) { return _matchesSearch(exp, ['hypothesis', 'status', 'risk', 'primary_metric']); });
    if (!filtered.length) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhum experimento encontrado.']));
      return;
    }
    filtered.forEach(function(exp) {
      var statusColor = exp.status === 'active' ? 'green' : exp.status === 'proposed' ? 'yellow' : exp.status === 'completed' ? 'blue' : exp.status === 'paused' ? 'gray' : 'red';
      var valid = ExperimentEngine.isValid(exp);
      mc.appendChild(_card(exp.hypothesis || 'Hipotese nao definida', [
        _el('div', { style: 'margin-bottom:8px' }, [_badge(I18n.t(exp.status, exp.status), statusColor), exp.approved ? _badge('Aprovado', 'green') : _badge('Nao aprovado', 'gray')]),
        _el('div', { className: 'grid-2', style: 'font-size:0.82rem' }, [
          _el('div', {}, [_el('strong', {}, ['Metrica: ']), exp.primary_metric || 'Metrica ainda nao definida.']),
          _el('div', {}, [_el('strong', {}, ['Custo max: ']), exp.max_cost ? 'R$ ' + exp.max_cost : 'Custo ainda nao definido.']),
          _el('div', {}, [_el('strong', {}, ['Duracao: ']), (exp.duration_days || 'Nao informado') + ' dias']),
          _el('div', {}, [_el('strong', {}, ['Risco: ']), _badge(I18n.t(exp.risk, exp.risk), exp.risk === 'alto' ? 'red' : exp.risk === 'medio' ? 'yellow' : 'green')])
        ]),
        exp.conclusion ? _el('div', { style: 'margin-top:8px;padding:8px;background:var(--bg-primary);border-radius:4px;font-size:0.82rem' }, ['Conclusao: ' + exp.conclusion]) : _el('div', { style: 'margin-top:8px;font-size:0.78rem;color:var(--text-muted)' }, ['Conclusao ainda nao registrada.']),
        exp.knowledge_card_id ? _el('div', { style: 'margin-top:4px;font-size:0.75rem;color:var(--text-muted)' }, ['Knowledge Card: ' + exp.knowledge_card_id]) : null
      ], { action: valid ? null : _el('span', { style: 'color:var(--danger);font-size:0.78rem' }, ['Incompleto: ' + valid]) }));
    });
  }

  /* ===== PATTERNS ===== */
  function _renderPatterns(mc) {
    mc.appendChild(_sectionTitle('Padroes de Mercado', 'Padroes identificados por frequencia e fontes independentes. Total: ' + state.patterns.length));
    mc.appendChild(_searchBar('Buscar padrao...'));
    var sorted = state.patterns.slice().sort(function(a, b) { return b.strength - a.strength; });
    if (state.searchTerm) sorted = sorted.filter(function(p) { return (p.tag || '').includes(state.searchTerm) || (p.description || '').toLowerCase().includes(state.searchTerm); });
    sorted.forEach(function(p) {
      var color = p.strength >= 70 ? 'green' : p.strength >= 50 ? 'yellow' : 'gray';
      mc.appendChild(_card(p.description || 'Nao informado', [
        _el('div', { style: 'margin-bottom:6px' }, [_badge(p.tag, color)]),
        _progress(p.strength, color),
        _el('div', { style: 'margin-top:6px;font-size:0.82rem;color:var(--text-secondary)' }, ['Forca: ' + p.strength + '% | ' + p.sources.length + ' fontes | Tag: ' + (p.tag || 'Nao informado')])
      ]));
    });
  }

  /* ===== TOOLS ===== */
  function _renderTools(mc) {
    mc.appendChild(_sectionTitle('Ferramentas Descobertas', 'Ferramentas e plataformas mencionadas nas fontes. Total: ' + state.tools.length));
    mc.appendChild(_searchBar('Buscar ferramenta...'));
    var sorted = state.tools.slice().sort(function(a, b) { return b.frequency - a.frequency; });
    if (state.searchTerm) sorted = sorted.filter(function(t) { return (t.name || '').toLowerCase().includes(state.searchTerm) || (t.category || '').includes(state.searchTerm) || (t.notes || '').toLowerCase().includes(state.searchTerm); });
    sorted.forEach(function(t) {
      mc.appendChild(_card(t.name, [
        _el('span', { className: 'badge badge-blue' }, [t.category]),
        _el('div', { style: 'margin-top:6px;font-size:0.82rem' }, ['Citado ' + (t.frequency || 0) + 'x | ' + (t.sources || []).length + ' fontes']),
        _el('p', { style: 'margin-top:4px;color:var(--text-secondary);font-size:0.82rem' }, [t.notes || 'Nao informado'])
      ]));
    });
  }

  /* ===== SOFTWARE ===== */
  function _renderSoftware(mc) {
    mc.appendChild(_sectionTitle('Oportunidades de Software', 'Ideias de produtos baseadas em necessidades recorrentes do mercado. Total: ' + state.softwareOpps.length));
    mc.appendChild(_searchBar('Buscar oportunidade...'));
    var filtered = state.softwareOpps.filter(function(opp) { return _matchesSearch(opp, ['title', 'description']); });
    filtered.forEach(function(opp) {
      var score = SoftwareOpportunityEngine.score(opp);
      var color = score.total >= 70 ? 'green' : score.total >= 50 ? 'yellow' : 'red';
      mc.appendChild(_card(opp.title || 'Nao informado', [
        _el('p', {}, [opp.description || 'Nao informado']),
        _el('div', { style: 'margin:8px 0' }, [_progress(score.total, color)]),
        _el('div', { style: 'margin-bottom:6px' }, [_badge('Score: ' + score.total + '%', color)]),
        _el('div', { className: 'grid-3', style: 'font-size:0.82rem;margin-top:6px' }, [
          _el('div', {}, [_el('strong', {}, ['Frequencia: ']), (opp.frequency || 'Nao informado') + 'x']),
          _el('div', {}, [_el('strong', {}, ['Publico: ']), (opp.source_count || 'Nao informado') + ' fontes']),
          _el('div', {}, [_el('strong', {}, ['Intensidade: ']), (opp.intensity || 'Nao informado') + '/10']),
          _el('div', {}, [_el('strong', {}, ['Disposicao pagar: ']), (opp.payment_willingness || 'Nao informado')]),
          _el('div', {}, [_el('strong', {}, ['Complexidade: ']), (opp.complexity || 'Nao informado')]),
          _el('div', {}, [_el('strong', {}, ['Sinergia: ']), opp.synergy_with_factory ? 'Sim' : 'Nao'])
        ]),
        _el('div', { style: 'margin-top:6px;font-size:0.8rem;color:var(--text-muted)' }, [
          'Solucao: ' + (opp.description || 'Nao informado').slice(0, 80) + '...',
          ' | Dificuldade: ' + (opp.complexity || 'Nao informado'),
          ' | Risco: ' + I18n.t(opp.risk || 'medio', opp.risk)
        ]),
        opp.alternatives_exist ? _el('div', { style: 'margin-top:4px;font-size:0.78rem;color:var(--text-secondary)' }, ['Alternativas: ' + opp.alternatives_exist]) : null,
        _el('div', { style: 'margin-top:6px' }, [(opp.sources || []).map(function(s) { return _badge(s, 'blue'); })])
      ], { action: _disabledBtn('Ver Detalhes') }));
    });
    if (!filtered.length) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhuma oportunidade encontrada.']));
    }
  }

  /* ===== LEARNING ===== */
  function _renderLearning(mc) {
    mc.appendChild(_sectionTitle('Aprendizados Aprovados', 'Licoes extraidas e aprovadas. Nao confundir observacao com verdade.'));
    mc.appendChild(_searchBar('Buscar aprendizado...'));
    var approved = state.learningLog.filter(function(l) { return l.approved && _matchesSearch(l, ['title', 'observation']); });
    var pending = state.learningLog.filter(function(l) { return !l.approved && _matchesSearch(l, ['title', 'observation']); });
    if (pending.length) {
      mc.appendChild(_el('h3', { style: 'margin:16px 0 8px;font-size:0.95rem' }, ['Pendentes de Aprovacao (' + pending.length + ')']));
      pending.forEach(function(l) {
        mc.appendChild(_card(l.title, [
          _el('p', {}, [l.observation || 'Nao informado']),
          _el('div', { style: 'margin-top:8px;display:flex;gap:8px' }, [_badge(I18n.t(l.cardinality, l.cardinality), 'yellow'), _badge('Nao aprovado', 'gray')])
        ], { action: _el('button', { className: 'btn btn-sm btn-success', onclick: '_approveLearning("' + l.id + '")' }, ['Aprovar (FLUXO 6)']) }));
      });
    }
    mc.appendChild(_el('h3', { style: 'margin:16px 0 8px;font-size:0.95rem' }, ['Aprovados (' + approved.length + ')']));
    if (!approved.length && !pending.length) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhum aprendizado encontrado.']));
    } else if (!approved.length) {
      mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhum aprendizado aprovado ainda.']));
    }
    approved.forEach(function(l) {
      mc.appendChild(_card(l.title, [
        _el('p', {}, [l.observation || 'Nao informado']),
        _el('div', { style: 'margin-top:6px' }, [_badge(I18n.t(l.cardinality, l.cardinality), l.cardinality === 'comprovado' ? 'green' : 'yellow'), _badge('Aprovado', 'green')])
      ]));
    });
  }

  window._approveLearning = function(id) {
    var item = state.learningLog.find(function(l) { return l.id === id; });
    if (!item) return;
    _confirm('Aprovar aprendizado "' + (item.title || 'Nao informado') + '"?', function(yes) {
      if (!yes) return;
      item.approved = true;
      /* FLUXO 6: aprendizado aprovado */
      _toast('Aprendizado aprovado: ' + (item.title || 'Nao informado'), 'success');
      _rerenderCurrentView();
    });
  };

  /* ===== EMPLOYEES ===== */
  function _renderEmployees(mc) {
    mc.appendChild(_sectionTitle('Atualizacao de Funcionarios', 'Departamentos que seriam impactados por novos aprendizados. Nenhum funcionario real e alterado.'));
    mc.appendChild(_el('p', { style: 'margin-bottom:16px;color:var(--text-muted);font-size:0.85rem' }, ['Esta simulacao mostra quais departamentos seriam afetados se os Knowledge Cards e aprendizados fossem aplicados.']));
    var deps = [
      { name: 'Script Department', key: 'script', cards: state.cards.filter(function(c) { return (c.departments || []).includes('script'); }).length + state.knowledgeCandidates.filter(function(c) { return (c.departments || []).includes('script'); }).length, learnings: state.learningLog.filter(function(l) { return l.approved && (l.id === 'LL-005' || l.id === 'LL-007'); }).length },
      { name: 'Video Department', key: 'video', cards: state.cards.filter(function(c) { return (c.departments || []).includes('video'); }).length + state.knowledgeCandidates.filter(function(c) { return (c.departments || []).includes('video'); }).length, learnings: state.learningLog.filter(function(l) { return l.approved && l.id === 'LL-005'; }).length },
      { name: 'Affiliate Deals', key: 'affiliate_deals', cards: state.cards.filter(function(c) { return (c.departments || []).includes('affiliate_deals'); }).length + state.knowledgeCandidates.filter(function(c) { return (c.departments || []).includes('affiliate_deals'); }).length, learnings: state.learningLog.filter(function(l) { return l.approved && (l.id === 'LL-002' || l.id === 'LL-003' || l.id === 'LL-006'); }).length },
      { name: 'Strategy Intelligence', key: 'strategy_intelligence', cards: state.cards.filter(function(c) { return (c.departments || []).includes('strategy_intelligence'); }).length + state.knowledgeCandidates.filter(function(c) { return (c.departments || []).includes('strategy_intelligence'); }).length, learnings: state.learningLog.filter(function(l) { return l.approved && l.id === 'LL-007'; }).length }
    ];
    deps.forEach(function(d) {
      mc.appendChild(_card(d.name, [
        _el('div', { className: 'stat-row' }, [_el('span', { className: 'stat-label' }, ['Knowledge Cards + Candidatos']), _el('span', { className: 'stat-value' }, [String(d.cards)])]),
        _el('div', { className: 'stat-row' }, [_el('span', { className: 'stat-label' }, ['Aprendizados aprovados aplicaveis']), _el('span', { className: 'stat-value' }, [String(d.learnings)])]),
        _el('div', { style: 'margin-top:8px;font-size:0.82rem;color:var(--text-muted)' }, ['Atualizacao MOCK — nenhum funcionario real alterado.'])
      ]));
    });
  }

  /* ===== CAPITAL ===== */
  function _renderCapital(mc) {
    mc.appendChild(_sectionTitle('Alocacao de Capital', 'Simulacao de alocacao de orcamento para experimentos. Nenhum dinheiro real envolvido.'));
    mc.appendChild(_el('div', { className: 'form-group', style: 'max-width:300px;margin-bottom:16px' }, [
      _el('label', {}, ['Orcamento simulado (R$)']),
      _el('input', { id: 'mi-budget-input', type: 'number', value: '1000', style: 'max-width:200px' })
    ]));
    var budgetVal = 1000;
    var inputEl = document.getElementById('mi-budget-input');
    if (inputEl) budgetVal = parseFloat(inputEl.value) || 1000;

    var calcBtn = _el('button', { className: 'btn btn-primary btn-sm', onclick: '_calcCapital()', style: 'margin-bottom:16px' }, ['Calcular Carteira MOCK']);
    mc.appendChild(calcBtn);

    var profiles = [
      { key: 'conservative', label: 'Conservador (max 20% exposure, 60% reserva)' },
      { key: 'moderate', label: 'Moderado (max 40% exposure, 40% reserva)' },
      { key: 'exploratory', label: 'Exploratorio (max 60% exposure, 20% reserva)' }
    ];

    var eligibleExps = state.experiments.filter(function(e) { return e.status !== 'paused'; });

    var container = _el('div', { id: 'capitalProfiles' });
    profiles.forEach(function(p) {
      var alloc = CapitalAllocator.allocate(budgetVal, eligibleExps, p.key);
      var allocItems = alloc.allocations && alloc.allocations.length ? alloc.allocations.map(function(a) {
        return _el('div', { style: 'padding:2px 0;font-size:0.82rem;color:var(--text-secondary)' }, ['R$ ' + (a.allocated || 0) + ' — ' + ((a.title || 'Nao informado').slice(0, 60))]);
      }) : _el('p', { style: 'font-size:0.82rem;color:var(--text-muted)' }, ['Nenhum experimento atendeu aos criterios. Nao utilizar orcamento agora.']);
      var rejectedItems = alloc.rejected && alloc.rejected.length ? alloc.rejected.map(function(a) {
        return _el('div', { style: 'padding:2px 0;font-size:0.78rem;color:var(--danger)' }, ['Rejeitado: ' + (a.reason || 'Nao informado')]);
      }) : null;

      /* Donut chart for allocation */
      var chartId = 'capitalChart-' + p.key;
      var chartDiv = _el('div', { id: chartId, style: 'width:100%;max-width:250px;margin:8px auto' });

      container.appendChild(_card(p.label, [
        _el('div', { className: 'stat-row' }, [_el('span', { className: 'stat-label' }, ['Orcamento']), _el('span', { className: 'stat-value' }, ['R$ ' + budgetVal])]),
        _el('div', { className: 'stat-row' }, [_el('span', { className: 'stat-label' }, ['Alocado']), _el('span', { className: 'stat-value' }, ['R$ ' + (alloc.totalAllocated || 0)])]),
        _el('div', { className: 'stat-row' }, [_el('span', { className: 'stat-label' }, ['Reserva']), _el('span', { className: 'stat-value' }, ['R$ ' + (alloc.reserve || 0)])]),
        chartDiv,
        _el('div', { className: 'card-header', style: 'font-size:0.85rem;font-weight:600;margin-top:8px' }, ['Alocaes']),
        allocItems,
        rejectedItems ? _el('div', {}, [_el('div', { className: 'card-header', style: 'font-size:0.82rem;font-weight:600;margin-top:8px;color:var(--danger)' }, ['Rejeitados']), rejectedItems]) : null,
        _el('p', { style: 'margin-top:8px;font-size:0.82rem;color:var(--text-muted)' }, [alloc.conclusion || 'Conclusao ainda nao registrada.'])
      ]));

      setTimeout(function() {
        var cd = document.getElementById(chartId);
        if (cd) {
          var chartData = [
            { label: 'Alocado', value: alloc.totalAllocated || 1, color: '#3b82f6' },
            { label: 'Reserva', value: alloc.reserve || 1, color: '#8b5cf6' }
          ];
          if (alloc.allocations && alloc.allocations.length) {
            chartData = alloc.allocations.filter(function(a) { return a.allocated > 0; }).map(function(a, i) {
              var colors = ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#ec4899'];
              return { label: (a.title || 'Exp').slice(0, 15), value: a.allocated, color: colors[i % colors.length] };
            });
            var totalAlloc = chartData.reduce(function(s, d) { return s + d.value; }, 0);
            if (alloc.reserve > 0) chartData.push({ label: 'Reserva', value: alloc.reserve, color: '#64748b' });
            if (totalAlloc < budgetVal && alloc.reserve === 0) {
              chartData.push({ label: 'Nao alocado', value: budgetVal - totalAlloc, color: '#334155' });
            }
          }
          Charts.create(chartId, { type: 'donut', data: chartData, label: 'Alocacao ' + p.key, w: 250, h: 200 });
        }
      }, 100);
    });
    mc.appendChild(container);

    var recalc = _el('button', { className: 'btn btn-sm btn-ghost', onclick: '_recalcCapital()', style: 'margin-top:8px' }, ['Recalcular']);
    mc.appendChild(recalc);
  }

  window._calcCapital = function() {
    _rerenderCurrentView();
  };

  window._recalcCapital = function() {
    _rerenderCurrentView();
    _toast('Alocacao recalculada', 'success');
  };

  /* ===== HISTORY ===== */
  function _renderHistory(mc) {
    mc.appendChild(_sectionTitle('Historico', 'Registro de atividades do Market Intelligence.'));
    mc.appendChild(_searchBar('Buscar no historico...'));
    var events = [];
    state.cards.forEach(function(c) { events.push({ date: c.approved_at || c.created_at || new Date().toISOString(), text: 'Knowledge Card promovido: ' + (c.title || 'Nao informado'), type: 'card' }); });
    state.cards.forEach(function(c) { if (c.created_at) events.push({ date: c.created_at, text: 'Knowledge Card criado: ' + (c.title || 'Nao informado'), type: 'card_created' }); });
    state.experiments.forEach(function(e) { events.push({ date: e.created_at || new Date().toISOString(), text: 'Experimento ' + (e.status || 'Nao informado') + ': ' + ((e.hypothesis || e.title || '').slice(0, 60) || 'Nao informado'), type: 'experiment' }); });
    state.sources.forEach(function(s) { events.push({ date: (s.date || new Date().toISOString().slice(0, 10)) + 'T00:00:00Z', text: 'Fonte adicionada: ' + (s.title || 'Nao informado'), type: 'source' }); });
    state.learningLog.forEach(function(l) { if (l.approved) events.push({ date: new Date().toISOString(), text: 'Aprendizado aprovado: ' + (l.title || 'Nao informado'), type: 'learning' }); });
    events.sort(function(a, b) { return ((b.date || '') > (a.date || '') ? 1 : -1); });
    if (state.searchTerm) events = events.filter(function(ev) { return (ev.text || '').toLowerCase().includes(state.searchTerm); });
    if (!events.length) { mc.appendChild(_el('div', { className: 'empty-state' }, ['Nenhum evento registrado.'])); return; }
    events.slice(0, 60).forEach(function(ev) {
      var colorMap = { card: 'green', card_created: 'blue', experiment: 'cyan', source: 'gray', learning: 'purple' };
      var color = colorMap[ev.type] || 'gray';
      mc.appendChild(_card(((ev.date || '').slice(0, 10) || 'Nao informado') + ' — ' + (ev.type || 'Nao informado'), [
        _el('p', { style: 'font-size:0.85rem' }, [ev.text || 'Nao informado']),
        _el('span', { className: 'badge badge-' + color }, [ev.type || 'Nao informado'])
      ]));
    });
  }

  /* ===== SETTINGS ===== */
  function _renderSettings(mc) {
    mc.appendChild(_sectionTitle('Configuracoes', 'Preferencias do Market Intelligence.'));
    mc.appendChild(_card('Modo de Exibicao', [
      _el('div', { style: 'display:flex;align-items:center;gap:12px' }, [
        _el('span', { style: 'font-size:0.85rem' }, ['Modo atual: ' + (state.mode === 'understand' ? 'Entender' : 'Profissional')]),
        _el('button', { className: 'btn btn-sm btn-ghost', onclick: 'App.toggleMode()' }, ['Alternar para ' + (state.mode === 'understand' ? 'Profissional' : 'Entender')])
      ]),
      _el('p', { style: 'margin-top:8px;font-size:0.78rem;color:var(--text-muted)' }, ['Entender: tons azuis, explicativo. Profissional: tons indigo, compacto.'])
    ]));
    mc.appendChild(_card('Armazenamento Local', [
      _el('p', { style: 'margin-bottom:8px;font-size:0.85rem' }, ['Dados mock carregados: ' + state.sources.length + ' fontes, ' + state.segments.length + ' segmentos, ' + state.tools.length + ' ferramentas, ' + state.cards.length + ' cards, ' + state.experiments.length + ' experimentos.']),
      _el('p', { style: 'font-size:0.78rem;color:var(--text-muted)' }, ['Tudo em memoria — nada persiste no servidor. Use export/import via Storage.']),
      _el('div', { style: 'margin-top:12px;display:flex;gap:8px;flex-wrap:wrap' }, [
        _el('button', { className: 'btn btn-sm btn-primary', onclick: '_exportData()' }, ['Exportar Dados']),
        _el('button', { className: 'btn btn-sm btn-ghost', onclick: '_importData()' }, ['Importar Dados']),
        _el('button', { className: 'btn btn-sm btn-danger', onclick: '_resetAll()' }, ['Resetar Dados'])
      ])
    ]));
    mc.appendChild(_card('Narracao Local', [
      _el('p', { style: 'font-size:0.85rem;margin-bottom:8px' }, ['Testar narracao speechSynthesis do navegador.']),
      _el('div', { style: 'display:flex;gap:8px' }, [
        _el('button', { className: 'btn btn-sm btn-primary', onclick: 'Narration.speak && Narration.speak("Teste de narracao do Market Intelligence. Modo " + (App.getState().mode === "understand" ? "Entender" : "Profissional"))' }, ['Testar Voz']),
        _el('button', { className: 'btn btn-sm btn-ghost', onclick: 'Narration.stop && Narration.stop()' }, ['Parar'])
      ]),
      _el('p', { style: 'margin-top:8px;font-size:0.78rem;color:var(--text-muted)' }, ['Narration.isSupported: ' + (typeof Narration !== 'undefined' && Narration.isSupported())])
    ]));
    mc.appendChild(_card('Sobre', [
      _el('p', { style: 'font-size:0.85rem' }, ['Market Intelligence — Prototipo Operacional Isolado']),
      _el('p', { style: 'font-size:0.82rem;color:var(--text-muted)' }, ['Versao: 3.1 — MODALFIX-3 | 14 motores deterministicos | 17 views | Sidebar Layout']),
      _el('p', { style: 'font-size:0.82rem;color:var(--text-muted)' }, ['Nao usar dados para decisoes reais. Nao fingir que IA executou tarefa.']),
      _el('p', { style: 'font-size:0.82rem;color:var(--text-muted)' }, ['MOCK | Nao integrado ao core | AI Content Factory'])
    ]));
  }

  window._exportData = function() {
    var data = JSON.stringify(state, null, 2);
    var blob = new Blob([data], { type: 'application/json' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'market_intelligence_data_' + new Date().toISOString().slice(0, 10) + '.json'; a.click();
    _toast('Dados exportados', 'success');
  };

  window._importData = function() {
    var input = document.getElementById('workspace-import-input');
    if (!input) {
      var newInput = document.createElement('input');
      newInput.type = 'file'; newInput.accept = 'application/json,.json';
      newInput.style.display = 'none';
      document.body.appendChild(newInput);
      input = newInput;
    }
    input.value = '';
    input.onchange = function(e) {
      var file = e.target.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function(ev) {
        try {
          var imported = JSON.parse(ev.target.result);
          if (imported.sources) state.sources = imported.sources;
          if (imported.segments) state.segments = imported.segments;
          if (imported.cards) state.cards = imported.cards;
          if (imported.experiments) state.experiments = imported.experiments;
          if (imported.knowledgeCandidates) state.knowledgeCandidates = imported.knowledgeCandidates;
          if (imported.learningLog) state.learningLog = imported.learningLog;
          if (imported.tools) state.tools = imported.tools;
          if (imported.patterns) state.patterns = imported.patterns;
          if (imported.softwareOpps) state.softwareOpps = imported.softwareOpps;
          _rerenderCurrentView();
          _toast('Dados importados com sucesso.', 'success');
        } catch(e) {
          _toast('Erro ao importar: ' + e.message, 'error');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  window._resetAll = function() {
    _confirm('Resetar todos os dados para o estado MOCK original? As alteracoes serao perdidas.', function(yes) {
      if (!yes) return;
      _loadMockData();
      _rerenderCurrentView();
      _toast('Dados resetados para o estado MOCK original.', 'success');
    });
  };

  /* ===== MODAL - MODALFIX-3 ===== */
  function _closeModalInternal() {
    var overlay = document.getElementById('app-modal-overlay');
    var modal = document.getElementById('app-modal');
    if (overlay) {
      overlay.setAttribute('hidden', '');
      overlay.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('inert', '');
      overlay.classList.remove('is-open');
      overlay.style.display = '';
    }
    if (modal) {
      modal.innerHTML = '';
    }
    document.body.style.overflow = '';
    document.body.style.pointerEvents = '';
    _modalOpen = false;
    if (window.console) console.log('[MI] Modal fechado');
  }

  function openModal(html) {
    var overlay = document.getElementById('app-modal-overlay');
    var modal = document.getElementById('app-modal');
    if (!overlay || !modal) return;
    if (!html || typeof html !== 'string') {
      if (window.console) console.warn('[MI] openModal: conteudo ausente ou invalido');
      _toast('Nao foi possivel abrir esta janela.', 'error');
      return;
    }
    var clean = html.trim();
    if (!clean) {
      if (window.console) console.warn('[MI] openModal: conteudo vazio');
      _toast('Nao foi possivel abrir esta janela.', 'error');
      return;
    }
    if (!clean.includes('<h3') && !clean.includes('<h2') && !clean.includes('<h1') && !clean.includes('<p')) {
      if (window.console) console.warn('[MI] openModal: conteudo sem titulo ou paragrafo');
      _toast('Conteudo invalido.', 'error');
      return;
    }
    if (!clean.includes('Cancelar') && !clean.includes('Fechar') && !clean.includes('fechar')) {
      if (window.console) console.warn('[MI] openModal: sem botao de fechar');
      _toast('Conteudo invalido.', 'error');
      return;
    }
    modal.innerHTML = clean;
    overlay.removeAttribute('hidden');
    overlay.removeAttribute('inert');
    overlay.setAttribute('aria-hidden', 'false');
    overlay.classList.add('is-open');
    overlay.style.display = '';
    document.body.style.overflow = 'hidden';
    document.body.style.pointerEvents = '';
    _modalOpen = true;
    state._lastFocused = document.activeElement;
    var firstBtn = modal.querySelector('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (firstBtn) setTimeout(function() { firstBtn.focus(); }, 50);
    if (window.console) console.log('[MI] Modal aberto');
  }

  function closeModal() {
    _closeModalInternal();
    if (state._lastFocused && state._lastFocused.focus) {
      try { state._lastFocused.focus(); } catch(e) {}
      state._lastFocused = null;
    }
  }

  function _setupModalKeyboard() {
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && _modalOpen) {
        closeModal();
        e.preventDefault();
      }
    });
  }

  function _ensureAllOverlaysClosed() {
    var overlay = document.getElementById('app-modal-overlay');
    if (!overlay) return;
    if (!overlay.classList.contains('is-open')) {
      overlay.setAttribute('hidden', '');
      overlay.setAttribute('aria-hidden', 'true');
      overlay.setAttribute('inert', '');
      overlay.classList.remove('is-open');
      if (overlay.style.display) overlay.style.display = '';
    }
    var modal = document.getElementById('app-modal');
    if (modal) {
      if (!modal.innerHTML || modal.innerHTML.trim() === '<') {
        modal.innerHTML = '';
      }
    }
    if (_modalOpen) {
      var checkContent = document.getElementById('app-modal');
      if (!checkContent || !checkContent.innerHTML.trim()) {
        _closeModalInternal();
      }
    }
  }

  /* ===== EXPLANATION TEXTS ===== */
  var EXPLANATIONS = {
    fonts: 'Mostra quantos conteudos entraram no sistema para analise.',
    segmentos: 'Uma transcricao e dividida em pequenos trechos para que cada informacao seja analisada separadamente.',
    extracoes: 'Sao ferramentas, estrategias, numeros ou alegacoes identificados dentro das transcricoes.',
    knowledge_candidate: 'E uma informacao que parece util, mas ainda nao foi aprovada como conhecimento da fabrica.',
    knowledge_card: 'E uma ficha organizada com fonte, evidencia, riscos e possivel aplicacao.',
    experimento: 'E um teste pequeno criado para descobrir se uma ideia realmente funciona.',
    auditoria: 'Verifica o que esta faltando antes de acreditar em uma afirmacao.',
    score: 'E uma nota calculada por regras. Nao significa que a informacao seja verdadeira.',
    padrao_mercado: 'E uma ideia ou pratica que apareceu em varias fontes diferentes.',
    alocar_capital: 'E simular quanto poderia ser reservado para cada teste. Nenhum dinheiro real e movimentado.',
    funcionarios: 'Mostra quais departamentos poderiam receber um aprendizado aprovado. Nenhum funcionario real e alterado.',
    funil: 'Mostra como o conhecimento e filtrado: da fonte bruta ate o experimento aprovado.',
    carteira: 'Simulacao de alocacao de orcamento para experimentos. Nenhum dinheiro real envolvido.'
  };

  var TOUR_DEFS = {
    overview: [
      { selector: '.grid-4', text: 'Estas sao as fontes que entraram no sistema. Cada card mostra metricas importantes.', highlight: 'card' },
      { selector: '#overviewFunnel', text: 'O funil mostra como o conhecimento e filtrado: da fonte bruta ate o experimento aprovado.', highlight: 'container' },
      { selector: '#mainContent .card:nth-child(5)', text: 'Das informacoes encontradas, apenas parte virou candidata a conhecimento.', highlight: 'card' },
      { selector: '#mainContent .card:nth-child(6)', text: 'Experimentos sao criados somente para ideias que merecem um teste controlado.', highlight: 'card' }
    ],
    inbox: [
      { selector: '#mainContent h3', text: 'A Caixa de Entrada agrupa fontes por status. Cada fonte precisa ser processada.', highlight: 'element' },
      { selector: '#mi-search', text: 'Use a busca para encontrar fontes especificas rapidamente.', highlight: 'element' },
      { selector: '.btn-primary', text: 'Clique em "Iniciar Transcricao" para processar uma fonte pendente.', highlight: 'button' }
    ],
    extractions: [
      { selector: '.section-title', text: 'Extracoes sao ferramentas, estrategias ou alegacoes identificadas nas transcricoes.', highlight: 'element' },
      { selector: '.btn-primary', text: 'Envie extracoes para auditoria para validar sua credibilidade.', highlight: 'button' }
    ],
    audit: [
      { selector: '.section-title', text: 'Auditoria verifica o que esta faltando antes de acreditar em uma afirmacao.', highlight: 'element' },
      { selector: '.card', text: 'Cada alegacao recebe um score baseado em 9 criterios deterministicos.', highlight: 'card' }
    ],
    knowledge: [
      { selector: '.section-title', text: 'Knowledge Cards sao fichas organizadas com fonte, evidencia e riscos.', highlight: 'element' },
      { selector: '.btn-primary', text: 'Crie novos cards ou promova candidatos existentes.', highlight: 'button' }
    ],
    experiments: [
      { selector: '.section-title', text: 'Experimentos sao testes controlados para descobrir se uma ideia funciona.', highlight: 'element' },
      { selector: '.card', text: 'Cada experimento tem metrica, custo, duracao e criterios de sucesso/parada.', highlight: 'card' }
    ],
    patterns: [
      { selector: '.section-title', text: 'Padroes de Mercado sao ideias que apareceram em varias fontes diferentes.', highlight: 'element' },
      { selector: '.card', text: 'A forca do padrao e calculada por frequencia e numero de fontes independentes.', highlight: 'card' }
    ],
    tools: [
      { selector: '.section-title', text: 'Ferramentas mencionadas nas fontes, com frequencia e categoria.', highlight: 'element' }
    ],
    software: [
      { selector: '.section-title', text: 'Oportunidades de software baseadas em necessidades recorrentes do mercado.', highlight: 'element' }
    ],
    learning: [
      { selector: '.section-title', text: 'Licoes extraidas e aprovadas. Nao confundir observacao com verdade.', highlight: 'element' },
      { selector: '.card', text: 'Aprendizados pendentes precisam de aprovacao antes de virarem conhecimento.', highlight: 'card' }
    ],
    employees: [
      { selector: '.section-title', text: 'Mostra quais departamentos seriam afetados por novos aprendizados.', highlight: 'element' },
      { selector: '.card', text: 'Nenhum funcionario real e alterado. E apenas uma simulacao.', highlight: 'card' }
    ],
    capital: [
      { selector: '.section-title', text: 'Simulacao de alocacao de orcamento para experimentos.', highlight: 'element' },
      { selector: '#capitalProfiles', text: 'Tres perfis de alocacao: Conservador, Moderado e Exploratorio.', highlight: 'container' },
      { selector: '#capitalProfiles .card', text: 'O sistema manteve parte do orcamento em reserva porque os experimentos ainda tem evidencias fracas.', highlight: 'card' }
    ],
    history: [
      { selector: '.section-title', text: 'Registro de atividades do Market Intelligence.', highlight: 'element' }
    ],
    settings: [
      { selector: '.section-title', text: 'Preferencias do Market Intelligence.', highlight: 'element' }
    ],
    transcripts: [
      { selector: '.section-title', text: 'Segmentos extraidos de cada fonte com timestamp e speaker.', highlight: 'element' },
      { selector: '.card', text: 'Cada segmento e um trecho da transcricao original.', highlight: 'card' }
    ],
    visual_evidence: [
      { selector: '.section-title', text: 'Necessidades de evidencia visual detectadas nas transcricoes.', highlight: 'element' },
      { selector: '.card', text: 'Cada cue visual mostra o que precisa ser capturado como prova.', highlight: 'card' }
    ],
    new_source: [
      { selector: '.section-title', text: 'Adicione fontes externas para processamento.', highlight: 'element' }
    ]
  };

  var WHY_MATTERS = {
    fonts: 'As fontes sao a materia-prima do conhecimento. Sem fontes, nao ha analise.',
    auditoria: 'Toda afirmacao precisa ser verificada antes de virar conhecimento. Uma alegacao sem auditoria e apenas opiniao.',
    funil: 'Das 52 extracoes, apenas 12 viraram candidatos. Isso mostra que a maior parte do conteudo bruto foi filtrada.',
    alocacao: 'O sistema manteve parte do orcamento em reserva porque os experimentos ainda tem evidencias fracas.',
    experimento: 'Esta hipotese ainda nao pode ser promovida porque o resultado esta ausente ou inconclusivo.',
    knowledge_card: 'Esta informacao continua como candidata porque ainda precisa de mais fonte, contexto ou teste.',
    extracoes: 'As extracoes sao o primeiro nivel de organizacao. Elas separam o que e relevante do que e propaganda.',
    capital: 'Alocar capital simulado ajuda a priorizar experimentos sem arriscar dinheiro real.',
    score: 'O score e um indicador calculado por regras deterministicas. Um score alto nao significa que a informacao seja verdadeira.'
  };

  function _addWhyMattersUnderstand(view) {
    if (state.mode !== 'understand') return;
    var mainEl = document.getElementById('mainContent');
    if (!mainEl) return;
    var cards = mainEl.querySelectorAll('.card');
    if (!cards.length) return;
    var mattersMap = {
      overview: { key: 'fontes', check: function(c) { return (c.querySelector('.stat-label') || {}).textContent === 'Com transcricao' || ((c.querySelector('h3') || {}).textContent || '').includes('Fontes'); } },
      audit: { key: 'auditoria', check: function(c) { return true; } },
      extractions: { key: 'extracoes', check: function(c) { return true; } },
      knowledge: { key: 'knowledge_card', check: function(c) { return ((c.querySelector('h3') || {}).textContent || '').includes('Candidatos') || ((c.querySelector('h3') || {}).textContent || '').includes('Em Revisao'); } },
      experiments: { key: 'experimento', check: function(c) { return ((c.querySelector('h3') || {}).textContent || '').includes('Proposto'); } },
      capital: { key: 'alocacao', check: function(c) { return true; } },
      inbox: { key: 'fontes', check: function(c) { return true; } }
    };
    var m = mattersMap[view];
    if (!m) return;
    var lastCard = cards[cards.length - 1];
    if (!lastCard.querySelector('.why-matters-container')) {
      _addWhyMatters(lastCard, m.key);
    }
  }
  function _addUnderstandHelp(target, explanationKey) {
    var btn = document.createElement('button');
    btn.className = 'understand-help-btn';
    btn.textContent = '?';
    btn.title = 'Clique para entender';
    var tip = document.createElement('div');
    tip.className = 'understand-tooltip';
    tip.textContent = EXPLANATIONS[explanationKey] || explanationKey;
    target.style.position = 'relative';
    target.appendChild(btn);
    target.appendChild(tip);
    btn.onclick = function(e) {
      e.stopPropagation();
      var allTips = document.querySelectorAll('.understand-tooltip.show');
      allTips.forEach(function(t) { t.classList.remove('show'); });
      tip.classList.toggle('show');
      setTimeout(function() { tip.classList.remove('show'); }, 4000);
    };
  }

  function _addWhyMatters(container, key) {
    var text = WHY_MATTERS[key];
    if (!text) return;
    var div = document.createElement('div');
    div.className = 'why-matters-container';
    div.textContent = 'Por que isso importa? ' + text;
    container.appendChild(div);
  }

  function _addUnderstandButtons(view) {
    if (state.mode !== 'understand') return;
    /* Adicionar botoes de ajuda nos elementos-chave de cada view */
    var mainEl = document.getElementById('mainContent');
    if (!mainEl) return;
    var sectionTitles = mainEl.querySelectorAll('.section-title');
    sectionTitles.forEach(function(t) {
      if (t.querySelector('.understand-help-btn')) return;
      var key = view;
      if (view === 'overview' || view === 'inbox' || view === 'transcripts') key = view;
      _addUnderstandHelp(t.parentNode, key);
    });
    /* Adicionar explicacoes em metricas */
    var statLabels = mainEl.querySelectorAll('.stat-label');
    statLabels.forEach(function(l) {
      var txt = (l.textContent || '').toLowerCase();
      if (txt.includes('fonte') || txt.includes('segmento')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'fonts'); }
      else if (txt.includes('extra')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'extracoes'); }
      else if (txt.includes('score')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'score'); }
      else if (txt.includes('reserva') || txt.includes('alocad')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'alocar_capital'); }
      else if (txt.includes('experiment')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'experimento'); }
      else if (txt.includes('audit')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'auditoria'); }
      else if (txt.includes('card') || txt.includes('promovid')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'knowledge_card'); }
      else if (txt.includes('candidat')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'knowledge_candidate'); }
      else if (txt.includes('padrao') || txt.includes('forca')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'padrao_mercado'); }
      else if (txt.includes('funcionario') || txt.includes('departament')) { if (!l.parentNode.querySelector('.understand-help-btn')) _addUnderstandHelp(l.parentNode, 'funcionarios'); }
    });
  }

  /* ===== TOUR SYSTEM ===== */
  function startTour() {
    if (state.tourVisible) return;
    var defs = TOUR_DEFS[state.currentView] || TOUR_DEFS.overview;
    if (!defs || !defs.length) {
      _toast('Nenhum tour disponivel para esta tela.', 'info');
      return;
    }
    state.tourStep = 0;
    state.tourActive = true;
    state.tourVisible = true;
    _renderTourStep(defs);
  }

  function _renderTourStep(defs) {
    if (!defs || state.tourStep >= defs.length) {
      _endTour();
      return;
    }
    var step = defs[state.tourStep];
    /* Remover tour anterior */
    var existing = document.getElementById('tourContainer');
    if (existing) existing.remove();

    var container = document.createElement('div');
    container.id = 'tourContainer';
    container.className = 'tour-overlay active';

    /* Backdrop */
    var backdrop = document.createElement('div');
    backdrop.className = 'tour-backdrop';
    container.appendChild(backdrop);
    backdrop.onclick = function() { _endTour(); };

    /* Tentar encontrar o elemento alvo */
    var targetEl = document.querySelector(step.selector);
    if (targetEl) {
      var rect = targetEl.getBoundingClientRect();
      var highlight = document.createElement('div');
      highlight.className = 'tour-highlight';
      highlight.style.left = (rect.left - 8) + 'px';
      highlight.style.top = (rect.top - 8) + 'px';
      highlight.style.width = (rect.width + 16) + 'px';
      highlight.style.height = (rect.height + 16) + 'px';
      container.appendChild(highlight);
    }

    /* Tour card */
    var card = document.createElement('div');
    card.className = 'tour-card';
    card.style.left = '50%';
    card.style.top = '50%';
    card.style.transform = 'translate(-50%, -50%)';
    card.style.maxWidth = '420px';

    var indicator = document.createElement('div');
    indicator.className = 'tour-step-indicator';
    indicator.textContent = 'Etapa ' + (state.tourStep + 1) + ' de ' + defs.length;
    card.appendChild(indicator);

    var text = document.createElement('p');
    text.textContent = step.text;
    card.appendChild(text);

    /* Actions */
    var actions = document.createElement('div');
    actions.className = 'tour-card-actions';
    if (state.tourStep > 0) {
      var prevBtn = document.createElement('button');
      prevBtn.className = 'btn btn-sm btn-ghost';
      prevBtn.textContent = 'Voltar';
      prevBtn.onclick = function(e) { e.stopPropagation(); state.tourStep--; _renderTourStep(defs); };
      actions.appendChild(prevBtn);
    }
    var repeatBtn = document.createElement('button');
    repeatBtn.className = 'btn btn-sm btn-ghost';
    repeatBtn.textContent = 'Repetir';
    repeatBtn.onclick = function(e) { e.stopPropagation(); _speakTourStep(step); };
    actions.appendChild(repeatBtn);

    var closeBtn = document.createElement('button');
    closeBtn.className = 'btn btn-sm btn-danger';
    closeBtn.textContent = 'Fechar';
    closeBtn.onclick = function(e) { e.stopPropagation(); _endTour(); };
    actions.appendChild(closeBtn);

    var nextBtn = document.createElement('button');
    nextBtn.className = 'btn btn-sm btn-primary';
    nextBtn.textContent = state.tourStep < defs.length - 1 ? 'Proximo' : 'Concluir';
    nextBtn.onclick = function(e) { e.stopPropagation(); state.tourStep++; _renderTourStep(defs); };
    actions.appendChild(nextBtn);
    card.appendChild(actions);

    /* Narration bar */
    var narrBar = document.createElement('div');
    narrBar.className = 'tour-narration-bar';
    narrBar.innerHTML = '<span>Narracao:</span>';
    var listenBtn = document.createElement('button');
    listenBtn.className = 'btn btn-sm btn-ghost';
    listenBtn.textContent = 'Ouvir';
    listenBtn.onclick = function(e) { e.stopPropagation(); _speakTourStep(step); };
    narrBar.appendChild(listenBtn);
    var pauseBtn = document.createElement('button');
    pauseBtn.className = 'btn btn-sm btn-ghost';
    pauseBtn.textContent = 'Pausar';
    pauseBtn.onclick = function(e) { e.stopPropagation(); Narration.pause(); };
    narrBar.appendChild(pauseBtn);
    var resumeBtn = document.createElement('button');
    resumeBtn.className = 'btn btn-sm btn-ghost';
    resumeBtn.textContent = 'Continuar';
    resumeBtn.onclick = function(e) { e.stopPropagation(); Narration.resume(); };
    narrBar.appendChild(resumeBtn);
    var stopNarrBtn = document.createElement('button');
    stopNarrBtn.className = 'btn btn-sm btn-ghost';
    stopNarrBtn.textContent = 'Parar';
    stopNarrBtn.onclick = function(e) { e.stopPropagation(); Narration.stop(); };
    narrBar.appendChild(stopNarrBtn);
    /* Speed selector */
    var speedLabel = document.createElement('span');
    speedLabel.textContent = 'Vel:';
    narrBar.appendChild(speedLabel);
    var speeds = Narration.getSpeeds ? Narration.getSpeeds() : [0.75, 1, 1.25];
    speeds.forEach(function(s) {
      var spdBtn = document.createElement('button');
      spdBtn.textContent = s + 'x';
      spdBtn.className = Narration.getSpeed && Narration.getSpeed() === s ? 'active' : '';
      spdBtn.onclick = function(e) { e.stopPropagation(); Narration.setSpeed(s); var allBtns = narrBar.querySelectorAll('button'); allBtns.forEach(function(b) { b.classList.remove('active'); }); spdBtn.classList.add('active'); };
      narrBar.appendChild(spdBtn);
    });
    var note = document.createElement('div');
    note.className = 'tour-narration-note';
    note.textContent = 'Narracao local do navegador. Nenhum servico externo foi chamado.' + (Narration.hasVoice && !Narration.hasVoice() ? ' (voz pt-BR nao disponivel)' : '');
    narrBar.appendChild(note);
    card.appendChild(narrBar);

    container.appendChild(card);
    document.body.appendChild(container);
  }

  function _speakTourStep(step) {
    if (Narration.isSupported && Narration.speak) {
      Narration.speak(step.text);
    } else {
      _toast('Narracao nao disponivel neste navegador.', 'warning');
    }
  }

  function _endTour() {
    state.tourActive = false;
    state.tourVisible = false;
    state.tourStep = 0;
    var existing = document.getElementById('tourContainer');
    if (existing) existing.remove();
    Narration.stop();
  }

  /* ===== PATCH: ensure all buttons have behavior ===== */
  function _ensureButtonConsistency() {
    /* Verificar e corrigir botoes que podem estar quebrados */
    /* Os botoes _disabledBtn ja estao corretos - o padrao de onclick via atributo HTML pode falhar */
    var allButtons = document.querySelectorAll('button[onclick]');
    allButtons.forEach(function(btn) {
      var onclickVal = btn.getAttribute('onclick');
      if (!onclickVal || onclickVal.trim() === '') {
        btn.disabled = true;
        btn.title = 'Nao implementado neste prototipo';
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
      }
    });
  }

  var _modalOpen = false;

  return {
    init: init,
    navigate: navigate,
    toggleMode: toggleMode,
    toggleSidebar: toggleSidebar,
    openDrawer: openDrawer,
    closeDrawer: closeDrawer,
    openModal: openModal,
    closeModal: closeModal,
    startTour: startTour,
    getState: function() { return state; },
    _rerenderCurrentView: _rerenderCurrentView
  };
})();

document.addEventListener('DOMContentLoaded', function() { App.init(); });
