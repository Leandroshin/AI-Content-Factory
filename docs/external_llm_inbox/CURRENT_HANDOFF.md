# Handoff Atual da AI Content Factory

Atualizado em: 2026-07-18

## Estado oficial

- A fabrica possui departamentos reais de Script, Audio, Imagem, Video, Strategy Intelligence, Product Research, Creative Review e Affiliate Deals.
- O painel oficial e `apps/factory_dashboard/`; prototipos em `prototypes/external_llm/` nao sao produto integrado.
- A Caixa de Aprendizado aceita URL do YouTube e transcricao fornecida pelo owner sem custo de provider.
- O `TranscriptEvidenceAuditWorkflow` preserva fonte, hash, trecho exato e auditoria; uma alegacao nasce parcial e seu Knowledge Card permanece candidato.
- Transcricao nao vira Organizational Memory, instrucao de funcionario, experimento ou publicacao automaticamente.
- Market Intelligence & Learning entra por missoes pequenas. O gate de evidencia e as duas primeiras alegacoes parciais estao integrados e testados.
- Offer Intelligence continua primeiro como modulo interno; o SaaS separado e os 12 projetos de monetizacao continuam propostas.
- Telegram possui capacidade REAL controlada e concluiu a primeira publicacao editorial aprovada pelo owner.
- Day Trade esta autorizado somente como laboratorio `PAPER_OFFLINE`, importacao de relatorios e analise de conta demonstrativa. Execucao real e proibida.

## Alegacoes integradas

### Low-Ticket

> Uma entrega inicial simples pode reduzir o tempo e o custo de preparacao antes de validar a demanda, dependendo do tipo de produto e do mercado.

- Status: `AUDITORIA PARCIAL - FALTA CORROBORACAO`.
- Confianca: `0.58`.
- `KnowledgeCardDraft`: `PENDING_AUDIT`.
- Nenhuma promocao para Organizational Memory ou instrucoes de funcionarios.

### Ethical Offer Intelligence

> Registrar anuncios e repetir a observacao em datas diferentes pode demonstrar persistencia da atividade publicitaria durante o periodo observado.

- Status: `AUDITORIA PARCIAL - FALTA CORROBORACAO`.
- Confianca: `0.58`.
- `KnowledgeCardDraft`: `PENDING_AUDIT`.
- Persistencia nao representa escala, venda, receita ou lucro.
- Nenhuma promocao para Organizational Memory ou instrucoes de funcionarios.

## Telegram

- Capacidade REAL controlada implementada.
- A mensagem editorial de boas-vindas foi aprovada por Leandro e publicada em `@achadosbaratosBrasil`.
- Resultado confirmado: status `sent`, `message_id=4`, sem erro e com somente um item processado pelo worker.
- Preparacao, aprovacao, fila e execucao permaneceram acoes separadas.
- O worker foi executado com opt-in explicito e processou `received=1`, `sent=1`, `failed=0`.
- A reserva `queued -> publishing` continua atomica e idempotente.
- Concorrencia, duplicidade e expiracao permanecem protegidas e testadas.
- Nenhuma outra publicacao foi executada nessa operacao.

## Seguranca

- Nenhum provider pago foi acionado.
- Nenhum gasto ocorreu.
- Nenhuma Organizational Memory foi atualizada.
- Nenhuma instrucao de funcionario foi alterada.
- Nenhuma publicacao externa foi realizada.
- A pasta `youtube/` permanece local, nao rastreada e sem autoridade oficial.
- Prototipos do DeepSeek continuam isolados quando nao integrados pelo Codex.

## Diferenca de status

- **Integrado:** codigo oficial, testes e regressao.
- **Prototipo isolado:** demonstracao separada, sem autoridade operacional.
- **Proposta:** ideia para auditoria.
- **MOCK:** dados ou execucao demonstrativos.
- **REAL controlado:** integracao oficial com opt-in, segredo, budget, aprovacao e auditoria.

## Bloqueios atuais

- Providers pagos de voz, imagem e video aguardam decisao e orcamento.
- Meta Ads aguarda token `ads_read` valido; nenhuma escrita e permitida.
- Digistore24/PayPal e outras redes aguardam onboarding financeiro.
- Nenhuma alegacao parcial pode ser promovida sem corroboracao, experimento e aprovacao humana.
- A primeira oferta comercial ainda precisa de pesquisa atual, preco reconfirmado, link monetizado e aprovacao humana antes de entrar na fila.

## Proximas missoes oficiais

1. **Primeira vertical operacional de ofertas:** pesquisar candidatos atuais sem provider pago e devolver shortlist auditavel.
2. **Preparar um pacote comercial:** confirmar preco, disponibilidade, link monetizado, criativo e copy sem publicar.
3. **Decisao humana separada:** Leandro aprova, solicita edicao ou rejeita o pacote.
4. **Distribuicao e metricas:** somente depois de nova autorizacao explicita, publicar um item e registrar clique, venda, comissao, custo e ROI.

## Base de verificacao

Verificacao local de 2026-07-18:

- `python -m compileall -q core`: passou.
- `python scripts/run_all_demos.py`: `119/119` demonstracoes, `1935` assertions explicitas, `0` falhas.
- Dashboard: build e `16/16` testes Node passaram, incluindo quatro testes de reserva atomica concorrente.
- Telegram: worker `27/27`, adapter `40/40` e HITL `35/35` passaram sem chamada externa.

Antes de aceitar numeros futuros, leia `AGENTS.md` e execute novamente a regressao. Os totais no GitHub so sao oficiais depois do ultimo checkpoint registrado.
