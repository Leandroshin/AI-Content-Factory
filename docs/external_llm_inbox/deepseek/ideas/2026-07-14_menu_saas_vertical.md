# Vertical: Menu SaaS (Cardapio Digital)

**Status:** PROPOSTA - NAO IMPLEMENTADA  
**Data:** 2026-07-14  
**Inspiracao:** Modelo micro SaaS via IA + operacao recorrente  
**Vantagem Fabrica:** Employees prontos para operar cada SaaS, nao apenas construir

---

## N0 — One-Sentence Idea

Vender assinatura mensal de cardapio digital com QR code para negocios locais (restaurantes, bares, acai, lanchonetes), onde a AI Content Factory opera todo o backend, atualizacao e suporte — o cliente paga R$97/mes e nunca precisa mexer em nada.

---

## N1 — Por que encaixa na Fabrica

| Requisito | O que ja temos |
|---|---|
| Producao de conteudo | ScriptWriter cria descricoes, ImageDesigner faz fotos/thumbnails |
| Publicacao | TelegramAdapter notifica cliente sobre views |
| Compliance | Disclosure de alergenicos, precos, termos |
| Provider control | Budget Guard para APIs externas (Google Maps, ifood) |
| Dashboard | Factory Dashboard v2 ja tem template de painel |
| Pagamento | Hotmart/Kangu integrado (webhook) |
| HITL | Approval Gateway para gate de publicacao de alteracoes |

---

## N2 — Business Model

### Precificacao

| Plano | Preco | O que inclui |
|---|---|---|
| Starter | R$ 47/mes | 1 cardapio, 10 categorias, 30 itens, QR code estatico |
| Pro | R$ 97/mes | 1 cardapio, categorias ilimitadas, fotos profissionais via ImageDept, QR code por mesa, pedidos online |
| Multi | R$ 197/mes | 3 cardapios (ex: matriz + filiais), relatorios, integracao iFood/WhatsApp |

### Numeros-alvo

| Cenario | Clientes | Ticket medio | MRR |
|---|---|---|---|
| Lancamento | 10 | R$ 77 | R$ 770/mes |
| Mes 3 | 50 | R$ 77 | R$ 3.850/mes |
| Mes 6 | 150 | R$ 87 | R$ 13.050/mes |
| Mes 12 | 300 | R$ 87 | R$ 26.100/mes |

### Canais de aquisicao (trafego pago + organico)

| Canal | Custo estimado | Conversao esperada |
|---|---|---|
| Facebook Ads (video + lead) | R$ 3-5/lead | 5-10% lead → cliente |
| TikTok organico (videos mostrando o cardapio) | R$ 0 | Viral potencial |
| Google Ads ("cardapio digital", "menu digital") | R$ 2-4/clique | 3-5% |
| Microinfluenciadores locais | R$ 200-500/post | 10-20 leads/post |
| Venda direta (whatsapp, presencia) | R$ 0 (tempo) | Alta |

---

## N3 — Arquitetura de Employees

### Novo Employee: `MenuOperatorEmployee`

Herda `ProductionEmployee`. Opera o cardapio digital de cada cliente.

**Hooks:**

| Hook | Comportamento |
|---|---|
| `_check_reject(task)` | Rejeita se `department != "menu"` |
| `_build_pipeline(task)` | `MenuProductionPipeline(menu_task)` |
| `_estimate_duration(ctx)` | 15s por item de cardapio |
| `_build_output_from_stages(output, parts)` | Extrai: `public_url`, `qr_code_svg`, `qr_code_png`, `admin_url`, `preview_html` |
| `_build_metrics(completed, failed, output, duration)` | `items_count`, `categories_count`, `photos_count`, `qr_code_generated` |
| `_run_quality_check(output)` | Valida: todos itens com preco, fotos presentes, QR code funcional, URLs acessiveis |
| `analyze_capability_needs()` | `MENU_MANAGEMENT`, `QR_CODE_GENERATION`, `MENU_PUBLISHING`, `IMAGE_EDITING`, `TEXT_GENERATION` |
| `state()` | Adiciona `client_name`, `plan_type`, `menus_active`, `total_views` |

### Capabilities Novas

| Capability | Descricao |
|---|---|
| `MENU_MANAGEMENT` | Criar, editar, organizar cardapios |
| `QR_CODE_GENERATION` | Gerar QR code estatico/dinamico para URL do cardapio |
| `MENU_PUBLISHING` | Publicar cardapio em URL publica + domínio personalizado |

### Outros Employees envolvidos

| Employee | Papel no fluxo |
|---|---|
| `ScriptWriterEmployee` | Cria descricoes de pratos, hooks de cardapio, SEO text |
| `ImageDesignerEmployee` | Gera fotos de pratos (MOCK: placeholder; REAL: provider de imagem) |
| `MenuOperatorEmployee` | Operacao continua: atualizar precos, adicionar itens, remover esgotados |
| `Compliance & Rights Employee` | (proposto) Verifica precos visiveis, disclosure de alergenicos, LGPD |
| `Community Engagement Employee` | (proposto) Suporte ao cliente, dúvidas, onboarding |

---

## N4 — Models (frozen+slots)

```python
# core/departments/menu_saas/models.py

class MenuClient:
    """Cliente que assina o cardapio digital"""
    client_id: str
    business_name: str
    business_type: str        # "restaurant", "bar", "acai", "lanchonete"
    address: str
    phone: str
    plan_type: str             # "starter", "pro", "multi"
    active: bool
    subscription_id: str       # Hotmart/Kangu
    monthly_price: Decimal
    created_at: datetime
    updated_at: datetime


class MenuCategory:
    """Categoria dentro de um cardapio"""
    category_id: str
    client_id: str
    name: str
    description: str
    display_order: int
    active: bool


class MenuItem:
    """Item individual do cardapio"""
    item_id: str
    category_id: str
    client_id: str
    name: str
    description: str
    price: Decimal
    original_price: Decimal | None  # preco riscado (promocao)
    photo_url: str | None
    photo_file_path: str | None     # asset fisico
    tags: list[str]                 # "vegano", "sem gluten", "promocao"
    available: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class MenuQRCode:
    """QR code gerado para um cardapio"""
    qr_id: str
    client_id: str
    menu_url: str
    qr_type: str               # "static" (unico) ou "table" (por mesa)
    table_number: int | None   # se for QR por mesa
    svg_data: str              # SVG do QR code
    png_file_path: str         # asset fisico
    generated_at: datetime


class MenuView:
    """View/click tracking"""
    view_id: str
    client_id: str
    item_id: str | None
    timestamp: datetime
    source: str                # "qr_code", "direct_link", "instagram", "google"
    ip_hash: str               # hash anonimizado


class MenuTask:
    """Task que o MenuOperatorEmployee recebe"""
    task_type: str             # "create_menu", "update_items", "add_photos", "publish"
    client_id: str
    client: MenuClient
    categories: list[MenuCategory]
    items: list[MenuItem]
    qr_codes: list[MenuQRCode]
    custom_domain: str | None
    publish_immediately: bool
```

---

## N5 — Pipeline (MenuProductionPipeline)

8 stages deterministicos:

```python
class MenuPipelineStage(Enum):
    CLIENT_ONBOARDING = "client_onboarding"      # Validar dados do cliente e plano
    MENU_STRUCTURE = "menu_structure"             # Criar categorias e organizacao
    ITEM_POPULATION = "item_population"           # Popular itens com nome e preco
    DESCRIPTION_GENERATION = "description_gen"    # ScriptWriter cria descricoes
    IMAGE_PRODUCTION = "image_production"         # ImageDesigner gera fotos
    QR_CODE_GENERATION = "qr_code_generation"     # Gerar QR codes + download
    PUBLISHING = "publishing"                      # Publicar URL + dominio
    BILLING_SETUP = "billing_setup"               # Configurar cobranca recorrente
```

### Stage Details

| Stage | Input | Output | Regra de sucesso |
|---|---|---|---|
| CLIENT_ONBOARDING | MenuClient | validated_client, plan_config | business_name preenchido, plan_type valido, subscription_id ok |
| MENU_STRUCTURE | validated_client | categories list | Min 1 categoria, max 20, nomes unicos |
| ITEM_POPULATION | categories | items list | Min 3 itens por categoria, precos > 0 |
| DESCRIPTION_GENERATION | items | items + descriptions | ScriptWriter gera 1-2 linhas por item |
| IMAGE_PRODUCTION | items | items + photo_urls | ImageDesigner gera 1 foto/item (MOCK: placeholder) |
| QR_CODE_GENERATION | menu_url | qr_codes (svg+png) | QR valido escaneavel, URL funcional |
| PUBLISHING | complete menu | public_url, admin_url | URL publica responde 200, admin URL protegida |
| BILLING_SETUP | client + plan | billing_webhook_config | Hotmart webhook configurado, trial de 7 dias |

---

## N6 — Fluxo Completo (Cliente → Operacao → Recorrencia)

### Ciclo de vida do cliente

```
[FACEBOOK ADS] --> [LANDING PAGE] --> [CADASTRO (7 dias gratis)]
       |                                      |
       v                                      v
  Lead criado                        Cliente no Hotmart
       |                                      |
       v                                      v
  [ONBOARDING AUTOMATICO] <---- [WEBHOOK ASSINATURA]
       |
       |-- MenuOperatorEmployee recebe MenuTask(task_type="create_menu")
       |-- Executa pipeline: estrutura + itens + fotos + QR + publicacao
       |-- Envia para o cliente: URL publica + QR code para imprimir
       |-- Compliance check: precos, alergenicos, disclosure
       |
       v
  [CLIENTE ATIVO] --> Coloca QR nas mesas --> Clientes escaneiam --> Views
       |
       v (todo mes)
  [FATURAMENTO RECORRENTE]
       |
       |-- Cliente quer alterar preco? Manda WhatsApp
       |-- Community Employee recebe, cria MenuTask(task_type="update_items")
       |-- MenuOperatorEmployee executa update em < 30s
       |-- Publica automaticamente
       |
       v
  [CLIENTE FELIZ] --> Renova --> Indica --> Novo lead
```

### Tela do cliente final (quem escaneia o QR)

```
┌──────────────────────────────┐
│         🍔 CARDAPIO          │
│     Restaurante do Caio      │
│         Rua do Caio, 123     │
├──────────────────────────────┤
│                              │
│  🔍 [Buscar no cardapio...]  │
│                              │
│  ─── PRATOS INDIVIDUAIS ─── │
│                              │
│  🍝 Macarronada       R$9,90 │
│     Massa ao molho sugo...   │
│                              │
│  🥗 Salada Caesar    R$12,90 │
│     Alface, croutons,...     │
│                              │
│  ─── BEBIDAS ─────────────── │
│                              │
│  🥤 Coca-Cola         R$5,00 │
│  🍺 Cerveja           R$8,00 │
│                              │
│  [🛒 FAZER PEDIDO VIA WHATS] │
│                              │
│  ★★★★★ 4.8 (120 avaliações)  │
└──────────────────────────────┘
```

### Painel do cliente (dono do restaurante)

```
┌──────────────────────────────────────┐
│  📊 CardapioPro ─ Dashboard          │
├──────────────────────────────────────┤
│  [Visao Geral] [Cardapio] [QR] [Pagar]│
├──────────────────────────────────────┤
│                                      │
│  Views hoje: 47   ||  Pedidos: 12    │
│  Views mes: 1.230 ||  Taxa conv: 25% │
│                                      │
│  ─── ITENS MAIS VISTOS ───           │
│  1. Macarronada     230 views        │
│  2. Coca-Cola       180 views        │
│  3. Salada Caesar   145 views        │
│                                      │
│  [EDITAR CARDAPIO] [QR CODE] [PLANOS]│
└──────────────────────────────────────┘
```

### Painel da Fabrica (operacao interna)

```
┌──────────────────────────────────────┐
│  🏭 Fabrica ─ Cardapios Ativos: 47  │
├──────────────────────────────────────┤
│                                      │
│  🔴 PENDENTES (3)                    │
│  │─ Restaurante KiDelicia ── R$97    │
│  │   Status: aguardando fotos        │
│  │─ Bar do Ze ── R$47                │
│  │   Status: criar categorias        │
│  │─ Acai da Maria ── R$97            │
│  │   Status: publicar                │
│                                      │
│  🟢 ATIVOS (44)                      │
│  │─ Restaurante do Caio ── 47 views  │
│  │─ Pizzaria Napoli ── 230 views     │
│  └─ ...                              │
│                                      │
│  [NOVO CLIENTE] [FILA] [RELATORIOS]  │
└──────────────────────────────────────┘
```

---

## N7 — Integracoes com a Fabrica Existente

| Componente atual | Uso no Menu SaaS |
|---|---|
| `TelegramAdapter` | Notificar cliente: "Seu cardapio teve 47 views hoje!" |
| `HotmartWebhook` | Receber confirmacao de pagamento, cancelamento, trial |
| `Provider/BudgetGuard` | Se usar API de imagem REAL (Gemini, DALL-E) para fotos |
| `QualityRuntime` | Validar itens sem preco, fotos faltando, QR quebrado |
| `OrganizationalMemory` | Armazenar metricas de cada cliente, aprendizado |
| `PersistenceRuntime` | Salvar estado de cada cardapio |
| `HITL/ApprovalGateway` | Gate para publicar alteracoes criticas (precos, itens novos) |
| `Observability` | Snapshots de cada operacao de cardapio |
| `Factory Dashboard` | Painel interno para ver fila de cardapios pendentes |
| `Script Department` | Descricoes de pratos, textos de SEO, descricao do restaurante |
| `Image Department` | Fotos de pratos, logo do cliente, capa do cardapio |
| `KokoroTTS` | (futuro) Audiodescricao do cardapio para acessiveis |

### Adaptadores Novos Necessarios

| Adapter | Funcao | MOCK | REAL |
|---|---|---|---|
| `QRCodeAdapter` | Gerar QR code SVG+PNG | `qrcode` lib Python (MIT) | Mesmo, local |
| `DomainAdapter` | Conectar dominio personalizado | Simular config | Cloudflare API / Hostinger |
| `MenuViewTracker` | Rastrear views/click | Log local | Analytics leve (Plausible/umami) |
| `WhatsAppSenderAdapter` | Enviar confirmacao de pedido | Log | API WhatsApp Business |
| `GoogleMapsAdapter` | Mostrar localizacao do restaurante | Placeholder | Google Maps Embed |

---

## N8 — Fases de Implementacao

### Fase 0 — Proposta e Prototipo (agora)

- [ ] Documento de especificacao (este arquivo)
- [ ] Prototipo HTML estatico: public menu + admin dashboard + factory panel
- [ ] Validacao visual com Shin
- [ ] Codex revisa e ajusta

### Fase 1 — MOCK Operacional (sem site real)

- [ ] Criar `core/departments/menu_saas/models.py` (frozen+slots)
- [ ] Criar `core/departments/menu_saas/pipeline.py` (8 stages)
- [ ] Criar `core/departments/menu_saas/employee.py` (MenuOperatorEmployee)
- [ ] Criar `core/departments/menu_saas/__init__.py`
- [ ] Criar `demo_menu_saas_department.py` (30+ assertions)
- [ ] Tudo MOCK: cardapio gerado em memoria, QR code simulado, fotos placeholder
- [ ] compileall + regressao

### Fase 2 — QR Code + Visual

- [ ] Instalar `qrcode` + `Pillow` no requirements
- [ ] `QRCodeAdapter` (MOCK via lib, REAL via lib tambem — nao precisa de API)
- [ ] Render HTML do cardapio publico (template responsivo)
- [ ] Gerar QR code PNG real
- [ ] Testar: escanear QR → ver cardapio no celular

### Fase 3 — Ciclo de Pagamento

- [ ] Integrar webhook Hotmart (ja existe)
- [ ] Criar trial de 7 dias: cliente usa gratis, depois cobra
- [ ] MenuOperatorEmployee recebe task automatica ao receber webhook
- [ ] Cancelamento: desativar cardapio, notificar cliente via Telegram

### Fase 4 — Site Real + Dominio

- [ ] Comprar `cardapiopro.com.br` (ou similar)
- [ ] Hostinger/Orzons para hospedar o site do cardapio
- [ ] Cada cliente ganha `seurestaurante.cardapiopro.com.br`
- [ ] Opcao de dominio personalizado (`cardapio.dorestaurante.com.br`)

### Fase 5 — Trafego Pago

- [ ] Criar landing page oficial do CardapioPro
- [ ] Criar imagem/criativo META (ImageDepartment + ScriptWriter)
- [ ] Subir campanha Facebook Ads (MOCK: simular lead)
- [ ] Pipeline: Lead → Trial → Onboarding automatico → Ativo

### Fase 6 — Escala

- [ ] `ComplianceEmployee` para verificar cardapios antes de publicar
- [ ] `CommunityEmployee` para suporte ao cliente
- [ ] Relatorios mensais automaticos para cada cliente
- [ ] Pedidos online via WhatsApp (WhatsAppSenderAdapter)
- [ ] Integracao iFood (API oficial iFood)

---

## Riscos e Auto-crítica (Camada 3)

### O que eu (LLM) posso ter deixado passar:

1. **Suporte ao cliente:** Se tiver 50 clientes pagando R$97, cada um vai pedir alteracao 2-3x por semana. 150 tarefas/semana. Precisa de fila automatizada ou vai virar pesadelo operacional. A pipeline de 30s por item resolve? Talvez precise de batch processing.

2. **Fotos reais:** O ImageDepartment MOCK gera placeholder colorido. Cliente real quer foto REAL do prato dele. Ou a gente pede foto, ou usa provider de geracao de imagem (Gemini/DALL-E = custo). **Decisao de Shin/Codex.**

3. **QR code em mesas:** Cliente com 20 mesas precisa de 20 QR codes diferentes (um por mesa). Nosso modelo suporta `table_number`. Mas a logistica de imprimir e plastificar cada QR code é fisica — a fabrica nao imprime.

4. **Concorrencia:** Cardapio digital tem CONCORRENCIA (CardapioWeb, MenuDigital, iFood Cardapio, etc.). Nosso diferencial é OPERACAO via fabrica — mas isso é invisivel pro cliente final. **Como comunicar isso na landing page?**

5. **O que NAO pensei:** O cliente pode querer integracao com maquininha de cartao (Stone, PagSeguro) para pedir e pagar na mesa. Isso é N8+ — nao no MVP.

6. **Trial de 7 dias:** 7 dias gratis significa que a fabrica opera de graca por 7 dias. Se 100 trials entrarem, sao 700 cardapios-dia de processamento gratuito. Custo operacional MOCK = 0, mas REAL = tempo de processamento.

### O que so Shin/Codex decide:

- Nome final do produto (CardapioPro? MenuPro? CardapioFabrica?)
- Quanto cobrar (R$47/97/197 ou tabela diferente)
- Orzons vs autogerenciado (Hostinger + Cloudflare)
- Se vale a pena virar agencia (operar pra terceiros) ou so SaaS puro
- Quem faz as vendas: Shin (trafego pago), vendedor, ou automatizado via lead + onboarding?
- Se integra iFood na Fase 2 ou deixa pra depois

---

## Caminho Critico (Camada 4)

```
Ordem de implementacao recomendada:
                       
  F0: Proposta + Prototipo (agora, este arquivo)
       |
  F1: MOCK operacional (models + pipeline + employee + demo)
       |
  F2: QR Code real + template HTML responsivo
       |
  F3: Pagamento (webhook Hotmart + trial)
       |
  F4: Site real + dominio (Hostinger/Orzons)
       |
  F5: Trafego pago (criativos + campanha)
       |
  F6: Escala (suporte, compliance, relatorios, iFood)
```

**Primeiro passo concreto apos Codex revisar:** Criar os 4 arquivos do departamento `menu_saas/` (models, pipeline, employee, __init__) + demo com 30+ assertions. Tudo MOCK, zero gasto, zero API externa.

---

## Checklist pessoal da LLM

- [x] Detalhei TUDO que precisa acontecer? — Sim, 8 fases, modelos, pipeline, employee, integracoes, riscos
- [ ] O que eu NAO pensei? — Integracao com maquininha de cartao na mesa, e logistica de imprimir QR code fisico
- [x] Shin consegue executar sem documentacao externa? — Sim, tudo explicado
- [x] Custo real minimo para testar? — Fase 1 = R$ 0 (MOCK), Fase 2 = R$ 0 (qrcode lib gratuita), Fase 3 = R$ 0 (Hotmart ja integrado)
- [x] O que so Codex decide? — Nome, precos, infraestrutura real (Orzons vs manual)

---

## Fontes

- Video original: YouTube, Kaio Martins — "Micro SaaS com IA" (2026)
- Concorrente ativo: CardapioWeb, MenuDigital, iFood Cardapio
- Tecnologia: `qrcode` Python (MIT), Hostinger/Orzons, Hotmart/Kangu
