# FASE 2 — LandingPageBuilderAdapter

## 1. Objective

`LandingPageBuilderAdapter` gera HTML de pagina intermediaria que o Google Ads aceita como destino legitimo (Video B 00:15:50). A pagina tem copy persuasiva informativa (nao agressiva), simula aceite de cookies para marcar cookie de afiliado (Video B 00:13:48), e leva ao checkout do produto via link de afiliado com `rel="sponsored"`. O fundo de funil anuncia o nome do produto (ex: "ProstaVive"), nao o problema generico (Video B 00:14:09).

---

## 2. Models (frozen+slots)

```python
@dataclass(frozen=True, slots=True)
class LandingPageSection:
    """Enum-like string constants for template sections."""
    HERO: str = "hero"
    BENEFITS: str = "benefits"
    CTA: str = "cta"
    DISCLOSURE: str = "disclosure"
    COOKIE_POPUP: str = "cookie_popup"
    FOOTER: str = "footer"


@dataclass(frozen=True, slots=True)
class LandingPageConfig:
    product_name: str
    headline: str                     # produto + beneficio principal
    subheadline: str                  # 1-2 linhas de apoio
    benefits: list[str]               # 5-8 bullet points
    affiliate_link: str               # URL completa com ID de afiliado
    primary_color: str                # hex ex: "#2D6A4F"
    target_countries: list[str]       # ex: ["US", "BR"]
    product_type: str                 # "nutraceutical", "ecommerce", "digital"
    logo_path: str | None = None      # path para PNG se ImageDepartment gerou
    language: str = "en"


@dataclass(frozen=True, slots=True)
class LandingPageResult:
    html_path: str                    # caminho absoluto do arquivo gerado
    product_name: str
    styles_inline: bool               # sempre True
    file_size_bytes: int
    sections_present: list[str]       # LandingPageSection values
```

---

## 3. HTML Template Structure (pseudo-HTML)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="...">
  <meta name="robots" content="noindex, nofollow">
  <title>{{ product_name }} — Official Information</title>
  <style>
    /* CSS inline: responsive, mobile-first, dark theme optional */
    /* cookie popup z-index > body content */
  </style>
</head>
<body>

  <!-- COOKIE CONSENT POPUP (fixed, overlay) -->
  <div id="cookie-popup">
    <p>This site uses cookies to improve your experience. By clicking "Accept", you agree to our use of cookies.</p>
    <button id="cookie-accept">Accept</button>
  </div>

  <!-- HERO -->
  <section id="hero">
    <h1>{{ product_name }}</h1>
    <p class="headline">{{ headline }}</p>
    <p class="subheadline">{{ subheadline }}</p>
  </section>

  <!-- BENEFITS -->
  <section id="benefits">
    <ul>
      {% for benefit in benefits %}
      <li>{{ benefit }}</li>
      {% endfor %}
    </ul>
  </section>

  <!-- CTA -->
  <section id="cta">
    <a href="{{ affiliate_link }}" rel="sponsored" class="cta-button">
      Visit Official Website →
    </a>
  </section>

  <!-- DISCLOSURE -->
  <section id="disclosure">
    <p>We may earn a commission if you purchase through links on this page.</p>
  </section>

  <!-- FOOTER -->
  <footer>
    <p>&copy; 2026 {{ product_name }}. All rights reserved.</p>
  </footer>

  <script>
    // Cookie setter + popup dismiss
    document.getElementById('cookie-accept').addEventListener('click', function() {
      document.cookie = "affiliate_consent=1; path=/; max-age=" + 60*60*24*30;
      document.getElementById('cookie-popup').style.display = 'none';
    });
  </script>
</body>
</html>
```

---

## 4. Copywriting Rules

| Element | Regra | Fonte |
|---|---|---|
| Headline | `product_name` + main benefit. Ex: "ProstaVive — Support Your Prostate Health Naturally" | Video B 00:14:09 (fundo de funil = nome do produto) |
| Subheadline | 1-2 linhas reforçando o benefício sem exageros | Video C 00:09:56 (copy persuasiva mas factual) |
| Benefits | 5-8 bullets baseados em dores comuns do tipo de produto | Video C 00:10:44 |
| CTA | "Visit Official Website" + seta. NUNCA "Buy Now" ou "Get Rich" | Video B 00:14:41 (Google aceita porque tem conteudo real) |
| Meta description | product_name + 2 beneficios, max 155 chars | Video B 00:15:50 |
| Tone | Informativo, confiavel. Sem linguagem agressiva ou hype | Google penaliza tom agressivo |
| Cookie popup | "Accept" marca cookie de afiliado (Video B 00:15:29) | Video B 00:13:48 |
| Disclosure | Obrigatoria, no final. "We may earn a commission..." | FTC + boas praticas |

---

## 5. Adapter Pseudo-code

```python
class LandingPageBuilderAdapter(AbstractToolAdapter):
    """
    Gera landing pages HTML intermediarias para Google Ads.
    MOCK: escreve HTML local em output/landing_pages/<slug>/index.html
    REAL: (futuro) publica via SCP/SSH em VPS — NAO IMPLEMENTADO
    """

    def build_landing_page(self, config: LandingPageConfig) -> LandingPageResult:
        html = self._render_html(config)
        path = self._write_to_file(html, config.product_name)
        return LandingPageResult(
            html_path=path,
            product_name=config.product_name,
            styles_inline=True,
            file_size_bytes=len(html.encode("utf-8")),
            sections_present=[s.value for s in LandingPageSection.__members__.values()]
        )

    def _render_html(self, config: LandingPageConfig) -> str:
        headline = self._generate_headline(config.product_name, config.product_type)
        benefits = self._generate_benefits(config.product_type, config.product_name)
        meta_desc = self._generate_meta_description(config.product_name, benefits)
        return self._apply_template(
            product_name=config.product_name,
            headline=headline,
            subheadline=config.subheadline,
            benefits=benefits,
            affiliate_link=config.affiliate_link,
            meta_description=meta_desc,
            primary_color=config.primary_color,
            logo_path=config.logo_path,
            language=config.language,
        )

    def _generate_headline(self, product_name: str, product_type: str) -> str:
        # retorna: "{product_name} — {beneficio principal para o tipo}"
        ...

    def _generate_benefits(self, product_type: str, product_name: str) -> list[str]:
        # lookup MOCK benefits por product_type
        ...

    def _generate_meta_description(self, product_name: str, benefits: list[str]) -> str:
        # concatena product_name + 2 benefits, corta em 155 chars
        ...

    def _apply_template(self, **kwargs) -> str:
        # string.Template ou f-string com HTML completo + CSS inline
        ...

    def _write_to_file(self, html: str, product_name: str) -> str:
        slug = product_name.lower().replace(" ", "_").replace("-", "_")
        output_dir = Path("output/landing_pages") / slug
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "index.html"
        path.write_text(html, encoding="utf-8")
        return str(path.resolve())

    # ToolRuntime compatibility
    def execute(self, config: LandingPageConfig, mode: ExecutionMode = ExecutionMode.MOCK) -> LandingPageResult:
        if mode == ExecutionMode.MOCK:
            return self.build_landing_page(config)
        # REAL: raise NotImplementedError("VPS publish not implemented yet")
```

---

## 6. MOCK Data — Benefits por Product Type

### Nutraceutical (ProstaVive, Ignatra, Prodentin)
```python
NUTRACEUTICAL_BENEFITS = {
    "ProstaVive": [
        "Supports healthy prostate function and urinary comfort",
        "Formulated with natural, clinically studied ingredients",
        "Manufactured in FDA-registered, GMP-certified facility",
        "Helps maintain normal urinary flow and bladder health",
        "Supports restful sleep by reducing nighttime bathroom trips",
        "180-day money-back guarantee — try risk-free",
        "Free from GMOs, gluten, and artificial additives",
    ],
    "Ignatra": [
        "Promotes natural hair regrowth and reduces thinning",
        "Targets DHT production at the follicular level",
        "Plant-based formula with Saw Palmetto and Biotin",
        "Visible results in as little as 90 days",
        "No harsh chemicals or prescription side effects",
        "Recommended by dermatologists and trichologists",
        "60-day satisfaction guarantee",
    ],
    "Prodentin": [
        "Supports strong, healthy teeth and gums naturally",
        "Reduces gum inflammation and sensitivity",
        "Fortifies enamel with natural minerals",
        "Fights harmful oral bacteria without alcohol",
        "Fresh breath that lasts — no artificial mint",
        "Dentist-formulated, made in the USA",
        "Risk-free with 90-day money-back guarantee",
    ],
}
```

### Ecommerce / Physical Product (Matsato — faca)
```python
ECOMMERCE_BENEFITS = {
    "Matsato": [
        "Premium Japanese stainless steel — razor-sharp edge retention",
        "Ergonomic handle designed for all-day comfort",
        "Full tang construction for maximum durability",
        "Versatile 8-inch blade — chef's favorite length",
        "Lifetime warranty backed by the manufacturer",
        "Includes protective sheath for safe storage",
        "Hand-sharpened by master craftsmen in Seki, Japan",
    ],
}
```

### Digital / Course / Software
```python
DIGITAL_BENEFITS = {
    "default": [
        "Instant access — start immediately after purchase",
        "Lifetime updates included at no extra cost",
        "Designed for beginners — no prior experience needed",
        "Step-by-step training with real-world examples",
        "24/7 customer support and active community",
        "Works on all devices — desktop, tablet, mobile",
        "30-day money-back guarantee — no questions asked",
    ],
}
```

---

## 7. Exemplo HTML Completo — ProstaVive

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="ProstaVive — natural prostate support supplement. Supports healthy urinary function, restful sleep, and prostate health with clinically studied ingredients.">
  <meta name="robots" content="noindex, nofollow">
  <title>ProstaVive — Official Information</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; line-height: 1.6; }
    .container { max-width: 720px; margin: 0 auto; padding: 2rem 1rem; }
    h1 { font-size: 2rem; color: #2D6A4F; margin-bottom: 0.5rem; }
    .headline { font-size: 1.25rem; color: #ccc; margin-bottom: 0.5rem; }
    .subheadline { font-size: 1rem; color: #999; margin-bottom: 2rem; }
    #benefits ul { list-style: none; margin-bottom: 2rem; }
    #benefits li { padding: 0.6rem 0 0.6rem 1.5rem; position: relative; border-bottom: 1px solid #222; }
    #benefits li::before { content: "✓"; color: #2D6A4F; position: absolute; left: 0; }
    .cta-button { display: inline-block; background: #2D6A4F; color: #fff; text-decoration: none; padding: 1rem 2.5rem; border-radius: 6px; font-size: 1.1rem; font-weight: 600; transition: background 0.2s; }
    .cta-button:hover { background: #1b4332; }
    #disclosure { margin-top: 2rem; font-size: 0.8rem; color: #777; }
    #disclosure p { margin-bottom: 0.5rem; }
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #222; text-align: center; font-size: 0.8rem; color: #555; }
    #cookie-popup { position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; padding: 1rem; text-align: center; z-index: 9999; border-top: 1px solid #333; }
    #cookie-popup p { display: inline; margin-right: 1rem; font-size: 0.85rem; color: #aaa; }
    #cookie-accept { background: #2D6A4F; color: #fff; border: none; padding: 0.5rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
    #cookie-accept:hover { background: #1b4332; }
    @media (max-width: 480px) {
      h1 { font-size: 1.5rem; }
      .cta-button { display: block; text-align: center; }
    }
  </style>
</head>
<body>
  <div id="cookie-popup">
    <p>This site uses cookies to improve your experience. By clicking "Accept", you agree to our use of cookies.</p>
    <button id="cookie-accept">Accept</button>
  </div>
  <div class="container">
    <section id="hero">
      <h1>ProstaVive</h1>
      <p class="headline">Support Your Prostate Health Naturally — Feel the Difference</p>
      <p class="subheadline">Clinically studied ingredients to help maintain healthy urinary function and prostate comfort as you age.</p>
    </section>
    <section id="benefits">
      <ul>
        <li>Supports healthy prostate function and urinary comfort</li>
        <li>Formulated with natural, clinically studied ingredients</li>
        <li>Manufactured in FDA-registered, GMP-certified facility</li>
        <li>Helps maintain normal urinary flow and bladder health</li>
        <li>Supports restful sleep by reducing nighttime bathroom trips</li>
        <li>180-day money-back guarantee — try risk-free</li>
        <li>Free from GMOs, gluten, and artificial additives</li>
      </ul>
    </section>
    <section id="cta">
      <a href="https://prostavive.com/affiliate?id=DEEPSEEK123" rel="sponsored" class="cta-button">Visit Official Website →</a>
    </section>
    <section id="disclosure">
      <p>We may earn a commission if you purchase through links on this page. This does not affect the price you pay.</p>
      <p>Statements on this page have not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease.</p>
    </section>
    <footer>
      <p>&copy; 2026 ProstaVive. All rights reserved.</p>
    </footer>
  </div>
  <script>
    document.getElementById('cookie-accept').addEventListener('click', function() {
      document.cookie = "affiliate_consent=1; path=/; max-age=" + 60*60*24*30;
      document.getElementById('cookie-popup').style.display = 'none';
    });
  </script>
</body>
</html>
```

### Exemplo 2 — Matsato (ecommerce/faca)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Matsato — premium Japanese chef knife. Hand-sharpened 8-inch stainless steel blade with ergonomic handle and lifetime warranty.">
  <meta name="robots" content="noindex, nofollow">
  <title>Matsato — Premium Japanese Chef Knife</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f0f0f; color: #e0e0e0; line-height: 1.6; }
    .container { max-width: 720px; margin: 0 auto; padding: 2rem 1rem; }
    h1 { font-size: 2rem; color: #c0a060; margin-bottom: 0.5rem; }
    .headline { font-size: 1.25rem; color: #ccc; margin-bottom: 0.5rem; }
    .subheadline { font-size: 1rem; color: #999; margin-bottom: 2rem; }
    #benefits ul { list-style: none; margin-bottom: 2rem; }
    #benefits li { padding: 0.6rem 0 0.6rem 1.5rem; position: relative; border-bottom: 1px solid #222; }
    #benefits li::before { content: "✓"; color: #c0a060; position: absolute; left: 0; }
    .cta-button { display: inline-block; background: #c0a060; color: #0f0f0f; text-decoration: none; padding: 1rem 2.5rem; border-radius: 6px; font-size: 1.1rem; font-weight: 600; transition: background 0.2s; }
    .cta-button:hover { background: #a08040; }
    #disclosure { margin-top: 2rem; font-size: 0.8rem; color: #777; }
    #disclosure p { margin-bottom: 0.5rem; }
    footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #222; text-align: center; font-size: 0.8rem; color: #555; }
    #cookie-popup { position: fixed; bottom: 0; left: 0; right: 0; background: #1a1a1a; padding: 1rem; text-align: center; z-index: 9999; border-top: 1px solid #333; }
    #cookie-popup p { display: inline; margin-right: 1rem; font-size: 0.85rem; color: #aaa; }
    #cookie-accept { background: #c0a060; color: #0f0f0f; border: none; padding: 0.5rem 1.5rem; border-radius: 4px; cursor: pointer; font-size: 0.85rem; }
    #cookie-accept:hover { background: #a08040; }
    @media (max-width: 480px) {
      h1 { font-size: 1.5rem; }
      .cta-button { display: block; text-align: center; }
    }
  </style>
</head>
<body>
  <div id="cookie-popup">
    <p>This site uses cookies to improve your experience. By clicking "Accept", you agree to our use of cookies.</p>
    <button id="cookie-accept">Accept</button>
  </div>
  <div class="container">
    <section id="hero">
      <h1>Matsato</h1>
      <p class="headline">Experience the Precision of a Hand-Forged Japanese Chef Knife</p>
      <p class="subheadline">8-inch stainless steel blade, master-crafted in Seki City, Japan — for chefs who demand perfection.</p>
    </section>
    <section id="benefits">
      <ul>
        <li>Premium Japanese stainless steel — razor-sharp edge retention</li>
        <li>Ergonomic handle designed for all-day comfort</li>
        <li>Full tang construction for maximum durability</li>
        <li>Versatile 8-inch blade — chef's favorite length</li>
        <li>Lifetime warranty backed by the manufacturer</li>
        <li>Includes protective sheath for safe storage</li>
        <li>Hand-sharpened by master craftsmen in Seki, Japan</li>
      </ul>
    </section>
    <section id="cta">
      <a href="https://matsato.com/discount/DEEPSEEK?af_id=123" rel="sponsored" class="cta-button">Visit Official Website →</a>
    </section>
    <section id="disclosure">
      <p>We may earn a commission if you purchase through links on this page. This does not affect the price you pay.</p>
    </section>
    <footer>
      <p>&copy; 2026 Matsato. All rights reserved.</p>
    </footer>
  </div>
  <script>
    document.getElementById('cookie-accept').addEventListener('click', function() {
      document.cookie = "affiliate_consent=1; path=/; max-age=" + 60*60*24*30;
      document.getElementById('cookie-popup').style.display = 'none';
    });
  </script>
</body>
</html>
```

---

## 8. Integration with ScriptDepartment + ImageDepartment

```
┌──────────────────────────────────────────────────┐
│              LandingPageBuilderAdapter            │
│                                                    │
│  1. Tenta obter copy do ScriptWriterEmployee:      │
│     - Se disponivel: usa headline/benefits/CTA     │
│       gerados pelo departamento de roteiro         │
│     - Senao: fallback interno MOCK benefits        │
│                                                    │
│  2. Tenta embedar PNG do ImageDesignerEmployee:    │
│     - Se logo_path for passado no config:          │
│       <img src="file:///path/to/hero.png">         │
│       ou base64 inline <img src="data:...">        │
│     - Senao: hero sem imagem, apenas texto         │
│                                                    │
│  3. Resultado final: HTML autossuficiente          │
│     sem dependencias externas de CSS/JS            │
└──────────────────────────────────────────────────┘
```

**Precedencia de copy:**
1. Se `ScriptWriterEmployee` estiver disponivel e o pipeline nao estiver ocupado: solicita `create_hook()` para gerar headline + benefits
2. Se `ImageDesignerEmployee` gerou asset PNG: converte para base64 e embeda como `<img>` no hero

Ambos sao opcionais. O adaptador SEMPRE gera HTML funcional mesmo sem nenhum departamento disponivel.

---

## 9. Demo Outline

Arquivo: `demo_landing_page_builder.py`

```python
def test_landing_page_builder():
    adapter = LandingPageBuilderAdapter()

    # Config para ProstaVive
    config = LandingPageConfig(
        product_name="ProstaVive",
        headline="Support Your Prostate Health Naturally",
        subheadline="Clinically studied ingredients for urinary comfort.",
        benefits=NUTRACEUTICAL_BENEFITS["ProstaVive"],
        affiliate_link="https://prostavive.com/affiliate?id=DEEPSEEK123",
        primary_color="#2D6A4F",
        target_countries=["US"],
        product_type="nutraceutical",
    )

    result = adapter.execute(config, mode=ExecutionMode.MOCK)

    # Asserts
    assert result.html_path is not None
    assert result.html_path.endswith("index.html")
    assert result.styles_inline is True
    assert result.file_size_bytes > 1000

    # O arquivo existe
    import os
    assert os.path.exists(result.html_path)

    # Le e verifica conteudo
    html = open(result.html_path, "r", encoding="utf-8").read()

    assert "ProstaVive" in html
    assert "Visit Official Website" in html
    assert "commission" in html.lower()
    assert "cookie" in html.lower()
    assert "disclosure" in html.lower()
    assert 'rel="sponsored"' in html
    assert 'name="viewport"' in html
    assert "affiliate_consent" in html
    assert "noindex" in html

    # Nenhum CSS externo
    assert '<link rel="stylesheet"' not in html
    assert "@import" not in html

    print(f"✅ Landing page gerada: {result.html_path} ({result.file_size_bytes} bytes)")
    print(f"✅ Secoes presentes: {result.sections_present}")
```

### Expected assertions: ~15

---

## 10. Riscos e Auto-critica

| Risco | Mitigacao |
|---|---|
| Google Ads rejeitar pagina por "thin content" | Template tem 5+ secoes, 7 beneficios, disclosure, footer — nao e pagina vazia |
| Cookie popup nao ser suficiente para GDPR | Usamos consentimento afirmativo (Accept), mas advogado deve revisar para UE |
| HTML gerado ser muito grande para Google Ads (limite 2048 chars?) | Nao ha limite de tamanho para destino final; o limite de 2048 e para display URL |
| ScriptDepartment nao existir ainda | Fallback interno com MOCK benefits funciona sem dependencias |
| Afiliado nao ser marcado se usuario nao clicar em Accept | Cookie so e marcado no clique; sem clique, sem comissao — comportamento esperado e compativel com leis de consentimento |
| Produto com nome que gera slug duplicado | Usar hash ou timestamp no nome da pasta se necessario |

---

## 11. O Que o Codex Precisa Fazer

1. `core/tools/adapters/landing_page_adapter.py` — classe `LandingPageBuilderAdapter` com template HTML, geracao de beneficios MOCK, escrita de arquivo, execucao MOCK
2. `demo_landing_page_builder.py` — demo com ~15 assertions, gera pagina ProstaVive em `output/landing_pages/prostavive/index.html`
3. Importar no `core/tools/adapters/__init__.py` se aplicavel
4. Rodar compileall + `python scripts/run_all_demos.py` para regressao completa
5. OBS: Nao mexer em `core/departments/`, `core/company/`, `core/events/`, `core/observability.py` — este adapter e uma ferramenta, nao um departamento
