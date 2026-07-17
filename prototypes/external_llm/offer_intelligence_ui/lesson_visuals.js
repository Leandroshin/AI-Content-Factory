/* Offer Intelligence — Lesson Visuals v1.0 */
/* SVG circles, arrows, labels, spotlight, campagne diagnosis. */

const LessonVisuals = (function() {
  'use strict';

  function createVisualDiagnosis(containerId, findings) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var html = '<div class="visual-diagnosis">';

    findings.forEach(function(f, idx) {
      html += '<div class="diagnosis-step" data-step="' + idx + '">';
      html += '<div class="diagnosis-number">' + (idx + 1) + '</div>';
      html += '<div class="diagnosis-content">';
      html += '<strong>' + f.title + '</strong>';
      html += '<p>' + f.description + '</p>';
      if (f.impact) {
        html += '<div class="diagnosis-impact" style="background:' + (f.impactColor || 'rgba(248,113,113,0.15)') + ';border-left:3px solid ' + (f.impactColor || 'var(--accent-red)') + '">';
        html += '<span class="diagnosis-impact-label">Impacto: </span>';
        html += '<span>' + f.impact + '</span>';
        html += '</div>';
      }
      html += '<button class="btn-sm diagnosis-show-btn" data-target="' + (f.selector || '') + '">Por que isso importa?</button>';
      html += '<div class="diagnosis-why hidden">' + (f.whyItMatters || '') + '</div>';
      html += '</div></div>';
    });

    html += '</div>';
    container.innerHTML = html;

    /* Bind "Por que isso importa?" buttons */
    container.querySelectorAll('.diagnosis-show-btn').forEach(function(btn) {
      btn.addEventListener('click', function() {
        var whyDiv = this.nextElementSibling;
        if (whyDiv) {
          whyDiv.classList.toggle('hidden');
          this.textContent = whyDiv.classList.contains('hidden') ? 'Por que isso importa?' : 'Ocultar explicacao';
        }
        var target = this.dataset.target;
        if (target) {
          var el = document.querySelector(target);
          if (el) {
            el.classList.add('learning-highlight');
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            setTimeout(function() {
              el.classList.remove('learning-highlight');
            }, 3000);
          }
        }
      });
    });
  }

  function createCampaignDiagnosis(containerId) {
    var findings = [
      {
        title: 'Custo elevado',
        description: 'A campanha gastou R$ 1.200 em 7 dias, mas o orcamento previsto era de R$ 500.',
        impact: 'Perdeu -3 pontos no score de eficiencia',
        impactColor: 'rgba(248,113,113,0.15)',
        selector: '.detail-field-value:contains("12")',
        whyItMatters: 'Custo alto sem retorno proporcional e o primeiro sinal de que algo nao esta certo. O orcamento foi excedido sem gerar resultados equivalentes.'
      },
      {
        title: 'Poucos cliques',
        description: 'Apenas 45 cliques em 7 dias para um investimento de R$ 1.200.',
        impact: 'Custo por clique de R$ 26,67 - muito acima do aceitavel',
        impactColor: 'rgba(251,191,36,0.15)',
        selector: '.detail-field:contains("Anuncios")',
        whyItMatters: 'Poucos cliques indicam que o anuncio ou a segmentacao nao estao atraindo a atencao do publico certo.'
      },
      {
        title: 'Nenhuma venda',
        description: 'Apesar dos cliques, nenhuma venda foi registrada.',
        impact: 'Taxa de conversao de 0% - investimento sem retorno',
        impactColor: 'rgba(248,113,113,0.15)',
        selector: '.comp-highlights',
        whyItMatters: 'Se as pessoas clicam mas nao compram, o problema pode estar na pagina de vendas, no preco ou na oferta em si.'
      },
      {
        title: 'Relacao entre os indicadores',
        description: 'Custo alto + poucos cliques + zero vendas forma um padrao claro: a campanha precisa ser interrompida ou completamente revisada.',
        impact: 'Score geral comprometido',
        impactColor: 'rgba(248,113,113,0.15)',
        selector: null,
        whyItMatters: 'Nenhum indicador isolado conta a historia completa. E a combinacao dos tres que mostra que a campanha nao esta funcionando.'
      }
    ];

    createVisualDiagnosis(containerId, findings);
  }

  function createVolumeComparison(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var html = '<div class="volume-comparison">';
    html += '<div class="volume-bar-container">';
    html += '<div class="volume-bar-label">Volume baixo (500)</div>';
    html += '<div class="volume-bar volume-bar-low"><div class="volume-bar-fill" style="width:10%"></div></div>';
    html += '</div>';
    html += '<div class="volume-bar-container">';
    html += '<div class="volume-bar-label">Volume medio (5.000)</div>';
    html += '<div class="volume-bar volume-bar-mid"><div class="volume-bar-fill" style="width:50%"></div></div>';
    html += '</div>';
    html += '<div class="volume-bar-container">';
    html += '<div class="volume-bar-label">Volume alto (25.000)</div>';
    html += '<div class="volume-bar volume-bar-high"><div class="volume-bar-fill" style="width:100%"></div></div>';
    html += '</div>';
    html += '</div>';
    container.innerHTML = html;
  }

  function createGrowthComparison(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var html = '<div class="growth-comparison">';
    html += '<div class="growth-box">';
    html += '<div class="growth-box-title">Oferta A</div>';
    html += '<div class="growth-box-value">200%</div>';
    html += '<div class="growth-box-detail">Volume: 500</div>';
    html += '<div class="growth-box-detail">+1.000 pessoas</div>';
    html += '</div>';
    html += '<div class="growth-vs">VS</div>';
    html += '<div class="growth-box">';
    html += '<div class="growth-box-title">Oferta B</div>';
    html += '<div class="growth-box-value">15%</div>';
    html += '<div class="growth-box-detail">Volume: 20.000</div>';
    html += '<div class="growth-box-detail">+3.000 pessoas</div>';
    html += '</div>';
    html += '</div>';
    container.innerHTML = html;
  }

  function createSaturationVisual(containerId) {
    var container = document.getElementById(containerId);
    if (!container) return;

    var html = '<div class="saturation-visual">';
    html += '<div class="sat-col"><div class="sat-label">Mercado vazio</div>';
    for (var i = 0; i < 2; i++) {
      html += '<div class="sat-person sat-person-single"></div>';
    }
    html += '</div>';
    html += '<div class="sat-arrow">→</div>';
    html += '<div class="sat-col"><div class="sat-label">Mercado lotado</div>';
    for (var i = 0; i < 10; i++) {
      html += '<div class="sat-person sat-person-many"></div>';
    }
    html += '</div>';
    html += '</div>';
    container.innerHTML = html;
  }

  return {
    createVisualDiagnosis,
    createCampaignDiagnosis,
    createVolumeComparison,
    createGrowthComparison,
    createSaturationVisual
  };
})();
