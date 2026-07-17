# Politica do Laboratorio de Day Trade

Status: **ARQUITETURA APROVADA PARA SIMULACAO; EXECUCAO REAL PROIBIDA**.

## Objetivo

Transformar uma estrategia explicada por Leandro em regras auditaveis, testar essas regras em dados historicos e contas demonstrativas e produzir relatorios. O laboratorio existe para aprender e medir. Ele nao movimenta dinheiro.

## Modos permitidos

- `PAPER_OFFLINE`: simulacao deterministica em dados locais versionados.
- `REPORT_IMPORT`: leitura de relatorios CSV/HTML exportados manualmente do MetaTrader 5.
- `DEMO_REVIEW`: comparacao humana de resultados obtidos em conta demonstrativa, sem controle automatico do terminal.

Qualquer outro modo deve falhar fechado. `real_execution_supported` permanece `false`.

## Proibicoes

- sem credenciais de corretora;
- sem login automatizado no MetaTrader;
- sem `order_send`, EA conectado, clique automatizado, compra, venda ou cancelamento;
- sem promessa de lucro, aluguel de robo ou divulgacao de resultado sem identificar claramente `SIMULACAO`;
- sem martingale, grid infinito, recuperacao de perdas ou aumento automatico de risco;
- sem uso do mesmo periodo para criar e validar a estrategia;
- sem promover uma regra para uso real por resultado isolado.

## Freios obrigatorios

- risco maximo por operacao, perda maxima diaria, drawdown maximo e numero maximo de operacoes;
- spread, comissao, slippage e latencia simulados;
- separacao treino/teste e validacao walk-forward;
- proveniencia e hash do dataset;
- versao imutavel da estrategia e dos parametros;
- revisao humana antes de iniciar **outra simulacao**;
- rollback por arquivo e historico completo de experimentos.

## Funcionarios candidatos

1. `StrategyResearchEmployee`: transforma a explicacao do owner em uma especificacao, sem inventar regras.
2. `PaperTradingSimulator`: executa apenas `PAPER_OFFLINE`.
3. `RiskReviewEmployee`: bloqueia configuracoes fora dos limites.
4. `PerformanceAnalystEmployee`: mede retorno, drawdown, expectativa, custos e estabilidade.
5. `MetaTraderReportImporter`: importa somente CSV/HTML escolhido pelo owner.
6. `ContentReporterEmployee`: cria material educativo rotulado como simulacao.

## Evidencia oficial consultada

- O Strategy Tester do MetaTrader 5 oferece teste, forward testing, ticks, atrasos e relatorios: https://www.metatrader5.com/en/terminal/help/algotrading/testing
- A integracao Python oficial contem funcoes de leitura e tambem `order_send`: https://www.mql5.com/en/docs/python_metatrader5
- `order_send` envia uma solicitacao de negociacao e esta explicitamente fora deste laboratorio: https://www.mql5.com/en/docs/python_metatrader5/mt5ordersend_py

Ultima consulta: 2026-07-17.

