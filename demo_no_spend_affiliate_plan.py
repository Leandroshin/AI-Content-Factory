"""Demonstration: zero-budget affiliate work plan.

When the owner is temporarily blocked by card balance, payout verification or
paid providers, the factory should keep preparing useful work without pushing
money-dependent steps.
"""

from __future__ import annotations

from core.departments.affiliate_deals import (
    build_no_spend_affiliate_plan,
    default_affiliate_platform_profiles,
)


_ASSERTION_COUNTER = 0


def _check(condition: bool, label: str) -> None:
    global _ASSERTION_COUNTER
    _ASSERTION_COUNTER += 1
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {_ASSERTION_COUNTER:>2}. {label}")
    if not condition:
        raise AssertionError(label)


def main() -> None:
    print("=" * 72)
    print("No-Spend Affiliate Plan - Keep Working Without Budget")
    print("=" * 72)

    plans = build_no_spend_affiliate_plan(default_affiliate_platform_profiles())
    by_name = {plan.platform_name: plan for plan in plans}

    print("\n" + "-" * 72)
    print("Step 1: Free work remains available")
    print("-" * 72)
    _check("digistore24" in by_name, "Digistore24 has a no-spend plan")
    _check("braip" in by_name, "Braip has a no-spend plan")
    _check("amazon_br" in by_name, "Amazon has a no-spend plan")
    _check("mercado_livre" in by_name, "Mercado Livre has a no-spend plan")

    digistore = by_name["digistore24"]
    braip = by_name["braip"]
    amazon = by_name["amazon_br"]
    mercado_livre = by_name["mercado_livre"]

    _check(digistore.status == "manual_intake_ready", "Digistore can still prepare manual intake")
    _check(
        any("Browse Marketplace" in action for action in digistore.allowed_actions),
        "Digistore allows marketplace browsing without budget",
    )
    _check(
        any("PayPal" in action for action in digistore.blocked_actions),
        "Digistore blocks PayPal verification until budget exists",
    )
    _check(
        any("Paid traffic" in action for action in digistore.blocked_actions),
        "Digistore blocks paid traffic in no-spend mode",
    )

    print("\n" + "-" * 72)
    print("Step 2: Credentials do not automatically unlock production")
    print("-" * 72)
    _check(braip.status == "manual_intake_ready", "Braip can collect offers with account/token ready")
    _check(
        any("read-only" in action for action in braip.allowed_actions),
        "Braip token is limited to future read-only checks",
    )
    _check(
        any("Paid traffic" in action for action in braip.blocked_actions),
        "Braip paid traffic remains blocked",
    )

    print("\n" + "-" * 72)
    print("Step 3: Organic/manual channels stay usable")
    print("-" * 72)
    _check(amazon.status == "manual_intake_ready", "Amazon remains usable for manual organic tests")
    _check(
        any("Telegram/WhatsApp copy" in action for action in amazon.allowed_actions),
        "Amazon can prepare organic channel copy",
    )
    _check(
        mercado_livre.status == "research_only",
        "Mercado Livre stays research-only without owned affiliate attribution",
    )
    _check(
        any("owned affiliate attribution" in action for action in mercado_livre.blocked_actions),
        "Mercado Livre blocks publication without owned attribution",
    )

    print(f"\n{'=' * 72}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
