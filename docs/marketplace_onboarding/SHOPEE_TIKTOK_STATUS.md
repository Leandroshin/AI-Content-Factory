# Shopee and TikTok Shop onboarding

Updated on 2026-07-11.

This document separates owner-controlled account enrollment from technical
connector work. The factory never stores marketplace login passwords and never
uses browser scripts to imitate a person.

## Shopee Affiliate

### Observed state

- The authenticated account is `leandrovieira290`.
- Opening the official Affiliate Open API portal redirects to the application
  form for the Programa de Afiliados.
- The owner's normal telephone was rejected as already registered. Do not use
  a substitute number or create another account; recover the original Shopee
  account association or resolve it through official support first.
- No API credential can be configured until the affiliate account is accepted
  and the portal exposes the account's API controls.

### Owner action required

1. Decide whether the contract and payments will use PF or PJ.
2. For PJ, retrieve the official Receita Federal CNPJ certificate and confirm
   with an accountant that a registered primary or secondary CNAE permits the
   service invoices and service codes required by the current Shopee terms.
   The owner reports that an online activity may already exist, but this is not
   accepted as verified until the official certificate is inspected.
3. Add only social accounts actually controlled by the owner, prioritizing the
   public Achados Baratos BR Instagram and Facebook assets.
4. Enter the real telephone number and the desired monitored contact email.
5. Read and personally accept the Shopee terms, confirm all declarations are
   truthful, and submit the application.
6. Report the approval result before the factory attempts Open API setup.

Official CNPJ lookup was prepared with `38.446.684/0001-22`; the Receita
Federal hCaptcha must be completed personally before the registered CNAEs can
be verified.

PF and PJ have different payment and tax-document flows. This project does not
make that legal or accounting choice for the owner.

### Connector after approval

1. Reopen `https://affiliate.shopee.com.br/open_api`.
2. Inventory only credentials and GraphQL scopes actually displayed.
3. Store secrets in the host secret provider, never in Git.
4. Prove a read-only product-offer query and normalize product, price,
   commission, image, seller and affiliate link evidence.
5. Keep publication behind HITL approval and official platform mechanisms.

## TikTok Shop Creator Affiliate

### Correct route

The current goal is to promote other sellers' products for commission. That is
the Creator Affiliate route, not a Seller account for inventory owned by Shin.

### Owner action required in the TikTok mobile app

1. Sign in to the intended public brand profile, currently
   `achadosbaratosbr2`.
2. Open **Profile -> three lines -> TikTok Studio -> TikTok Shop for Creator**.
3. Review the eligibility checklist and tap **Apply**.
4. Wait for the application result.
5. After approval, open the Verification Center and personally submit the
   requested photo ID and tax information.
6. Report whether the Creator Center and product marketplace are available.

### Connector after approval

- Affiliate links are initially generated through the official TikTok app.
- Partner/Affiliate API access is a separate application and approval process;
  a creator account does not automatically grant it.
- Until approved API scopes exist, intake remains manual: the owner supplies a
  product/link and the factory performs evidence, creative, compliance and
  HITL stages without automating TikTok login.

## Gate for both platforms

No automatic posting, identity submission, terms acceptance, payment setup or
API-scope assumption. The next technical milestone is a read-only connector
with redacted logs after each platform exposes official credentials.

## Account-growth bridge

TikTok growth now uses `AudienceGrowthPlanner` in
`core/content_factory/audience_growth.py`. It scores sourced opportunities,
blocks unsafe claims and creates production briefs only after owner approval.
The initial operating plan is in `docs/tiktok_growth/PILOT_PLAN_2026-07.md`.
