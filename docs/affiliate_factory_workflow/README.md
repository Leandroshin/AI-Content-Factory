# Affiliate Factory Workflow

Concrete flow:

`Strategy Intelligence -> Product Research -> Creative Review -> Affiliate Deals -> HITL Approval -> Telegram`

## Purpose

This workflow connects the departments that were previously working as separate proofs.
It turns strategy notes and candidate products into an approval-gated Telegram publication.

## Safety Defaults

- Strategy sources are analyzed as derived learning, not copied content.
- Product Research must shortlist products with affiliate targets.
- Creative Review only lets `use_as_is` assets proceed directly to publishing.
- Affiliate Deals always creates a human approval gate for Telegram.
- Telegram publication is blocked until `ApprovalRuntime` records an approved decision.
- The workflow can use `auto_approve=True` only for demos/tests.

## Output Package

The package records:

- selected product
- Product Research score
- creative decision
- Affiliate Deals score
- recommendation and publishing status
- approval id/status
- Telegram status/message id

## Daily Panel

`demo_affiliate_approval_dashboard.py` renders a local preview at
`output/affiliate_approval_dashboard/index.html`.

The panel shows the offer queue, selected offer details, Telegram message,
workflow steps, local approve/reject/publish interactions, and a printable A4
operator guide.
