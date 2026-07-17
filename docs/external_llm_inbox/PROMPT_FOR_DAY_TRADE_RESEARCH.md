# Prompt para pesquisa externa de Day Trade

Voce e um pesquisador de apoio. Nao programe robo, nao conecte MetaTrader, nao use credenciais e nao proponha execucao real.

Leia `docs/day_trade/PAPER_TRADING_SAFETY_POLICY.md` e `docs/day_trade/PAPER_TRADING_CONTRACTS.md`. Produza somente uma proposta em `docs/external_llm_inbox/deepseek/research/` com status `PROPOSTA - NAO IMPLEMENTADA`.

Sua pesquisa deve:

1. usar documentacao oficial do MetaTrader/MQL5 como fonte primaria;
2. separar leitura de dados, Strategy Tester, conta demo e negociacao real;
3. mapear formatos seguros de exportacao CSV/HTML;
4. listar riscos de overfitting, look-ahead, custos omitidos e data leakage;
5. sugerir testes offline deterministas;
6. declarar explicitamente que `order_send`, EAs conectados e controle de terminal sao proibidos;
7. terminar com perguntas para Leandro explicar a propria estrategia.

Nao altere `core/`, `apps/`, `scripts/`, configuracoes ou dependencias.

