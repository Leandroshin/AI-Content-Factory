# Idea Proposal: Content Scheduling & Calendar Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que gerencia o calendario editorial da fabrica: recebe metas de producao (ex: "3 posts por semana"), distribui tarefas entre departamentos existentes, evita conflitos de agendamento, respeita sazonalidades e produz um plano editorial semanal/mensal com status de cada peca.

## Why It Fits The AI Content Factory

Hoje a producao e reativa — uma task chega e os departamentos executam. Nao existe visao de "o que precisa ser produzido esta semana" ou "este feriado exige conteudo tematico". Um departamento de scheduling transforma a fabrica de reativa em proativa: ela mesma descobre o que precisa ser feito, distribui e acompanha.

## User Value

- Shin define "quero 2 videos, 3 posts de afiliado e 1 newsletter por semana" e o departamento quebra isso em tarefas diarias para os outros departamentos.
- Calendario visual com cores por departamento: verde (pronto), amarelo (em producao), vermelho (atrasado).
- Alertas automaticos: "Nenhum conteudo agendado para a Black Friday — deseja criar um briefing?"
- Feriados, eventos do nicho (lancamento de console, copa do mundo) sao automaticamente considerados.

## Proposed Workflow

```
ReceivedTask{action, content_goals, date_range, season_events}
  -> Pipeline stages (action=CREATE_PLAN):
     1. GOAL_ANALYSIS             (interpretar metas: "3 posts/semana" -> 12 posts/mes)
     2. CAPACITY_CHECK            (verificar se departamentos existentes dao conta)
     3. TIMELINE_BUILD            (distribuir tarefas nos dias uteis, evitar sobrecarga)
     4. SEASONALITY_SCAN          (detectar feriados, eventos, sazonalidades do nicho)
     5. DEPARTMENT_DISPATCH       (criar tarefas para cada departamento via CompanyTaskRuntime)
     6. CALENDAR_ASSEMBLY         (montar calendario com tarefas, prazos, dependencias)
     7. PROGRESS_TRACKING         (monitorar conclusao, detectar atrasos, sugerir replanejamento)
```

## Required Employees

1. **ContentSchedulerEmployee** — herda ProductionEmployee, gerencia pipeline de calendario.
   - Hooks: `_check_reject()` rejeita se `action` desconhecido ou `content_goals` vazio; `_build_pipeline()` monta SchedulingPipeline; `_build_output_from_stages()` extrai `calendar` do CALENDAR_ASSEMBLY.

2. (Futuro) **CalendarVisualizer** — helper que gera representacao textual ou HTML do calendario.

## Required Capabilities

Todas ja existentes:
- `DATABASE` (persistir calendario e tarefas)
- `DOCUMENT_GENERATION` (calendario como artefato)
- `STORAGE` (historico de planos executados)
- `CALENDAR` (ja declarada em core/tools/capabilities.py, atualmente sem uso em departamentos)

## Risks And Compliance

- **Superficie vs profundidade**: planejar muitos posts pode sacrificar qualidade. O departamento deve respeitar limites de capacidade e sugerir reducao quando a demanda exceder.
- **Dependencia entre departamentos**: um video depende de script e audio prontos. O scheduler deve respeitar a ordem correta e nao agendar renderizacao sem insumos.
- **Sazonalidade real**: feriados e eventos variam por nicho. O MVP deve usar uma tabela fixa de feriados nacionais + eventos de games (para o radar de gaming).

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages, action=CREATE_PLAN.
2. ContentSchedulerEmployee com hooks padrao.
3. Snapshot `ContentCalendarSnapshot` (tasks_created, tasks_completed, overdue_count, plan_week, plan_month).
4. Calendario MOCK de 30 dias com: 8 tarefas de script, 8 de audio, 8 de imagem, 4 de video, 4 de afiliado, 4 de email.
5. Tabela interna de feriados 2026/2027 (Natal, Ano Novo, Carnaval, Black Friday, Dia dos Pais/Maes).
6. Demo com 30+ assertions: goal analysis, timeline, seasonality, dispatch, calendar, progress tracking.
7. Capacidade de gerar "plano semanal" e "plano mensal" como saidas distintas.

## Later Integrations

- Sincronizacao com Google Calendar (para Shin ver no celular)
- Sincronizacao com o Factory Dashboard (exibir calendario na Central)
- Notificacoes no Telegram ("3 tarefas atrasadas hoje")
- Conectar ao Gaming News Desk para agendar automaticamente pautas aprovadas

## Open Questions For Shin/Codex

1. O scheduler deve disparar tasks automaticamente ou apenas gerar o plano e aguardar aprovacao humana?
2. A capacidade de cada departamento deve ser fixa (ex: 2 tarefas/dia) ou calculada dinamicamente baseada em metricas?
3. Shin quer que o calendario considere o "momento ideal de postagem" por plataforma (ex: Instagram as 18h, YouTube as 10h)?
4. Este departamento deve conversar com o Business Intelligence para aprender quais dias/horarios performam melhor?

## Sources

- Google Calendar API: https://developers.google.com/calendar/api
- Feriados nacionais brasileiros: https://www.gov.br/trabalho-e-emprego/pt-br/feriados-nacionais
- Best posting times por plataforma (dados gerais): https://blog.hootsuite.com/best-time-to-post-on-social-media/
