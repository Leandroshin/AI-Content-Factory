/* Offer Intelligence — Glossary v1.0 */

const GLOSSARY = [
  {
    term: 'Oferta',
    simple: 'Um produto ou servico que um afiliado pode divulgar e ganhar comissao.',
    example: 'Um curso online, um ebook, um fone de ouvido na Amazon.',
    analogy: 'E como um catalogo de produtos: voce escolhe o que quer mostrar para ganhar uma comissao.'
  },
  {
    term: 'Afiliado',
    simple: 'A pessoa que divulga produtos de outras empresas e ganha uma comissao por cada venda.',
    example: 'Voce divulga um curso de idiomas e ganha R$ 50 por cada aluno que se matricular.',
    analogy: 'E como ser um vendedor que trabalha em casa e so ganha quando vende.'
  },
  {
    term: 'Comissao',
    simple: 'A porcentagem do preco que o afiliado recebe quando alguem compra pelo seu link.',
    example: 'Se um produto custa R$ 100 e a comissao e 50%, voce ganha R$ 50.',
    analogy: 'E a sua parte no bolo: quanto maior a fatia, mais voce ganha.'
  },
  {
    term: 'Janela do cookie',
    simple: 'O tempo que o link do afiliado "lembra" de quem indicou a compra.',
    example: 'Se a janela e de 30 dias e a pessoa comprar 20 dias depois de clicar no seu link, voce ainda ganha a comissao.',
    analogy: 'E como um ticket de cinema que vale por varios dias: se a pessoa comprar dentro do prazo, voce ganha.'
  },
  {
    term: 'Volume de busca',
    simple: 'Quantas pessoas estao procurando por este produto ou assunto na internet.',
    example: '8.400 pessoas por mes procurando por "curso de criacao de conteudo".',
    analogy: 'E como uma fila na porta da loja: quanto mais gente na fila, mais chance de vender.'
  },
  {
    term: 'Tendencia',
    simple: 'Se a procura pelo produto esta aumentando, diminuindo ou continuando igual.',
    example: 'Uma tendencia de alta significa que mais pessoas estao procurando a cada mes.',
    analogy: 'E como um termometro: mostra se a procura esta esquentando ou esfriando.'
  },
  {
    term: 'Crescimento',
    simple: 'A velocidade com que a procura pelo produto esta mudando.',
    example: 'Crescimento de 90% em 90 dias significa que a procura quase dobrou em 3 meses.',
    analogy: 'E como a velocidade de um carro: mostra se esta acelerando ou desacelerando.'
  },
  {
    term: 'Score',
    simple: 'Uma nota de 0 a 100 que mostra se uma oferta merece atencao.',
    example: 'Nota 85: muito promissora. Nota 30: provavelmente nao vale o esforco.',
    analogy: 'E uma nota na escola: quanto maior, melhor a oportunidade.'
  },
  {
    term: 'Confianca',
    simple: 'O quanto podemos confiar nas informacoes disponiveis sobre a oferta.',
    example: 'Confianca 90%: dados recentes e de fontes confiaveis. Confianca 40%: dados antigos ou incertos.',
    analogy: 'E como a confianca em uma dica de amigo: quanto mais fontes confiaveis, mais seguranca.'
  },
  {
    term: 'Evidencia',
    simple: 'De onde vieram as informacoes sobre a oferta.',
    example: 'URL do produto, dados do marketplace, analise manual.',
    analogy: 'E a "fonte" da noticia: quem viu, onde viu e quando viu.'
  },
  {
    term: 'Saturacao',
    simple: 'Se muitas pessoas ja estao divulgando a mesma oferta.',
    example: 'Saturacao alta: muita concorrencia. Saturacao baixa: oportunidade pouco explorada.',
    analogy: 'E como uma praia: se ja tem muita gente, fica dificil achar um lugar bom.'
  },
  {
    term: 'Risco de politica',
    simple: 'Chance de as plataformas de anuncio limitarem ou bloquearem a divulgacao.',
    example: 'Produtos de saude sem comprovacao cientifica tem alto risco de politica.',
    analogy: 'E como tentar anunciar em um lugar que tem regras: alguns produtos sao proibidos ou restritos.'
  },
  {
    term: 'Anuncio ativo',
    simple: 'Quantas propagandas diferentes estao rodando para este produto.',
    example: '12 anuncios ativos significa que o produtor esta investindo em divulgacao paga.',
    analogy: 'E como ver quantas lojas estao fazendo propaganda na TV: quanto mais anuncios, mais investimento.'
  },
  {
    term: 'Anunciante',
    simple: 'Quantas pessoas ou empresas diferentes estao fazendo anuncio do mesmo produto.',
    example: '4 anunciantes significa que 4 afiliados diferentes estao investindo em propaganda.',
    analogy: 'E como contar quantos vendedores diferentes estao gritando o mesmo produto na feira.'
  },
  {
    term: 'Afiliação',
    simple: 'Se o produto possui um programa de afiliados que voce pode entrar.',
    example: 'Amazon Associates, Hotmart Afiliados, Digistore24 Afiliados.',
    analogy: 'E como ter a chave da loja: sem ela, voce nao pode vender.'
  },
  {
    term: 'ROI',
    simple: 'Retorno sobre o investimento: quanto voce ganhou comparado ao que gastou.',
    example: 'Se gastou R$ 100 e ganhou R$ 300, seu ROI e de 200%.',
    analogy: 'E como medir se valeu a pena: se ganhou mais do que gastou, o retorno e positivo.'
  }
];

const SIMPLE_EXPLANATIONS = {
  search_volume: 'Mostra aproximadamente quantas pessoas estao procurando por esta oferta ou assunto por mes.',
  growth_30d: 'Mostra se a procura aumentou ou diminuiu no ultimo mes.',
  growth_90d: 'Mostra se a procura aumentou ou diminuiu nos ultimos 3 meses.',
  commission_percent: 'E quanto o afiliado pode receber quando acontece uma venda, em porcentagem.',
  cookie_days: 'Por quantos dias o link do afiliado "lembra" quem indicou a compra.',
  evidence_confidence: 'Mostra o quanto podemos confiar nas informacoes disponiveis.',
  saturation_level: 'Mostra se muitas pessoas ja estao disputando a mesma oportunidade.',
  trend_persistence: 'Mostra se o crescimento durou varios meses ou foi apenas um pico rapido.',
  policy_risk: 'Mostra a possibilidade de anuncios serem limitados ou bloqueados pelas plataformas.',
  active_ads: 'Quantas propagandas diferentes estao rodando para este produto.',
  advertiser_count: 'Quantas pessoas diferentes estao anunciando este produto.',
  marketplace_trust: 'A confianca na plataforma onde o produto esta listado.',
  reviews_avg: 'A nota media que os compradores deram para o produto.',
  review_count: 'Quantas pessoas avaliaram o produto.',
  seller_reputation: 'A reputacao do vendedor na plataforma.',
  competition_level: 'Se tem muita ou pouca concorrencia divulgando o mesmo produto.'
};

function getSimpleExplanation(key) {
  return SIMPLE_EXPLANATIONS[key] || '';
}

function getGlossaryHTML() {
  return GLOSSARY.map(g => `
    <div class="glossary-item">
      <strong class="glossary-term">${g.term}</strong>
      <p class="glossary-simple">${g.simple}</p>
      <div class="glossary-details hidden">
        <p><em>Exemplo:</em> ${g.example}</p>
        ${g.analogy ? '<p><em>Analogia:</em> ' + g.analogy + '</p>' : ''}
      </div>
      <button class="glossary-toggle btn-sm" onclick="this.previousElementSibling.classList.toggle('hidden')">Ver mais</button>
    </div>
  `).join('');
}

function openGlossaryTerm(term) {
  /* Pause narration */
  if (Narration && Narration.pause) Narration.pause();
  /* Find and show the term */
  var item = null;
  for (var i = 0; i < GLOSSARY.length; i++) {
    if (GLOSSARY[i].term === term) {
      item = GLOSSARY[i];
      break;
    }
  }
  if (!item) return;

  var html = '<div class="card"><div class="card-header"><h2>Glossario: ' + item.term + '</h2><button class="btn-sm" onclick="closeGlossaryPopup()">Fechar</button></div>';
  html += '<p style="font-size:14px;font-weight:600">' + item.term + '</p>';
  html += '<p style="margin:8px 0;font-size:13px">' + item.simple + '</p>';
  html += '<p style="font-size:12px;color:var(--text-muted)"><em>Exemplo:</em> ' + item.example + '</p>';
  if (item.analogy) {
    html += '<p style="font-size:12px;color:var(--text-muted);margin-top:4px"><em>Analogia:</em> ' + item.analogy + '</p>';
  }
  html += '<button class="btn-sm" style="margin-top:12px" onclick="speakGlossaryTerm(\'' + term + '\')">Ouvir definicao</button>';
  html += '</div>';

  var popup = document.createElement('div');
  popup.id = 'glossary-popup';
  popup.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:9999;max-width:450px;width:90%;';
  popup.innerHTML = html;
  document.body.appendChild(popup);

  var overlay = document.createElement('div');
  overlay.id = 'glossary-popup-overlay';
  overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);z-index:9998;';
  overlay.onclick = function() { closeGlossaryPopup(); };
  document.body.appendChild(overlay);
}

function speakGlossaryTerm(term) {
  var item = null;
  for (var i = 0; i < GLOSSARY.length; i++) {
    if (GLOSSARY[i].term === term) {
      item = GLOSSARY[i];
      break;
    }
  }
  if (item && Narration) {
    Narration.stop();
    Narration.speak(item.term + ': ' + item.simple);
  }
}
