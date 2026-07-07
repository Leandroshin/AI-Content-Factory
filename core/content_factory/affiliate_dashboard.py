"""Interactive affiliate approval dashboard renderer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from typing import Any

from core.content_factory.affiliate_workflow import AffiliateFactoryWorkflowResult


class AffiliateApprovalDashboardRenderer:
    """Render affiliate approval queue state as a self-contained HTML panel."""

    @staticmethod
    def dashboard_state(results: tuple[AffiliateFactoryWorkflowResult, ...]) -> dict[str, Any]:
        """Build a bounded dashboard state from affiliate workflow results."""
        offers = [AffiliateApprovalDashboardRenderer._offer_state(result) for result in results if result.package]
        summary = {
            "total": len(offers),
            "pending": sum(1 for offer in offers if offer["approval_status"] == "pending"),
            "approved": sum(1 for offer in offers if offer["approval_status"] == "approved"),
            "published": sum(1 for offer in offers if offer["telegram_status"] in ("sent", "sent_mock")),
            "blocked": sum(1 for offer in offers if offer["status"] == "blocked"),
        }
        return {
            "title": "Affiliate Approval Dashboard",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "local_preview",
            "summary": summary,
            "offers": offers,
        }

    @staticmethod
    def render_html(dashboard_state: dict[str, Any]) -> str:
        """Return a self-contained HTML document for local preview."""
        offers = list(dashboard_state.get("offers", []))
        summary = dict(dashboard_state.get("summary", {}))
        payload = json.dumps(dashboard_state, ensure_ascii=False, indent=2)
        script_payload = payload.replace("</", "<\\/")
        rows = "\n".join(AffiliateApprovalDashboardRenderer._offer_row(offer) for offer in offers)
        offer_cards = "\n".join(AffiliateApprovalDashboardRenderer._offer_card(offer) for offer in offers)
        activity = "\n".join(AffiliateApprovalDashboardRenderer._activity_item(offer) for offer in offers)
        script = AffiliateApprovalDashboardRenderer._interactive_script(script_payload)
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Content Factory - Fila de Ofertas</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #080b10;
      --panel: #101720;
      --panel-2: #141d28;
      --line: #273241;
      --text: #f2f6fc;
      --muted: #98a5b7;
      --blue: #39a8ff;
      --green: #35d48a;
      --amber: #f0b949;
      --red: #ff6473;
      --violet: #9b75ff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      background: #080b10;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    .app {{
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      min-height: 100vh;
    }}
    aside.nav {{
      border-right: 1px solid var(--line);
      background: #0b1017;
      padding: 24px 18px;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 18px;
      font-weight: 800;
      margin-bottom: 30px;
    }}
    .mark {{
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, var(--blue), var(--violet));
    }}
    nav a {{
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 14px;
      border-radius: 8px;
      color: var(--muted);
      text-decoration: none;
      margin-bottom: 7px;
      font-size: 14px;
    }}
    nav a.active {{
      color: var(--text);
      background: #121a25;
      border: 1px solid var(--line);
    }}
    main {{
      min-width: 0;
      padding: 26px 30px 34px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0 0 6px;
      font-size: 31px;
      line-height: 1.12;
    }}
    .sub {{
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }}
    .actions {{
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;
    }}
    button {{
      border: 1px solid var(--line);
      background: #121925;
      color: var(--text);
      border-radius: 8px;
      padding: 10px 13px;
      font: inherit;
      cursor: pointer;
    }}
    button.primary {{
      border-color: #2273ad;
      background: linear-gradient(135deg, #1668a5, #2d9eff);
      color: white;
    }}
    button.good {{
      border-color: rgba(53, 212, 138, 0.5);
      background: rgba(53, 212, 138, 0.13);
      color: #baf7d7;
    }}
    button.warn {{
      border-color: rgba(240, 185, 73, 0.5);
      background: rgba(240, 185, 73, 0.13);
      color: #ffe2a0;
    }}
    button.danger {{
      border-color: rgba(255, 100, 115, 0.55);
      background: rgba(255, 100, 115, 0.13);
      color: #ffbdc4;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 8px;
      padding: 15px;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }}
    .metric strong {{
      font-size: 27px;
      line-height: 1;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(410px, 0.9fr);
      gap: 18px;
      align-items: start;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
    }}
    .panel-head {{
      padding: 17px 18px 0;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
    }}
    .panel h2 {{
      margin: 0;
      font-size: 18px;
      line-height: 1.2;
    }}
    .tabs {{
      display: flex;
      gap: 16px;
      border-bottom: 1px solid var(--line);
      padding: 16px 18px 0;
      overflow-x: auto;
    }}
    .tab {{
      border: 0;
      border-radius: 0;
      background: transparent;
      padding: 0 0 13px;
      color: var(--muted);
      white-space: nowrap;
    }}
    .tab.active {{
      color: #d7eaff;
      border-bottom: 2px solid var(--blue);
    }}
    .tools {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 15px 18px 0;
    }}
    input[type="search"] {{
      min-width: 230px;
      flex: 1;
      border: 1px solid var(--line);
      background: #090d13;
      color: var(--text);
      border-radius: 8px;
      padding: 11px 12px;
      font: inherit;
    }}
    input[type="text"], input[type="url"], input[type="number"], select, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      background: #090d13;
      color: var(--text);
      border-radius: 8px;
      padding: 10px 11px;
      font: inherit;
    }}
    textarea {{
      min-height: 76px;
      resize: vertical;
    }}
    label {{
      display: grid;
      gap: 6px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .modal-backdrop {{
      position: fixed;
      inset: 0;
      z-index: 30;
      display: grid;
      place-items: center;
      padding: 18px;
      background: rgba(4, 7, 11, 0.74);
    }}
    .modal-backdrop[hidden] {{
      display: none;
    }}
    .manual-form {{
      width: min(760px, 100%);
      max-height: min(820px, 92vh);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
      padding: 18px;
    }}
    .form-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .full-span {{
      grid-column: 1 / -1;
    }}
    .form-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 16px;
      flex-wrap: wrap;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
      margin-top: 15px;
    }}
    th, td {{
      border-top: 1px solid var(--line);
      padding: 13px 16px;
      text-align: left;
      vertical-align: middle;
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    th:nth-child(1), td:nth-child(1) {{ width: 42%; }}
    th:nth-child(2), td:nth-child(2) {{ width: 15%; }}
    th:nth-child(3), td:nth-child(3) {{ width: 12%; white-space: nowrap; }}
    th:nth-child(4), td:nth-child(4) {{ width: 15%; }}
    th:nth-child(5), td:nth-child(5) {{ width: 16%; }}
    th {{
      color: var(--muted);
      font-weight: 700;
    }}
    tr[data-offer-row] {{
      cursor: pointer;
    }}
    tr[data-offer-row].selected {{
      outline: 1px solid var(--blue);
      outline-offset: -1px;
      background: rgba(57, 168, 255, 0.08);
    }}
    .is-hidden {{
      display: none !important;
    }}
    .offer-title {{
      display: flex;
      gap: 11px;
      align-items: center;
      min-width: 0;
    }}
    .thumb {{
      width: 42px;
      height: 42px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #192333;
      color: #cde9ff;
      font-weight: 850;
      flex: 0 0 auto;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 750;
      white-space: nowrap;
      background: #1a2432;
      color: var(--muted);
    }}
    .pill.green {{ color: #a7f3ca; background: rgba(53, 212, 138, 0.13); }}
    .pill.amber {{ color: #ffe2a0; background: rgba(240, 185, 73, 0.13); }}
    .pill.red {{ color: #ffc4ca; background: rgba(255, 100, 115, 0.13); }}
    .pill.blue {{ color: #bde4ff; background: rgba(57, 168, 255, 0.14); }}
    .pill.violet {{ color: #ded3ff; background: rgba(155, 117, 255, 0.16); }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      padding: 18px;
    }}
    .offer-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
      padding: 14px;
      min-height: 144px;
      cursor: pointer;
    }}
    .offer-card.selected {{
      border-color: var(--blue);
      background: rgba(57, 168, 255, 0.09);
    }}
    .offer-card strong {{
      display: block;
      margin-bottom: 8px;
      line-height: 1.25;
    }}
    .score-line {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: center;
      margin-top: 12px;
    }}
    .bar {{
      height: 8px;
      border-radius: 999px;
      background: #263243;
      overflow: hidden;
    }}
    .bar span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--green), var(--blue));
    }}
    .detail {{
      display: grid;
      gap: 14px;
      padding: 18px;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .field {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #0b1119;
      min-height: 74px;
    }}
    .field span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 7px;
    }}
    .field strong {{
      font-size: 16px;
      line-height: 1.25;
    }}
    .message-preview {{
      white-space: pre-wrap;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #081017;
      padding: 14px;
      color: #d8e8f7;
      font-size: 13px;
      line-height: 1.55;
      max-height: 260px;
      overflow: auto;
    }}
    .step-list {{
      display: grid;
      gap: 8px;
    }}
    .step {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      background: #0b1119;
    }}
    .activity {{
      display: grid;
      gap: 9px;
      padding: 18px;
    }}
    .activity-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 11px 12px;
      background: #0b1119;
      font-size: 13px;
      color: var(--muted);
    }}
    @media (max-width: 1120px) {{
      .app {{ grid-template-columns: 1fr; }}
      aside.nav {{ display: none; }}
      main {{ padding: 18px; }}
      .summary, .layout, .cards {{ grid-template-columns: 1fr; }}
      .form-grid {{ grid-template-columns: 1fr; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      header {{ flex-direction: column; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside class="nav">
      <div class="brand"><span class="mark">A</span><span>AI Content Factory</span></div>
      <nav>
        <a href="#">Dashboard</a>
        <a href="#" class="active">Fila de ofertas</a>
        <a href="#">Produtos</a>
        <a href="#">Criativos</a>
        <a href="#">Aprovacoes</a>
        <a href="#">Telegram</a>
      </nav>
    </aside>
    <main>
      <header>
        <div>
          <h1>Fila de Ofertas</h1>
          <p class="sub">Curadoria, revisao criativa, aprovacao humana e envio Telegram em uma tela.</p>
        </div>
        <div class="actions">
          <button type="button" id="open-guide">Guia rapido</button>
          <button type="button" class="primary" id="new-offer">Nova oferta</button>
        </div>
      </header>

      <section class="summary">
        <div class="metric"><span>Total</span><strong id="metric-total">{int(summary.get("total", 0))}</strong></div>
        <div class="metric"><span>Pendentes</span><strong id="metric-pending">{int(summary.get("pending", 0))}</strong></div>
        <div class="metric"><span>Aprovadas</span><strong id="metric-approved">{int(summary.get("approved", 0))}</strong></div>
        <div class="metric"><span>Publicadas</span><strong id="metric-published">{int(summary.get("published", 0))}</strong></div>
      </section>

      <div class="layout">
        <section class="panel">
          <div class="tabs">
            <button class="tab active" data-filter="all" type="button">Todas</button>
            <button class="tab" data-filter="pending" type="button">Pendentes</button>
            <button class="tab" data-filter="approved" type="button">Aprovadas</button>
            <button class="tab" data-filter="published" type="button">Publicadas</button>
            <button class="tab" data-filter="blocked" type="button">Bloqueadas</button>
          </div>
          <div class="panel-head">
            <div>
              <h2>Ofertas em producao</h2>
              <p class="sub">Cada linha veio da esteira Strategy -> Research -> Creative -> Deals.</p>
            </div>
          </div>
          <div class="tools">
            <input id="offer-search" type="search" placeholder="Buscar produto, marketplace ou status" aria-label="Buscar oferta">
            <button type="button" id="sort-score">Ordenar score</button>
            <button type="button" id="reset-view">Limpar</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Produto</th>
                <th>Status</th>
                <th>Score</th>
                <th>Criativo</th>
                <th>Telegram</th>
              </tr>
            </thead>
            <tbody id="offer-rows">
              {rows}
            </tbody>
          </table>
          <div class="cards" id="offer-cards">
            {offer_cards}
          </div>
        </section>

        <aside class="panel">
          <div class="panel-head">
            <div>
              <h2>Revisao da oferta</h2>
              <p class="sub">Produto selecionado, mensagem e decisao de aprovacao.</p>
            </div>
          </div>
          <div class="detail" id="offer-detail"></div>
        </aside>
      </div>

      <section class="panel" style="margin-top:18px">
        <div class="panel-head">
          <div>
            <h2>Atividade</h2>
            <p class="sub">Eventos da fila local.</p>
          </div>
        </div>
        <div class="activity" id="activity-log">
          {activity}
        </div>
      </section>

      <div class="modal-backdrop" id="new-offer-modal" hidden>
        <section class="manual-form" role="dialog" aria-modal="true" aria-labelledby="manual-offer-title">
          <div class="panel-head" style="padding:0">
            <div>
              <h2 id="manual-offer-title">Nova oferta manual</h2>
              <p class="sub">Cole o produto agora; a pesquisa automatica entra na proxima etapa.</p>
            </div>
            <button type="button" id="close-new-offer" aria-label="Fechar">Fechar</button>
          </div>
          <form id="new-offer-form">
            <div class="form-grid">
              <label class="full-span">Nome do produto
                <input name="product_name" type="text" placeholder="PlayStation DualSense Controle sem fio" required>
              </label>
              <label>Marketplace
                <select name="marketplace">
                  <option value="Amazon">Amazon</option>
                  <option value="Mercado Livre">Mercado Livre</option>
                  <option value="Shopee">Shopee</option>
                  <option value="TikTok Shop">TikTok Shop</option>
                  <option value="Manual">Manual</option>
                </select>
              </label>
              <label>Categoria
                <input name="category" type="text" placeholder="games, casa, beleza">
              </label>
              <label class="full-span">URL do produto
                <input name="product_url" type="url" placeholder="https://www.amazon.com.br/...">
              </label>
              <label class="full-span">Link afiliado
                <input name="affiliate_url" type="url" placeholder="https://amzn.to/..." required>
              </label>
              <label>Preco atual
                <input name="current_price" type="number" min="0" step="0.01" placeholder="327.22">
              </label>
              <label>Preco antigo
                <input name="old_price" type="number" min="0" step="0.01" placeholder="499.90">
              </label>
              <label>Cupom
                <input name="coupon_code" type="text" placeholder="TUDOPRIME">
              </label>
              <label>Imagem
                <input name="image_url" type="url" placeholder="https://.../imagem.jpg">
              </label>
              <label class="full-span">Observacao
                <textarea name="notes" placeholder="Oferta Prime, estoque baixo, publico gamer..."></textarea>
              </label>
            </div>
            <div class="form-actions">
              <button type="button" id="cancel-new-offer">Cancelar</button>
              <button type="submit" class="primary">Adicionar na fila</button>
            </div>
          </form>
        </section>
      </div>
    </main>
  </div>
  {script}
</body>
</html>"""

    @staticmethod
    def _offer_state(result: AffiliateFactoryWorkflowResult) -> dict[str, Any]:
        package = result.package
        if package is None:
            return {}
        approval = result.approval_request
        approval_public = approval.public_dict() if approval is not None else {}
        steps = [
            {
                "department": step.department,
                "success": step.success,
                "summary": step.summary,
                "error": step.error,
            }
            for step in result.steps
        ]
        product_output = result.output_for("Product Research")
        affiliate_output = result.output_for("Affiliate Deals")
        product = affiliate_output.get("product_offer", {})
        status = AffiliateApprovalDashboardRenderer._queue_status(
            package.approval_status,
            package.telegram_status,
            package.publishing_status,
        )
        return {
            "id": str(package.package_id),
            "approval_id": str(package.approval_id or ""),
            "approval_short_id": str(package.approval_id or "")[:8],
            "title": package.selected_product_name,
            "marketplace": (product.get("marketplace") or {}).get("display_name", "") if isinstance(product, dict) else "",
            "category": product.get("category", "") if isinstance(product, dict) else "",
            "product_url": product.get("product_url", "") if isinstance(product, dict) else "",
            "image_url": product.get("image_url", "") if isinstance(product, dict) else "",
            "product_research_score": package.product_research_score,
            "creative_action": package.creative_action,
            "creative_score": package.creative_score,
            "deal_score": package.deal_score,
            "recommendation": package.recommendation,
            "publishing_status": package.publishing_status,
            "approval_status": package.approval_status,
            "telegram_status": package.telegram_status,
            "telegram_message_id": package.telegram_message_id,
            "status": status,
            "message_body": package.message_body,
            "primary_funnel": package.metadata.get("primary_funnel", ""),
            "telegram_text_length": package.metadata.get("telegram_text_length", len(package.message_body)),
            "approval": approval_public,
            "steps": steps,
            "shortlisted_count": len(product_output.get("shortlisted", [])),
            "published": package.telegram_status in ("sent", "sent_mock"),
        }

    @staticmethod
    def _queue_status(approval_status: str, telegram_status: str, publishing_status: str) -> str:
        if telegram_status in ("sent", "sent_mock"):
            return "published"
        if approval_status == "approved":
            return "approved"
        if approval_status == "rejected":
            return "blocked"
        if publishing_status in ("blocked", "rejected"):
            return "blocked"
        return "pending"

    @staticmethod
    def _offer_row(offer: dict[str, Any]) -> str:
        offer_id = escape(str(offer.get("id", "")))
        title = escape(str(offer.get("title", "")))
        marketplace = escape(str(offer.get("marketplace", "")))
        status = str(offer.get("status", "pending"))
        deal_score = float(offer.get("deal_score", 0.0) or 0.0)
        creative = escape(str(offer.get("creative_action", "")))
        telegram = escape(str(offer.get("telegram_status", "") or "aguardando"))
        initials = escape(_initials(title))
        return f"""<tr data-offer-row data-offer-id="{offer_id}" data-status="{escape(status)}" tabindex="0">
  <td><div class="offer-title"><span class="thumb">{initials}</span><div><strong>{title}</strong><br><span class="sub">{marketplace}</span></div></div></td>
  <td><span class="pill {AffiliateApprovalDashboardRenderer._status_class(status)}">{escape(status)}</span></td>
  <td>{deal_score:.1f}</td>
  <td><span class="pill blue">{creative}</span></td>
  <td>{telegram}</td>
</tr>"""

    @staticmethod
    def _offer_card(offer: dict[str, Any]) -> str:
        offer_id = escape(str(offer.get("id", "")))
        title = escape(str(offer.get("title", "")))
        status = str(offer.get("status", "pending"))
        deal_score = float(offer.get("deal_score", 0.0) or 0.0)
        creative_score = float(offer.get("creative_score", 0.0) or 0.0)
        return f"""<article class="offer-card" data-offer-card data-offer-id="{offer_id}" data-status="{escape(status)}" tabindex="0">
  <strong>{title}</strong>
  <span class="pill {AffiliateApprovalDashboardRenderer._status_class(status)}">{escape(status)}</span>
  <div class="score-line"><div class="bar"><span style="width:{min(100, int(deal_score))}%"></span></div><span>{deal_score:.1f}</span></div>
  <p class="sub" style="margin-top:10px">Criativo {creative_score:.1f} / Oferta {deal_score:.1f}</p>
</article>"""

    @staticmethod
    def _activity_item(offer: dict[str, Any]) -> str:
        title = escape(str(offer.get("title", "")))
        status = escape(str(offer.get("status", "")))
        short_id = escape(str(offer.get("approval_short_id", "")))
        return f"""<div class="activity-item" data-activity-static>{title}: {status} | approval {short_id}</div>"""

    @staticmethod
    def _interactive_script(payload: str) -> str:
        script = """<script>
window.__affiliateDashboard = __PAYLOAD__;
(function () {
  const state = window.__affiliateDashboard || { offers: [], summary: {} };
  const rows = Array.from(document.querySelectorAll("[data-offer-row]"));
  const cards = Array.from(document.querySelectorAll("[data-offer-card]"));
  const search = document.getElementById("offer-search");
  const detail = document.getElementById("offer-detail");
  const log = document.getElementById("activity-log");
  const newOfferModal = document.getElementById("new-offer-modal");
  const newOfferForm = document.getElementById("new-offer-form");
  const serverBacked = state.mode === "server";
  let selectedId = state.offers[0] ? state.offers[0].id : "";
  let filter = "all";
  let scoreDesc = true;

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function offerById(id) {
    return (state.offers || []).find((item) => item.id === id);
  }

  function statusClass(status) {
    if (status === "published") return "green";
    if (status === "approved") return "blue";
    if (status === "blocked") return "red";
    return "amber";
  }

  function recomputeSummary() {
    const offers = state.offers || [];
    const summary = {
      total: offers.length,
      pending: offers.filter((offer) => offer.approval_status === "pending").length,
      approved: offers.filter((offer) => offer.approval_status === "approved").length,
      published: offers.filter((offer) => offer.telegram_status === "sent" || offer.telegram_status === "sent_mock").length
    };
    document.getElementById("metric-total").textContent = summary.total;
    document.getElementById("metric-pending").textContent = summary.pending;
    document.getElementById("metric-approved").textContent = summary.approved;
    document.getElementById("metric-published").textContent = summary.published;
  }

  function addLog(text) {
    if (!log) return;
    const item = document.createElement("div");
    item.className = "activity-item";
    item.textContent = new Date().toLocaleTimeString("pt-BR") + " | " + text;
    log.prepend(item);
  }

  function openNewOfferModal() {
    if (!newOfferModal) return;
    newOfferModal.hidden = false;
    const firstInput = newOfferModal.querySelector("input[name='product_name']");
    if (firstInput) firstInput.focus();
  }

  function closeNewOfferModal() {
    if (!newOfferModal) return;
    newOfferModal.hidden = true;
  }

  async function createManualOffer(event) {
    event.preventDefault();
    if (!newOfferForm) return;
    if (!serverBacked) {
      addLog("Entrada manual salva de verdade apenas no modo servidor local.");
      closeNewOfferModal();
      return;
    }
    const body = Object.fromEntries(new FormData(newOfferForm).entries());
    try {
      const response = await fetch("/api/offers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await response.json();
      if (!response.ok || data.ok === false) {
        addLog(data.error || "Nao foi possivel criar a oferta manual.");
        return;
      }
      addLog(data.message || "Oferta manual criada.");
      window.location.reload();
    } catch (error) {
      addLog("Servidor local indisponivel para criar a oferta.");
    }
  }

  function updateOfferDom(offer) {
    const row = document.querySelector(`[data-offer-row][data-offer-id="${offer.id}"]`);
    const card = document.querySelector(`[data-offer-card][data-offer-id="${offer.id}"]`);
    if (row) {
      row.dataset.status = offer.status;
      row.children[1].innerHTML = `<span class="pill ${statusClass(offer.status)}">${esc(offer.status)}</span>`;
      row.children[4].textContent = offer.telegram_status || "aguardando";
    }
    if (card) {
      card.dataset.status = offer.status;
      const pill = card.querySelector(".pill");
      if (pill) {
        pill.className = "pill " + statusClass(offer.status);
        pill.textContent = offer.status;
      }
    }
  }

  function mergeOffer(updated) {
    const index = (state.offers || []).findIndex((item) => item.id === updated.id);
    if (index >= 0) {
      state.offers[index] = Object.assign({}, state.offers[index], updated);
    }
    return offerById(updated.id);
  }

  async function serverAction(action, body) {
    const offer = offerById(selectedId);
    if (!offer) return;
    try {
      const response = await fetch(`/api/offers/${encodeURIComponent(selectedId)}/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body || {})
      });
      const data = await response.json();
      if (!response.ok || data.ok === false) {
        addLog(data.error || "Acao recusada pelo servidor local.");
        return;
      }
      const updated = data.offer ? mergeOffer(data.offer) : offerById(selectedId);
      if (updated) updateOfferDom(updated);
      if (data.summary) state.summary = data.summary;
      recomputeSummary();
      renderDetail();
      addLog(data.message || "Acao executada no servidor local.");
    } catch (error) {
      addLog("Servidor local indisponivel para executar esta acao.");
    }
  }

  function approveOffer() {
    if (serverBacked) {
      serverAction("approve", { decided_by: "owner" });
      return;
    }
    const offer = offerById(selectedId);
    if (!offer || offer.status === "published") return;
    offer.approval_status = "approved";
    offer.status = "approved";
    updateOfferDom(offer);
    recomputeSummary();
    renderDetail();
    addLog("Oferta aprovada: " + offer.title);
  }

  function rejectOffer() {
    if (serverBacked) {
      serverAction("reject", { reason: "Rejected in local dashboard." });
      return;
    }
    const offer = offerById(selectedId);
    if (!offer || offer.status === "published") return;
    offer.approval_status = "rejected";
    offer.status = "blocked";
    updateOfferDom(offer);
    recomputeSummary();
    renderDetail();
    addLog("Oferta rejeitada: " + offer.title);
  }

  function publishOffer() {
    if (serverBacked) {
      serverAction("publish", {});
      return;
    }
    const offer = offerById(selectedId);
    if (!offer || offer.approval_status !== "approved") {
      addLog("Publicacao bloqueada: aprove a oferta primeiro.");
      return;
    }
    offer.telegram_status = offer.telegram_status || "sent_mock";
    if (offer.telegram_status === "aguardando") offer.telegram_status = "sent_mock";
    offer.status = "published";
    offer.telegram_message_id = offer.telegram_message_id || 1001;
    updateOfferDom(offer);
    recomputeSummary();
    renderDetail();
    addLog("Publicacao liberada para Telegram: " + offer.title);
  }

  function renderDetail() {
    const offer = offerById(selectedId);
    if (!offer || !detail) return;
    const steps = (offer.steps || []).map((step) => `
      <div class="step"><span>${esc(step.department)}</span><span class="pill ${step.success ? "green" : "red"}">${step.success ? "ok" : "falha"}</span></div>
    `).join("");
    const canPublish = offer.approval_status === "approved" && offer.status !== "published";
    detail.innerHTML = `
      <div class="detail-grid">
        <div class="field"><span>Produto</span><strong>${esc(offer.title)}</strong></div>
        <div class="field"><span>Status</span><strong><span class="pill ${statusClass(offer.status)}">${esc(offer.status)}</span></strong></div>
        <div class="field"><span>Score produto</span><strong>${Number(offer.product_research_score || 0).toFixed(1)}</strong></div>
        <div class="field"><span>Score oferta</span><strong>${Number(offer.deal_score || 0).toFixed(1)}</strong></div>
        <div class="field"><span>Criativo</span><strong>${esc(offer.creative_action)} (${Number(offer.creative_score || 0).toFixed(1)})</strong></div>
        <div class="field"><span>Telegram</span><strong>${esc(offer.telegram_status || "aguardando")}</strong></div>
      </div>
      <div>
        <h2 style="margin:0 0 9px;font-size:16px">Mensagem</h2>
        <div class="message-preview">${esc(offer.message_body || "")}</div>
      </div>
      <div>
        <h2 style="margin:0 0 9px;font-size:16px">Etapas</h2>
        <div class="step-list">${steps}</div>
      </div>
      <div class="actions">
        <button type="button" class="good" id="approve-offer">Aprovar</button>
        <button type="button" class="danger" id="reject-offer">Rejeitar</button>
        <button type="button" class="primary" id="publish-offer" ${canPublish ? "" : "disabled"}>Publicar</button>
      </div>
    `;
    document.getElementById("approve-offer").addEventListener("click", approveOffer);
    document.getElementById("reject-offer").addEventListener("click", rejectOffer);
    document.getElementById("publish-offer").addEventListener("click", publishOffer);
  }

  function selectOffer(id) {
    selectedId = id;
    rows.forEach((row) => row.classList.toggle("selected", row.dataset.offerId === id));
    cards.forEach((card) => card.classList.toggle("selected", card.dataset.offerId === id));
    renderDetail();
  }

  function matchesFilter(element) {
    if (filter === "all") return true;
    return element.dataset.status === filter;
  }

  function applyFilters() {
    const term = search ? search.value.trim().toLowerCase() : "";
    rows.concat(cards).forEach((item) => {
      const textMatch = !term || item.textContent.toLowerCase().includes(term);
      item.classList.toggle("is-hidden", !(textMatch && matchesFilter(item)));
    });
  }

  rows.concat(cards).forEach((item) => {
    item.addEventListener("click", () => selectOffer(item.dataset.offerId));
    item.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectOffer(item.dataset.offerId);
      }
    });
  });

  document.querySelectorAll("[data-filter]").forEach((tab) => {
    tab.addEventListener("click", function () {
      document.querySelectorAll("[data-filter]").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      filter = tab.dataset.filter;
      applyFilters();
    });
  });

  if (search) search.addEventListener("input", applyFilters);
  const reset = document.getElementById("reset-view");
  if (reset) {
    reset.addEventListener("click", function () {
      filter = "all";
      if (search) search.value = "";
      document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item.dataset.filter === "all"));
      applyFilters();
    });
  }
  const sort = document.getElementById("sort-score");
  if (sort) {
    sort.addEventListener("click", function () {
      scoreDesc = !scoreDesc;
      state.offers.sort((a, b) => scoreDesc ? b.deal_score - a.deal_score : a.deal_score - b.deal_score);
      addLog("Ordenacao local por score atualizada.");
    });
  }
  const openGuide = document.getElementById("open-guide");
  if (openGuide) {
    openGuide.addEventListener("click", () => {
      addLog("Guia externo: docs/affiliate_factory_workflow/visual_operator_guide.md");
    });
  }
  const newOffer = document.getElementById("new-offer");
  if (newOffer) newOffer.addEventListener("click", openNewOfferModal);
  if (newOfferForm) newOfferForm.addEventListener("submit", createManualOffer);
  const closeNewOffer = document.getElementById("close-new-offer");
  if (closeNewOffer) closeNewOffer.addEventListener("click", closeNewOfferModal);
  const cancelNewOffer = document.getElementById("cancel-new-offer");
  if (cancelNewOffer) cancelNewOffer.addEventListener("click", closeNewOfferModal);
  if (newOfferModal) {
    newOfferModal.addEventListener("click", (event) => {
      if (event.target === newOfferModal) closeNewOfferModal();
    });
  }

  if (selectedId) selectOffer(selectedId);
  applyFilters();
})();
</script>"""
        return script.replace("__PAYLOAD__", payload)

    @staticmethod
    def _status_class(status: str) -> str:
        return {
            "published": "green",
            "approved": "blue",
            "blocked": "red",
            "pending": "amber",
        }.get(status, "violet")


def _initials(value: str) -> str:
    parts = [part for part in value.replace("-", " ").split() if part]
    if not parts:
        return "OF"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()
