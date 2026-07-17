# Prototipo CardapioPro

**Status:** PROTOTIPO ISOLADO - NAO INTEGRADO  
**Data:** 2026-07-14

## Objetivo

Visualizar o ecossistema completo do Menu SaaS: como o cliente final ve o cardapio, como o dono do restaurante gerencia, e como a fabrica opera internamente.

## Como testar

Abra `index.html` em qualquer navegador moderno. Navegue pelas 4 abas:

1. **Cardapio** — Visao do cliente que escaneia o QR code na mesa
2. **Painel do Cliente** — Dashboard do dono do restaurante (views, edicao, QR)
3. **Fabrica** — Painel interno da AI Content Factory (fila de operacao, MRR, metricas)
4. **Planos** — Tabela de precos (Starter R$47 / Pro R$97 / Multi R$197)

## Limitacoes

- HTML estatico — nenhuma operacao real
- Dados ficticios — "Restaurante do Caio" como cliente exemplo
- QR code e placeholder visual, nao funcional
- Nao importa `core/`, nao usa API, nao persiste dados

## O que Codex deve revisar

- O prototipo em si (para referencia visual)
- A proposta completa em `docs/external_llm_inbox/deepseek/ideas/2026-07-14_menu_saas_vertical.md`
- Decisao: implementar como departamento `menu_saas/`?
