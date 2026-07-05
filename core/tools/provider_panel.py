"""Self-contained interactive provider settings panel renderer."""

from __future__ import annotations

import json
from html import escape
from typing import Any


class ProviderPanelRenderer:
    """Render ProviderControlCenter dashboard_state as a static HTML panel."""

    @staticmethod
    def render_html(dashboard_state: dict[str, Any]) -> str:
        """Return a self-contained HTML document for local preview."""
        providers = list(dashboard_state.get("providers", []))
        ready = tuple(dashboard_state.get("ready_real_providers", ()))
        payload = json.dumps(dashboard_state, ensure_ascii=False, indent=2)
        script_payload = payload.replace("</", "<\\/")
        script = ProviderPanelRenderer._interactive_script(script_payload)
        rows = "\n".join(ProviderPanelRenderer._provider_row(p) for p in providers)
        budget_cards = "\n".join(ProviderPanelRenderer._budget_card(p) for p in providers)
        approval_items = "\n".join(ProviderPanelRenderer._approval_item(p) for p in providers)
        total_providers = len(providers)
        real_ready = len(ready)
        blocked = sum(1 for p in providers if p.get("execution_mode") == "real" and not p.get("can_execute_real"))
        estimated_cost = sum(
            float((p.get("usage_summary") or {}).get("estimated_cost_usd") or 0.0)
            for p in providers
        )
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Content Factory - APIs e Custos</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #070b12;
      --panel: #0d141f;
      --panel-2: #111b29;
      --line: #243044;
      --text: #eef4ff;
      --muted: #93a1b8;
      --purple: #9b5cff;
      --green: #30d989;
      --amber: #f7b731;
      --blue: #35b8ff;
      --red: #ff5e6c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(180deg, #07101a 0%, var(--bg) 48%, #090d14 100%);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    .app {{
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      min-height: 100vh;
    }}
    .app > aside {{
      border-right: 1px solid var(--line);
      padding: 24px 18px;
      background: rgba(7, 11, 18, 0.72);
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 750;
      font-size: 18px;
      margin-bottom: 32px;
    }}
    .mark {{
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--purple), var(--blue));
      display: grid;
      place-items: center;
      font-weight: 900;
    }}
    nav a {{
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--muted);
      text-decoration: none;
      padding: 13px 14px;
      border-radius: 8px;
      margin-bottom: 6px;
      font-size: 14px;
    }}
    nav a.active {{
      color: var(--text);
      background: #121b29;
      border: 1px solid var(--line);
    }}
    .credits {{
      margin-top: 34px;
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
    }}
    .credits strong {{ display: block; font-size: 28px; margin: 8px 0; }}
    .bar {{ height: 7px; border-radius: 999px; background: #253044; overflow: hidden; }}
    .bar span {{ display: block; height: 100%; background: linear-gradient(90deg, var(--purple), var(--blue)); }}
    main {{ padding: 26px 30px 34px; }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 22px;
    }}
    h1 {{ margin: 0 0 6px; font-size: 32px; line-height: 1.1; }}
    .sub {{ color: var(--muted); margin: 0; font-size: 14px; }}
    .actions {{ display: flex; gap: 10px; align-items: center; }}
    button {{
      border: 1px solid var(--line);
      background: #121928;
      color: var(--text);
      padding: 11px 14px;
      border-radius: 8px;
      font: inherit;
    }}
    button.primary {{ border-color: #7245bc; background: linear-gradient(135deg, #6b2ce0, #9a5cff); }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.65fr) minmax(340px, 0.75fr);
      gap: 18px;
    }}
    .side {{
      display: grid;
      gap: 18px;
      align-content: start;
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(13, 20, 31, 0.88);
      overflow: hidden;
    }}
    .panel-head {{
      padding: 18px 18px 0;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: flex-start;
    }}
    .panel h2 {{ margin: 0; font-size: 18px; }}
    .panel .hint {{ color: var(--muted); margin: 5px 0 0; font-size: 13px; }}
    .tabs {{
      display: flex;
      gap: 18px;
      padding: 18px 18px 0;
      border-bottom: 1px solid var(--line);
    }}
    .tab {{
      padding-bottom: 14px;
      color: var(--muted);
      font-size: 14px;
      border: 0;
      border-radius: 0;
      background: transparent;
      cursor: pointer;
    }}
    .tab.active {{ color: #cda8ff; border-bottom: 2px solid var(--purple); }}
    .table-tools {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 16px 18px 0;
    }}
    input[type="search"] {{
      min-width: 220px;
      flex: 1;
      border: 1px solid var(--line);
      background: #0a1019;
      color: var(--text);
      border-radius: 8px;
      padding: 11px 12px;
      font: inherit;
    }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(17, 27, 41, 0.72);
    }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; font-size: 24px; margin-top: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ padding: 13px 16px; border-top: 1px solid var(--line); text-align: left; font-size: 13px; vertical-align: middle; }}
    th {{ color: var(--muted); font-weight: 650; }}
    tr[data-provider-row] {{ cursor: pointer; }}
    tr[data-provider-row].selected {{ outline: 1px solid var(--purple); outline-offset: -1px; background: rgba(155, 92, 255, 0.07); }}
    tr.is-hidden {{ display: none; }}
    .provider-name {{ display: flex; align-items: center; gap: 12px; }}
    .logo {{
      width: 34px;
      height: 34px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      background: #1a2333;
      font-weight: 800;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border-radius: 999px;
      padding: 5px 9px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
      background: #172235;
      color: var(--muted);
    }}
    .pill.green {{ color: #8af3bb; background: rgba(48, 217, 137, 0.12); }}
    .pill.amber {{ color: #ffd78b; background: rgba(247, 183, 49, 0.13); }}
    .pill.red {{ color: #ff9aa4; background: rgba(255, 94, 108, 0.13); }}
    .pill.purple {{ color: #d7bcff; background: rgba(155, 92, 255, 0.16); }}
    .toggle {{
      display: inline-grid;
      grid-template-columns: 1fr 1fr;
      gap: 2px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 2px;
      background: #0a1019;
      min-width: 104px;
    }}
    .toggle span {{ text-align: center; padding: 6px 8px; border-radius: 6px; color: var(--muted); font-size: 12px; font-weight: 800; }}
    .toggle .on {{ color: white; background: linear-gradient(135deg, #6b2ce0, #9a5cff); }}
    .cards {{ display: grid; gap: 12px; padding: 18px; }}
    .budget-card {{
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel-2);
    }}
    .budget-top {{ display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }}
    .budget-top strong {{ font-size: 15px; }}
    .usage {{ margin-top: 8px; height: 8px; background: #253044; border-radius: 999px; overflow: hidden; }}
    .usage span {{ display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--green), var(--purple)); }}
    .security {{
      margin-top: 18px;
      display: flex;
      gap: 16px;
      align-items: center;
      padding: 18px;
      border: 1px solid rgba(255, 94, 108, 0.55);
      background: rgba(255, 94, 108, 0.08);
      border-radius: 8px;
    }}
    .shield {{
      width: 52px;
      height: 52px;
      border-radius: 16px;
      display: grid;
      place-items: center;
      color: white;
      background: rgba(255, 94, 108, 0.22);
      font-size: 24px;
    }}
    .approval {{ padding: 18px; display: grid; gap: 10px; }}
    .approval-item {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #0b121d;
    }}
    .snapshot {{
      margin-top: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #050810;
      overflow: hidden;
    }}
    .snapshot.collapsed pre {{ display: none; }}
    .detail {{
      padding: 18px;
      display: grid;
      gap: 12px;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .detail-field {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #0b121d;
      min-height: 72px;
    }}
    .detail-field span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 7px; }}
    .detail-field strong {{ font-size: 16px; }}
    .logline {{
      border-top: 1px solid var(--line);
      padding-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }}
    pre {{
      margin: 0;
      padding: 16px;
      max-height: 260px;
      overflow: auto;
      color: #aeb8cc;
      font-size: 12px;
      line-height: 1.45;
    }}
    @media (max-width: 1100px) {{
      .app {{ grid-template-columns: 1fr; }}
      aside {{ display: none; }}
      main {{ padding: 18px; }}
      .grid, .summary {{ grid-template-columns: 1fr; }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      header {{ flex-direction: column; }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <div class="brand"><span class="mark">A</span><span>AI Content Factory</span></div>
      <nav>
        <a href="#">Dashboard</a>
        <a href="#">Producoes</a>
        <a href="#">Pipeline</a>
        <a href="#">Funcionarios</a>
        <a href="#" class="active">APIs e Custos</a>
        <a href="#">Aprovacoes</a>
      </nav>
      <div class="credits">
        <span class="sub">Creditos disponiveis</span>
        <strong>12.450</strong>
        <span class="sub">de 20.000 creditos</span>
        <div class="bar" style="margin-top:12px"><span style="width:62%"></span></div>
      </div>
    </aside>
    <main>
      <header>
        <div>
          <h1>APIs e Custos</h1>
          <p class="sub">Configure providers, modos de execucao, aprovacao e limites antes de usar APIs reais.</p>
        </div>
        <div class="actions">
          <button>Ver logs</button>
          <button class="primary">Adicionar provider</button>
        </div>
      </header>

      <section class="summary">
        <div class="metric"><span>Providers</span><strong>{total_providers}</strong></div>
        <div class="metric"><span>REAL prontos</span><strong>{real_ready}</strong></div>
        <div class="metric"><span>Bloqueados</span><strong>{blocked}</strong></div>
        <div class="metric"><span>Custo estimado</span><strong>${estimated_cost:.2f}</strong></div>
      </section>

      <div class="grid">
        <section class="panel">
          <div class="tabs">
            <button class="tab active" data-tab="integracoes" type="button">Integracoes</button>
            <button class="tab" data-tab="orcamentos" type="button">Orcamentos</button>
            <button class="tab" data-tab="uso" type="button">Uso e custos</button>
            <button class="tab" data-tab="aprovacoes" type="button">Aprovacoes</button>
            <button class="tab" data-tab="auditoria" type="button">Auditoria</button>
          </div>
          <div class="panel-head">
            <div>
              <h2>Provedores e APIs</h2>
              <p class="hint">MOCK e seguro para testes. REAL so executa quando chave, budget e aprovacao estiverem corretos.</p>
            </div>
            <button id="toggle-snapshot" type="button">Auditoria</button>
          </div>
          <div class="table-tools">
            <input id="provider-search" type="search" placeholder="Buscar provider" aria-label="Buscar provider">
            <button id="filter-blocked" type="button">Bloqueados</button>
            <button id="reset-filters" type="button">Todos</button>
          </div>
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Status</th>
                <th>Chave</th>
                <th>Modo</th>
                <th>Aprovacao</th>
                <th>Uso</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
          <div class="security">
            <div class="shield">!</div>
            <div>
              <strong>Nenhuma API real roda sem aprovacao</strong>
              <p class="sub">A execucao REAL exige chave configurada, budget explicito e aprovacao manual do dono.</p>
            </div>
          </div>
        </section>

        <aside class="side">
          <section class="panel" id="provider-detail-panel">
            <div class="panel-head">
              <div>
                <h2>Provider selecionado</h2>
                <p class="hint">Estado calculado no navegador a partir do snapshot.</p>
              </div>
            </div>
            <div class="detail" id="provider-detail"></div>
          </section>
          <section class="panel">
            <div class="panel-head">
              <div>
                <h2>Orcamentos por provider</h2>
                <p class="hint">Limites vindos do ProviderControlCenter.</p>
              </div>
            </div>
            <div class="cards">
              {budget_cards}
            </div>
          </section>
          <section class="panel" style="margin-top:18px">
            <div class="panel-head">
              <div>
                <h2>Fila de aprovacao</h2>
                <p class="hint">Providers em REAL que ainda precisam de acao.</p>
              </div>
            </div>
            <div class="approval">
              {approval_items}
            </div>
          </section>
        </aside>
      </div>

      <section class="panel" style="margin-top:18px">
        <div class="panel-head">
          <div>
            <h2>Snapshot usado pela UI</h2>
            <p class="hint">Payload real gerado por ProviderControlCenter.dashboard_state().</p>
          </div>
        </div>
        <div class="snapshot" id="snapshot-panel"><pre>{escape(payload)}</pre></div>
      </section>
    </main>
  </div>
  {script}
</body>
</html>"""

    @staticmethod
    def _interactive_script(payload: str) -> str:
        script = """<script>
window.__providerDashboard = __PAYLOAD__;
(function () {
  const state = window.__providerDashboard || { providers: [] };
  const rows = Array.from(document.querySelectorAll("[data-provider-row]"));
  const search = document.getElementById("provider-search");
  const detail = document.getElementById("provider-detail");
  const snapshot = document.getElementById("snapshot-panel");
  let selectedProvider = state.providers[0] ? state.providers[0].provider : "";
  let blockedOnly = false;

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function providerByKey(key) {
    return (state.providers || []).find((item) => item.provider === key);
  }

  function usageFor(provider) {
    provider.usage_summary = provider.usage_summary || {
      requests: 0,
      successes: 0,
      failures: 0,
      billable_units: 0,
      estimated_cost_usd: 0
    };
    return provider.usage_summary;
  }

  function rowBlocked(provider) {
    return provider.execution_mode === "real" && !provider.can_execute_real;
  }

  function updateRow(provider) {
    const row = document.querySelector(`[data-provider="${provider.provider}"]`);
    if (!row) return;
    const usage = usageFor(provider);
    const usageCell = row.querySelector("td:last-child");
    if (usageCell) {
      usageCell.innerHTML = `${usage.billable_units || 0} unidades<br><span class="sub">$${Number(usage.estimated_cost_usd || 0).toFixed(4)}</span>`;
    }
  }

  function renderProviderDetail() {
    const provider = providerByKey(selectedProvider) || (state.providers || [])[0];
    if (!provider || !detail) return;
    const usage = usageFor(provider);
    const capabilities = provider.metadata && provider.metadata.capabilities
      ? provider.metadata.capabilities.join(", ")
      : "sem metadata";
    const secretState = provider.missing_secret_keys && provider.missing_secret_keys.length
      ? "faltando"
      : (provider.configured_secret_keys || []).length ? "configurada" : "nao requerida";
    const canReal = provider.can_execute_real ? "sim" : "nao";
    detail.innerHTML = `
      <div class="detail-grid">
        <div class="detail-field"><span>Provider</span><strong>${esc(provider.display_name || provider.provider)}</strong></div>
        <div class="detail-field"><span>Status</span><strong>${esc(provider.status)}</strong></div>
        <div class="detail-field"><span>Modo</span><strong>${esc(String(provider.execution_mode).toUpperCase())}</strong></div>
        <div class="detail-field"><span>REAL liberado</span><strong>${canReal}</strong></div>
        <div class="detail-field"><span>Chave</span><strong>${secretState}</strong></div>
        <div class="detail-field"><span>Budget</span><strong>$${Number(provider.max_cost_usd || 0).toFixed(2)}</strong></div>
        <div class="detail-field"><span>Uso</span><strong>${usage.billable_units || 0} unidades</strong></div>
        <div class="detail-field"><span>Custo</span><strong>$${Number(usage.estimated_cost_usd || 0).toFixed(4)}</strong></div>
      </div>
      <div class="logline">Capabilities: ${esc(capabilities)}</div>
      <button id="simulate-usage" type="button">Simular uso local</button>
    `;
    const simulate = document.getElementById("simulate-usage");
    if (simulate) {
      simulate.addEventListener("click", function () {
        const current = providerByKey(selectedProvider);
        if (!current) return;
        const currentUsage = usageFor(current);
        currentUsage.requests = Number(currentUsage.requests || 0) + 1;
        currentUsage.successes = Number(currentUsage.successes || 0) + 1;
        currentUsage.billable_units = Number(currentUsage.billable_units || 0) + 10;
        currentUsage.estimated_cost_usd = Number((Number(currentUsage.estimated_cost_usd || 0) + 0.001).toFixed(6));
        updateRow(current);
        renderProviderDetail();
      });
    }
  }

  function selectProvider(key) {
    selectedProvider = key;
    rows.forEach((row) => row.classList.toggle("selected", row.dataset.provider === key));
    renderProviderDetail();
  }

  function applyFilters() {
    const term = search ? search.value.trim().toLowerCase() : "";
    rows.forEach((row) => {
      const provider = providerByKey(row.dataset.provider);
      const textMatch = !term || row.textContent.toLowerCase().includes(term);
      const blockMatch = !blockedOnly || (provider && rowBlocked(provider));
      row.classList.toggle("is-hidden", !(textMatch && blockMatch));
    });
  }

  rows.forEach((row) => {
    row.addEventListener("click", () => selectProvider(row.dataset.provider));
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectProvider(row.dataset.provider);
      }
    });
  });

  if (search) search.addEventListener("input", applyFilters);
  const blockedButton = document.getElementById("filter-blocked");
  if (blockedButton) {
    blockedButton.addEventListener("click", function () {
      blockedOnly = true;
      applyFilters();
    });
  }
  const resetButton = document.getElementById("reset-filters");
  if (resetButton) {
    resetButton.addEventListener("click", function () {
      blockedOnly = false;
      if (search) search.value = "";
      applyFilters();
    });
  }
  const snapshotButton = document.getElementById("toggle-snapshot");
  if (snapshotButton && snapshot) {
    snapshotButton.addEventListener("click", () => snapshot.classList.toggle("collapsed"));
  }
  document.querySelectorAll("[data-tab]").forEach((tab) => {
    tab.addEventListener("click", function () {
      document.querySelectorAll("[data-tab]").forEach((item) => item.classList.remove("active"));
      tab.classList.add("active");
      if (tab.dataset.tab === "aprovacoes") {
        blockedOnly = true;
        applyFilters();
      }
      if (tab.dataset.tab === "auditoria" && snapshot) {
        snapshot.classList.remove("collapsed");
      }
    });
  });

  if (selectedProvider) selectProvider(selectedProvider);
  applyFilters();
})();
</script>"""
        return script.replace("__PAYLOAD__", payload)

    @staticmethod
    def _provider_row(provider: dict[str, Any]) -> str:
        name = escape(str(provider.get("display_name", provider.get("provider", ""))))
        key = escape(str(provider.get("provider", "")))
        category = escape(str(provider.get("category", "")))
        status = escape(str(provider.get("status", "")))
        secret = ProviderPanelRenderer._secret_text(provider)
        mode = str(provider.get("execution_mode", "mock"))
        approval = bool(provider.get("owner_approved"))
        summary = provider.get("usage_summary") or {}
        units = int(summary.get("billable_units") or 0)
        cost = float(summary.get("estimated_cost_usd") or 0.0)
        can_real = bool(provider.get("can_execute_real"))
        status_class = "green" if can_real or mode == "mock" else "amber"
        if status in ("missing_credentials", "missing_budget"):
            status_class = "red"
        approval_class = "green" if approval else "amber"
        return f"""<tr data-provider-row data-provider="{key}" data-status="{status}" tabindex="0">
  <td><div class="provider-name"><span class="logo">{escape(name[:2].upper())}</span><div><strong>{name}</strong><br><span class="sub">{category}</span></div></div></td>
  <td><span class="pill {status_class}">{status}</span></td>
  <td>{secret}</td>
  <td>{ProviderPanelRenderer._mode_toggle(mode)}</td>
  <td><span class="pill {approval_class}">{"Aprovado" if approval else "Pendente"}</span></td>
  <td>{units} unidades<br><span class="sub">${cost:.4f}</span></td>
</tr>"""

    @staticmethod
    def _budget_card(provider: dict[str, Any]) -> str:
        name = escape(str(provider.get("display_name", provider.get("provider", ""))))
        summary = provider.get("usage_summary") or {}
        max_units = int(provider.get("max_units") or 0)
        units = int(summary.get("billable_units") or 0)
        max_cost = float(provider.get("max_cost_usd") or 0.0)
        cost = float(summary.get("estimated_cost_usd") or 0.0)
        pct = 0
        if max_units > 0:
            pct = min(100, int(units / max_units * 100))
        elif max_cost > 0:
            pct = min(100, int(cost / max_cost * 100))
        return f"""<div class="budget-card">
  <div class="budget-top"><strong>{name}</strong><span class="pill purple">{pct}% usado</span></div>
  <div class="sub">{units} / {max_units or "sem limite"} unidades</div>
  <div class="sub">${cost:.4f} / ${max_cost:.2f}</div>
  <div class="usage"><span style="width:{pct}%"></span></div>
</div>"""

    @staticmethod
    def _approval_item(provider: dict[str, Any]) -> str:
        name = escape(str(provider.get("display_name", provider.get("provider", ""))))
        mode = str(provider.get("execution_mode", "mock"))
        can_real = bool(provider.get("can_execute_real"))
        status = escape(str(provider.get("status", "")))
        if mode == "mock":
            label = "Seguro em MOCK"
            klass = "green"
        elif can_real:
            label = "REAL aprovado"
            klass = "green"
        else:
            label = "Requer acao"
            klass = "amber"
        return f"""<div class="approval-item">
  <div><strong>{name}</strong><br><span class="sub">{status}</span></div>
  <span class="pill {klass}">{label}</span>
</div>"""

    @staticmethod
    def _mode_toggle(mode: str) -> str:
        mock_class = "on" if mode == "mock" else ""
        real_class = "on" if mode == "real" else ""
        return f"""<span class="toggle"><span class="{mock_class}">MOCK</span><span class="{real_class}">REAL</span></span>"""

    @staticmethod
    def _secret_text(provider: dict[str, Any]) -> str:
        hints = provider.get("secret_hints") or {}
        configured = provider.get("configured_secret_keys") or ()
        missing = provider.get("missing_secret_keys") or ()
        if configured:
            first = str(configured[0])
            hint = escape(str(hints.get(first, "configurado")))
            return f"<span class=\"pill green\">{hint}</span>"
        if missing:
            return "<span class=\"pill red\">faltando</span>"
        return "<span class=\"pill\">nao requerido</span>"
