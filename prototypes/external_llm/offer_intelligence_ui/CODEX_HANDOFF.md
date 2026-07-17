# CODEX HANDOFF — Offer Intelligence Prototipo Visual

**Origem:** DeepSeek (GPT da Web) -> DeepSeek (workspace seguro)
**Data:** 2026-07-16
**Status:** PROTOTIPO ISOLADO - NAO INTEGRADO

## O que foi construido

### Fase 1 — Base (aprovada)
Prototype inicial com 15 ofertas MOCK, score v1.0, 9 areas.

### Fase 2 — Camada Educacional (aprovada)
Graficos SVG, narracao speechSynthesis, tour guiado 18 etapas, glossario 16 termos, Modo Aprender/Profissional, diagnostico visual, correcoes de portugues.

Smoke: 72/72 assertions.

### Fase 3 — Academia Offer Intelligence (atual)
Curso guiado interativo completo com 8 modulos e 26 aulas.

### Arquivos criados (5 novos)
| Arquivo | Proposito |
|---|---|
| `learning_data.js` | 8 modulos, 26 aulas com textos, narracoes, analogias, quizzes, resumos |
| `learning_engine.js` | Motor de aulas: iniciar, pausar, continuar, destacar elemento, spotlight SVG |
| `quiz_engine.js` | Multipla escolha, 2 tentativas, feedback, correcao, progresso |
| `lesson_visuals.js` | Diagnosis visual, campanha ruim, comparacao volume/crescimento, saturacao |
| `progress_tracker.js` | Progresso persistente em localStorage, modulos, reset com confirmacao |

### Arquivos modificados (12)
`index.html`, `styles.css`, `app.js`, `mock_data.js`, `narration.js`, `beginner_mode.js`, `glossary.js`, `tutorial.js`, `charts.js`, `smoke_test.py`, `README.md`, `CODEX_HANDOFF.md`

### Nao alterados
`scoring.js`, `comparator.js`, `start_server.bat`

## Codex,

Leandro pediu que o Offer Intelligence nao apenas apresente metricas, mas ensine visualmente como interpreta-las.

A Academia foi criada para demonstrar conceitos na propria interface, com narracao, destaques, exemplos, exercicios e correcao.

Uma necessidade central e o diagnostico visual:
- escurecer a tela;
- circular o ponto relevante;
- explicar o motivo;
- relacionar varias metricas;
- mostrar quando uma campanha ou oferta parece problematica.

A experiencia deve continuar disponivel em dois niveis:
- iniciante, com aulas e linguagem simples;
- profissional, com metricas, pesos, evidencias e formula completa.

Os links reais ainda nao foram integrados. O prototipo contem apenas o contrato visual e os campos futuros (MOCK_URL_FIELDS em mock_data.js). Quando houver fontes validadas, os links deverao abrir destinos oficiais e seguros em outra aba, sem inventar URLs ou links de afiliado.

A narracao continua sendo local, usando speechSynthesis. Uma possivel integracao futura com Kokoro devera ser avaliada separadamente.

### Fase 3 — Detalhamento

#### 8 Modulos
1. Primeiros Passos (3 aulas: oferta, afiliado, comissao)
2. Entendendo a Procura (3 aulas: volume, crescimento, crescimento enganoso)
3. Confianca e Evidencias (3 aulas: confianca, fontes, dados antigos)
4. Riscos (3 aulas: saturacao, risco de politica, penalidades)
5. Interpretando o Score (3 aulas: score, componentes, nota vs garantia)
6. Comparando Ofertas (4 aulas: crescimento, publico, comissao, decisao)
7. Campanhas e Testes (4 aulas: teste limitado, campanha ruim, parar, ampliar)
8. ROI e Decisao (3 aulas: receita vs lucro, ROI, decisao final)

#### 26 aulas obrigatorias
- Aula 6: Crescimento alto pode enganar (com visualizacao)
- Aula 12: Por que esta oferta perdeu pontos? (diagnostico visual)
- Aula 19: Qual escolher? (exercicio comparativo)
- Aula 21: Campanha ruim — descubra o motivo (4 etapas de diagnostico)
- Aula 26: Decisao final (simulacao completa)

#### Narracao
- Exclusivamente window.speechSynthesis
- Voz pt-BR quando disponivel
- Velocidade 0.75x / 1x / 1.25x
- Pausar, repetir, pular
- Fallback textual completo
- Mensagem "Narracao local do navegador. Nenhum servico externo foi chamado."

#### Diagnostico visual
- Borda pulsante no elemento destacado
- Circulo SVG + seta apontando
- Etiqueta explicativa
- Linha ligando explicacao ao elemento
- Respeita prefers-reduced-motion
- Botao "Por que isso importa?" em cada etapa

#### Exercicios
- Multipla escolha com 2 tentativas
- Feedback apos cada resposta
- Segunda tentativa apos erro
- Explicacao da resposta correta
- Progresso registrado

#### Progresso
- localStorage: aula atual, concluidas, respostas, tentativas, velocidade, narracao
- Barra de progresso por modulo e total
- Status: nao iniciada, em andamento, concluida, recomendada para revisao
- Reset com confirmacao

#### Links MOCK
- Campos preparados: official_product_url, sales_page_url, affiliate_program_url, checkout_url, ad_library_url, evidence_url
- Disclaimer: "Indisponivel em dados MOCK"
- Documentacao de seguranca futura: HTTPS, target="_blank", rel="noopener noreferrer"

#### Acessibilidade
- Foco visivel (outline)
- ARIA roles
- prefers-reduced-motion
- Controles por teclado (Escape, setas)
- Alternativa textual para narracao
- Sem dependencia exclusiva de cor

#### Avisos dentro da Academia
- "Todos os dados sao MOCK"
- "Nenhum produto real esta sendo recomendado"
- "Nenhuma campanha real foi analisada"
- "Nenhuma API foi chamada"
- "Nenhuma previsao de lucro foi feita"
- "Decisoes reais exigem evidencias e aprovacao"

### Smoke Test
100+ assertions validando todos os recursos novos e existentes.
Nenhum teste existente foi removido.

### Para Codex revisar
1. Estrutura da Academia atende aos requisitos de Leandro?
2. Learning engine esta bem integrado com os modulos existentes?
3. Quiz engine funciona corretamente com 2 tentativas?
4. Visual diagnosis (campanha ruim) esta claro para um iniciante?
5. Links MOCK estao preparados corretamente para futura integracao?

### Decisao de Leandro (2026-07-16)
A Academia Offer Intelligence foi aprovada como **PROVA TECNICA DE APRENDIZAGEM**. A estrutura de aulas, narracao, glossario, progresso, exercicios e destaques visuais foi validada.

**Nenhum refinamento adicional sera feito nesta versao.**

### Visao Futura — Aprendizagem Contextual
A versao final do treinamento devera ser construida somente quando existirem dados reais:
- fontes reais
- ofertas reais
- graficos reais
- campanhas reais
- custos, cliques, vendas, comissao, ROI
- evidencias validadas

O comportamento esperado e contextual:
1. Usuario abre uma oferta ou campanha real
2. Clica em "Aprender com esta oferta" ou "Explicar esta campanha"
3. Sistema abre a area correta, escurece o restante, destaca e circula a metrica
4. Voz explica o numero usando o caso real
5. Relaciona a metrica com grafico, tendencia, custo, risco ou resultado
6. Compara com outro caso real
7. Faz pergunta pratica e comenta a resposta

### Proximos passos (fora do escopo do workspace seguro)
1. Codex revisar arquitetura e integracao
2. Decidir sobre proxima fase (Market Intelligence & Learning ou integracao com core)
3. Nao modificar codigo da Academia nesta fase
