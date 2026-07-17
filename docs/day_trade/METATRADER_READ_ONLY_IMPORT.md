# Importacao Segura do MetaTrader 5

## Primeira integracao permitida

1. Leandro exporta manualmente um relatorio do Strategy Tester ou da conta demonstrativa.
2. O arquivo CSV/HTML e copiado para uma pasta local de entrada.
3. O importador valida extensao, tamanho, colunas, timezone e hash.
4. O sistema converte os dados para contratos internos imutaveis.
5. O Performance Analyst gera um relatorio comparavel.

## Limites

- somente arquivo local selecionado pelo owner;
- nenhuma senha, token, terminal ou conta conectada;
- nenhuma rede durante importacao;
- HTML tratado como dados, nunca executado;
- CSV com formula injection neutralizada;
- arquivo original preservado e resultado derivado com hash.

## Fase futura opcional

Uma integracao Python **somente leitura** podera ser estudada depois. A allowlist devera excluir explicitamente `order_send` e qualquer funcao de negociacao. Essa fase depende de nova auditoria e aprovacao.

