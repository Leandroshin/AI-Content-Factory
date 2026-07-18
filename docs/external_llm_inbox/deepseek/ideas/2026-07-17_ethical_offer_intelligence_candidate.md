# Ethical Offer Intelligence Candidate

**Status:** PROPOSTA - NAO IMPLEMENTADA
**Data:** 2026-07-17
**Executor:** DeepSeek no OpenCode/VS Code
**Revisor esperado:** Codex

---

## 1. Identificacao da fonte

| Campo | Valor |
|---|---|
| Titulo | COMO MINERAR OFERTAS ESCALADAS E CLONAR EM MINUTOS |
| URL | https://www.youtube.com/watch?v=odCjvopmUlc |
| Duracao | ~25 min |
| Caminho | `docs/external_llm_inbox/incoming/2026-07-17_offer_mining_cloning_video.txt` |
| SHA-256 | `B8FE57E9B08364167D35DD931723A84C890471C0A5016847E63517EC052E4C97` |
| Tamanho | 37.311 bytes, 723 linhas |
| Natureza | Videoaula pratica de mineracao de ofertas para afiliados |
| Funcao promocional | Vende cupom do Minera Ads, divulga ferramenta ArcTrix, promove curso/mentoria proprios |
| Apresentador | Identificado provisoriamente na transcricao — nome nao confirmado |
| Alegacoes financeiras | "faturar pelo menos R$10.000 todos os dias"; "mais de R$260.000 de faturamento com uma oferta low ticket" |
| Qualidade da transcricao | Automatica (tactiq.io); fala com ruido; alguns trechos cortados |

### Separacao

- **OBSERVADO:** Autor mostra na pratica o uso da biblioteca de anuncios, Reclame Aqui e navegacao no feed do Facebook.
- **DECLARADO PELO AUTOR:** R$260.000 de faturamento com oferta low ticket; metodos de mineracao "avançados".
- **INFERIDO:** O metodo pressupoe acesso a perfis alternativos, ferramentas de mineracao pagas (Minera Ads, RL Scan, ArcTrix) e multilogin (Ads Power).
- **NAO VERIFICADO:** Valores financeiros; se as ofertas encontradas realmente geraram receita; se o metodo de clonagem e legal.
- **RISCO ELEVADO:** Praticas de clonagem de pagina, uso de cartao falso e quebra de cloaking sao explicitamente ensinadas.

---

## 2. Resumo executivo

**O que pode ser aproveitado:** Principios de uso de fontes publicas (biblioteca de anuncios, Reclame Aqui, Google), registro sistematico de ofertas, triangulacao entre fontes e observacao de persistencia temporal de anuncios. Estes metodos sao compativeis com inteligencia competitiva etica.

**O que nao pode ser aproveitado:** Clonagem de paginas (ArcTrix), uso de cartao falso para gerar compra negada, compra de perfis, multilogin para manipular algoritmo, quebra de cloaking, reutilizacao de criativos e paginas alheias.

**Por que essa fonte possui alto risco:** O titulo e a maior parte do conteudo promovem praticas que violam termos de plataforma (Facebook, Hotmart) e podem configurar concorrencia desleal, violacao de direitos autorais e fraude. Apenas uma fracao do video contem metodos eticos reutilizaveis.

**Por que nao pode virar instrucao automatica:** Praticas ilegitimas estao entrelacadas com as legitimas. Separar exige criterio manual. Nenhuma alegacao financeira foi verificada.

---

## 3. Metodos legitimos aproveitaveis

### M01: Uso de multiplas fontes publicas
- **Timestamp:** 00:01:58 - 00:02:14
- **Trecho:** "A melhor mineracao sempre vai ser aquela que voce faz utilizando tudo... cada um desses espacos aqui em conjunto"
- **Objetivo:** Combinar biblioteca de anuncios, Reclame Aqui e busca no Google para cruzar sinais
- **Entrada:** Palavras-chave, nomes de oferta, URLs
- **Saida:** Lista de ofertas com multiplos indicadores
- **Risco:** Baixo
- **Departamento:** Strategy Intelligence, Product Research
- **Limitacao:** Nao substitui analise de lucratividade real
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M02: Biblioteca publica de anuncios
- **Timestamp:** 00:02:46 - 00:04:52
- **Trecho:** "Nao tem segredo... pegar algumas palavras chave e jogando la na biblioteca"
- **Objetivo:** Identificar anunciantes ativos por keyword
- **Entrada:** Termos de busca (palavras-chave especificas)
- **Saida:** Lista de paginas com anuncios ativos
- **Risco:** Baixo (fonte publica oficial do Meta)
- **Departamento:** Product Research, Offer Intelligence
- **Limitacao:** Meta Ads Library mostra apenas anuncios ativos, nao receita
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M03: Registro de quantidade de anuncios ativos
- **Timestamp:** 00:04:52 - 00:04:57
- **Trecho:** "Encontrei essa oferta aqui com 34 anuncios"
- **Objetivo:** Quantificar anuncios como sinal de atividade
- **Entrada:** Pagina da biblioteca de anuncios
- **Saida:** Contagem de anuncios ativos por pagina
- **Risco:** Baixo
- **Departamento:** Product Research, Offer Intelligence
- **Limitacao:** Numero de anuncios nao prova vendas ou lucro
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M04: Registro de data e hora da observacao
- **Timestamp:** 00:06:39 - 00:06:42
- **Trecho:** "70 anuncios ativos hoje, dia 18 de marco, as 15:37"
- **Objetivo:** Timestampar cada observacao para rastrear persistencia
- **Entrada:** Data/hora atual + contagem de anuncios
- **Saida:** Registro historico de atividade
- **Risco:** Baixo
- **Departamento:** Observability, Offer Intelligence
- **Limitacao:** Nao impede que o anunciante pause e retome
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M05: Persistencia ao longo do tempo
- **Timestamp:** 00:10:29 - 00:10:37
- **Trecho:** "A gente ve que a oferta se mantem constante, nao que ele ta em teste ou para escala"
- **Objetivo:** Distinguir oferta mantida (escalada) de campanha temporaria
- **Entrada:** Duas ou mais observacoes com data
- **Saida:** Classificacao: temporaria vs mantida
- **Risco:** Baixo
- **Departamento:** Product Research, Offer Intelligence
- **Limitacao:** Requer disciplina de registro ao longo de dias/semanas
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M06: Busca publica pelo nome da oferta
- **Timestamp:** 00:09:23 - 00:09:43
- **Trecho:** "Pesquisei ele no Google, que a gente encontra as vezes anuncios do Google Ads aparecendo"
- **Objetivo:** Validar nome de oferta alem da Meta
- **Entrada:** Nome do produto
- **Saida:** Presenca em Google Ads, pagina oficial, concorrentes
- **Risco:** Baixo
- **Departamento:** Product Research
- **Limitacao:** Google pode nao mostrar anúncios de todos os anunciantes
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M07: Identificacao do tipo de funil
- **Timestamp:** 00:09:50 - 00:09:57
- **Trecho:** "Pagina de vendas do cara, funil de quiz"
- **Objetivo:** Classificar funil por tipo (quiz, VSL, checkout direto)
- **Entrada:** URL do funil, pagina de vendas
- **Saida:** Tipo de funil registrado
- **Risco:** Baixo
- **Departamento:** Affiliate Deals, Script Department
- **Limitacao:** Tipo de funil nao determina conversao
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M08: Registro organizado de ofertas (swipe file)
- **Timestamp:** 00:06:11 - 00:06:47
- **Trecho:** "Vou est anotando tudo no nosso swipe"
- **Objetivo:** Manter registro estruturado de ofertas observadas
- **Entrada:** Nome, funil, fonte, data, anuncios ativos
- **Saida:** Base de ofertas candidatas
- **Risco:** Baixo
- **Departamento:** Product Research, Affiliate Deals
- **Limitacao:** Depende de disciplina manual
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M09: Comparacao entre fontes
- **Timestamp:** 00:09:23 - 00:09:57
- **Trecho:** (cruzamento entre Reclame Aqui, biblioteca e Google)
- **Objetivo:** Validar oferta por presenca em multiplas fontes
- **Entrada:** Nome da oferta
- **Saida:** Score de confianca por quantidade de fontes
- **Risco:** Baixo
- **Departamento:** Strategy Intelligence, Product Research
- **Limitacao:** Fontes podem refletir apenas atividade de marketing, nao qualidade
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

### M10: Distincao entre sinal de atividade e prova de lucro
- **Timestamp:** 00:07:20 - 00:07:55
- **Trecho:** "Isso porque as vezes um produtor tem 5.000 vendas no dia... 50 pessoas, 30 pessoas vao querer reembolsar"
- **Objetivo:** Reclame Aqui como sinal de volume, nao de golpe
- **Entrada:** Quantidade de reclamacoes por produto
- **Saida:** Indicador de atividade (vendas altas geram mais reclamacoes)
- **Risco:** Medio (pode ser mal interpretado)
- **Departamento:** Creative Review, Quality Runtime
- **Limitacao:** Nao distingue reclamacao legitima de abuso
- **Status:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

---

## 4. Duas alegacoes prioritarias

### Alegacao A: Multiplas fontes publicas produzem avaliacao mais confiavel

**Formulacao neutra:** "Combinar diferentes fontes publicas pode produzir uma avaliacao mais confiavel da atividade de uma oferta do que utilizar somente a quantidade de anuncios ativos."

**Timestamp:** 00:01:58 - 00:02:14; 00:09:23 - 00:09:57
**Trecho:** "A melhor mineracao sempre vai ser aquela que voce faz utilizando tudo... cada um desses espacos aqui em conjunto"

**O que sustenta:** O autor demonstra usar 3 fontes (biblioteca, Reclame Aqui, Google) para a mesma oferta, cada uma fornecendo um angulo diferente.

**O que nao sustenta:** Que 3 fontes garantem acuracia; que combinacao de fontes substitui dados financeiros reais.

**Evidencia ausente:** Estatistica de quantas ofertas identificadas por 3+ fontes realmente venderam.

**Confianca:** 0,45 (`AUDITORIA PARCIAL - FALTA CORROBORACAO` apos gate)
**Experimento MOCK:** EXP-01 (consistencia de scoring com 1 vs 3+ fontes)
**Condicao de rejeicao:** Se ofertas com 3+ fontes nao tiverem taxa de atividade superior a ofertas com 1 fonte.
**Status inicial:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`
**Promocao automatica:** Proibida

### Alegacao B: Observacao repetida distingue ofertas mantidas de temporarias

**Formulacao neutra:** "Registrar anuncios e repetir a observacao em datas diferentes pode ajudar a distinguir campanhas temporarias de ofertas mantidas por mais tempo."

**Timestamp:** 00:10:29 - 00:10:37; 00:06:39 - 00:06:42
**Trecho:** "A gente ve que a oferta se mantem constante... Importante e encontrar ofertas de fato escaladas"

**O que sustenta:** O autor registra data, hora e contagem, e usa a repeticao para avaliar consistencia.

**O que nao sustenta:** Que persistencia de anuncios equivale a escalabilidade ou lucratividade.

**Evidencia ausente:** Correlacao entre tempo de atividade e receita real.

**Confianca:** 0,50 (`AUDITORIA PARCIAL - FALTA CORROBORACAO` apos gate)
**Experimento MOCK:** EXP-02 (persistencia simulada)
**Condicao de rejeicao:** Se ofertas mantidas por 30+ dias nao tiverem sinal de atividade superior a ofertas novas.
**Status inicial:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`
**Promocao automatica:** Proibida

---

## 5. Candidatos a Knowledge Cards

1. **KC-01: Triangulacao de sinais** — Combinar biblioteca, Reclame Aqui e Google produz quadro mais completo que fonte unica. (M01, M09)
2. **KC-02: Biblioteca de anuncios como fonte publica** — Meta Ads Library e ferramenta de livre acesso para identificar anunciantes ativos. (M02)
3. **KC-03: Persistencia temporal** — Anuncios mantidos por dias/semanas sugerem operacao escalada, nao teste. (M05)
4. **KC-04: Registro historico** — Timestamp e contagem permitem rastrear atividade ao longo do tempo. (M04)
5. **KC-05: Quantidade de anuncios como sinal, nao prova** — Muitos anuncios indicam investimento em escala, mas nao provam lucro. (M03, M10)
6. **KC-06: Reclamacoes como evidencia de exposicao** — Volume de reclamacoes correlaciona com volume de vendas, nao com qualidade do produto. (M10)
7. **KC-07: Identificacao publica do tipo de funil** — Classificar funil (quiz, VSL, checkout) por observacao publica e possivel. (M07)
8. **KC-08: Diferenciacao entre observacao e espionagem abusiva** — Usar fontes publicas e etico; clonar pagina, nao. (M01-M10 vs PR-01-PR-19)
9. **KC-09: Nao copiar criativos** — Observar estimula criacao propria, nao reuso. (PR-12)
10. **KC-10: Compliance em saude e emagrecimento** — Nichos regulados exigem cuidado redobrado com alegacoes. (PR-17)

**Status de todos:** `CANDIDATO A EVIDENCIA - NAO AUDITADO`

---

## 6. Praticas rejeitadas

`REJEITADO - NAO USAR`

| ID | Timestamp | Descricao | Risco | Alternativa |
|---|---|---|---|---|
| PR-01 | 00:21:50 | Cartao falso para gerar compra negada | Fraude, violacao termos Hotmart/Meta | Nao simular compra |
| PR-02 | 00:21:50 | Gerar compra negada para enganar algoritmo | Manipulacao de plataforma | Observar sem interagir |
| PR-03 | 00:21:50 | Simular comprador para Facebook | Falsidade ideologica digital | Usar dados publicos apenas |
| PR-04 | 00:17:50 | Comprar perfis de terceiros | Violacao termos Facebook, risco legal | Usar conta propria |
| PR-05 | 00:17:55 | Utilizar perfis de terceiros sem consentimento | Violacao de privacidade | Nao usar |
| PR-06 | 00:17:55 | Proxy para disfarcar identidade | Violacao termos de servico | Nao disfarcar identidade |
| PR-07 | 00:17:50 | Multilogin para manipular plataforma | Automacao nao autorizada, banimento | Nao manipular |
| PR-08 | 00:20:18 | Manipular algoritmo de recomendacao | Termos Meta proibem engajamento artificial | Nao fazer |
| PR-09 | 00:20:18 | Contornar ou quebrar cloaking | Violacao de seguranca de terceiros | Nao contornar |
| PR-10 | 00:23:40 | Clonar paginas (ArcTrix) | Violacao direitos autorais, termos de uso | Criar pagina original |
| PR-11 | 00:24:31 | Substituir pixel e links de pagina copiada | Apropriacao indevida de infraestrutura alheia | Nao copiar |
| PR-12 | 00:23:40 | Baixar e reutilizar criativos | Violacao direitos autorais | Criar criativos originais |
| PR-13 | 00:23:40 | Copiar funil completo | Concorrencia desleal | Inspirar-se, nao copiar |
| PR-14 | 00:23:40 | Reutilizar textos, imagens ou videos | Violacao de propriedade intelectual | Producao original |
| PR-15 | 00:07:20 | Usar reclamacoes com dados pessoais | Violacao LGPD/privacidade | Dados anonimizados |
| PR-16 | 00:23:40 | Copiar estrutura expressiva de concorrente | Violacao de direito autoral | Criacao independente |
| PR-17 | 00:05:17 | Anuncios de saude sem compliance | Risco regulatorio (ANVISA, CDC) | Compliance obrigatorio |
| PR-18 | 00:00:12 | Afirmar "R$10.000 por dia" | Propaganda enganosa sem verificacao | Nao replicar |
| PR-19 | 00:00:18 | Aceitar R$260.000 como resultado comprovado | Ausencia de verificacao independente | Tratar como alegacao nao verificada |

Nenhuma instrucao operacional para executar estas praticas foi registrada.

---

## 7. Mapeamento para componentes existentes

| Componente | Metodos aproveitaveis | Praticas rejeitadas |
|---|---|---|
| Caixa de Aprendizado | Entrada da transcricao + 2 alegacoes | Nao inserir metodos ilegitimos |
| Strategy Intelligence | M01, M09 (triangulacao, comparacao) | Ignorar sinais de cloaking/perfil falso |
| Product Research | M02, M03, M05, M06, M08 (scoring, registro) | Nao usar dados de anuncios clonados |
| Creative Review | M10 (reclamacoes como sinal) | PR-12, PR-14, PR-16 (criativos copiados) |
| Offer Intelligence | M01-M10 (base para scoring etico) | Nao incorporar metricas de clonagem |
| Quality Runtime | Regras de compliance baseadas em PR-01 a PR-19 | Bloquear automaticamente praticas rejeitadas |
| Approval Gateway | Gate para qualquer oferta pesquisada | Exigir confirmacao de origem etica |
| Observabilidade | M04 (timestamp) para rastrear atividade | Nao registrar metodos ilegitimos |
| Dashboard | Registro de ofertas (M08) como learning source | Nao exibir ofertas obtidas por clonagem |

Nenhum novo departamento e necessario.

---

## 8. Experimentos MOCK

| ID | Hipotese | Mede | Gasto real |
|---|---|---|---|
| EXP-01 | Scoring com 3+ fontes produz ranking mais consistente que 1 fonte | Consistencia, reproducibilidade | R$0 |
| EXP-02 | Observacao repetida em 3 datas diferentes permite classificar oferta como temporaria ou mantida | Persistencia simulada | R$0 |
| EXP-03 | Duas fontes divergentes (biblioteca vs Reclame Aqui) geram score de confianca menor que fontes convergentes | Divergencia, confianca | R$0 |
| EXP-04 | Ofertas em nichos regulados (saude) tem mais praticas rejeitadas associadas que nichos nao regulados | Risco, compliance | R$0 |
| EXP-05 | Registro com 5+ campos (nome, data, fonte, anuncios, tipo funil) e mais completo que registro com 2 campos | Completude | R$0 |

MOCK nao mede: lucratividade, vendas, conversao, ROAS, comportamento de compra.
Gasto real: R$0. Saldo real movimentado: R$0.

---

## 9. MVP recomendado ao Codex

1. Confirmar arquivo e hash
2. Inserir a fonte na Caixa de Aprendizado
3. Registrar Alegacao A
4. Registrar Alegacao B
5. Preservar timestamps
6. Produzir auditorias parciais (ambas PARTIAL)
7. Exibir que anuncios ativos nao provam lucratividade
8. Registrar praticas rejeitadas no pacote auditado
9. Exportar Markdown/JSON
10. Registrar decisao humana

**Bloqueios:** Cards automaticos, memoria, funcionarios, scraping, navegador, provider, clonagem, publicacao, gasto.

---

## 10. Decisoes de Leandro

### Decisoes atuais
- Autorizar a fonte na Caixa de Aprendizado
- Usar as duas alegacoes
- Priorizar Alegacao B (persistencia temporal tem risco menor)
- Manter todas as 19 praticas rejeitadas

### Decisoes adiadas
- Eventual monitoramento publico de anuncios (requer definicao de ferramenta)
- Frequencia de observacao (diaria, semanal)
- Campos do registro de ofertas (minimos vs completos)
- Regras adicionais de compliance no QualityRuntime

---

## 11. Criterios de aceitacao

- [x] Arquivo de entrada preservado
- [x] SHA-256 registrado
- [x] 2 alegacoes rastreaveis (A e B)
- [x] 10 Knowledge Cards candidatos
- [x] 10 metodos legitimos extraidos
- [x] 19 praticas rejeitadas explicitas
- [x] 5 experimentos MOCK
- [x] Nenhuma pratica ilegitima instruida
- [x] Nenhum gasto
- [x] Nenhum provider
- [x] Nenhuma publicacao
- [ ] Regressao pelo Codex (pendente)

*Documento produzido por DeepSeek no OpenCode/VS Code em 2026-07-17.*
*Status: PROPOSTA - NAO IMPLEMENTADA*
