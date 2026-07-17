# Offer Intelligence — Prototipo Visual

**Status:** PROTOTIPO ISOLADO - NAO INTEGRADO

## Sobre
Prototipo visual navegavel da vertical Offer Intelligence para AI Content Factory.
SPA com 11 areas, tema escuro operacional, responsivo (390px a 1440px), sem CDN ou dependencias externas.

## Como executar
```bash
start_server.bat
# Abrir http://localhost:8765
```

Ou:
```bash
python -m http.server 8765
```

## Estrutura
```
offer_intelligence_ui/
  index.html              # SPA com 11 views (inclui Academia)
  styles.css              # Tema escuro + claro, responsivo, sem CDN, ~700 linhas
  app.js                  # Navegacao, filtros, renderizacao, localStorage, Academia
  mock_data.js            # 15 ofertas MOCK + alertas + historicos + campos URL futuros
  scoring.js              # Formula offer-score-v1.0 (11 componentes)
  comparator.js           # Comparacao 2-4 ofertas + analise IA MOCK
  charts.js               # Graficos SVG (donut, scatter, bar, sparkline, comparacao, tendencia)
  narration.js            # speechSynthesis local, fila, pt-BR, velocidade
  glossary.js             # 16 termos + explicacoes + exemplos + analogias
  beginner_mode.js        # Modo Aprender/Profissional + one-liner + scoreReasons
  tutorial.js             # Tour guiado 19 etapas com destaque visual
  learning_data.js        # 8 modulos, 26 aulas, quizzes, narracoes, analogias
  learning_engine.js      # Motor de aulas: destaque, spotlight, navegacao
  quiz_engine.js          # Multipla escolha, 2 tentativas, feedback, correcao
  progress_tracker.js     # Progresso em localStorage, modulos, resumo, reset
  lesson_visuals.js       # Diagnosis visual, comparacao volume/crescimento, saturacao
  start_server.bat        # Servidor local porta 8765
  smoke_test.py           # Testes de validacao (100+ assertions)
  README.md               # Este arquivo
  CODEX_HANDOFF.md        # Handoff para Codex
```

## Funcionalidades Base
- **Visao Geral:** Dashboard com resumo, top ofertas, alertas, tendencias e nichos
- **Radar:** Tabela completa com filtros por nicho, plataforma, status, score; ordenacao
- **Detalhe:** Score breakdown, dados da oferta, qualidade, risco, evidencias
- **Comparador:** 2 a 4 ofertas lado a lado com ranking e destaques
- **Analise IA:** Explicacao MOCK baseada em regras (nenhum LLM chamado)
- **Fontes:** Transparencia de dados: origem, data, confianca por componente
- **Monitoramento:** Alertas com filtro por severidade
- **Configuracoes:** Tema, densidade, moeda, confianca minima, glossario, persistidos via localStorage

## Academia Offer Intelligence (Fase 3)

**Status: PROVA TECNICA DE APRENDIZAGEM — NAO E A VERSAO FINAL DO TREINAMENTO**

Curso guiado interativo com 8 modulos e 26 aulas. A estrutura foi aprovada por Leandro como prova de conceito, mas esta versao nao recebera refinamentos agora.

### Modulos
1. **Primeiros Passos** (3 aulas): Oferta, afiliado, comissao
2. **Entendendo a Procura** (3 aulas): Volume, crescimento, crescimento enganoso
3. **Confianca e Evidencias** (3 aulas): Confianca, fontes, dados antigos
4. **Riscos** (3 aulas): Saturacao, risco de politica, penalidades
5. **Interpretando o Score** (3 aulas): Score, componentes, nota vs garantia
6. **Comparando Ofertas** (4 aulas): Crescimento, publico, comissao, decisao
7. **Campanhas e Testes** (4 aulas): Teste limitado, campanha ruim, parar, ampliar
8. **ROI e Decisao** (3 aulas): Receita vs lucro, ROI, decisao final

### Funcionalidades da Academia
- Progresso persistido em localStorage
- Narracao local com speechSynthesis (pt-BR se disponivel)
- Destaque visual com borda pulsante, circulo SVG e seta
- Exercicios de multipla escolha com 2 tentativas e correcao
- Diagnostico visual de campanha ruim (4 etapas)
- Glossario com 16 termos consultavel durante as aulas
- Botao "Por que isso importa?" em diagnosticos
- Modo Aprender ativado automaticamente ao entrar na Academia
- Fallback textual se voz nao estiver disponivel
- Respeita prefers-reduced-motion

### Visao Futura — Aprendizagem Contextual (nao implementada)
A versao final do treinamento devera ser construida somente quando existirem fontes reais, ofertas reais, graficos reais, campanhas reais, custos, cliques, vendas, comissao, ROI e evidencias validadas.

O comportamento esperado e:
1. Usuario abre uma oferta ou campanha real
2. Clica em "Aprender com esta oferta" ou "Explicar esta campanha"
3. O sistema abre a area correta, escurece o restante, destaca e circula a metrica
4. A voz explica o numero usando o caso real
5. Relaciona a metrica com grafico, tendencia, custo, risco ou resultado
6. Compara com outro caso real
7. Faz pergunta pratica e comenta a resposta

## Limitacoes
- Todos os dados sao MOCK — nenhum produto real esta sendo recomendado
- Nenhuma campanha real foi analisada
- Nenhuma API foi chamada (speechSynthesis e local do navegador)
- Nenhuma previsao de lucro foi feita
- Links reais nao estao integrados — estrutura preparada para futura integracao
- Links futuros deverao usar apenas HTTPS, target="_blank" e rel="noopener noreferrer"

## Regras
- Score deterministico offer-score-v1.0; IA nunca altera nota
- Todo dado MOCK explicito como MOCK
- Nenhuma dependencia externa, CDN ou API
- Nenhuma chamada paga, scraping ou LLM real
