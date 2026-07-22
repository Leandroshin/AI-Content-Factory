"""Product URL Intake demo with safe extraction and affiliate handoff."""

from __future__ import annotations

from uuid import uuid4

from core.approval import ApprovalRuntime
from core.company.specialist_employee import EmployeeSkill
from core.content_factory import (
    AffiliateCommerceWorkflow,
    AffiliateFactoryEmployees,
    ProductUrlIntake,
    ProductUrlIntakeStatus,
)
from core.departments.affiliate_deals import AffiliateDealsEmployee
from core.departments.creative_review import CreativeReviewEmployee
from core.departments.product_research import ProductResearchEmployee
from core.departments.strategy_intelligence import (
    StrategyIntelligenceEmployee,
    StrategySource,
)
from core.events.bus import EventBus
from core.runtime import CompanyRuntime
from core.tools import TelegramAdapter
from core.tools.http import HttpResponse, MockHttpClient

_ASSERTION_COUNTER = 0
_PRODUCT_URL = "https://produto.mercadolivre.com.br/MLB-123456-controle-gamer"


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def _product_html() -> str:
    return """
    <!doctype html><html><head>
      <link rel="canonical" href="https://produto.mercadolivre.com.br/MLB-123456-controle-gamer">
      <meta property="og:title" content="Controle Gamer Pro">
      <meta property="og:image" content="https://http2.mlstatic.com/controle.jpg">
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Controle Gamer Pro",
        "sku": "MLB-123456",
        "image": ["https://http2.mlstatic.com/controle.jpg"],
        "brand": {"@type": "Brand", "name": "GameTech"},
        "offers": {
          "@type": "Offer",
          "price": "199.90",
          "priceCurrency": "BRL",
          "availability": "https://schema.org/InStock",
          "seller": {"@type": "Organization", "name": "Loja Oficial GameTech"}
        }
      }
      </script>
    </head><body><h1>Controle Gamer Pro</h1></body></html>
    """


def _mercado_livre_short_link_html() -> str:
    return """
    <!doctype html><html><head>
      <meta property="og:title" content="Violão Clássico Giannini N-14">
      <meta property="og:image" content="https://http2.mlstatic.com/viola.jpg">
    </head><body>
      <script>
        {"price":{"previous_price":{"value":408,"currency":"BRL"},"current_price":{"value":387.6,"currency":"BRL"}},"item_id":"MLB3535284749"}
      </script>
    </body></html>
    """


def _mercado_livre_affiliate_card_html() -> str:
    return """
    <!doctype html><html><head>
      <meta property="og:title" content="Jogo de Panelas Ceramica 10 Pecas">
      <meta property="og:image" content="https://http2.mlstatic.com/panelas.webp">
    </head><body>
      <section class="rl-card-featured">
        <a href="https://www.mercadolivre.com.br/panelas/up/MLBU123?pdp_filters=item_id%3AMLB5768690226&amp;wid=MLB5768690226"
           class="poly-component__title">Jogo de Panelas Ceramica 10 Pecas</a>
        <span class="poly-component__seller">Por Loja Oficial Mimo</span>
        <s aria-label="Antes: 645 reais"></s>
        <span class="poly-price__current" aria-label="Agora: 499 reais com 99 centavos"></span>
      </section>
    </body></html>
    """


def _employees(
    company: CompanyRuntime, event_bus: EventBus
) -> AffiliateFactoryEmployees:
    return AffiliateFactoryEmployees(
        strategy_intelligence=StrategyIntelligenceEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="source_triage", proficiency=0.88),),
            event_bus=event_bus,
        ),
        product_research=ProductResearchEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="risk_triage", proficiency=0.84),),
            event_bus=event_bus,
        ),
        creative_review=CreativeReviewEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="image_readiness", proficiency=0.9),),
            event_bus=event_bus,
        ),
        affiliate_deals=AffiliateDealsEmployee(
            company_runtime=company,
            employee_id=uuid4(),
            skills=(EmployeeSkill(name="affiliate_compliance", proficiency=0.9),),
            event_bus=event_bus,
        ),
    )


def _overrides() -> dict[str, object]:
    return {
        "category": "gamer",
        "niche": "games",
        "old_price": 299.90,
        "commission_percent": 8.0,
        "metadata": {
            "visual_quality": 10,
            "product_visibility": 10,
            "resolution_score": 10,
            "text_clutter": 0,
            "watermark_risk": 0,
            "brand_safety": 10,
            "coupon_code": "GAME10",
            "coupon_description": "10% de desconto",
            "urgency_level": "medium",
            "stock_status": "available",
            "audience": "jogadores brasileiros",
        },
    }


def main() -> None:
    print("=" * 70)
    print("Product URL Intake - Controlled Evidence to Affiliate Workflow")
    print("=" * 70)

    http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            headers={"content-type": "text/html; charset=utf-8"},
            body=_product_html(),
        )
    )
    intake = ProductUrlIntake(http, clock=lambda: 1_786_000_000.0)

    print("\nStep 1: extract structured marketplace evidence")
    result = intake.intake(
        _PRODUCT_URL,
        affiliate_url="https://mercadolivre.com/sec/affiliate-demo",
        overrides=_overrides(),
    )
    _check(result.status == ProductUrlIntakeStatus.READY, "Structured product is ready")
    _check(result.usable, "Ready result is usable")
    _check(result.candidate is not None, "ProductCandidate is created")
    assert result.candidate is not None
    _check(
        result.candidate.product_name == "Controle Gamer Pro", "Name comes from JSON-LD"
    )
    _check(result.candidate.current_price == 199.9, "Price is normalized")
    _check(
        result.candidate.old_price == 299.9, "Manual old-price evidence is preserved"
    )
    _check(result.candidate.marketplace == "mercado_livre", "Marketplace is identified")
    _check(
        result.candidate.metadata["seller"] == "Loja Oficial GameTech",
        "Seller is preserved",
    )
    _check(
        result.candidate.metadata["availability"] == "InStock",
        "Availability is normalized",
    )
    _check(result.evidence.extractor == "json_ld_product", "Extractor is auditable")
    _check(len(result.evidence.content_sha256) == 64, "Evidence hash is recorded")
    _check(
        result.evidence.fetched_at == 1_786_000_000.0,
        "Evidence timestamp is controlled",
    )
    _check(len(http.sent_requests) == 1, "Exactly one request is made")
    _check(
        "ProductEvidence" in http.last_request().headers["User-Agent"],
        "Purpose-specific user agent used",
    )

    print("\nStep 1b: read Mercado Livre price embedded in an affiliate short link")
    short_link_intake = ProductUrlIntake(
        MockHttpClient(default_response=HttpResponse(status_code=200, body=_mercado_livre_short_link_html()))
    )
    short_link = short_link_intake.intake("https://meli.la/15n93JQ")
    _check(short_link.status == ProductUrlIntakeStatus.READY, "Short link yields ready product evidence")
    _check(short_link.evidence.current_price == 387.6, "Embedded Mercado Livre current price is extracted")
    _check(short_link.evidence.old_price == 408.0, "Embedded Mercado Livre previous price is extracted")
    _check(short_link.evidence.sku == "MLB3535284749", "Embedded Mercado Livre item ID is preserved")
    _check(short_link.evidence.extractor == "mercado_livre_page_data", "Short link extractor remains auditable")

    print("\nStep 1c: read the highlighted card rendered by a Mercado Livre affiliate link")
    card_intake = ProductUrlIntake(
        MockHttpClient(default_response=HttpResponse(status_code=200, body=_mercado_livre_affiliate_card_html()))
    )
    card = card_intake.intake("https://meli.la/21HvzyE")
    _check(card.status == ProductUrlIntakeStatus.READY, "Highlighted affiliate card yields ready evidence")
    _check(card.evidence.current_price == 499.99, "Portuguese current price label is normalized")
    _check(card.evidence.old_price == 645.0, "Portuguese previous price label is normalized")
    _check(card.evidence.sku == "MLB5768690226", "Highlighted card item ID is preserved")
    _check(card.evidence.seller == "Loja Oficial Mimo", "Highlighted card seller is preserved")
    _check(card.evidence.extractor == "mercado_livre_page_data", "Highlighted card extractor remains auditable")

    print("\nStep 2: block unsafe and unsupported URLs before HTTP")
    before = len(http.sent_requests)
    blocked_local = intake.intake("https://127.0.0.1/admin")
    blocked_credentials = intake.intake("https://user:pass@amazon.com.br/item")
    blocked_unknown = intake.intake("https://unknown.example/item")
    blocked_http = intake.intake("http://amazon.com.br/item")
    _check(
        blocked_local.status == ProductUrlIntakeStatus.BLOCKED, "Private IP is blocked"
    )
    _check(
        blocked_credentials.status == ProductUrlIntakeStatus.BLOCKED,
        "Embedded credentials are blocked",
    )
    _check(
        blocked_unknown.status == ProductUrlIntakeStatus.BLOCKED,
        "Unknown marketplace is blocked",
    )
    _check(
        blocked_http.status == ProductUrlIntakeStatus.BLOCKED, "Plain HTTP is blocked"
    )
    _check(len(http.sent_requests) == before, "Blocked URLs never reach HTTP")

    adidas = intake.intake(
        "https://www.adidas.com.br/tenis/produto-demo.html",
        overrides=_overrides(),
    )
    _check(adidas.status != ProductUrlIntakeStatus.BLOCKED, "Adidas Brazil is allowlisted")
    _check(
        adidas.candidate is not None and adidas.candidate.marketplace == "adidas",
        "Adidas URL keeps its marketplace identity",
    )

    print("\nStep 3: reject unsafe canonical and image metadata")
    poisoned_http = MockHttpClient(
        default_response=HttpResponse(
            status_code=200,
            body="""
            <html><head>
              <link rel="canonical" href="https://127.0.0.1/private">
              <meta property="og:title" content="Produto com metadado inseguro">
              <meta property="og:image" content="http://127.0.0.1/image.jpg">
              <meta property="product:price:amount" content="99.90">
            </head></html>
            """,
        )
    )
    poisoned = ProductUrlIntake(poisoned_http).intake(
        "https://www.amazon.com.br/dp/B0SAFE1234"
    )
    _check(
        poisoned.status == ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW,
        "Unsafe metadata needs review",
    )
    _check(
        poisoned.evidence.canonical_url == "https://www.amazon.com.br/dp/B0SAFE1234",
        "Unsafe canonical is replaced",
    )
    _check(poisoned.evidence.image_url == "", "Unsafe image URL is removed")
    _check(
        "canonical_url_rejected" in poisoned.evidence.warnings,
        "Canonical rejection is audited",
    )
    _check(
        "image_url_rejected" in poisoned.evidence.warnings, "Image rejection is audited"
    )

    print("\nStep 4: preserve manual fallback when marketplace blocks access")
    denied_http = MockHttpClient(
        default_response=HttpResponse(status_code=403, body="Access denied")
    )
    denied_intake = ProductUrlIntake(denied_http, clock=lambda: 1_786_000_001.0)
    denied = denied_intake.intake(
        "https://www.amazon.com.br/dp/B0DEMO1234",
        affiliate_url="https://amzn.to/demo",
        overrides={
            **_overrides(),
            "product_name": "Controle Gamer Pro",
            "current_price": "R$ 199,90",
            "image_url": "https://m.media-amazon.com/images/I/demo.jpg",
        },
    )
    _check(
        denied.status == ProductUrlIntakeStatus.NEEDS_MANUAL_REVIEW,
        "403 enters manual review",
    )
    _check(denied.candidate is not None, "Complete manual evidence remains usable")
    _check(denied.evidence.extractor == "manual_fallback", "Fallback is explicit")
    _check("HTTP 403" in denied.error, "Fetch failure is visible")
    _check(denied.evidence.current_price == 199.9, "Brazilian manual price is parsed")

    thousands = denied_intake.intake(
        "https://www.amazon.com.br/dp/B0DEMO5678",
        overrides={
            "product_name": "Notebook de teste",
            "current_price": "R$ 1.234",
            "image_url": "https://m.media-amazon.com/images/I/notebook.jpg",
        },
    )
    _check(
        thousands.evidence.current_price == 1234.0,
        "Brazilian thousands separator is parsed",
    )

    print("\nStep 5: connect URL intake to the full affiliate workflow")
    event_bus = EventBus()
    company = CompanyRuntime(event_bus)
    company.initialize_company()
    approvals = ApprovalRuntime(event_bus=event_bus)
    telegram = TelegramAdapter()
    telegram.configure({"bot_token": "test_product_url_intake_token"})
    telegram.authenticate()
    telegram.mark_ready()
    workflow = AffiliateCommerceWorkflow(
        approvals,
        telegram,
        owner_chat_id="-1001234567890",
        telegram_chat_id="@achadosbaratosBrasil",
    )
    workflow_result = workflow.run_offer_pipeline_from_urls(
        title="Controle gamer coletado por URL",
        employees=_employees(company, event_bus),
        strategy_sources=(
            StrategySource(
                title="Validação de ofertas gamer",
                source_url="https://youtube.example/product-validation",
                transcript_text=(
                    "Compare preço histórico, comissão, imagem do produto e "
                    "aprovação humana antes de publicar oferta no Telegram."
                ),
                tags=("affiliate", "product_research"),
            ),
        ),
        product_urls=(_PRODUCT_URL,),
        product_intake=intake,
        affiliate_urls={_PRODUCT_URL: "https://mercadolivre.com/sec/affiliate-demo"},
        overrides_by_url={_PRODUCT_URL: _overrides()},
        shortlist_size=1,
        auto_approve=False,
    )
    _check(workflow_result.success, "URL enters the affiliate workflow")
    _check(
        len(workflow_result.product_intake_results) == 1,
        "Intake evidence stays attached",
    )
    _check(len(workflow_result.steps) == 4, "Four departments execute")
    _check(workflow_result.package is not None, "Publication package is prepared")
    assert workflow_result.package is not None
    _check(
        workflow_result.package.selected_product_name == "Controle Gamer Pro",
        "Package uses extracted product",
    )
    _check(
        workflow_result.package.approval_status == "pending",
        "Human approval still gates publication",
    )
    _check(workflow_result.publication_result is None, "Nothing is auto-published")

    print(f"\n{'=' * 70}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print("No real marketplace request and no publication were performed.")
    print("=" * 70)


if __name__ == "__main__":
    main()
