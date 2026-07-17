/* Offer Intelligence — Learning Data v1.0 */
/* 26 aulas em 8 modulos. Dados MOCK. Nenhuma API externa chamada. */

const LEARNING_MODULES = [
  {
    id: 'mod-1',
    title: 'Primeiros Passos',
    subtitle: 'O basico sobre ofertas, afiliados e comissao',
    lessons: [
      {
        id: 'lesson-1',
        title: 'O que e uma oferta?',
        objective: 'Entender o que compoe uma oferta: produto, preco, pagina, promessa, comissao e plataforma.',
        duration: '4 min',
        narration: 'Uma oferta nao e apenas o produto. E o conjunto de produto, preco, pagina de vendas, promessa, comissao e plataforma de afiliados. Vamos ver um exemplo pratico.',
        highlight: { element: '#detail-content', view: 'detail', offerId: 'off-001' },
        steps: [
          { text: 'O produto e o curso ou servico que esta sendo vendido.', highlight: '.detail-field:first-child', label: 'Produto' },
          { text: 'O preco e o valor atual. Repare que ha um preco original riscado para mostrar desconto.', highlight: '.detail-field:nth-child(1)', label: 'Preco' },
          { text: 'A comissao e o percentual que o afiliado recebe por venda.', highlight: '.detail-field:nth-child(3)', label: 'Comissao' },
          { text: 'A plataforma e onde a oferta esta hospedada, como Hotmart, Amazon ou Braip.', highlight: '.detail-grid .detail-field:nth-child(6)', label: 'Plataforma' }
        ],
        analogy: 'Imagine uma loja. O produto e o que esta na prateleira. A oferta inclui o preco, a apresentacao, as condicoes e o motivo dado para comprar.',
        quiz: {
          question: 'Qual destes elementos faz parte de uma oferta?',
          options: ['Apenas o produto', 'Produto, preco, pagina e comissao', 'Apenas o preco', 'Apenas a comissao'],
          correct: 1,
          explanation: 'Uma oferta inclui produto, preco, pagina de vendas, promessa e comissao. Nao e apenas o produto ou apenas o preco.'
        },
        exercise: { type: 'identify', target: '.detail-field-label:contains("Comissao")', instruction: 'Localize onde aparece a comissao nesta oferta.', hint: 'Olhe os campos na secao de Informacoes da Oferta.' },
        summary: 'Oferta = produto + preco + pagina + comissao + plataforma'
      },
      {
        id: 'lesson-2',
        title: 'O que e um afiliado?',
        objective: 'Entender o papel do afiliado: divulgacao, link rastreavel, venda atribuida e comissao.',
        duration: '3 min',
        narration: 'Afiliado e a pessoa que divulga produtos de outras empresas e ganha comissao por cada venda realizada atraves do seu link unico.',
        highlight: { element: '.detail-field:contains("Afiliacao")', view: 'detail', offerId: 'off-001' },
        steps: [
          { text: 'Afiliado divulga produtos de outras empresas.', highlight: '.detail-field:nth-child(5)', label: 'Afiliacao' },
          { text: 'Cada afiliado tem um link unico que rastreia quem indicou a venda.', highlight: '.detail-field-value', label: 'Link' },
          { text: 'Nao existe garantia de venda. O afiliado so ganha quando alguem compra.', highlight: null, label: '' }
        ],
        analogy: 'E como ser um vendedor que trabalha em casa e so ganha quando vende. Seu link e seu cracha de identificacao.',
        quiz: {
          question: 'Como o afiliado ganha dinheiro?',
          options: ['Pagando para divulgar', 'Quando alguem compra pelo seu link', 'Apenas por se cadastrar', 'Divulgando de graca'],
          correct: 1,
          explanation: 'O afiliado so recebe comissao quando uma compra e realizada atraves do seu link de afiliado.'
        },
        summary: 'Afiliado divulga, link rastreia, venda atribui, comissao paga'
      },
      {
        id: 'lesson-3',
        title: 'O que e uma comissao?',
        objective: 'Entender comissao percentual, valor aproximado e que comissao nao e lucro.',
        duration: '4 min',
        narration: 'Comissao e a porcentagem do preco que o afiliado recebe quando alguem compra pelo seu link. Mas atencao: comissao nao e lucro.',
        highlight: { element: '.detail-field:nth-child(3)', view: 'detail', offerId: 'off-014' },
        steps: [
          { text: 'Esta oferta tem comissao de 70%. Se custa R$ 47, a comissao bruta seria R$ 32,90.', highlight: '.detail-field:nth-child(3)', label: 'Comissao 70%' },
          { text: 'Comissao nao e lucro. Custos com anuncio, ferramentas, impostos e reembolsos reduzem o valor.', highlight: null, label: '' },
          { text: 'Uma comissao alta pode ser atraente, mas precisa ser avaliada junto com outros fatores.', highlight: null, label: '' }
        ],
        analogy: 'E a sua parte no bolo: quanto maior a fatia, mais voce ganha. Mas o bolo inteiro (preco) tambem importa.',
        quiz: {
          question: 'Se um produto custa R$ 100 e paga 50% de comissao, quanto o afiliado recebe?',
          options: ['R$ 100', 'R$ 50', 'R$ 25', 'R$ 75'],
          correct: 1,
          explanation: '50% de R$ 100 = R$ 50 de comissao bruta. Mas lembre-se: ainda ha custos antes de ter lucro.'
        },
        summary: 'Comissao = percentual do preco; comissao nao e lucro'
      }
    ]
  },
  {
    id: 'mod-2',
    title: 'Entendendo a Procura',
    subtitle: 'Volume, crescimento e quando o crescimento alto pode enganar',
    lessons: [
      {
        id: 'lesson-4',
        title: 'O que e volume de busca?',
        objective: 'Entender volume como tamanho aproximado da procura e que volume nao significa venda.',
        duration: '4 min',
        narration: 'Volume de busca mostra quantas pessoas estao procurando por este produto ou assunto. Quanto maior o volume, maior o publico potencial.',
        highlight: { element: '.detail-field:contains("Volume")', view: 'detail', offerId: 'off-013' },
        steps: [
          { text: 'Este produto tem volume de 18.900 buscas por mes. E um numero alto.', highlight: '.detail-field:contains("Volume")', label: '18.900' },
          { text: 'Compare com uma oferta de volume baixo, como 450 buscas.', highlight: null, label: '' },
          { text: 'Volume alto significa que muitas pessoas procuram, mas nao significa que todas comprarao.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Volume de busca alto significa:',
          options: ['Venda garantida', 'Muitas pessoas procurando', 'Produto de qualidade', 'Comissao alta'],
          correct: 1,
          explanation: 'Volume alto indica que muitas pessoas estao procurando, mas nao garante venda ou qualidade.'
        },
        summary: 'Volume = tamanho da procura; nao significa venda'
      },
      {
        id: 'lesson-5',
        title: 'O que e crescimento?',
        objective: 'Entender crescimento percentual, direcao e periodo de 30 vs 90 dias.',
        duration: '4 min',
        narration: 'Crescimento mostra se a procura pelo produto esta aumentando, diminuindo ou estavel. O grafico abaixo mostra a tendencia.',
        highlight: { element: '.detail-field:contains("Cresc 90d")', view: 'detail', offerId: 'off-010' },
        steps: [
          { text: 'Crescimento de 180% em 90 dias significa que a procura quase triplicou em 3 meses.', highlight: '.detail-field:contains("Cresc")', label: '+180%' },
          { text: 'Direcao "up" significa tendencia de alta.', highlight: '.detail-field:contains("Direcao")', label: 'up' },
          { text: 'Persistencia indica ha quanto tempo a tendencia se mantem.', highlight: '.detail-field:contains("Persistencia")', label: '12 meses' }
        ],
        quiz: {
          question: 'Um crescimento de 90% em 90 dias significa:',
          options: ['A procura caiu', 'A procura quase dobrou', 'O preco aumentou', 'Nada mudou'],
          correct: 1,
          explanation: '90% de crescimento significa que a procura quase dobrou em relacao ao periodo anterior.'
        },
        summary: 'Crescimento = direcao + percentual + periodo'
      },
      {
        id: 'lesson-6',
        title: 'Crescimento alto pode enganar',
        objective: 'Entender que crescimento percentual alto sobre base pequena pode representar menos que crescimento baixo sobre base grande.',
        duration: '5 min',
        narration: 'Cuidado: crescer 200% sobre um numero pequeno pode representar menos pessoas do que crescer 15% sobre um numero grande. Vamos comparar.',
        highlight: { element: '#view-comparator', view: 'comparator' },
        steps: [
          { text: 'Oferta A: volume 500, crescimento de 200% -> aumento de 1.000 pessoas.', highlight: null, label: 'A: +1.000' },
          { text: 'Oferta B: volume 20.000, crescimento de 15% -> aumento de 3.000 pessoas.', highlight: null, label: 'B: +3.000' },
          { text: 'Crescimento de 15% sobre 20.000 = 3.000 novas pessoas. Crescimento de 200% sobre 500 = 1.000.', highlight: null, label: '' },
          { text: 'Por isso, olhe sempre o numero absoluto, nao apenas o percentual.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Oferta A: volume 500, crescimento 200%. Oferta B: volume 20.000, crescimento 15%. Qual adicionou mais pessoas?',
          options: ['Oferta A', 'Oferta B', 'As duas igual', 'Nao da para saber'],
          correct: 1,
          explanation: '200% de 500 = 1.000 pessoas. 15% de 20.000 = 3.000 pessoas. A oferta B adicionou mais pessoas, mesmo com crescimento percentual menor.'
        },
        summary: 'Crescimento percentual alto em base pequena pode enganar'
      }
    ]
  },
  {
    id: 'mod-3',
    title: 'Confianca e Evidencias',
    subtitle: 'De onde vieram os dados e quanto confiar neles',
    lessons: [
      {
        id: 'lesson-7',
        title: 'O que e confianca?',
        objective: 'Entender os niveis de confianca: alta, media e baixa, baseados em fontes e atualidade.',
        duration: '3 min',
        narration: 'Confianca mostra o quanto podemos confiar nas informacoes. Dados recentes de fontes confiaveis geram confianca alta. Dados antigos ou de fontes unicas geram confianca baixa.',
        highlight: { element: '.detail-field:contains("Confianca")', view: 'detail', offerId: 'off-013' },
        steps: [
          { text: 'Confianca 95%: dados muito recentes de fonte confiavel (Amazon API).', highlight: '.detail-score', label: '95%' },
          { text: 'Confianca media (60-79%): dados recentes mas de fontes manuais.', highlight: null, label: '' },
          { text: 'Confianca baixa (abaixo de 60%): dados antigos ou poucas fontes.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'O que gera confianca alta nos dados?',
          options: ['Dados antigos', 'Fontes recentes e confiaveis', 'Poucas fontes', 'Dados sem verificacao'],
          correct: 1,
          explanation: 'Confianca alta vem de fontes confiaveis, dados recentes e multiplas fontes corroborando.'
        },
        summary: 'Confianca = fontes + atualidade + qualidade'
      },
      {
        id: 'lesson-8',
        title: 'De onde veio este numero?',
        objective: 'Entender as classificacoes de fonte: REAL, ESTIMADO, MANUAL, INFERIDO, CALCULADO, MOCK.',
        duration: '4 min',
        narration: 'Cada dado tem uma origem registrada. Vamos ver as diferencas entre os tipos de fonte.',
        highlight: { element: '#view-sources', view: 'sources', offerId: 'off-003' },
        steps: [
          { text: 'Fonte REAL: dados obtidos diretamente de uma API oficial ou banco de dados.', highlight: '.source-item:first-child', label: 'REAL' },
          { text: 'Fonte ESTIMADA: calculo aproximado baseado em dados indiretos.', highlight: null, label: 'ESTIMADO' },
          { text: 'Fonte MANUAL: inserido por analise humana.', highlight: null, label: 'MANUAL' },
          { text: 'Fonte INFERIDA: deduzida de outros dados disponiveis.', highlight: null, label: 'INFERIDO' },
          { text: 'Fonte CALCULADA: derivada de formula.', highlight: null, label: 'CALCULADO' },
          { text: 'Fonte MOCK: dados ficticios para demonstracao.', highlight: null, label: 'MOCK' }
        ],
        quiz: {
          question: 'Qual classificacao indica que o dado veio diretamente de uma API oficial?',
          options: ['MOCK', 'REAL', 'ESTIMADO', 'MANUAL'],
          correct: 1,
          explanation: 'REAL significa que o dado foi obtido de uma fonte oficial como API de marketplace ou banco de dados.'
        },
        summary: 'Fontes: REAL, ESTIMADO, MANUAL, INFERIDO, CALCULADO, MOCK'
      },
      {
        id: 'lesson-9',
        title: 'Dados antigos podem enganar',
        objective: 'Entender que dados desatualizados podem nao refletir o mercado atual.',
        duration: '3 min',
        narration: 'Este dado pode ter sido verdadeiro quando foi coletado, mas o mercado pode ter mudado. Dados antigos sao menos confiaveis.',
        highlight: { element: '.detail-field:contains("Atualizacao")', view: 'detail', offerId: 'off-015' },
        steps: [
          { text: 'Esta oferta foi atualizada ha 25 dias. O mercado pode ter mudado desde entao.', highlight: '.detail-field:contains("Atualizacao")', label: '25 dias' },
          { text: 'Sempre prefira dados com menos de 7 dias para decisoes.', highlight: null, label: '' },
          { text: 'Dados muito antigos (30+ dias) podem levar a decisoes equivocadas.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Dados de 25 dias atras sao considerados:',
          options: ['Muito recentes', 'Antigos - podem estar desatualizados', 'Sempre confiaveis', 'Melhores que dados novos'],
          correct: 1,
          explanation: 'Dados com mais de 7 dias podem estar desatualizados. Com 25 dias, o mercado pode ter mudado significativamente.'
        },
        summary: 'Dados recentes = mais confiaveis; dados antigos podem enganar'
      }
    ]
  },
  {
    id: 'mod-4',
    title: 'Riscos',
    subtitle: 'Saturacao, politica de anuncios e penalidades',
    lessons: [
      {
        id: 'lesson-10',
        title: 'O que e saturacao?',
        objective: 'Entender saturacao como nivel de concorrencia na divulgacao da mesma oferta.',
        duration: '4 min',
        narration: 'Saturacao mostra se muitas pessoas ja estao divulgando a mesma oferta. Muita concorrencia pode aumentar o custo para conseguir vendas.',
        highlight: { element: '.detail-field:contains("Saturacao")', view: 'detail', offerId: 'off-013' },
        steps: [
          { text: 'Saturacao alta: muitos afiliados divulgando. Concorrencia acirrada.', highlight: '.detail-field:contains("Saturacao")', label: 'Alto' },
          { text: 'Saturacao baixa: oportunidade pouco explorada. Pode ser mais facil vender.', highlight: null, label: '' },
          { text: 'Saturacao nao significa impossibilidade, mas exige mais investimento e criatividade.', highlight: null, label: '' }
        ],
        analogy: 'E como uma praia: se ja tem muita gente, fica dificil achar um lugar bom. Se esta vazia, voce escolhe o melhor lugar.',
        quiz: {
          question: 'Saturacao alta significa:',
          options: ['Muitas pessoas divulgando', 'Pouca concorrencia', 'Produto ruim', 'Preco baixo'],
          correct: 0,
          explanation: 'Saturacao alta indica que muitos afiliados ja estao divulgando, aumentando a concorrencia.'
        },
        summary: 'Saturacao = nivel de concorrencia; alta = mais disputa'
      },
      {
        id: 'lesson-11',
        title: 'O que e risco de politica?',
        objective: 'Entender que algumas ofertas podem ser restritas por politicas de plataformas de anuncio.',
        duration: '3 min',
        narration: 'Risco de politica indica a chance de as plataformas de anuncio limitarem ou bloquearem a divulgacao de um produto.',
        highlight: { element: '.detail-field:contains("Risco Politica")', view: 'detail', offerId: 'off-002' },
        steps: [
          { text: 'Risco alto: produtos de saude sem comprovacao cientifica, financas com promessas exageradas.', highlight: '.detail-field:contains("Risco")', label: 'Alto' },
          { text: 'Risco medio: produtos em areas regulamentadas mas com documentacao.', highlight: null, label: '' },
          { text: 'Risco baixo: produtos gerais sem restricoes.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Qual produto tem maior risco de politica?',
          options: ['Curso de idiomas', 'Produto de saude sem comprovacao', 'Fone Bluetooth', 'Livro de receitas'],
          correct: 1,
          explanation: 'Produtos de saude sem comprovacao cientifica tem alto risco de serem bloqueados por plataformas de anuncio.'
        },
        summary: 'Risco de politica = chance de restricao de anuncios'
      },
      {
        id: 'lesson-12',
        title: 'Por que esta oferta perdeu pontos?',
        objective: 'Entender como penalidades afetam o score, usando diagnostico visual.',
        duration: '6 min',
        narration: 'Esta oferta nao recebeu nota baixa por um unico motivo. Ela perdeu pontos porque a procura e pequena, os dados estao antigos e a concorrencia e elevada.',
        highlight: { element: '#detail-content', view: 'detail', offerId: 'off-009' },
        steps: [
          { text: 'Baixo volume: apenas 680 buscas por mes. Procura muito pequena.', highlight: '.detail-field:contains("Volume")', label: '680 buscas' },
          { text: 'Dados antigos: evidencia de 20 dias atras. Confianca comprometida.', highlight: '.detail-field:contains("Atualizacao")', label: '20 dias' },
          { text: 'Declinio acelerado: -45% em 90 dias. A procura esta caindo rapido.', highlight: '.detail-field:contains("Cresc")', label: '-45%' },
          { text: 'Penalidade por saturacao + risco de politica reduzem ainda mais o score.', highlight: '.detail-field:contains("Penalties")', label: 'Penalidades' }
        ],
        quiz: {
          question: 'Por que esta oferta perdeu pontos?',
          options: ['Apenas um motivo', 'Multiplos fatores: volume baixo, dados antigos, declinio', 'O preco e alto', 'A comissao e baixa'],
          correct: 1,
          explanation: 'A oferta perdeu pontos por varios motivos combinados: baixa procura, dados desatualizados e tendencia de queda.'
        },
        summary: 'Penalidades acumulam: baixo volume + dados antigos + saturacao'
      }
    ]
  },
  {
    id: 'mod-5',
    title: 'Interpretando o Score',
    subtitle: 'Entendendo a nota, componentes e o que ela realmente significa',
    lessons: [
      {
        id: 'lesson-13',
        title: 'O que e o score?',
        objective: 'Entender que score e uma combinacao de metricas, nao uma garantia de resultado.',
        duration: '3 min',
        narration: 'O score e uma nota de 0 a 100 que combina 11 componentes: crescimento, volume, comissao, persistencia, anuncios, qualidade, afiliacao, atualidade, confianca, saturacao e politica.',
        highlight: { element: '.detail-score', view: 'detail', offerId: 'off-010' },
        steps: [
          { text: 'Score 96: nota excelente. Significa que os sinais disponiveis sao muito favoraveis.', highlight: '.detail-score-value', label: '96/100' },
          { text: 'Mas atencao: score nao e previsao garantida de lucro. E apenas uma indicacao.', highlight: null, label: '' },
          { text: 'A versao da formula usada e offer-score-v1.0.', highlight: '.detail-score-label', label: 'v1.0' }
        ],
        quiz: {
          question: 'O score e:',
          options: ['Previsao garantida de lucro', 'Combinacao de metricas indicativas', 'Opiniao pessoal', 'Preco do produto'],
          correct: 1,
          explanation: 'O score combina metricas como crescimento, volume e confianca para dar uma indicacao, mas nao e garantia de resultado.'
        },
        summary: 'Score = 0 a 100, combina metricas, nao e garantia'
      },
      {
        id: 'lesson-14',
        title: 'Pontos positivos e penalidades',
        objective: 'Entender a separacao entre pontos conquistados e pontos perdidos no score.',
        duration: '4 min',
        narration: 'O score separa visualmente o que a oferta conquistou e o que ela perdeu em penalidades. Vamos analisar.',
        highlight: { element: '.comp-list', view: 'detail', offerId: 'off-014' },
        steps: [
          { text: 'Pontos conquistados: componentes como crescimento e comissao contribuem positivamente.', highlight: '.comp-item:first-child', label: 'Positivos' },
          { text: 'Pontos perdidos: saturacao e risco de politica sao penalidades.', highlight: '.detail-field:contains("Penalties")', label: 'Penalidades' },
          { text: 'Dados ausentes tambem reduzem a confianca final do score.', highlight: '.detail-field:contains("Dados Ausentes")', label: 'Ausentes' }
        ],
        quiz: {
          question: 'O que acontece quando uma oferta tem dados ausentes?',
          options: ['O score aumenta', 'A confianca e reduzida', 'Nada acontece', 'O preco diminui'],
          correct: 1,
          explanation: 'Dados ausentes reduzem a confianca do score porque menos informacoes estao disponiveis para a analise.'
        },
        summary: 'Score = pontos positivos - penalidades + ajuste de confianca'
      },
      {
        id: 'lesson-15',
        title: 'Uma nota alta nao garante resultado',
        objective: 'Entender que score alto indica sinais favoraveis, mas ainda exige teste real.',
        duration: '3 min',
        narration: 'Uma nota alta significa que os sinais disponiveis sao favoraveis. Ainda e necessario testar com limite de custo e condicao de parada.',
        highlight: { element: '.detail-score', view: 'detail', offerId: 'off-001' },
        steps: [
          { text: 'Score 83 e uma nota forte. Mas isso nao significa lucro certo.', highlight: '.detail-score-value', label: '83/100' },
          { text: 'Teste sempre com orcamento limitado e condicao de parada definida.', highlight: null, label: '' },
          { text: 'Acompanhe os resultados e ajuste conforme os dados reais aparecerem.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Com um score alto, voce deve:',
          options: ['Investir todo o orcamento', 'Ignorar e procurar outra', 'Testar com limite controlado', 'Desistir do produto'],
          correct: 2,
          explanation: 'Score alto e um bom sinal, mas sempre teste com orcamento controlado e condicao de parada antes de escalar.'
        },
        summary: 'Nota alta = sinal favoravel, nao lucro garantido'
      }
    ]
  },
  {
    id: 'mod-6',
    title: 'Comparando Ofertas',
    subtitle: 'Usando o comparador para escolher entre multiplas opcoes',
    lessons: [
      {
        id: 'lesson-16',
        title: 'Oferta que cresce mais',
        objective: 'Aprender a identificar a oferta com maior potencial de crescimento usando o comparador.',
        duration: '3 min',
        narration: 'Vamos usar o comparador para ver qual oferta esta crescendo mais.',
        highlight: { element: '#view-comparator', view: 'comparator' },
        steps: [
          { text: 'Selecione duas ofertas no comparador.', highlight: '.comp-select', label: 'Selecionar' },
          { text: 'Compare a coluna de crescimento 90d. Quanto maior, melhor.', highlight: '.comp-table-wrap', label: 'Crescimento' },
          { text: 'Verifique tambem a persistencia do crescimento.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Ao comparar crescimento, voce deve olhar:',
          options: ['Apenas o percentual', 'Percentual e periodo', 'Apenas o nome', 'Apenas o preco'],
          correct: 1,
          explanation: 'Compare tanto o percentual de crescimento quanto o periodo para ter uma visao completa.'
        },
        summary: 'Crescimento + persistencia = sinais de oportunidade'
      },
      {
        id: 'lesson-17',
        title: 'Oferta com maior publico',
        objective: 'Identificar qual oferta tem maior volume de busca e publico potencial.',
        duration: '3 min',
        narration: 'Vamos usar o comparador para ver qual oferta tem o maior publico potencial.',
        highlight: { element: '#view-comparator', view: 'comparator' },
        steps: [
          { text: 'Compare a coluna de volume de busca.', highlight: '.comp-table-wrap', label: 'Volume' },
          { text: 'Maior volume = maior publico potencial.', highlight: null, label: '' },
          { text: 'Mas lembre-se: volume alto nao significa venda garantida.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Volume de busca maior significa:',
          options: ['Venda garantida', 'Maior publico potencial', 'Melhor produto', 'Maior comissao'],
          correct: 1,
          explanation: 'Maior volume indica mais pessoas procurando, o que significa maior publico potencial, mas nao venda garantida.'
        },
        summary: 'Volume = tamanho do publico potencial'
      },
      {
        id: 'lesson-18',
        title: 'Oferta que paga mais',
        objective: 'Comparar comissao percentual, valor aproximado e entender custos.',
        duration: '3 min',
        narration: 'Vamos ver qual oferta paga a melhor comissao.',
        highlight: { element: '#view-comparator', view: 'comparator' },
        steps: [
          { text: 'Compare a comissao percentual entre as ofertas.', highlight: '.comp-table-wrap', label: 'Comissao' },
          { text: 'Calcule o valor aproximado: preco x comissao.', highlight: null, label: '' },
          { text: 'Lembre-se: comissao bruta nao considera custos de anuncio.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Comissao de 70% sobre R$ 47 equivale a:',
          options: ['R$ 47', 'R$ 32,90', 'R$ 70', 'R$ 100'],
          correct: 1,
          explanation: '70% de R$ 47 = R$ 32,90 de comissao bruta. Mas ainda ha custos a considerar.'
        },
        summary: 'Comissao = percentual x preco; bruta nao e liquida'
      },
      {
        id: 'lesson-19',
        title: 'Qual escolher?',
        objective: 'Exercicio interativo de escolha entre tres ofertas com perfis diferentes.',
        duration: '6 min',
        narration: 'Vamos analisar tres ofertas diferentes e decidir qual parece mais adequada para um teste pequeno e controlado.',
        highlight: { element: '.comp-select', view: 'comparator' },
        steps: [
          { text: 'Oferta A: crescimento alto, volume baixo, comissao alta, confianca media.', highlight: null, label: 'A' },
          { text: 'Oferta B: crescimento moderado, volume alto, comissao media, confianca alta.', highlight: null, label: 'B' },
          { text: 'Oferta C: comissao muito alta, tendencia em queda, risco alto.', highlight: null, label: 'C' }
        ],
        quiz: {
          question: 'Qual oferta parece mais adequada para um teste pequeno e controlado?',
          options: ['Oferta A: alto crescimento mas baixo volume', 'Oferta B: volume alto e confianca alta', 'Oferta C: comissao alta mas em queda'],
          correct: 1,
          explanation: 'A oferta B combina volume alto com confianca alta e crescimento moderado. A oferta A tem base pequena e a oferta C esta em declinio. Nao ha resposta unica, mas a B oferece menor risco para um teste inicial.'
        },
        summary: 'Escolha = equilibrar crescimento, volume, confianca e risco'
      }
    ]
  },
  {
    id: 'mod-7',
    title: 'Campanhas e Testes',
    subtitle: 'Testes limitados, diagnostico de campanha e quando parar ou ampliar',
    lessons: [
      {
        id: 'lesson-20',
        title: 'O que e um teste limitado?',
        objective: 'Entender os elementos de um teste: orcamento maximo, prazo, hipotese, metrica e condicao de parada.',
        duration: '4 min',
        narration: 'Um teste limitado tem orcamento maximo, prazo definido, hipotese clara e condicao de parada. Nunca invista todo o orcamento de uma vez.',
        highlight: { element: '#view-analysis', view: 'analysis', offerId: 'off-001' },
        steps: [
          { text: 'Defina um orcamento maximo que voce esta disposto a gastar.', highlight: '.analysis-section:contains("Plano de Teste")', label: 'Orcamento' },
          { text: 'Estabeleca um prazo para avaliar os resultados.', highlight: null, label: '' },
          { text: 'Defina condicoes de parada: se nao vender ate X, pare o teste.', highlight: '.analysis-section:contains("Condicoes")', label: 'Parada' }
        ],
        quiz: {
          question: 'Um teste limitado deve ter:',
          options: ['Orcamento ilimitado', 'Prazo, orcamento e condicao de parada', 'Apenas orcamento', 'Apenas prazo'],
          correct: 1,
          explanation: 'Um teste limitado precisa de orcamento maximo, prazo definido e condicao de parada para evitar perdas.'
        },
        summary: 'Teste = orcamento + prazo + hipotese + condicao de parada'
      },
      {
        id: 'lesson-21',
        title: 'Campanha ruim — descubra o motivo',
        objective: 'Diagnosticar visualmente uma campanha problematica: custo alto, poucos cliques, nenhuma venda.',
        duration: '6 min',
        narration: 'Esta campanha esta com problema. Vamos descobrir juntos o motivo.',
        highlight: { element: '#view-analysis', view: 'analysis', offerId: 'off-006' },
        steps: [
          { text: 'Custo alto: a campanha gastou muito em relacao aos resultados.', highlight: null, label: 'Custo alto' },
          { text: 'Poucos cliques: as pessoas viram o anuncio mas nao clicaram.', highlight: null, label: 'Poucos cliques' },
          { text: 'Nenhuma venda: mesmo com alguns cliques, ninguem comprou.', highlight: null, label: 'Sem vendas' },
          { text: 'A campanha gastou muito, recebeu poucos cliques e nao gerou vendas. O problema nao esta apenas no custo: poucas pessoas demonstraram interesse depois de ver o anuncio.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Qual o principal problema desta campanha?',
          options: ['Apenas o custo alto', 'Combinacao de custo alto, poucos cliques e nenhuma venda', 'Apenas a falta de vendas', 'Nao ha problema'],
          correct: 1,
          explanation: 'A campanha combina tres problemas: gastou muito, teve poucos cliques e nao gerou vendas. Cada indicador agrava o outro.'
        },
        summary: 'Campanha problematica = alto custo + baixo engajamento + zero conversao'
      },
      {
        id: 'lesson-22',
        title: 'Quando parar uma campanha?',
        objective: 'Ensinar os sinais de que uma campanha deve ser interrompida.',
        duration: '3 min',
        narration: 'Saiba reconhecer quando e hora de parar: limite de gasto atingido, ausencia de sinal de melhora, piora nos resultados, erro tecnico ou risco elevado.',
        highlight: { element: '#view-monitoring', view: 'monitoring' },
        steps: [
          { text: 'Limite de gasto: pare quando o orcamento definido acabar.', highlight: '.alert-item', label: 'Limite' },
          { text: 'Ausencia de sinal: se nenhuma metrica positiva aparecer, pare.', highlight: null, label: '' },
          { text: 'Piora consistente: se os resultados estao piorando, nao insista.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Quando voce deve parar uma campanha?',
          options: ['Nunca', 'Quando o orcamento acabar sem resultados', 'Apenas se der prejuizo', 'Depois de 1 dia'],
          correct: 1,
          explanation: 'Pare quando o orcamento definido acabar sem sinais positivos, ou antes se os resultados estiverem piorando.'
        },
        summary: 'Pare ao atingir o limite, se nao houver sinal ou se piorar'
      },
      {
        id: 'lesson-23',
        title: 'Quando ampliar?',
        objective: 'Ensinar os criterios para escalar uma campanha que esta funcionando.',
        duration: '3 min',
        narration: 'Amplie quando tiver resultado repetido, margem positiva, confianca nos dados, capacidade de entrega e aprovacao.',
        highlight: { element: '#view-dashboard', view: 'dashboard' },
        steps: [
          { text: 'Resultado repetido: a campanha funcionou mais de uma vez.', highlight: '.stat-item:first-child', label: 'Consistencia' },
          { text: 'Margem positiva: o retorno supera os custos.', highlight: null, label: '' },
          { text: 'Escala gradual: aumente o orcamento aos poucos, nunca de uma vez.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Antes de ampliar uma campanha, voce precisa de:',
          options: ['Sorte', 'Resultado repetido e margem positiva', 'Muito dinheiro', 'Indicacao de amigo'],
          correct: 1,
          explanation: 'So amplie quando tiver resultados repetidos, margem positiva e confianca nos dados. Escale gradualmente.'
        },
        summary: 'Amplie com consistencia, margem positiva e escala gradual'
      }
    ]
  },
  {
    id: 'mod-8',
    title: 'ROI e Decisao',
    subtitle: 'Receita vs lucro, ROI, decisao final e revisao geral',
    lessons: [
      {
        id: 'lesson-24',
        title: 'Receita nao e lucro',
        objective: 'Entender a diferenca entre vendas, comissao, gastos e lucro liquido.',
        duration: '4 min',
        narration: 'Vender muito nao significa lucro alto. E preciso considerar gastos com anuncio, ferramentas, impostos e reembolsos.',
        highlight: { element: '#view-analysis', view: 'analysis', offerId: 'off-001' },
        steps: [
          { text: 'Vendas: o valor total vendido.', highlight: null, label: 'Vendas' },
          { text: 'Comissao: o percentual que voce recebe.', highlight: null, label: 'Comissao' },
          { text: 'Gastos: anuncio, ferramentas, impostos e reembolsos reduzem o lucro.', highlight: null, label: 'Gastos' },
          { text: 'Lucro liquido = comissao - gastos. Nem sempre e positivo.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Lucro liquido e:',
          options: ['O valor total vendido', 'A comissao bruta', 'Comissao - gastos', 'O preco do produto'],
          correct: 2,
          explanation: 'Lucro liquido = comissao recebida - todos os gastos (anuncio, ferramentas, impostos, reembolsos).'
        },
        summary: 'Lucro = comissao - gastos; receita nao e lucro'
      },
      {
        id: 'lesson-25',
        title: 'O que e ROI?',
        objective: 'Entender ROI de forma simples: retorno sobre o investimento.',
        duration: '3 min',
        narration: 'ROI mostra quanto voce ganhou comparado ao que gastou. E uma medida simples de eficiencia.',
        highlight: { element: '#view-setting', view: 'settings' },
        steps: [
          { text: 'Exemplo: gastou R$ 100, retorno liquido de R$ 150. Ganhou R$ 50 acima do gasto.', highlight: null, label: '' },
          { text: 'ROI positivo = ganhou mais do que gastou. ROI negativo = perdeu dinheiro.', highlight: null, label: '' },
          { text: 'Use ROI para comparar diferentes campanhas e ofertas.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'ROI positivo significa:',
          options: ['Gastou mais do que ganhou', 'Ganhou mais do que gastou', 'Nao teve lucro', 'So teve prejuizo'],
          correct: 1,
          explanation: 'ROI positivo indica que o retorno foi maior que o investimento, ou seja, houve lucro.'
        },
        summary: 'ROI = (retorno - investimento) / investimento'
      },
      {
        id: 'lesson-26',
        title: 'Decisao final',
        objective: 'Simulacao completa de analise e decisao com tres ofertas.',
        duration: '8 min',
        narration: 'Vamos simular uma decisao completa: observar, analisar, comparar e escolher uma oferta para teste.',
        highlight: { element: '#view-comparator', view: 'comparator' },
        steps: [
          { text: 'Observe as tres ofertas disponiveis no comparador.', highlight: '.comp-select', label: '3 ofertas' },
          { text: 'Analise os detalhes de cada uma: score, crescimento, volume, comissao.', highlight: '#analysis-content', label: 'Analise' },
          { text: 'Compare lado a lado: pontos fortes e fracos de cada.', highlight: '.comp-table-wrap', label: 'Comparar' },
          { text: 'Escolha uma para teste com orcamento MOCK e condicao de parada.', highlight: null, label: '' }
        ],
        quiz: {
          question: 'Qual o primeiro passo para uma decisao informada?',
          options: ['Escolher aleatoriamente', 'Observar, analisar e comparar', 'Investir tudo de uma vez', 'Perguntar a um amigo'],
          correct: 1,
          explanation: 'Sempre observe as opcoes, analise os dados disponiveis e compare antes de decidir.'
        },
        summary: 'Decisao = observar + analisar + comparar + testar com controle'
      }
    ]
  }
];

const REVIEW_LESSON = {
  id: 'lesson-review',
  title: 'Revisao geral',
  moduleTitle: 'Revisao',
  objective: 'Revisar todos os conceitos aprendidos ao longo do curso.',
  duration: '5 min',
  narration: 'Parabens por chegar ate aqui! Vamos revisar os principais conceitos que voce aprendeu ao longo do curso.',
  highlight: { element: '#view-dashboard', view: 'dashboard' },
  steps: [
    { text: 'Voce aprendeu o que e uma oferta, um afiliado e como funciona a comissao.', highlight: null, label: '' },
    { text: 'Entendeu volume de busca, crescimento e como crescimento alto pode enganar.', highlight: null, label: '' },
    { text: 'Descobriu a importancia da confianca, fontes de dados e riscos.', highlight: null, label: '' },
    { text: 'Aprendeu a interpretar o score e comparar ofertas.', highlight: null, label: '' },
    { text: 'Praticou diagnostico de campanhas e entendeu ROI.', highlight: null, label: '' }
  ],
  summary: 'Curso concluido! Voce esta pronto para interpretar ofertas com mais confianca.'
};

/* Total: 26 lessons + 1 review = 27 aulas disponiveis */
function getLesson(id) {
  for (const mod of LEARNING_MODULES) {
    const found = mod.lessons.find(l => l.id === id);
    if (found) return found;
  }
  return null;
}

function getModule(id) {
  return LEARNING_MODULES.find(m => m.id === id);
}

function getAllLessons() {
  const all = [];
  for (const mod of LEARNING_MODULES) {
    for (const lesson of mod.lessons) {
      all.push(lesson);
    }
  }
  return all;
}
