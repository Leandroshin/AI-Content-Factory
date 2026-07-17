# Contratos do Laboratorio de Day Trade

Estes contratos descrevem a futura implementacao. Ainda nao autorizam codigo que controle o MetaTrader.

## StrategySpec

- `strategy_id`, `version`, `market`, `timeframe`;
- condicoes exatas de entrada, saida e invalidacao;
- horario operacional e calendario;
- stop, alvo e dimensionamento;
- parametros permitidos e faixas;
- suposicoes declaradas pelo owner;
- pontos ainda ambiguos, que bloqueiam o teste.

## DatasetProvenance

- arquivo, origem, instrumento, timezone e periodo;
- granularidade, campos, ausencias e ajustes;
- `sha256`, data de importacao e responsavel;
- separacao treino, validacao e teste.

## PaperExperimentSpec

- estrategia e dataset versionados;
- capital virtual;
- spread, comissao, slippage e latencia;
- limites de risco;
- janela de treino/teste e walk-forward;
- criterios de aprovacao definidos antes da execucao.

## PaperExecutionRecord

- decisao, timestamp, preco teorico, custos e motivo;
- nenhuma ordem externa;
- estado antes/depois e identificador do experimento.

## PaperExperimentReport

- retorno liquido virtual, drawdown, expectativa, profit factor e estabilidade;
- quantidade de operacoes e exposicao;
- comparacao treino/teste;
- falhas, vieses e limitacoes;
- rotulo visivel `SIMULACAO - NAO E RECOMENDACAO FINANCEIRA`.

## Estados

`DRAFT -> NEEDS_OWNER_RULES -> READY_FOR_SIMULATION -> RUNNING_OFFLINE -> REVIEW -> REJECTED | ARCHIVED`

Nao existe estado `LIVE`, `DEPLOYED` ou `TRADING`.

