# AI Content Factory — Onboarding para LLM

Leia os arquivos na ordem abaixo. Cada etapa pressupõe que você leu as anteriores.

---

## PARTE 0 — Fundação do Projeto

### 0.1 `AGENTS.md`
**Por que ler primeiro:**
Contém todo o estado atual do projeto: decisões arquiteturais, regras de não-modificação, o que já foi feito, o que é próximo passo, e lista de arquivos relevantes. É a âncora.

Após ler, você saberá:
- Quais classes NUNCA podem ser modificadas (CEO, DM, SE, ToolRuntime, etc.)
- A cadeia de herança: SpecialistEmployee → ProductionEmployee → VideoEditorEmployee
- O padrão de hooks que todo departamento deve seguir
- Que existem 10 demos com 345 assertions que não podem quebrar

---

## PARTE 1 — Núcleo da Empresa (não modificar)

### 1.1 `core/company/specialist_employee.py`
**Por que ler antes de tudo:**
É a classe base de TODOS os funcionários. ProductionEmployee herda dela. VideoEditorEmployee herda de ProductionEmployee. Entender SpecialistEmployee é entender o alicerce.

Foco:
- `SpecialistEmployee.__init__` — parâmetros, `_event_bus`, `_publish()`
- `receive_task()` — retorna `TaskDecision.ACCEPTED` ou `REJECTED`
- `execute_task()` — retorna `ExecutionResult`
- Eventos: `TaskAccepted`, `TaskRejected`, `TaskStarted`, `TaskFinished`, `TaskBlocked`
- `request_capability()` — como o funcionário pede capacidades sem nomear ferramentas
- `state()` — serialização do estado

### 1.2 `core/company/department_manager.py`
**Por que ler:**
É o orquestrador que recebe planos do CEO, decompõe em tarefas, e as atribui a funcionários. O VideoEditorEmployee interage com ele via `_department_manager.complete_task()`.

Foco:
- `receive_plan()` → `assign_task()` → `complete_task()`
- Como o DM gerencia o ciclo de vida das tarefas

### 1.3 `core/company/quality.py`
**Por que ler:**
ProductionEmployee (e portanto VideoEditorEmployee) usa QualityRuntime para validação pós-produção. É rule-based, sem IA.

Foco:
- `register_rule()`, `validate()`, `generate_correction()`, `reports()`
- 4 categorias built-in
- O padrão: valida → recebe relatório → gera correções se falhou

### 1.4 `core/runtime.py`
**Por que ler:**
`CompanyRuntime` é a "empresa" criada nos demos. Fornece `event_bus`, `employee_runtime`, `register_employee()`, `initialize_company()`. Todo demo cria uma.

---

## PARTE 2 — Camada Base (template para departamentos)

### 2.1 `core/departments/base/pipeline.py`
**Por que ler:**
Define `StageResult` (frozen+slots) e `ProductionPipeline` (ABC). Todo pipeline departamental estende `ProductionPipeline`.

Foco:
- `StageResult(stage, success, summary, output, error, next_stage)` — genérico
- `ProductionPipeline` — `advance()` abstrato, `stage`, `progress`, `stages_log`, `reset()`

### 2.2 `core/departments/base/models.py`
**Por que ler:**
`ProductionMetrics` genérico com campos: total_stages, completed_stages, failed_stages, quality_passed, quality_corrections, duration_minutes.

Cada departamento define seu próprio `ProductionMetrics` com campos adicionais.

### 2.3 `core/departments/base/employee.py`
**Por que ler:**
`ProductionEmployee` — a classe que todo departamento concreto herda. Entender os hooks é essencial.

Foco nos hooks (cada departamento sobrescreve apenas estes):
- `_check_reject(task)` → retorna `str` (rejeita) ou `None` (aceita)
- `_build_pipeline(task)` → **obrigatório**, retorna `ProductionPipeline`
- `_estimate_duration(ctx)` → tempo estimado em minutos
- `_build_output_from_stages(output, parts)` → extrair resultado dos stages
- `_build_metrics(completed, failed, output, duration)` → métricas final
- `_build_summary(success, parts)` → mensagem final
- `_run_quality_check(output)` → validação de qualidade
- `analyze_capability_needs()` → `tuple[Capability, ...]`
- `state()` → adicionar campos específicos ao dict

O `execute_task()` genérico: avança pipeline até completed/failed, coleta output, roda quality, constrói métricas, publica eventos.

---

## PARTE 3 — Departamento de Vídeo (prova do conceito)

### 3.1 `core/departments/video/models.py`
**Por que ler:**
Todos frozen+slots. Mostra o padrão de modelos departamentais.

- `VideoTask(task_id, title, video_type, duration_seconds, assets, subtitles, timeline, render_profile)`
- `VideoAsset`, `AudioAsset`, `ImageAsset` — tipos de mídia
- `TimelineSegment`, `SubtitleSegment`
- `RenderProfile(format, codec, resolution, fps, bitrate, quality)`
- `VideoProject` — agregação completa

### 3.2 `core/departments/video/pipeline.py`
**Por que ler:**
`PipelineStage` enum com 9 stages (CREATED → ANALYZING → VALIDATING → PLANNING → EXECUTING → RENDERING → DELIVERING → COMPLETED / FAILED).

`VideoProductionPipeline` estende `ProductionPipeline`. Cada stage é um método handler. A máquina de estados é determinística (sem AI).

Veja como `advance()` é implementado: mapeia `PipelineStage` para handlers, executa, transiciona.

### 3.3 `core/departments/video/employee.py`
**Por que ler:**
`VideoEditorEmployee(ProductionEmployee)` — o departamento concreto.

Veja o padrão de implementação:
- `_DEPARTMENT_KEYWORD = "video"` — usado no `_check_reject`
- `VideoCapability` — 11 capacidades específicas de vídeo
- `ProductionMetrics` — versão com campos de vídeo (assets_validated, segments_processed, effects_applied, render_format, render_resolution, estimated_size_mb) + campos genéricos
- `receive_task()` extrai `render_profile`, `timeline`, `assets`, `subtitles` do `task.context` (dict)
- `_build_pipeline()` → `VideoProductionPipeline(self._current_video_task)`
- `_build_output_from_stages()` → puxa `render` do RENDERING, output do DELIVERING
- `_build_metrics()` → preenche métricas de vídeo
- `analyze_capability_needs()` → retorna `VIDEO_EDITING`, `TRANSLATION`, `BROWSER_AUTOMATION`, `IMAGE_GENERATION`
- `state()` → adiciona `video_capabilities`, `current_video_task` ao dict

### 3.4 `core/departments/video/__init__.py`
**Por que ler:**
Exports públicos do departamento. Padrão para futuros departamentos.

---

## PARTE 4 — Observabilidade

### 4.1 `core/observability.py`
**Por que ler:**
Mostra a hierarquia de snapshots.

- `ProductionSnapshot(task_id, pipeline_stage, progress, stages_completed, stages_failed, quality_passed, duration_minutes)` — genérico
- `VideoProductionSnapshot(ProductionSnapshot)` — + `video_type`
- `VideoDepartmentSnapshot`, `RenderSnapshot`
- `ObservabilitySnapshot` — contém TODAS as snapshots
- `ObservabilityProjector` — event-driven, handlers para cada tipo de evento

---

## PARTE 5 — Infraestrutura (Tool Adapters, HTTP, Persistence)

### 5.1 `core/company/persistence.py`
**Por que ler:**
`PersistenceRuntime` — salva/carrega sessões, execution records, evidências. Usa JSON em `.ai_company/`.

### 5.2 `core/company/organizational_memory.py`
**Por que ler:**
`OrganizationalMemoryRuntime` — documentos versionados, CRUD completo.

### 5.3 `core/tools/http/`
**Por que ler:**
`HttpClient`, `RealHttpClient` (urllib), `RateLimiter` (token-bucket), eventos HTTP.

### 5.4 `core/tools/adapters/` (youtube_adapter.py, github_adapter.py, elevenlabs_adapter.py, playwright_adapter.py)
**Por que ler:**
Cada adapter implementa `execute()` com dual mode: MOCK (dados deterministicos) / REAL (chamadas HTTP reais).

`AbstractToolAdapter` + `set_secret_provider()` — padrão aditivo.

### 5.5 `core/events/domain_events.py`
**Por que ler:**
11 eventos de domínio: SessionCreated/Loaded/Saved, ExecutionPersisted/Restored, MemoryDocumentCreated/Updated/Archived, QualityValidationStarted/Finished.

---

## PARTE 6 — Demos (prova de funcionamento)

### 6.1 `demo_video_department.py`
**Por que ler primeiro entre as demos:**
55 assertions que cobrem: criação, aceite/rejeição, pipeline, métricas, state, workload, quality events, capability analysis.

### 6.2 `demo_quality_loop.py`
34 assertions: register rules, validate success/fail, generate corrections, observability.

### 6.3 `demo_persistence.py`
26 assertions: persistir execution record, session, evidence, reload.

### 6.4 `demo_organizational_memory.py`
37 assertions: CRUD documentos, versionamento, arquivamento.

### 6.5 `demo_session_recovery.py`
30 assertions: salvar sessão, reconstruir estado, continuar.

### 6.6 `demo_tool_runtime.py`
38 assertions: register, configure, execute tools, credential store.

### 6.7 `demo_adapter_lifecycle.py`
49 assertions: lifecycle completo dos adapters, status, owner guidance.

### 6.8 `demo_adapter_execution.py`
20 assertions: execute adapters em MOCK mode.

### 6.9 `demo_capability_resolver.py`
32 assertions: register capabilities, request, resolve, unavailable.

### 6.10 `demo_real_adapters.py`
24 assertions: MOCK/REAL dual mode com fallback por env vars.

---

## Resumo da Cadeia

```
CEO (core/company/ceo.py)
  └── cria plano
        └── DepartmentManager (core/company/department_manager.py)
              ├── decompõe em tarefas
              ├── atribui a SpecialistEmployee ou ProductionEmployee
              └── completa tarefa
                    └── SpecialistEmployee (core/company/specialist_employee.py)
                          └── ProductionEmployee (core/departments/base/employee.py)   ← CAMADA BASE
                                ├── pipeline (core/departments/base/pipeline.py)
                                ├── quality (core/company/quality.py)
                                ├── metrics (core/departments/base/models.py)
                                └── hooks para departamentos
                                      └── VideoEditorEmployee (core/departments/video/employee.py)  ← VÍDEO
                                            ├── VideoProductionPipeline (core/departments/video/pipeline.py)
                                            ├── VideoTask, RenderProfile, etc. (core/departments/video/models.py)
                                            ├── VideoProductionSnapshot (core/observability.py)
                                            └── demo_video_department.py
```

---

## Regras de Ouro (copiadas do AGENTS.md)

1. NUNCA modifique: CEO, DepartmentManager, SpecialistEmployee, ToolRuntime, CapabilityRegistry, ToolRegistry, QualityRuntime, PersistenceRuntime, OrganizationalMemoryRuntime, CompanyOrchestrator
2. NUNCA remova APIs ou quebre compatibilidade reversa
3. Toda implementação aditiva (frozen+slots)
4. compileall + TODAS as demos obrigatório antes de concluir
5. Novos departamentos herdam de ProductionEmployee, NUNCA de SpecialistEmployee
6. Employee usa CapabilityRegistry, nunca nomeia ferramentas específicas
