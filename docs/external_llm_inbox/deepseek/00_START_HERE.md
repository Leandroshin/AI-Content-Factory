# Comece aqui — OpenCode + DeepSeek

Este e o ponto de entrada reutilizavel para delegar pesquisas, propostas e pequenos prototipos ao DeepSeek sem permitir alteracoes no produto validado.

## Como abrir

1. No VS Code, abra a pasta raiz `Novo_projeto_Ai_Content_Factory`.
2. Inicie o OpenCode nessa mesma pasta.
3. Selecione o modelo DeepSeek.
4. Envie o prompt abaixo e, no final, descreva a tarefa desejada.

## Prompt inicial para colar

```text
Voce e uma LLM auxiliar da AI Content Factory. Antes de responder ou criar arquivos, leia nesta ordem:

1. AGENTS.md
2. docs/external_llm_inbox/README.md
3. docs/external_llm_inbox/LOCAL_LLM_WORK_PROTOCOL.md
4. docs/external_llm_inbox/deepseek/00_START_HERE.md
5. docs/external_llm_inbox/deepseek/INDEX.md
6. docs/external_llm_inbox/CURRENT_HANDOFF.md
7. docs/external_llm_inbox/DECISION_LEDGER.md
8. docs/external_llm_inbox/STATUS_TAXONOMY.md

Trabalhe somente nas pastas permitidas pelo protocolo. Nao altere core/, apps/, scripts/, demo_*.py, AGENTS.md, configuracoes, dependencias, credenciais ou sites existentes.

Para pesquisa, proposta, funcionario, departamento ou briefing, use a pasta correspondente dentro de docs/external_llm_inbox/deepseek/.

Se eu pedir algo executavel, crie apenas um prototipo isolado em prototypes/external_llm/<nome-da-tarefa>/. O prototipo nao pode importar nem modificar o core da fabrica, usar segredos, fazer chamadas pagas, publicar, instalar dependencias ou substituir um produto existente. Testes podem rodar apenas dentro do proprio prototipo.

Antes de trabalhar, repita em cinco linhas: objetivo entendido, pasta de saida, arquivos que pretende criar, testes permitidos e o que ficara para revisao do Codex. Se a tarefa exigir sair das pastas permitidas, pare e produza apenas uma proposta.

Ao terminar:
- marque tudo como PROPOSTA - NAO IMPLEMENTADA ou PROTOTIPO ISOLADO - NAO INTEGRADO;
- registre fontes, licencas, custos, riscos, fatos e hipoteses;
- atualize docs/external_llm_inbox/deepseek/INDEX.md;
- preencha docs/external_llm_inbox/deepseek/HANDOFF_CHECKLIST.md;
- informe exatamente quais arquivos o Codex deve revisar.
- preencha uma copia de docs/external_llm_inbox/deepseek/SESSION_HANDOFF_TEMPLATE.md.

Minha tarefa de hoje e:
[ESCREVA AQUI O QUE VOCE QUER QUE ELE FACA]
```

## Instrucao extra para LLMs futuras

Se Shin pedir uma ideia ou projeto, NÃO pare na Camada 1 (proposta simples).
Siga o **Workflow Evolved** abaixo automaticamente:
- Faca a arvore de dependencia (N0 a N8)
- Inclua auto-critica do que voce pode ter esquecido
- Se Shin pedir multiplas ideias, entregue o mapa de dependencias entre elas E o caminho critico

O documento `2026-07-13_MASTER_PROJECT_TREES.md` e o exemplo do nivel esperado.
Leia-o antes de comecar se Shin disser "faz igual a ultima vez".

## Onde cada trabalho deve ficar

| Tipo | Pasta |
|---|---|
| Ideia de renda ou melhoria | `ideas/` |
| Novo funcionario | `employees/` |
| Novo departamento | `departments/` |
| Pesquisa de ferramentas/APIs | `research/` |
| Diagnostico de cliente | `client_briefs/` |
| Codigo para experimentar | `prototypes/external_llm/<tarefa>/` |

## Workflow Evolved (2026-07-13)

A partir da conversa com Shin, o padrao de entrega foi refinado. Toda nova ideia, departamento ou projeto deve seguir esta estrutura em 4 camadas:

### Camada 1 — Proposta inicial (IDEA_TEMPLATE.md)
- One-Sentence Idea, Why It Fits, User Value, MVP Scope, Later Integrations
- **Entregar em 15-20 linhas**, nao em 80. Se Shin quiser aprofundar, ele pede.

### Camada 2 — Arvore de dependencia (se Shin pedir "estrutura")
- Por nivel: do conceito (N0) a integracao paga (N8)
- O que ja existe (checklist), o que construir (diamante), risco financeiro ($), decisao humana (?)
- Employees, Capabilities, Custos MOCK vs REAL

### Camada 3 — Riscos e auto-critica (sempre)
- O que eu (LLM) posso ter deixado passar
- O que so Shin/Codex pode decidir
- Dependencias externas, fallbacks, manutencao

### Camada 4 — Caminho critico
- Se Shin tem multiplas ideias, mapear dependencias entre elas
- O que construir primeiro para desbloquear as outras
- Recomendacao sincera de prioridade

### Checklist pessoal da LLM antes de entregar:
- [ ] Eu realmente detalhei TUDO que precisa acontecer para isso ficar pronto?
- [ ] O que eu NAO pensei? (se nao sei, escreva "nao sei o que falta")
- [ ] Essa ideia depende de outra ideia da lista?
- [ ] Shin consegue executar isso sem ler documentacao externa?
- [ ] Qual o custo real minimo para testar? (nao so MOCK, mas tempo de Shin)
- [ ] O que so o Codex pode decidir? (separei claramente?)

## Regra de integracao

O DeepSeek pode pesquisar, especificar e montar um prototipo isolado. Somente o Codex revisa, adapta, testa contra a regressao completa e integra ao produto real.
