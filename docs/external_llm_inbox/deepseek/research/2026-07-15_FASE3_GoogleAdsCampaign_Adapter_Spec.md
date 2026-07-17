# FASE 3 — GoogleAdsCampaignAdapter

## 1. Objective

`GoogleAdsCampaignAdapter` gera um arquivo de campanha estruturado (JSON/CSV) que Shin pode importar diretamente no Google Ads. Contém todas as configurações do Video B (HNgMXUNsEi8): CPA = 50% da comissão, rede de pesquisa com display desligado, localizações específicas, idioma "todos", palavra-chave em FRASE, campanha de pesquisa tradicional (NÃO Performance Max). Modo MOCK apenas — sem chamadas de API, sem gasto real.

A cadeia é: `Google Ad → Landing Page (cookie) → Affiliate Checkout`.

## 2. Models (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class CampaignConfig:
    product_name: str
    target_url: str                          # landing page URL
    affiliate_link: str                      # link de afiliado final
    commission_usd: float                    # comissão por venda
    target_countries: tuple[str, ...] = ("US", "CA", "AU", "GB")
    daily_budget_usd: float = 20.0
    language: str = "all"
    keyword_match_type: str = "phrase"       # "phrase" | "exact" | "broad"
    bidding_strategy: str = "target_cpa"     # target_cpa = 50% da comissao

@dataclass(frozen=True, slots=True)
class KeywordGroup:
    keywords: tuple[str, ...]
    match_type: str                          # phrase | exact | broad
    negatives: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class AdGroup:
    name: str
    keywords: KeywordGroup
    headlines: tuple[str, ...]               # 3-5, max 30 chars each
    descriptions: tuple[str, ...]            # 2-3, max 90 chars each
    final_url: str
    display_path: str

@dataclass(frozen=True, slots=True)
class CampaignStructure:
    campaign_name: str
    status: str                              # "paused" (MOCK nunca publica)
    network_settings: dict                   # search_only, display off
    locations: tuple[str, ...]               # codigos de localizacao
    languages: str
    bidding: dict                            # strategy + target_cpa
    budget: dict                             # daily
    ad_groups: tuple[AdGroup, ...]

@dataclass(frozen=True, slots=True)
class CampaignExport:
    format: str                              # "json" | "csv"
    file_path: str
    structure: CampaignStructure
    product_name: str
```

## 3. Campaign Settings (Video B 00:16:36–00:21:45)

| Setting | Value | Fonte |
|---|---|---|
| `campaign_type` | `"search"` | B 00:19:30 — pesquisa tradicional |
| `network` | `"search_only"` | B 00:18:00 — desligar display |
| `search_partners` | `False` | B 00:18:00 — desligar search partners |
| `display_expansion` | `False` | B 00:18:00 |
| `locations` | `["US", "CA", "AU", "GB"]` | B 00:18:10 — presenca (nao interesse) |
| `location_presence` | `"people_in"` | B 00:18:10 |
| `languages` | `"all"` | B 00:19:10 |
| `bidding_strategy` | `"target_cpa"` | B 00:17:00 |
| `target_cpa` | `commission_usd * 0.50` | B 00:17:24 |
| `keyword_match` | `"phrase"` | B 00:20:31 — aspas duplas |
| `daily_budget` | `config.daily_budget_usd` | default $20.00 |
| `status` | `"paused"` | MOCK nunca publica |

**Location IDs** (Google Ads API):
- US = `2840`
- CA = `2124`
- AU = `2036`
- GB = `2826`

## 4. Ad Copy Generation Rules

### Headlines (max 30 chars, min 3)

Regra baseada no produto + "Official" para sinalizar marca real:

```
1. "{product_name} Official"          → "ProstaVive Official"
2. "Try {product_name} Today"         → "Try ProstaVive Today"
3. "Official {product_name} Site"     → "Official ProstaVive Site"
4. "Buy {product_name} Now"           → "Buy ProstaVive Now"          (se char < 30)
5. "{product_name} Results"           → "ProstaVive Results"          (se char < 30)
```

### Descriptions (max 90 chars, min 2)

```
1. "Support your health with {product_name}. Clinically studied formula trusted by thousands. Try it today risk-free!"
   → "Support your health with ProstaVive. Clinically studied formula trusted by thousands. Try it today risk-free!"

2. "Join satisfied customers who found relief with {product_name}. Order now with fast shipping and excellent support."
   → "Join satisfied customers who found relief with ProstaVive. Order now with fast shipping and excellent support."
```

### Display Path

`/{product_name_slug}` — ex: `/ProstaVive`

## 5. JSON Export Format — Schema Completo

```json
{
  "campaign": {
    "name": "ProstaVive - Search - US_CA_AU_GB",
    "type": "search",
    "status": "paused",
    "bidding_strategy_type": "target_cpa",
    "target_cpa_micros": 87800000,
    "budget_micros": 20000000,
    "budget_type": "daily",
    "network_settings": {
      "target_google_search": true,
      "target_search_network": false,
      "target_content_network": false,
      "target_partner_search_network": false
    },
    "locations": [
      {"id": 2840, "name": "United States", "presence": "people_in"},
      {"id": 2124, "name": "Canada", "presence": "people_in"},
      {"id": 2036, "name": "Australia", "presence": "people_in"},
      {"id": 2826, "name": "United Kingdom", "presence": "people_in"}
    ],
    "languages": ["all"],
    "ad_groups": [
      {
        "name": "ProstaVive - Phrase",
        "status": "paused",
        "keywords": [
          {"text": "prosta vive", "match_type": "phrase"},
          {"text": "prostavive", "match_type": "phrase"},
          {"text": "prostavive supplement", "match_type": "phrase"},
          {"text": "prosta vive review", "match_type": "exact"}
        ],
        "negative_keywords": [
          "free", "review", "amazon", "walmart", "ebay",
          "coupon", "discount", "cheap", "side effects",
          "complaints", "scam"
        ],
        "headlines": [
          "ProstaVive Official",
          "Try ProstaVive Today",
          "Official ProstaVive Site",
          "Buy ProstaVive Now"
        ],
        "descriptions": [
          "Support your health with ProstaVive. Clinically studied formula trusted by thousands. Try it today risk-free!",
          "Join satisfied customers who found relief with ProstaVive. Order now with fast shipping and excellent support."
        ],
        "final_url": "https://shinsite.vercel.app/prostavive",
        "display_path": "/ProstaVive"
      }
    ]
  }
}
```

**target_cpa_micros** = commission * 0.50 * 1_000_000

Ex: ProstaVive $175.60 commission → $87.80 CPA → `87800000` micros.

**budget_micros** = daily_budget * 1_000_000

Ex: $20.00 daily → `20000000` micros.

## 6. CSV Export Format (Google Ads Editor)

```csv
Campaign,Ad Group,Keyword,Match Type,Headline,Description 1,Description 2,Final URL,Display Path,Bid Strategy,Target CPA,Budget,Status,Location,Language
"ProstaVive - Search","ProstaVive - Phrase","prosta vive",phrase,"ProstaVive Official","Support your health with ProstaVive. Clinically studied formula trusted by thousands. Try it today risk-free!","Join satisfied customers who found relief with ProstaVive. Order now with fast shipping and excellent support.","https://shinsite.vercel.app/prostavive","/ProstaVive","target_cpa",87.80,20.00,paused,"US,CA,AU,GB","all"
```

Separate rows for each keyword + negative keyword:

```csv
Campaign,Ad Group,Keyword,Match Type,Headline,Description 1,Description 2,Final URL,Display Path,Bid Strategy,Target CPA,Budget,Status,Location,Language,Negative
"ProstaVive - Search","ProstaVive - Phrase","prosta vive",phrase,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",
"ProstaVive - Search","ProstaVive - Phrase","prostavive",phrase,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",
"ProstaVive - Search","ProstaVive - Phrase","prostavive supplement",phrase,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",
"ProstaVive - Search","ProstaVive - Phrase","prosta vive review",exact,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",
"ProstaVive - Search","ProstaVive - Negatives","free",,,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",TRUE
"ProstaVive - Search","ProstaVive - Negatives","review",,,,,,,,target_cpa,87.80,20.00,paused,"US,CA,AU,GB","all",TRUE
```

## 7. Adapter Pseudo-code

```python
class GoogleAdsCampaignAdapter(AbstractToolAdapter):
    """Gera arquivo de campanha Google Ads (JSON/CSV) para importacao.
    
    MOCK only — sem chamadas HTTP, sem gasto real.
    Nao requer Provider, SecretProvider ou HttpClient.
    """

    CAPABILITY = Capability.ADS_CAMPAIGN_MANAGEMENT

    def build_campaign(
        self,
        config: CampaignConfig,
        output_dir: str = "output/campaigns",
        export_format: str = "json"
    ) -> CampaignExport:
        """
        1. Valida config (commission > 0, target_url valida)
        2. Gera KeywordGroup via _generate_keywords
        3. Gera headlines via _generate_headlines
        4. Gera descriptions via _generate_descriptions
        5. Monta AdGroup
        6. Monta CampaignStructure com configuracoes do Video B
        7. Serializa para JSON ou CSV
        8. Escreve arquivo em output_dir
        9. Retorna CampaignExport com file_path
        """
        keyword_group = self._generate_keywords(config.product_name)
        headlines = self._generate_headlines(config.product_name)
        descriptions = self._generate_descriptions(
            config.product_name, "supplement", "prostate health"
        )

        ad_group = AdGroup(
            name=f"{config.product_name} - Phrase",
            keywords=keyword_group,
            headlines=headlines,
            descriptions=descriptions,
            final_url=config.target_url,
            display_path=f"/{config.product_name}"
        )

        target_cpa = round(config.commission_usd * 0.50, 2)

        structure = CampaignStructure(
            campaign_name=f"{config.product_name} - Search - US_CA_AU_GB",
            status="paused",
            network_settings={
                "target_google_search": True,
                "target_search_network": False,
                "target_content_network": False,
                "target_partner_search_network": False
            },
            locations=config.target_countries,
            languages="all",
            bidding={
                "strategy": "target_cpa",
                "target_cpa": target_cpa,
                "target_cpa_micros": int(target_cpa * 1_000_000)
            },
            budget={
                "daily": config.daily_budget_usd,
                "daily_micros": int(config.daily_budget_usd * 1_000_000)
            },
            ad_groups=(ad_group,)
        )

        if export_format == "json":
            content = self._build_json(structure)
        else:
            content = self._build_csv(structure)

        file_path = self._write_file(
            content, output_dir, config.product_name, export_format
        )

        return CampaignExport(
            format=export_format,
            file_path=file_path,
            structure=structure,
            product_name=config.product_name
        )

    def _generate_keywords(self, product_name: str) -> KeywordGroup:
        """
        - product_name convertido para lowercase + variacoes
        - match_type: "phrase" (Video B 00:20:31)
        - negatives fixos: "free", "review", "amazon", "walmart",
          "ebay", "coupon", "discount", "cheap", "side effects",
          "complaints", "scam"
        Keywords:
        1. product_name lowercase (ex: "prosta vive")
        2. product_name sem espacos (ex: "prostavive")
        3. product_name + "supplement" (ex: "prostavive supplement")
        4. product_name + "review" match EXACT (ex: "prosta vive review")
        """
        slug = self._slugify(product_name)
        no_space = product_name.lower().replace(" ", "")
        return KeywordGroup(
            keywords=(
                slug,                                    # phrase
                no_space,                                # phrase
                f"{no_space} supplement",                # phrase
                f"{slug} review",                        # exact
            ),
            match_type="phrase",
            negatives=(
                "free", "review", "amazon", "walmart",
                "ebay", "coupon", "discount", "cheap",
                "side effects", "complaints", "scam"
            )
        )

    def _generate_headlines(self, product_name: str) -> tuple[str, ...]:
        """
        Min 3 headlines, max 30 chars cada.
        """
        headlines = [
            f"{product_name} Official",
            f"Try {product_name} Today",
            f"Official {product_name} Site",
        ]
        buy_now = f"Buy {product_name} Now"
        if len(buy_now) <= 30:
            headlines.append(buy_now)
        results = f"{product_name} Results"
        if len(results) <= 30:
            headlines.append(results)
        return tuple(headlines)

    def _generate_descriptions(
        self,
        product_name: str,
        product_type: str,
        benefits: str
    ) -> tuple[str, ...]:
        """
        Min 2 descriptions, max 90 chars cada.
        """
        desc1 = (
            f"Support your health with {product_name}. "
            f"Clinically studied formula trusted by thousands. "
            f"Try it today risk-free!"
        )[:90]

        desc2 = (
            f"Join satisfied customers who found relief with {product_name}. "
            f"Order now with fast shipping and excellent support."
        )[:90]

        return (desc1, desc2)

    def _build_json(self, structure: CampaignStructure) -> str:
        """Converte CampaignStructure para JSON formatado."""
        ...

    def _build_csv(self, structure: CampaignStructure) -> str:
        """
        Gera CSV no formato Google Ads Editor.
        Linhas separadas para campanha, ad group, keywords, negatives.
        """
        ...

    def _write_file(
        self, content: str, output_dir: str,
        product_name: str, export_format: str
    ) -> str:
        """
        Escreve arquivo em output_dir/{product_name}_campaign.{json|csv}
        Cria diretorio se nao existir.
        """
        ...

    def _slugify(self, text: str) -> str:
        return text.lower().replace(" ", "-")

    def execute(self, ...) -> AdapterExecutionResult:
        """
        Executa build_campaign com config padrao.
        MOCK: gera arquivo, retorna sucesso.
        REAL: bloqueado — nao faz chamada Google Ads API.
        """
        ...

    def validate_config(self, config: CampaignConfig) -> list[str]:
        errors = []
        if config.commission_usd <= 0:
            errors.append("commission_usd must be > 0")
        if not config.target_url.startswith("https://"):
            errors.append("target_url must be HTTPS")
        if config.keyword_match_type not in ("phrase", "exact", "broad"):
            errors.append("keyword_match_type must be phrase, exact, or broad")
        if config.bidding_strategy != "target_cpa":
            errors.append("bidding_strategy must be target_cpa (Video B 00:17:00)")
        return errors
```

## 8. MOCK Data — Full Campaign Examples

### ProstaVive (Nutraceutical)
```
Commission:   $175.60
Target CPA:   $87.80   (50% de 175.60)
Daily Budget: $20.00
Keywords:     "prosta vive", prostavive, "prostavive supplement"
Match Type:   Phrase (Video B 00:20:31)
Negatives:    free, review, amazon, walmart, ebay, coupon, discount, cheap, side effects, complaints, scam
Locations:    US, CA, AU, GB
Languages:    all
Bidding:      target_cpa $87.80
```

### Matsato (Ecommerce)
```
Commission:   $70.00
Target CPA:   $35.00   (50% de 70.00)
Daily Budget: $15.00
Keywords:     "matsato", "matsato store", "matsato online"
Match Type:   Phrase
Negatives:    free, review, amazon, walmart, ebay, coupon, discount, cheap
Locations:    US, CA, AU, GB
Languages:    all
Bidding:      target_cpa $35.00
```

### Ignatra (Nutraceutical)
```
Commission:   $180.00
Target CPA:   $90.00   (50% de 180.00)
Daily Budget: $25.00
Keywords:     "ignatra", "ignatra supplement", "try ignatra"
Match Type:   Phrase
Negatives:    free, review, amazon, walmart, ebay, coupon, discount, cheap, side effects, complaints, scam
Locations:    US, CA, AU, GB
Languages:    all
Bidding:      target_cpa $90.00
```

## 9. Negative Keywords List

A partir de Video B 00:21:45 (palavra ampla torra dinheiro) e boas práticas:

| Negative | Motivo |
|---|---|
| `free` | Atrai quem quer gratis, nao comprar |
| `review` | Atrai leitores, nao compradores |
| `amazon` | Desvia para concorrente |
| `walmart` | Desvia para concorrente |
| `ebay` | Desvia para concorrente |
| `coupon` | Atrai quem so compra com desconto |
| `discount` | Margem apertada, nao sustenta CPA |
| `cheap` | Publico de baixo valor |
| `side effects` | Medo/negatividade |
| `complaints` | Reclamacoes |
| `scam` | Golpe — evita trafego toxico |

## 10. Quality Rules

```python
class GoogleAdsQualityCheck:
    """
    Regras de qualidade validades ANTES de exportar.
    """

    @staticmethod
    def check_target_cpa(commission_usd: float, target_cpa: float) -> QualityResult:
        """
        Video B 00:17:00 — CPA deve ser EXATAMENTE 50% da comissao.
        """
        expected = commission_usd * 0.50
        if abs(target_cpa - expected) > 0.01:
            return QualityResult(
                passed=False,
                issue=f"target_cpa ${target_cpa} != 50% of commission (${expected})"
            )
        return QualityResult(passed=True)

    @staticmethod
    def check_ad_copy(headlines: tuple, descriptions: tuple) -> QualityResult:
        if len(headlines) < 3:
            return QualityResult(passed=False, issue="Need at least 3 headlines")
        if len(descriptions) < 2:
            return QualityResult(passed=False, issue="Need at least 2 descriptions")
        for h in headlines:
            if len(h) > 30:
                return QualityResult(passed=False, issue=f"Headline too long: '{h}'")
        for d in descriptions:
            if len(d) > 90:
                return QualityResult(passed=False, issue=f"Description too long: '{d}'")
        return QualityResult(passed=True)

    @staticmethod
    def check_network_settings(settings: dict) -> QualityResult:
        """
        Video B 00:18:00 — display DEVE estar desligado.
        """
        if settings.get("target_content_network", False):
            return QualityResult(passed=False, issue="Display network must be OFF")
        if settings.get("target_partner_search_network", False):
            return QualityResult(passed=False, issue="Search partners must be OFF")
        return QualityResult(passed=True)

    @staticmethod
    def check_locations(locations: tuple) -> QualityResult:
        """
        Video B 00:18:10 — US, CA, AU, GB com presenca.
        """
        required = {"US", "CA", "AU", "GB"}
        if not required.issubset(set(locations)):
            missing = required - set(locations)
            return QualityResult(
                passed=False,
                issue=f"Missing required locations: {missing}"
            )
        return QualityResult(passed=True)

    @staticmethod
    def check_keyword_match(keywords: KeywordGroup) -> QualityResult:
        """
        Video B 00:20:31 — FRASE, nao ampla, nao exata.
        """
        if keywords.match_type == "broad":
            return QualityResult(
                passed=False,
                issue="Broad match wastes budget (Video B 00:21:45)"
            )
        if keywords.match_type == "exact":
            return QualityResult(
                passed=False,
                issue="Exact match too restrictive and expensive (Video B 00:21:25)"
            )
        return QualityResult(passed=True)

    @staticmethod
    def check_bidding_strategy(strategy: str) -> QualityResult:
        """
        Video B 00:17:34 — SEMPRE definir CPA. Nunca 'maximize conversions'.
        """
        if strategy != "target_cpa":
            return QualityResult(
                passed=False,
                issue=f"Must be target_cpa, not '{strategy}' (Video B 00:17:34)"
            )
        return QualityResult(passed=True)
```

## 11. Integration with Landing Page

```
                     Google Ads
                        |
                   [Google Ad]
                   final_url ▼
                ┌──────────────────────┐
                │   Landing Page       │
                │  (products/{slug})   │
                │                      │
                │  - Product info      │
                │  - Buy button ───────┤───► Affiliate Link
                │  - Cookie set        │     (commission tracking)
                └──────────────────────┘
                        |
                   [Affiliate Checkout]
                   (Hotmart / Digistore24 / etc.)
```

- `final_url` no Google Ads aponta para a Landing Page
- Landing Page contém o `affiliate_link` no botão de compra (ex: Hotmart link)
- A landing page seta cookie de afiliado (se aplicável)
- Quando o usuário clica em "Comprar", vai para o checkout do afiliado
- A comissão é tracking via o link de afiliado

**No MOCK mode:** o adapter apenas referencia `config.target_url` e `config.affiliate_link` nos metadados. Nenhum click é gerado, nenhum cookie é setado.

## 12. Demo Outline

```python
def test_google_ads_campaign_adapter():
    """
    Teste principal do GoogleAdsCampaignAdapter.
    100% MOCK — sem API, sem gasto.
    """

    # Setup
    adapter = GoogleAdsCampaignAdapter()

    # 1. Criar config para ProstaVive (commission $175.60)
    config = CampaignConfig(
        product_name="ProstaVive",
        target_url="https://shinsite.vercel.app/prostavive",
        affiliate_link="https://hotmart.com/product/prostavive/ref=SHIN",
        commission_usd=175.60,
        daily_budget_usd=20.00,
    )

    # 2. Validar config
    errors = adapter.validate_config(config)
    assert len(errors) == 0                    # config valida

    # 3. Build campaign
    export = adapter.build_campaign(config, output_dir="output/campaigns", export_format="json")
    assert export.format == "json"
    assert export.product_name == "ProstaVive"

    # 4. Verificar CPA = 50% da comissao (Video B 00:17:24)
    structure = export.structure
    target_cpa = structure.bidding["target_cpa"]
    assert target_cpa == 87.80                 # 175.60 * 0.50

    # 5. Verificar campaign_type = search (Video B 00:19:30)
    assert structure.network_settings["target_google_search"] is True

    # 6. Verificar display desligado (Video B 00:18:00)
    assert structure.network_settings["target_content_network"] is False
    assert structure.network_settings["target_partner_search_network"] is False

    # 7. Verificar localizacoes (Video B 00:18:10)
    assert "US" in structure.locations
    assert "CA" in structure.locations
    assert "AU" in structure.locations
    assert "GB" in structure.locations

    # 8. Verificar keyword match = phrase (Video B 00:20:31)
    ad_group = structure.ad_groups[0]
    assert ad_group.keywords.match_type == "phrase"

    # 9. Verificar negative keywords
    assert "free" in ad_group.keywords.negatives
    assert "review" in ad_group.keywords.negatives
    assert "amazon" in ad_group.keywords.negatives
    assert "scam" in ad_group.keywords.negatives

    # 10. Verificar ad copy
    assert len(ad_group.headlines) >= 3
    assert len(ad_group.descriptions) >= 2
    for h in ad_group.headlines:
        assert len(h) <= 30
    for d in ad_group.descriptions:
        assert len(d) <= 90

    # 11. Verificar display path
    assert ad_group.display_path == "/ProstaVive"

    # 12. Verificar bidding strategy (Video B 00:17:00)
    assert structure.bidding["strategy"] == "target_cpa"
    quality = GoogleAdsQualityCheck.check_bidding_strategy(structure.bidding["strategy"])
    assert quality.passed is True

    # 13. Verificar que arquivo foi gerado
    import os
    assert os.path.exists(export.file_path)

    # 14. Verificar JSON valido
    import json
    with open(export.file_path, "r") as f:
        data = json.load(f)
    assert "campaign" in data
    assert data["campaign"]["type"] == "search"

    # 15. Verificar quality rules passam
    assert GoogleAdsQualityCheck.check_network_settings(structure.network_settings).passed
    assert GoogleAdsQualityCheck.check_ad_copy(ad_group.headlines, ad_group.descriptions).passed
    assert GoogleAdsQualityCheck.check_locations(structure.locations).passed
    assert GoogleAdsQualityCheck.check_keyword_match(ad_group.keywords).passed

    # 16. Verificar que NAO houve chamada de API (MOCK mode)
    assert adapter.execution_count == 0         # sem execucao real

    print("All 16+ assertions passed. Campaign file ready for Google Ads import.")
```

### Cenario 2 — Matsato com CSV

```python
def test_matsato_csv_export():
    adapter = GoogleAdsCampaignAdapter()
    config = CampaignConfig(
        product_name="Matsato",
        target_url="https://shinsite.vercel.app/matsato",
        affiliate_link="https://hotmart.com/product/matsato/ref=SHIN",
        commission_usd=70.00,
        daily_budget_usd=15.00,
    )

    export = adapter.build_campaign(config, export_format="csv")
    assert export.format == "csv"
    assert export.structure.bidding["target_cpa"] == 35.00
    assert os.path.exists(export.file_path)

    with open(export.file_path, "r") as f:
        content = f.read()
    assert "Campaign" in content
    assert "Matsato - Search" in content
    assert "target_cpa" in content
```

### Cenario 3 — Falha de Validacao

```python
def test_validation_failure():
    adapter = GoogleAdsCampaignAdapter()
    config = CampaignConfig(
        product_name="Ignatra",
        target_url="http://http-site.com",       # HTTP, nao HTTPS
        affiliate_link="",
        commission_usd=0,
    )
    errors = adapter.validate_config(config)
    assert len(errors) > 0
    assert any("commission" in e for e in errors)
    assert any("HTTPS" in e for e in errors)
```

## 13. Observability Snapshot

```python
@dataclass(frozen=True, slots=True)
class GoogleAdsCampaignSnapshot:
    product_name: str
    target_cpa: float
    daily_budget: float
    keyword_count: int
    negative_keyword_count: int
    headline_count: int
    description_count: int
    locations: tuple[str, ...]
    export_format: str
    quality_passed: bool
```

## 14. Eventos

| Event | Disparado em |
|---|---|
| `GoogleAdsCampaignBuilt` | Fim de `build_campaign()` |
| `GoogleAdsCampaignExported` | Arquivo escrito em disco |
| `GoogleAdsQualityFailed` | Quality check reprova |

## 15. Nao-Funcionais (desta fase)

- **Nenhuma chamada Google Ads API** — MOCK gera arquivo local
- **Nenhum gasto** — campanha sempre `paused`
- **Nenhum provider, secret provider ou HTTP client** necessario
- **Deterministico** — mesmos inputs geram mesmos outputs
- **Arquivos em `output/campaigns/`** — ignorados pelo .gitignore

## 16. Proximas Fases (Fora do Escopo)

| Phase | O que faz | Quando |
|---|---|---|
| FASE 4 | Google Ads REAL (API) com budget guard | Apos FASE 3 aprovado |
| FASE 5 | Dashboard de campanhas (status, clicks, spend) | Apos FASE 4 |
| FASE 6 | Auto-otimizacao (pausar keyword cara, ajustar CPA) | Apos FASE 5 |
| FASE 7 | Multi-canal (Meta Ads + TikTok Ads + Google Ads) | Apos FASE 6 |

---

### O Que o Codex Precisa Fazer

1. Criar `core/departments/ads/__init__.py` — exports
2. Criar `core/departments/ads/models.py` — CampaignConfig, KeywordGroup, AdGroup, CampaignStructure, CampaignExport (frozen+slots)
3. Criar `core/departments/ads/pipeline.py` — GoogleAdsCampaignPipeline (se houver pipeline multi-etapa) ou omitir se adapter for auto-suficiente
4. Criar `core/tools/adapters/google_ads_campaign_adapter.py` — GoogleAdsCampaignAdapter com `build_campaign()`, `_generate_keywords()`, `_generate_headlines()`, `_generate_descriptions()`, `_build_json()`, `_build_csv()`, `_write_file()`, `validate_config()`
5. Adicionar `Capability.ADS_CAMPAIGN_MANAGEMENT` em `core/company/capability_registry.py`
6. Criar `core/tools/adapters/quality/google_ads_quality.py` — GoogleAdsQualityCheck com 6 regras
7. Criar `demo_google_ads_campaign_adapter.py` — 3 cenarios com 20+ assertions
8. Adicionar snapshot `GoogleAdsCampaignSnapshot` em `core/observability.py` (opcional nesta fase)
9. Adicionar eventos (opcional nesta fase — 3 eventos em `core/events/domain_events.py`)
10. Executar `python -m compileall core/` + `python scripts/run_all_demos.py` — garantir 0 falhas
