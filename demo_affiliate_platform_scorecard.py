"""Demonstration: affiliate platform scorecard for Shin's factory.

This demo turns creator advice ("avoid X, start with Y") into a deterministic
factory decision. The scorecard does not publish, buy traffic, scrape, or create
affiliate links. It only decides what the owner should configure next.
"""

from __future__ import annotations

from core.departments.affiliate_deals import (
    AffiliatePlatformProfile,
    default_affiliate_platform_profiles,
    evaluate_affiliate_platform,
    rank_affiliate_platforms,
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
    print("Affiliate Platform Scorecard - Portfolio Prioritization")
    print("=" * 72)

    profiles = default_affiliate_platform_profiles()
    ranked = rank_affiliate_platforms(profiles)
    names = tuple(item.platform.name for item in ranked)

    print("\n" + "-" * 72)
    print("Step 1: Current portfolio is ranked by readiness and economics")
    print("-" * 72)
    _check(len(profiles) >= 6, "Default portfolio includes physical and digital platforms")
    _check("digistore24" in names, "Digistore24 is in the portfolio")
    _check("braip" in names, "Braip is in the portfolio")
    _check("amazon_br" in names, "Amazon Brasil remains in the portfolio")
    _check("mercado_livre" in names, "Mercado Livre remains in the portfolio")

    digistore = next(item for item in ranked if item.platform.name == "digistore24")
    amazon = next(item for item in ranked if item.platform.name == "amazon_br")
    mercado_livre = next(item for item in ranked if item.platform.name == "mercado_livre")
    maxweb = next(item for item in ranked if item.platform.name == "maxweb")

    _check(digistore.recommendation == "prepare_next", "Digistore24 is prepared next, not treated as already ready")
    _check("owner_action_required" in digistore.reasons, "Digistore24 still requires owner onboarding")
    _check("better_for_commission_testing" in digistore.reasons, "Digital network is marked better for commission testing")
    _check(any("affiliate account" in action for action in digistore.next_actions), "Digistore24 next action asks for account setup")
    _check(digistore.score_total > mercado_livre.score_total, "Digistore24 outranks Mercado Livre for first-revenue strategy")

    _check(amazon.recommendation == "start_now", "Amazon can start now for organic testing")
    _check("owner_account_ready" in amazon.reasons, "Amazon readiness is based on owned account status")
    _check("useful_for_organic_testing" in amazon.reasons, "Amazon is explicitly framed as organic testing")
    _check(amazon.economics_score < digistore.economics_score, "Amazon commission economics stay below digital networks")

    _check(mercado_livre.recommendation == "blocked", "Mercado Livre is blocked until affiliate attribution is ready")
    _check(any("official affiliate access" in action for action in mercado_livre.next_actions), "Mercado Livre asks for official affiliate access")
    _check(maxweb.recommendation != "start_now", "MaxWeb is not a first action despite high commission")
    _check("strong_commission_economics" in maxweb.reasons, "MaxWeb commission strength is recorded")
    _check(maxweb.friction_penalty > digistore.friction_penalty, "Manual application networks carry more friction")

    print("\n" + "-" * 72)
    print("Step 2: Paid traffic raises the compliance bar")
    print("-" * 72)
    paid_ranked = rank_affiliate_platforms(profiles, paid_traffic=True)
    paid_digistore = next(item for item in paid_ranked if item.platform.name == "digistore24")
    paid_amazon = next(item for item in paid_ranked if item.platform.name == "amazon_br")

    _check("paid_traffic_not_ready" in paid_digistore.reasons, "Paid traffic requires an extra Digistore24 rule check")
    _check(paid_digistore.score_total < digistore.score_total, "Paid traffic readiness reduces Digistore24 score")
    _check(paid_amazon.recommendation == "prepare_next", "Amazon should not be pushed as paid-traffic engine")
    _check(any("paid traffic rules" in action for action in paid_amazon.next_actions), "Paid traffic next action asks for platform rules")

    print("\n" + "-" * 72)
    print("Step 3: A fully prepared digital offer becomes production-ready")
    print("-" * 72)
    prepared = AffiliatePlatformProfile(
        name="digistore24_prepared_offer",
        display_name="Digistore24 Prepared Offer",
        category="digital_network",
        onboarding_status="ready",
        primary_use_case="One manually reviewed offer with allowed channels.",
        affiliate_link_ease=0.92,
        commission_potential=0.84,
        payout_friction=0.32,
        compliance_complexity=0.46,
        offer_evidence_strength=0.86,
        paid_traffic_allowed_confidence=0.78,
        owner_ready=True,
        manual_review_required=True,
        recommended_channels=("landing_page", "telegram", "youtube_short"),
        evidence_requirements=("Keep source screenshots and offer terms in the dashboard.",),
    )
    prepared_eval = evaluate_affiliate_platform(prepared, paid_traffic=False)
    prepared_paid_eval = evaluate_affiliate_platform(prepared, paid_traffic=True)

    _check(prepared_eval.recommendation == "start_now", "Prepared digital offer can start in organic mode")
    _check(prepared_eval.score_total >= 62.0, "Prepared digital offer crosses start threshold")
    _check("affiliate_link_easy" in prepared_eval.reasons, "Prepared offer keeps easy affiliate link reason")
    _check("offer_evidence_available" in prepared_eval.reasons, "Prepared offer has evidence")
    _check(prepared_paid_eval.recommendation == "start_now", "Prepared offer can also pass paid-traffic precheck")
    _check("paid_traffic_not_ready" not in prepared_paid_eval.reasons, "Prepared paid offer has no paid-traffic block")

    print("\n" + "-" * 72)
    print("Step 4: Unknown hype is not enough")
    print("-" * 72)
    hype = AffiliatePlatformProfile(
        name="new_hype_network",
        display_name="New Hype Network",
        category="digital_network",
        onboarding_status="unknown",
        primary_use_case="Creator screenshot with high revenue claim.",
        affiliate_link_ease=0.3,
        commission_potential=0.95,
        payout_friction=0.9,
        compliance_complexity=0.85,
        offer_evidence_strength=0.2,
        paid_traffic_allowed_confidence=0.0,
        owner_ready=False,
        manual_review_required=True,
        required_owner_actions=("Research official terms before any integration.",),
        evidence_requirements=("Collect official payout, refund, traffic, and creative rules.",),
    )
    hype_eval = evaluate_affiliate_platform(hype)
    _check(hype_eval.recommendation == "blocked", "Unknown high-commission network is blocked")
    _check("strong_commission_economics" in hype_eval.reasons, "High commission is recorded")
    _check("needs_offer_evidence" in hype_eval.reasons, "Missing evidence still blocks")
    _check(hype_eval.friction_penalty >= 14.0, "High payout friction is penalized")
    _check(hype_eval.compliance_penalty >= 11.0, "High compliance complexity is penalized")

    print(f"\n{'=' * 72}")
    print(f"All {_ASSERTION_COUNTER} assertions passed.")
    print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
