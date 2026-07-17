/* Offer Intelligence — App v1.0 */
/* SPA com 9 areas. Nenhuma dependencia externa. */

(function() {
  'use strict';

  /* ===== STATE ===== */
  const state = {
    currentView: 'dashboard',
    selectedDetail: null,
    selectedAnalysis: null,
    selectedSources: null,
    compSelection: [null, null, null, null],
    settings: Object.assign({}, DEFAULT_SETTINGS),
    sortBy: 'score_total',
    sortDesc: true,
    filters: { niche: '', platform: '', status: '', scoreRange: '' },
    alertFilter: ''
  };

  /* ===== PERSISTENCE ===== */
  function loadSettings() {
    try {
      const saved = localStorage.getItem('offer_intel_settings');
      if (saved) {
        const parsed = JSON.parse(saved);
        Object.assign(state.settings, parsed);
      }
    } catch(e) { /* ignore */ }
    applySettings();
  }

  function saveSettings() {
    try {
      localStorage.setItem('offer_intel_settings', JSON.stringify(state.settings));
    } catch(e) { /* ignore */ }
    applySettings();
  }

  function applySettings() {
    const s = state.settings;
    document.body.classList.toggle('light', s.theme === 'light');
    document.body.classList.toggle('compact', s.density === 'compact');
    document.getElementById('set-theme').value = s.theme;
    document.getElementById('set-density').value = s.density;
    document.getElementById('set-currency').value = s.currency;
    document.getElementById('set-rows').value = String(s.rows_per_page);
    document.getElementById('set-confidence').value = String(s.min_confidence);
    document.getElementById('confidence-label').textContent = String(s.min_confidence);
    document.getElementById('set-advanced').checked = s.show_advanced;
  }

  /* ===== NAVIGATION ===== */
  function navigate(view) {
    state.currentView = view;
    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.view === view);
    });
    document.querySelectorAll('.view').forEach(el => {
      el.classList.toggle('active', el.id === 'view-' + view);
    });
    const titles = {
      dashboard: 'Visao Geral',
      radar: 'Radar de Ofertas',
      detail: 'Detalhe da Oferta',
      comparator: 'Comparador',
      analysis: 'Analise IA',
      sources: 'Fontes e Evidencias',
      monitoring: 'Monitoramento',
      academia: 'Academia Offer Intelligence',
      'academia-lesson': 'Aula',
      settings: 'Configuracoes'
    };
    document.getElementById('view-title').textContent = titles[view] || 'Offer Intelligence';
    document.getElementById('offer-count').textContent = OFFERS.length + ' ofertas';
    renderView(view);
  }

  function renderView(view) {
    switch(view) {
      case 'dashboard': renderDashboard(); break;
      case 'radar': renderRadar(); break;
      case 'detail': renderDetail(); break;
      case 'comparator': renderComparator(); break;
      case 'analysis': renderAnalysis(); break;
      case 'sources': renderSources(); break;
      case 'monitoring': renderMonitoring(); break;
      case 'academia': renderAcademia(); break;
      case 'academia-lesson': renderAcademiaLesson(); break;
    }
  }

  /* ===== UTILITY ===== */
  function fmtPrice(val, currency) {
    const c = currency || state.settings.currency;
    const prefix = c === 'USD' ? '$' : 'R$';
    return prefix + ' ' + val.toFixed(2).replace('.', ',');
  }

  function pct(val) { return val + '%'; }

  function scoreColor(s) {
    if (s >= 80) return 'var(--score-strong)';
    if (s >= 60) return 'var(--score-promising)';
    if (s >= 40) return 'var(--score-review)';
    if (s >= 20) return 'var(--score-weak)';
    return 'var(--score-skip)';
  }

  function scoreBg(s) {
    if (s >= 80) return 'rgba(74,222,128,0.15)';
    if (s >= 60) return 'rgba(96,165,250,0.15)';
    if (s >= 40) return 'rgba(251,191,36,0.15)';
    if (s >= 20) return 'rgba(251,146,60,0.15)';
    return 'rgba(248,113,113,0.15)';
  }

  function statusLabel(s) {
    const map = {
      growing: 'Crescendo',
      stable: 'Estavel',
      declining: 'Declinio',
      insufficient_data: 'Dados Insuf.'
    };
    return map[s] || s;
  }

  function statusClass(s) {
    return 'status-' + s;
  }

  function severityIcon(sev) {
    const map = { critical: '\u26A0\uFE0F', warning: '\u26A0', positive: '\u2705', info: '\u2139\uFE0F' };
    return map[sev] || '\u2139\uFE0F';
  }

  function daysAgo(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 86400000);
    if (diff === 0) return 'hoje';
    if (diff === 1) return '1 dia';
    return diff + ' dias';
  }

  function getFilteredOffers() {
    let list = OFFERS;
    const f = state.filters;
    if (f.niche) list = list.filter(o => o.niche === f.niche);
    if (f.platform) list = list.filter(o => o.platform === f.platform);
    if (f.status) list = list.filter(o => o.status === f.status);
    if (f.scoreRange) {
      const [min, max] = f.scoreRange.split('-').map(Number);
      list = list.filter(o => {
        const s = calculateScore(o).score_total;
        return s >= min && (max ? s <= max : true);
      });
    }
    const minConf = parseFloat(state.settings.min_confidence);
    if (minConf > 0) list = list.filter(o => o.evidence_confidence >= minConf);

    const search = (document.getElementById('global-search').value || '').toLowerCase().trim();
    if (search) {
      list = list.filter(o =>
        o.product_name.toLowerCase().includes(search) ||
        o.domain.toLowerCase().includes(search) ||
        o.niche.toLowerCase().includes(search) ||
        o.platform.toLowerCase().includes(search)
      );
    }

    return list;
  }

  function sortedOffers(list) {
    const sorted = [...list];
    const by = state.sortBy;
    const desc = state.sortDesc;
    sorted.sort((a, b) => {
      let va, vb;
      if (by === 'score_total') {
        va = calculateScore(a).score_total;
        vb = calculateScore(b).score_total;
      } else {
        va = a[by];
        vb = b[by];
      }
      if (typeof va === 'string') return desc ? vb.localeCompare(va) : va.localeCompare(vb);
      return desc ? vb - va : va - vb;
    });
    return sorted;
  }

  /* ===== RENDER: DASHBOARD ===== */
  function renderDashboard() {
    /* Stats */
    const scores = OFFERS.map(o => calculateScore(o));
    const avgScore = Math.round(scores.reduce((s, c) => s + c.score_total, 0) / scores.length);
    const strongCount = scores.filter(s => s.score_total >= 80).length;
    const promisingCount = scores.filter(s => s.score_total >= 60 && s.score_total < 80).length;
    const growingCount = OFFERS.filter(o => o.status === 'growing').length;
    const totalVolume = OFFERS.reduce((s, o) => s + o.search_volume, 0);
    const alertsCount = MOCK_ALERTS.filter(a => a.severity === 'critical' || a.severity === 'warning').length;

    document.getElementById('stats-container').innerHTML = [
      { val: OFFERS.length, label: 'Ofertas', color: 'var(--accent-blue)' },
      { val: avgScore, label: 'Score Medio', color: scoreColor(avgScore), suffix: '/100' },
      { val: strongCount, label: 'Teste Forte (80+)', color: 'var(--accent-green)' },
      { val: promisingCount, label: 'Promissoras (60-79)', color: 'var(--accent-blue)' },
      { val: growingCount, label: 'Em Crescimento', color: 'var(--accent-green)' },
      { val: totalVolume.toLocaleString(), label: 'Volume Busca Total', color: 'var(--accent-purple)' },
      { val: alertsCount, label: 'Alertas Ativos', color: alertsCount > 0 ? 'var(--accent-red)' : 'var(--accent-green)' }
    ].map(st => `
      <div class="stat-item">
        <div class="stat-value" style="color:${st.color}">${st.val}${st.suffix || ''}</div>
        <div class="stat-label">${st.label}</div>
      </div>
    `).join('');

    /* Top offers */
    const top = sortedOffers(OFFERS).slice(0, 8);
    document.getElementById('top-offers-container').innerHTML = top.map(o => {
      const s = calculateScore(o);
      return `
        <div class="offer-mini" data-id="${o.id}">
          <div class="offer-mini-score" style="color:${scoreColor(s.score_total)}">${s.score_total}</div>
          <div class="offer-mini-info">
            <div class="offer-mini-name">${o.product_name}</div>
            <div class="offer-mini-meta">${o.platform} \u00B7 ${fmtPrice(o.current_price, o.currency)} \u00B7 ${o.niche}</div>
          </div>
          <span class="status-badge ${statusClass(o.status)}">${statusLabel(o.status)}</span>
        </div>
      `;
    }).join('');
    document.querySelectorAll('#top-offers-container .offer-mini').forEach(el => {
      el.addEventListener('click', function() {
        state.selectedDetail = this.dataset.id;
        navigate('detail');
      });
    });

    /* Alerts */
    document.getElementById('alerts-container').innerHTML = MOCK_ALERTS.slice(0, 5).map(a => {
      const offer = OFFERS.find(o => o.id === a.offer_id);
      return `
        <div class="alert-item alert-${a.severity}">
          <span class="alert-icon">${severityIcon(a.severity)}</span>
          <span class="alert-message">${a.message}</span>
          <span class="alert-date">${daysAgo(a.date)}</span>
        </div>
      `;
    }).join('');

    /* Trends */
    const trending = OFFERS.filter(o => o.trend_direction === 'up').sort((a, b) => b.growth_90d - a.growth_90d).slice(0, 5);
    document.getElementById('trends-container').innerHTML = trending.map(o => `
      <div class="trend-item">
        <span class="trend-direction trend-up">\u2191</span>
        <span class="offer-mini-name">${o.product_name}</span>
        <span style="color:var(--accent-green);font-weight:600;margin-left:auto">+${o.growth_90d}%</span>
        <span class="text-muted">${o.trend_persistence}</span>
      </div>
    `).join('');

    /* Niches */
    const nicheCounts = {};
    OFFERS.forEach(o => { nicheCounts[o.niche] = (nicheCounts[o.niche] || 0) + 1; });
    const maxNiche = Math.max(...Object.values(nicheCounts), 1);
    const nicheOrder = Object.entries(nicheCounts).sort((a, b) => b[1] - a[1]);
    const colors = ['var(--accent-blue)','var(--accent-green)','var(--accent-yellow)','var(--accent-orange)','var(--accent-purple)','var(--accent-red)','var(--score-promising)','var(--score-review)','var(--score-weak)','var(--score-skip)'];
    document.getElementById('niches-container').innerHTML = nicheOrder.map(([name, count], i) => `
      <div class="niche-bar">
        <span class="niche-name">${name.charAt(0).toUpperCase() + name.slice(1)}</span>
        <div class="niche-bar-track">
          <div class="niche-bar-fill" style="width:${(count/maxNiche)*100}%;background:${colors[i % colors.length]}"></div>
        </div>
        <span class="niche-count">${count}</span>
      </div>
    `).join('');
  }

  /* ===== RENDER: RADAR ===== */
  function renderRadar() {
    const filtered = getFilteredOffers();
    const sorted = sortedOffers(filtered);
    document.getElementById('radar-count').textContent = sorted.length + ' ofertas encontradas';

    if (sorted.length === 0) {
      document.getElementById('radar-body').innerHTML = '';
      document.getElementById('radar-empty').classList.remove('hidden');
      return;
    }
    document.getElementById('radar-empty').classList.add('hidden');

    document.getElementById('radar-body').innerHTML = sorted.map(o => {
      const s = calculateScore(o);
      const confPct = Math.round(o.evidence_confidence * 100);
      return `
        <tr class="clickable" data-id="${o.id}">
          <td class="score-cell" style="color:${scoreColor(s.score_total)};background:${scoreBg(s.score_total)}">${s.score_total}</td>
          <td><strong>${o.product_name}</strong><br><span class="text-muted" style="font-size:11px">${o.domain}</span></td>
          <td><span class="platform-badge">${o.platform_logo || o.platform}</span></td>
          <td>${o.niche}</td>
          <td>${fmtPrice(o.current_price, o.currency)}</td>
          <td>${pct(o.commission_percent)}</td>
          <td>${o.cookie_days}d</td>
          <td>${o.search_volume.toLocaleString()}</td>
          <td style="color:${o.growth_90d >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${o.growth_90d >= 0 ? '+' : ''}${o.growth_90d}%</td>
          <td><span class="status-badge ${statusClass(o.status)}">${statusLabel(o.status)}</span></td>
          <td>
            <div class="conf-bar"><div class="conf-bar-fill" style="width:${confPct}%;background:${confPct >= 80 ? 'var(--accent-green)' : confPct >= 60 ? 'var(--accent-blue)' : 'var(--accent-orange)'}"></div></div>
            <span style="font-size:11px;color:var(--text-muted)">${confPct}%</span>
          </td>
        </tr>
      `;
    }).join('');

    document.querySelectorAll('#radar-body tr').forEach(el => {
      el.addEventListener('click', function() {
        state.selectedDetail = this.dataset.id;
        navigate('detail');
      });
    });
  }

  /* ===== RENDER: DETAIL ===== */
  function renderDetail() {
    const sel = document.getElementById('detail-select');
    const currentId = state.selectedDetail || sel.value;
    if (currentId) sel.value = currentId;
    if (!currentId) {
      document.getElementById('detail-content').innerHTML = '<div class="empty-state">Selecione uma oferta para ver detalhes.</div>';
      return;
    }

    const offer = OFFERS.find(o => o.id === currentId);
    if (!offer) return;

    const score = calculateScore(offer);
    const confPct = Math.round(offer.evidence_confidence * 100);

    document.getElementById('detail-content').innerHTML = `
      <div class="detail-header">
        <h3 style="font-size:18px">${offer.product_name}</h3>
        <span class="text-muted">${offer.domain} \u00B7 ${offer.platform} \u00B7 ${offer.niche}</span>
      </div>
      <div class="detail-score" style="background:${scoreBg(score.score_total)}">
        <div class="detail-score-value" style="color:${scoreColor(score.score_total)}">${score.score_total}</div>
        <div class="detail-score-label">${score.classification_label} \u00B7 offer-score-v1.0</div>
        <div style="margin-top:6px">
          <span class="status-badge ${statusClass(offer.status)}">${statusLabel(offer.status)}</span>
          <span class="mock-badge" style="margin-left:6px">conf ${confPct}%</span>
        </div>
      </div>
      <div class="detail-section">
        <h3>Informacoes da Oferta</h3>
        <div class="detail-grid">
          <div class="detail-field"><span class="detail-field-label">Preco Atual</span><span class="detail-field-value">${fmtPrice(offer.current_price, offer.currency)}</span></div>
          <div class="detail-field"><span class="detail-field-label">Preco Original</span><span class="detail-field-value">${offer.old_price ? fmtPrice(offer.old_price, offer.currency) : 'N/A'}</span></div>
          <div class="detail-field"><span class="detail-field-label">Comissao</span><span class="detail-field-value">${pct(offer.commission_percent)}</span></div>
          <div class="detail-field"><span class="detail-field-label">Cookie</span><span class="detail-field-value">${offer.cookie_days} dias</span></div>
          <div class="detail-field"><span class="detail-field-label">Afiliacao</span><span class="detail-field-value">${offer.affiliate_available ? offer.affiliate_program : 'N/A'}</span></div>
          <div class="detail-field"><span class="detail-field-label">Tipo</span><span class="detail-field-value">${offer.has_physical ? 'Fisico' : 'Digital'}</span></div>
          <div class="detail-field"><span class="detail-field-label">Entrega</span><span class="detail-field-value">${offer.shipping_notes || 'N/A'}</span></div>
          <div class="detail-field"><span class="detail-field-label">Pais</span><span class="detail-field-value">${offer.country}</span></div>
        </div>
      </div>
      <div class="detail-section">
        <h3>Demanda e Tendencias</h3>
        <div class="detail-grid">
          <div class="detail-field"><span class="detail-field-label">Volume Busca</span><span class="detail-field-value">${offer.search_volume.toLocaleString()}</span></div>
          <div class="detail-field"><span class="detail-field-label">Cresc 30d</span><span class="detail-field-value" style="color:${offer.growth_30d >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${offer.growth_30d >= 0 ? '+' : ''}${offer.growth_30d}%</span></div>
          <div class="detail-field"><span class="detail-field-label">Cresc 90d</span><span class="detail-field-value" style="color:${offer.growth_90d >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">${offer.growth_90d >= 0 ? '+' : ''}${offer.growth_90d}%</span></div>
          <div class="detail-field"><span class="detail-field-label">Direcao</span><span class="detail-field-value">${offer.trend_direction}</span></div>
          <div class="detail-field"><span class="detail-field-label">Persistencia</span><span class="detail-field-value">${offer.trend_persistence}</span></div>
          <div class="detail-field"><span class="detail-field-label">Anuncios Ativos</span><span class="detail-field-value">${offer.active_ads}</span></div>
          <div class="detail-field"><span class="detail-field-label">Anunciantes</span><span class="detail-field-value">${offer.advertiser_count}</span></div>
          <div class="detail-field"><span class="detail-field-label">Saturacao</span><span class="detail-field-value">${offer.saturation_level}</span></div>
        </div>
      </div>
      <div class="detail-section">
        <h3>Qualidade e Risco</h3>
        <div class="detail-grid">
          <div class="detail-field"><span class="detail-field-label">Trust Marketplace</span><span class="detail-field-value">${(offer.marketplace_trust * 100).toFixed(0)}%</span></div>
          <div class="detail-field"><span class="detail-field-label">Reviews</span><span class="detail-field-value">${offer.reviews_avg} (${offer.review_count})</span></div>
          <div class="detail-field"><span class="detail-field-label">Reputacao</span><span class="detail-field-value">${offer.seller_reputation}</span></div>
          <div class="detail-field"><span class="detail-field-label">Risco Politica</span><span class="detail-field-value" style="color:${offer.policy_risk === 'alto' ? 'var(--accent-red)' : offer.policy_risk === 'medio' ? 'var(--accent-orange)' : 'var(--accent-green)'}">${offer.policy_risk}</span></div>
          <div class="detail-field"><span class="detail-field-label">Flags Risco</span><span class="detail-field-value">${offer.risk_flags.length ? offer.risk_flags.join(', ') : 'Nenhum'}</span></div>
        </div>
      </div>
      <div class="detail-section" style="grid-column:1/-1">
        <h3>Score Breakdown (${score.components.length} componentes)</h3>
        <div class="comp-list">
          ${score.components.map(c => {
            const pct = c.weight > 0 ? Math.round((c.weighted / c.weight) * 100) : 0;
            return `
              <div class="comp-item">
                <span class="comp-name">${c.name.replace(/_/g, ' ')}</span>
                <div class="comp-bar"><div class="comp-bar-fill" style="width:${pct}%;background:${pct >= 70 ? 'var(--accent-green)' : pct >= 40 ? 'var(--accent-yellow)' : 'var(--accent-red)'}"></div></div>
                <span class="comp-value">${c.weighted}/${c.weight}</span>
                <span class="comp-note">${c.note}</span>
              </div>
            `;
          }).join('')}
        </div>
      </div>
      <div class="detail-section" style="grid-column:1/-1">
        <div class="detail-grid">
          <div class="detail-field"><span class="detail-field-label">Formula</span><span class="detail-field-value">${score.formula_version}</span></div>
          <div class="detail-field"><span class="detail-field-label">Confianca</span><span class="detail-field-value">${score.confidence}</span></div>
          <div class="detail-field"><span class="detail-field-label">Dados Ausentes</span><span class="detail-field-value">${score.data_missing.length ? score.data_missing.join(', ') : 'Nenhum'}</span></div>
          <div class="detail-field"><span class="detail-field-label">Penalties</span><span class="detail-field-value">-${score.penalties} (saturacao: ${score.penalties_detail.saturacao}, politica: ${score.penalties_detail.politica})</span></div>
        </div>
      </div>
      <div class="detail-section" style="grid-column:1/-1">
        <div class="detail-grid">
          <div class="detail-field"><span class="detail-field-label">Fonte Evidencia</span><span class="detail-field-value">${offer.evidence_source}</span></div>
          <div class="detail-field"><span class="detail-field-label">Atualizacao</span><span class="detail-field-value">${offer.last_updated} (${daysAgo(offer.last_updated)})</span></div>
          <div class="detail-field"><span class="detail-field-label">Descricao</span><span class="detail-field-value" style="font-size:12px;color:var(--text-secondary);max-width:400px;white-space:normal;text-align:right">${offer.description}</span></div>
        </div>
      </div>
    `;
  }

  /* ===== RENDER: COMPARATOR ===== */
  function renderComparator() {
    const selected = state.compSelection.filter(id => id);
    if (selected.length < 2) {
      document.getElementById('comp-results').innerHTML =
        '<div class="empty-state">Selecione 2 a 4 ofertas para comparar.</div>';
      return;
    }

    const result = compareOffers(selected);
    if (result.error) {
      document.getElementById('comp-results').innerHTML =
        '<div class="empty-state">' + result.error + '</div>';
      return;
    }

    const fields = result.fields;
    const offers = result.offers;

    /* Table */
    let html = '<div class="comp-table-wrap"><table><thead><tr><th>Campo</th>';
    offers.forEach(o => { html += '<th>' + o.offer.product_name + '</th>'; });
    html += '</tr></thead><tbody>';
    fields.forEach(f => {
      html += '<tr><td style="font-weight:500">' + f.label + '</td>';
      offers.forEach(o => {
        let val;
        if (f.key === 'score_total') val = o.score.score_total + '/100';
        else if (f.key === 'confidence_label') val = o.score.confidence;
        else if (f.key === 'saturation_risk') val = o.score.penalties_detail.saturacao + '/8';
        else if (f.key === 'policy_risk') val = o.score.penalties_detail.politica + '/10';
        else if (f.key === 'evidence_confidence') val = Math.round(o.offer.evidence_confidence * 100) + '%';
        else if (f.key === 'evidence_freshness_days') val = o.offer.evidence_freshness_days + ' dias';
        else val = o.offer[f.key] + (f.unit ? ' ' + f.unit : '');
        const isBest = f.higher_better
          ? (f.key === 'score_total' ? o.offer.id === result.highlights.best_overall : false)
          : false;
        html += '<td' + (isBest ? ' style="color:var(--accent-green);font-weight:600"' : '') + '>' + val + '</td>';
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';

    /* Highlights */
    html += '<div class="comp-highlights">';
    html += '<div class="comp-highlight"><div class="comp-highlight-label">Melhor Score Geral</div>' +
      '<div class="comp-highlight-value" style="color:var(--accent-green)">' +
      (result.offers.find(o => o.offer.id === result.highlights.best_overall)?.offer.product_name || '') +
      '</div></div>';
    html += '<div class="comp-highlight"><div class="comp-highlight-label">Melhor Comissao</div>' +
      '<div class="comp-highlight-value" style="color:var(--accent-blue)">' +
      (result.offers.find(o => o.offer.id === result.highlights.best_commission)?.offer.product_name || '') +
      '</div></div>';
    html += '<div class="comp-highlight"><div class="comp-highlight-label">Maior Crescimento</div>' +
      '<div class="comp-highlight-value" style="color:var(--accent-purple)">' +
      (result.offers.find(o => o.offer.id === result.highlights.best_growth)?.offer.product_name || '') +
      '</div></div>';
    html += '<div class="comp-highlight"><div class="comp-highlight-label">Menor Risco</div>' +
      '<div class="comp-highlight-value" style="color:var(--accent-yellow)">' +
      (result.offers.find(o => o.offer.id === result.highlights.lowest_risk)?.offer.product_name || '') +
      '</div></div>';
    html += '</div>';

    /* Conclusion */
    html += '<div class="comp-conclusion">' + result.conclusion + '</div>';

    document.getElementById('comp-results').innerHTML = html;
  }

  /* ===== RENDER: ANALYSIS ===== */
  function renderAnalysis() {
    const sel = document.getElementById('analysis-select');
    const id = state.selectedAnalysis || sel.value;
    if (id) sel.value = id;
    if (!id) {
      document.getElementById('analysis-content').innerHTML =
        '<div class="empty-state">Selecione uma oferta para analisar.</div>';
      return;
    }

    const analysis = generateAIAnalysis(id);
    if (!analysis) return;

    document.getElementById('analysis-content').innerHTML = `
      <div class="analysis-header">
        <div class="analysis-score" style="color:${scoreColor(
          OFFERS.find(o => o.id === id) ? calculateScore(OFFERS.find(o => o.id === id)).score_total : 0
        )}">${analysis.offer_name}</div>
      </div>
      <div class="analysis-section">
        <h3>Sumario Executivo</h3>
        <p style="font-size:14px">${analysis.executive_summary}</p>
      </div>
      <div class="analysis-section">
        <h3>Explicacao do Score</h3>
        <p style="font-size:13px">${analysis.score_explanation}</p>
      </div>
      <div class="analysis-section">
        <h3>Pontos Fortes</h3>
        <ul>${analysis.strengths.map(s => '<li>' + s + '</li>').join('')}</ul>
      </div>
      <div class="analysis-section">
        <h3>Pontos Fracos</h3>
        <ul>${analysis.weaknesses.map(w => '<li>' + w + '</li>').join('')}</ul>
      </div>
      <div class="analysis-section">
        <h3>Riscos</h3>
        <ul>${analysis.risks.map(r => '<li>' + r + '</li>').join('')}</ul>
      </div>
      <div class="analysis-section">
        <h3>Dados Ausentes</h3>
        <ul>${analysis.missing_data.map(m => '<li>' + m + '</li>').join('')}</ul>
      </div>
      <div class="analysis-section">
        <h3>Plano de Teste Sugerido</h3>
        <p style="font-size:13px">${analysis.suggested_test_plan}</p>
      </div>
      <div class="analysis-section">
        <h3>Condicoes de Parada</h3>
        <p style="font-size:13px;color:var(--accent-orange)">${analysis.stop_conditions}</p>
      </div>
      <div class="analysis-section">
        <h3>Perguntas em Aberto</h3>
        <ul>${analysis.open_questions.map(q => '<li>' + q + '</li>').join('')}</ul>
      </div>
      <div class="analysis-section">
        <h3>Fontes Utilizadas</h3>
        <p style="font-size:13px">${analysis.sources_used.join(', ')}</p>
      </div>
      <div class="analysis-disclaimer">${analysis.disclaimer}</div>
    `;
  }

  /* ===== RENDER: SOURCES ===== */
  function renderSources() {
    const sel = document.getElementById('sources-select');
    const id = state.selectedSources || sel.value;
    if (id) sel.value = id;
    if (!id) {
      document.getElementById('sources-detail').innerHTML =
        '<div class="empty-state">Selecione uma oferta para ver as fontes.</div>';
      return;
    }

    const offer = OFFERS.find(o => o.id === id);
    if (!offer) return;
    const score = calculateScore(offer);

    document.getElementById('sources-detail').innerHTML = `
      <div style="grid-column:1/-1;margin-bottom:8px">
        <strong style="font-size:15px">${offer.product_name}</strong>
        <span class="text-muted" style="margin-left:8px">Score: ${score.score_total}/100</span>
      </div>
      ${score.components.map(c => `
        <div class="source-item">
          <strong>${c.name.replace(/_/g, ' ')}</strong>
          <div>Valor: ${c.weighted}/${c.weight} | Peso: ${c.weight}</div>
          <div class="source-meta">Fonte: ${c.source} | Confianca: ${Math.round(c.confidence * 100)}% | Dado disponivel: ${c.data_available ? 'Sim' : 'Nao'}</div>
          <div class="source-meta">Nota: ${c.note}</div>
        </div>
      `).join('')}
      <div class="source-item" style="grid-column:1/-1">
        <strong>Resumo das Fontes</strong>
        <div class="source-meta">Fonte principal: ${offer.evidence_source}</div>
        <div class="source-meta">Ultima atualizacao: ${offer.last_updated} (${daysAgo(offer.last_updated)})</div>
        <div class="source-meta">Confianca geral: ${Math.round(offer.evidence_confidence * 100)}% (${score.confidence})</div>
        <div class="source-meta">Dados ausentes: ${score.data_missing.length ? score.data_missing.join(', ') : 'Nenhum'}</div>
        <div class="source-meta">Formula: ${score.formula_version}</div>
      </div>
    `;
  }

  /* ===== RENDER: MONITORING ===== */
  function renderMonitoring() {
    let alerts = MOCK_ALERTS;
    const sev = state.alertFilter || document.getElementById('alert-severity').value;
    if (sev) alerts = alerts.filter(a => a.severity === sev);

    if (alerts.length === 0) {
      document.getElementById('monitoring-list').innerHTML =
        '<div class="empty-state">Nenhum alerta encontrado para este filtro.</div>';
      return;
    }

    document.getElementById('monitoring-list').innerHTML = alerts.map(a => {
      const offer = OFFERS.find(o => o.id === a.offer_id);
      return `
        <div class="alert-item alert-${a.severity}">
          <span class="alert-icon">${severityIcon(a.severity)}</span>
          <div style="flex:1">
            <span class="alert-message">${a.message}</span>
            <div class="text-muted" style="font-size:11px;margin-top:2px">
              ${offer ? offer.product_name + ' \u00B7 ' : ''}${a.type} \u00B7 ${a.date}
            </div>
          </div>
          <span class="alert-date">${daysAgo(a.date)}</span>
        </div>
      `;
    }).join('');
  }

  /* ===== RENDER: ACADEMIA ===== */
  function renderAcademia() {
    var progress = ProgressTracker.getTotalProgress();
    document.getElementById('academia-progress-bar').style.width = progress.percentage + '%';
    document.getElementById('academia-progress-text').textContent = progress.completed + ' de ' + progress.total + ' aulas concluidas';
    document.getElementById('academia-percentage').textContent = progress.percentage + '%';

    /* Continue button */
    var continueBtn = document.getElementById('academia-continue');
    var lastId = ProgressTracker.getLastLessonId();
    var firstIncomplete = ProgressTracker.getFirstIncompleteLesson();
    if (lastId && !ProgressTracker.isLessonCompleted(lastId)) {
      continueBtn.textContent = 'Continuar aprendendo';
      continueBtn.onclick = function() { openLesson(lastId); };
    } else if (firstIncomplete) {
      continueBtn.textContent = 'Continuar aprendendo';
      continueBtn.onclick = function() { openLesson(firstIncomplete); };
    } else if (progress.completed > 0) {
      continueBtn.textContent = 'Revisar curso';
      continueBtn.onclick = function() { openLesson(getAllLessons()[0].id); };
    } else {
      continueBtn.textContent = 'Comecar aprender';
      continueBtn.onclick = function() { var first = getAllLessons()[0]; if (first) openLesson(first.id); };
    }

    /* Restart */
    document.getElementById('academia-restart').onclick = function() {
      if (confirm('Tem certeza? Todo o progresso na Academia sera perdido.')) {
        ProgressTracker.resetProgress();
        renderAcademia();
      }
    };

    /* Repeat last completed */
    var repeatBtn = document.getElementById('academia-repeat-last');
    if (lastId && ProgressTracker.isLessonCompleted(lastId)) {
      repeatBtn.classList.remove('hidden');
      repeatBtn.onclick = function() { openLesson(lastId); };
    } else {
      repeatBtn.classList.add('hidden');
    }

    /* Narration settings */
    document.getElementById('academia-narration-toggle').checked = ProgressTracker.isNarrationActive();
    document.getElementById('academia-narration-toggle').onchange = function() {
      ProgressTracker.setNarrationActive(this.checked);
    };
    document.getElementById('academia-speed').value = String(ProgressTracker.getSpeed());
    document.getElementById('academia-speed').onchange = function() {
      ProgressTracker.setSpeed(parseFloat(this.value));
    };

    /* Settings toggle */
    var settingsVisible = false;
    document.getElementById('academia-settings-toggle').onclick = function() {
      settingsVisible = !settingsVisible;
      document.getElementById('academia-settings-panel').classList.toggle('hidden', !settingsVisible);
      this.textContent = settingsVisible ? 'Fechar opcoes' : 'Opcoes de aula';
    };

    /* Render modules */
    var modulesHtml = '';
    LEARNING_MODULES.forEach(function(mod) {
      var modProgress = ProgressTracker.getModuleProgress(mod.id);
      var lessonsHtml = '';
      mod.lessons.forEach(function(lesson) {
        var completed = ProgressTracker.isLessonCompleted(lesson.id);
        var inProgress = ProgressTracker.getLessonProgress(lesson.id);
        var recommended = ProgressTracker.getRecommendedReviewLessons();
        var needsReview = recommended.indexOf(lesson.id) !== -1;
        var statusClass, statusText;
        if (completed) {
          statusClass = 'academia-lesson-status-done';
          statusText = '\u2713';
        } else if (inProgress && inProgress.started) {
          statusClass = 'academia-lesson-status-inprogress';
          statusText = '\u25B6';
        } else if (needsReview) {
          statusClass = 'academia-lesson-status-review';
          statusText = '!';
        } else {
          statusClass = 'academia-lesson-status-pending';
          statusText = '';
        }
        lessonsHtml += '<div class="academia-lesson-item" data-lesson-id="' + lesson.id + '">' +
          '<div class="academia-lesson-status ' + statusClass + '">' + statusText + '</div>' +
          '<span class="academia-lesson-name">' + lesson.title + '</span>' +
          '<span class="academia-lesson-duration">' + lesson.duration + '</span>' +
          (needsReview ? '<span class="academia-lesson-recommended">revisar</span>' : '') +
        '</div>';
      });
      modulesHtml += '<div class="academia-module-card">' +
        '<div class="academia-module-header">' +
          '<div><div class="academia-module-title">' + mod.title + '</div>' +
          '<div class="academia-module-subtitle">' + mod.subtitle + '</div></div>' +
          '<div class="academia-module-progress">' + modProgress.completed + '/' + modProgress.total + '</div>' +
        '</div>' +
        '<div class="academia-module-bar"><div class="academia-module-bar-fill" style="width:' + modProgress.percentage + '%"></div></div>' +
        '<div class="academia-lesson-list">' + lessonsHtml + '</div>' +
      '</div>';
    });
    document.getElementById('academia-modules').innerHTML = modulesHtml;

    /* Bind lesson click */
    document.querySelectorAll('.academia-lesson-item').forEach(function(el) {
      el.addEventListener('click', function() {
        openLesson(this.dataset.lessonId);
      });
    });

    /* Glossary preview */
    document.getElementById('academia-glossary-preview').innerHTML = GLOSSARY.slice(0, 4).map(function(g) {
      return '<div class="glossary-mini"><strong>' + g.term + '</strong>: ' + g.simple + '</div>';
    }).join('') + '<button class="btn-sm" style="margin-top:8px" onclick="navigate(\'settings\')">Ver glossario completo</button>';
    /* Note: settings has the glossary; we'll also add it to settings view later */
  }

  function openLesson(lessonId) {
    var lesson = getLesson(lessonId);
    if (!lesson) return;

    /* Save current lesson before navigating */
    state._academiaReturnView = state.currentView;

    /* Activate beginner mode */
    if (BeginnerMode && !BeginnerMode.isBeginner()) {
      BeginnerMode.toggle();
    }

    navigate('academia-lesson');
    renderAcademiaLesson(lessonId);
  }

  function renderAcademiaLesson(lessonId) {
    var lesson = getLesson(lessonId);
    if (!lesson) {
      document.getElementById('academia-lesson-content').innerHTML = '<div class="empty-state">Aula nao encontrada.</div>';
      return;
    }

    /* Get module info */
    var moduleInfo = '';
    var lessonIndex = 0;
    for (var mi = 0; mi < LEARNING_MODULES.length; mi++) {
      var mod = LEARNING_MODULES[mi];
      for (var li = 0; li < mod.lessons.length; li++) {
        lessonIndex++;
        if (mod.lessons[li].id === lessonId) {
          moduleInfo = mod.title + ' - ';
        }
      }
    }

    document.getElementById('academia-lesson-counter').textContent = 'Aula ' + lessonIndex + ' de 26';
    document.getElementById('view-title').textContent = moduleInfo + lesson.title;

    /* Start lesson in engine */
    LearningEngine.startLesson(lessonId, function(id) {
      /* On finish - go back to academia */
      var msg = 'Aula concluida!';
      if (lesson.exercise || lesson.quiz) {
        /* Check if quiz was answered */
      }
      renderAcademiaLessonComplete(lesson);
    });

    /* Render lesson content */
    renderLessonStep(lesson);
    bindLessonEvents(lesson);
  }

  function renderLessonStep(lesson) {
    var stepIndex = LearningEngine.getCurrentStepIndex();
    var step = lesson.steps[stepIndex];
    var container = document.getElementById('academia-lesson-content');

    if (!step) {
      /* No steps or beyond - show quiz/summary */
      renderLessonComplete(lesson);
      return;
    }

    var html = '<div class="lesson-title">' + lesson.title + '</div>';
    html += '<div class="lesson-objective">' + lesson.objective + '</div>';

    if (lesson.steps.length > 1) {
      html += '<div class="lesson-step-text">' + step.text + '</div>';
    } else {
      html += '<div class="lesson-step-text">' + (lesson.narration || step.text) + '</div>';
    }

    if (lesson.analogy) {
      html += '<div class="lesson-analogy"><strong>Analogia:</strong> ' + lesson.analogy + '</div>';
    }

    html += '<div id="lesson-visual-area"></div>';

    container.innerHTML = html;

    /* Render visual aids based on lesson */
    if (lesson.id === 'lesson-4' || lesson.id === 'lesson-5') {
      LessonVisuals.createVolumeComparison('lesson-visual-area');
    }
    if (lesson.id === 'lesson-6') {
      LessonVisuals.createGrowthComparison('lesson-visual-area');
    }
    if (lesson.id === 'lesson-10') {
      LessonVisuals.createSaturationVisual('lesson-visual-area');
    }
    if (lesson.id === 'lesson-21') {
      LessonVisuals.createCampaignDiagnosis('lesson-visual-area');
    }

    /* Update step info */
    document.getElementById('academia-lesson-step-info').textContent = 'Passo ' + (stepIndex + 1) + ' de ' + lesson.steps.length;

    /* Narration */
    if (ProgressTracker.isNarrationActive()) {
      var textToSpeak = step.text || lesson.narration || '';
      if (textToSpeak) {
        Narration.stop();
        Narration.speak(textToSpeak);
      }
    }

    /* Highlight the element */
    if (step.highlight) {
      LearningEngine._highlightElement(step.highlight, step.label || '');
    }
    if (step.label && step.highlight) {
      LearningEngine._createSpotlight(step.highlight, step.label);
    }

    /* Show quiz at the end */
    var exerciseArea = document.getElementById('academia-exercise-area');
    if (lesson.quiz && stepIndex === lesson.steps.length - 1) {
      QuizEngine.startQuiz(lesson.id, function() {
        /* Quiz done */
        exerciseArea.innerHTML += '<p class="text-muted" style="margin-top:8px;font-size:12px">Exercicio concluido. Va para o proximo passo ou conclua a aula.</p>';
      });
    }
    if (lesson.exercise) {
      exerciseArea.innerHTML = QuizEngine.renderExercise(lesson.exercise);
    }
  }

  function renderLessonComplete(lesson) {
    var container = document.getElementById('academia-lesson-content');
    var html = '<div class="lesson-title">' + lesson.title + '</div>';
    if (lesson.summary) {
      html += '<div class="lesson-summary">' + lesson.summary + '</div>';
    }
    html += '<div class="lesson-objective" style="margin-top:12px">Aula concluida! ' + (lesson.objective || '') + '</div>';
    if (lesson.quiz) {
      html += '<div id="final-quiz-area"></div>';
    }
    html += '<div style="margin-top:16px"><button id="lesson-finish-btn" class="btn academia-btn-primary">Concluir aula e voltar</button></div>';
    container.innerHTML = html;

    document.getElementById('academia-lesson-step-info').textContent = 'Aula concluida';

    if (lesson.quiz) {
      QuizEngine.startQuiz(lesson.id, function() {
        document.getElementById('final-quiz-area').innerHTML = '<p class="text-muted" style="margin-top:8px;font-size:12px">Exercicio concluido.</p>';
      });
    }

    document.getElementById('lesson-finish-btn').onclick = function() {
      LearningEngine.finishLesson();
      navigate('academia');
    };
  }

  function renderAcademiaLessonComplete(lesson) {
    /* Called when LearningEngine finishes - show summary */
    var container = document.getElementById('academia-lesson-content');
    var html = '<div class="lesson-title">' + lesson.title + '</div>';
    if (lesson.summary) {
      html += '<div class="lesson-summary">' + lesson.summary + '</div>';
    }
    html += '<div style="margin-top:16px;text-align:center;padding:20px">';
    html += '<div style="font-size:48px;margin-bottom:12px">\u2713</div>';
    html += '<p style="font-size:16px;font-weight:600;color:var(--accent-green)">Aula concluida com sucesso!</p>';
    html += '<p class="text-muted">Continue praticando para fixar o conteudo.</p>';
    html += '<button id="back-to-academia-btn" class="btn academia-btn-primary" style="margin-top:16px">Voltar para Academia</button>';
    html += '</div>';
    container.innerHTML = html;

    document.getElementById('back-to-academia-btn').onclick = function() {
      navigate('academia');
    };
  }

  function bindLessonEvents(lesson) {
    if (!lesson) return;

    /* Prev step */
    document.getElementById('academia-lesson-prev').onclick = function() {
      LearningEngine.prevStep();
      renderLessonStep(lesson);
    };

    /* Next step */
    document.getElementById('academia-lesson-next').onclick = function() {
      /* If last step and quiz is not answered, prevent */
      var isLastStep = LearningEngine.getCurrentStepIndex() >= lesson.steps.length - 1;
      if (lesson.quiz && isLastStep && !QuizEngine.isAnsweredCorrectly()) {
        /* Allow but warn - quiz answer is optional for progress */
      }
      LearningEngine.nextStep();
      if (LearningEngine.isLessonActive()) {
        renderLessonStep(lesson);
      } else {
        renderLessonComplete(lesson);
      }
    };

    /* Back to academia */
    document.getElementById('academia-lesson-back').onclick = function() {
      LearningEngine.stopLesson();
      QuizEngine.reset();
      navigate('academia');
    };

    /* Glossary during lesson */
    document.getElementById('academia-lesson-glossary').onclick = function() {
      Narration.pause();
      var glossaryHtml = '<div class="card"><div class="card-header"><h2>Glossario</h2><button class="btn-sm" onclick="closeGlossaryPopup()">Fechar</button></div>';
      glossaryHtml += '<div style="max-height:300px;overflow-y:auto">';
      GLOSSARY.forEach(function(g) {
        glossaryHtml += '<div class="glossary-item" style="padding:6px 0;border-bottom:1px solid var(--border-light)">';
        glossaryHtml += '<strong>' + g.term + '</strong>';
        glossaryHtml += '<p style="font-size:12px;color:var(--text-secondary);margin:2px 0">' + g.simple + '</p>';
        glossaryHtml += '<div class="glossary-details hidden"><p style="font-size:11px;color:var(--text-muted)"><em>Exemplo:</em> ' + g.example + '</p></div>';
        glossaryHtml += '<button class="btn-sm" style="font-size:10px" onclick="this.previousElementSibling.classList.toggle(\'hidden\')">Ver exemplo</button>';
        glossaryHtml += '</div>';
      });
      glossaryHtml += '</div></div>';
      var existing = document.getElementById('glossary-popup');
      if (existing) existing.remove();
      var popup = document.createElement('div');
      popup.id = 'glossary-popup';
      popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:9999;max-width:500px;width:90%;';
      popup.innerHTML = glossaryHtml;
      document.body.appendChild(popup);
      var overlay = document.createElement('div');
      overlay.id = 'glossary-popup-overlay';
      overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9998;';
      overlay.onclick = function() { closeGlossaryPopup(); };
      document.body.appendChild(overlay);
    };

    /* Narration toggle */
    document.getElementById('academia-lesson-narration-toggle').onclick = function() {
      var active = !ProgressTracker.isNarrationActive();
      ProgressTracker.setNarrationActive(active);
      this.textContent = active ? 'Narracao' : 'Sem voz';
      this.classList.toggle('btn-sm', true);
    };

    /* Restart lesson */
    document.getElementById('academia-lesson-restart').onclick = function() {
      LearningEngine.stopLesson();
      QuizEngine.reset();
      LearningEngine.startLesson(lesson.id, function() {
        renderAcademiaLessonComplete(lesson);
      });
      renderLessonStep(lesson);
    };

    /* Narration bar controls */
    document.getElementById('narration-prev').onclick = function() {
      LearningEngine.prevStep();
      renderLessonStep(lesson);
    };
    document.getElementById('narration-next').onclick = function() {
      LearningEngine.nextStep();
      if (LearningEngine.isLessonActive()) {
        renderLessonStep(lesson);
      } else {
        renderLessonComplete(lesson);
      }
    };
    document.getElementById('narration-play-pause').onclick = function() {
      var status = Narration.getStatus();
      if (status.isPaused) {
        Narration.resume();
        this.textContent = '\u23F8';
      } else if (status.isPlaying) {
        Narration.pause();
        this.textContent = '\u25B6';
      } else {
        var step = LearningEngine.getCurrentStep();
        if (step && step.text) {
          Narration.speak(step.text);
          this.textContent = '\u23F8';
        }
      }
    };
    document.getElementById('narration-skip').onclick = function() {
      Narration.stop();
      document.getElementById('narration-play-pause').textContent = '\u25B6';
    };
  }

  function closeGlossaryPopup() {
    var popup = document.getElementById('glossary-popup');
    var overlay = document.getElementById('glossary-popup-overlay');
    if (popup) popup.remove();
    if (overlay) overlay.remove();
    Narration.resume();
  }

  /* Expose for onclick */
  window.closeGlossaryPopup = closeGlossaryPopup;
  window.openLesson = openLesson;

  /* ===== POPULATE SELECTS ===== */
  function populateSelects() {
    /* Filter selects */
    const nicheSel = document.getElementById('filter-niche');
    NICHES.forEach(n => {
      nicheSel.innerHTML += '<option value="' + n + '">' + n.charAt(0).toUpperCase() + n.slice(1) + '</option>';
    });
    const platSel = document.getElementById('filter-platform');
    PLATFORMS.forEach(p => {
      platSel.innerHTML += '<option value="' + p + '">' + p + '</option>';
    });
    const statusSel = document.getElementById('filter-status');
    ['growing', 'stable', 'declining', 'insufficient_data'].forEach(s => {
      statusSel.innerHTML += '<option value="' + s + '">' + statusLabel(s) + '</option>';
    });
    const scoreSel = document.getElementById('filter-score-range');
    [
      { v: '80-100', l: 'Teste Forte (80-100)' },
      { v: '60-79', l: 'Promissora (60-79)' },
      { v: '40-59', l: 'Revisao (40-59)' },
      { v: '20-39', l: 'Fraca (20-39)' },
      { v: '0-19', l: 'Pular (0-19)' }
    ].forEach(s => {
      scoreSel.innerHTML += '<option value="' + s.v + '">' + s.l + '</option>';
    });

    /* Detail select */
    const detSel = document.getElementById('detail-select');
    const sorted = sortedOffers(OFFERS);
    sorted.forEach(o => {
      const s = calculateScore(o);
      detSel.innerHTML += '<option value="' + o.id + '">[' + s.score_total + '] ' + o.product_name + '</option>';
    });

    /* Analysis select */
    const analSel = document.getElementById('analysis-select');
    sorted.forEach(o => {
      const s = calculateScore(o);
      analSel.innerHTML += '<option value="' + o.id + '">[' + s.score_total + '] ' + o.product_name + '</option>';
    });

    /* Sources select */
    const srcSel = document.getElementById('sources-select');
    sorted.forEach(o => {
      const s = calculateScore(o);
      srcSel.innerHTML += '<option value="' + o.id + '">[' + s.score_total + '] ' + o.product_name + '</option>';
    });

    /* Comparator selects */
    sorted.forEach(o => {
      const s = calculateScore(o);
      const opt = '<option value="' + o.id + '">[' + s.score_total + '] ' + o.product_name + '</option>';
      document.querySelectorAll('.comp-select').forEach(el => {
        el.innerHTML += opt;
      });
    });
  }

  /* ===== EVENT BINDING ===== */
  function bindEvents() {
    /* Nav */
    document.querySelectorAll('.nav-item').forEach(el => {
      el.addEventListener('click', function() {
        navigate(this.dataset.view);
        document.getElementById('sidebar').classList.remove('open');
      });
    });

    /* Menu toggle */
    document.getElementById('menu-toggle').addEventListener('click', function() {
      document.getElementById('sidebar').classList.toggle('open');
    });
    document.addEventListener('click', function(e) {
      const sidebar = document.getElementById('sidebar');
      const toggle = document.getElementById('menu-toggle');
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(e.target) &&
          !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });

    /* Global search */
    document.getElementById('global-search').addEventListener('input', function() {
      if (state.currentView === 'radar') renderRadar();
    });

    /* Filter events */
    document.getElementById('filter-niche').addEventListener('change', function() {
      state.filters.niche = this.value; renderRadar();
    });
    document.getElementById('filter-platform').addEventListener('change', function() {
      state.filters.platform = this.value; renderRadar();
    });
    document.getElementById('filter-status').addEventListener('change', function() {
      state.filters.status = this.value; renderRadar();
    });
    document.getElementById('filter-score-range').addEventListener('change', function() {
      state.filters.scoreRange = this.value; renderRadar();
    });
    document.getElementById('reset-filters').addEventListener('click', function() {
      state.filters = { niche: '', platform: '', status: '', scoreRange: '' };
      document.querySelectorAll('.radar-controls select').forEach(el => el.value = '');
      renderRadar();
    });

    /* Sort */
    document.getElementById('sort-by').addEventListener('change', function() {
      state.sortBy = this.value; renderRadar();
    });
    document.getElementById('sort-order').addEventListener('click', function() {
      state.sortDesc = !state.sortDesc;
      this.textContent = state.sortDesc ? '\u2193' : '\u2191';
      renderRadar();
    });

    /* Detail select */
    document.getElementById('detail-select').addEventListener('change', function() {
      state.selectedDetail = this.value;
      renderDetail();
    });

    /* Analysis select */
    document.getElementById('analysis-select').addEventListener('change', function() {
      state.selectedAnalysis = this.value;
      renderAnalysis();
    });

    /* Sources select */
    document.getElementById('sources-select').addEventListener('change', function() {
      state.selectedSources = this.value;
      renderSources();
    });

    /* Comparator selects */
    document.querySelectorAll('.comp-select').forEach(el => {
      el.addEventListener('change', function() {
        const idx = parseInt(this.dataset.idx);
        state.compSelection[idx] = this.value || null;
        renderComparator();
      });
    });

    document.getElementById('comp-clear').addEventListener('click', function() {
      state.compSelection = [null, null, null, null];
      document.querySelectorAll('.comp-select').forEach(el => el.value = '');
      document.getElementById('comp-results').innerHTML =
        '<div class="empty-state">Selecione 2 a 4 ofertas para comparar.</div>';
    });

    /* Alert severity filter */
    document.getElementById('alert-severity').addEventListener('change', function() {
      state.alertFilter = this.value;
      renderMonitoring();
    });

    /* Settings */
    document.getElementById('set-theme').addEventListener('change', function() {
      state.settings.theme = this.value; saveSettings(); applySettings();
    });
    document.getElementById('set-density').addEventListener('change', function() {
      state.settings.density = this.value; saveSettings(); applySettings();
    });
    document.getElementById('set-currency').addEventListener('change', function() {
      state.settings.currency = this.value; saveSettings();
    });
    document.getElementById('set-rows').addEventListener('change', function() {
      state.settings.rows_per_page = parseInt(this.value); saveSettings();
    });
    document.getElementById('set-confidence').addEventListener('input', function() {
      state.settings.min_confidence = parseFloat(this.value);
      document.getElementById('confidence-label').textContent = this.value;
      saveSettings();
    });
    document.getElementById('set-advanced').addEventListener('change', function() {
      state.settings.show_advanced = this.checked; saveSettings();
    });
    document.getElementById('reset-settings').addEventListener('click', function() {
      state.settings = Object.assign({}, DEFAULT_SETTINGS);
      saveSettings();
      applySettings();
    });
  }

  /* ===== INIT ===== */
  function init() {
    loadSettings();
    populateSelects();
    bindEvents();
    navigate('dashboard');
  }

  document.addEventListener('DOMContentLoaded', init);
})();
