# Product Dashboard Intake

## What the owner submits

The **Produtos** area accepts the normal public product-page URL from Amazon Brasil, Mercado Livre, or Shopee. An affiliate link is a separate optional field.

The factory never converts or fabricates an affiliate link without an official account, portal, or API authorized by the owner.

## States

1. `queued`: URL was received and no product claim has been validated.
2. `analyzing`: a controlled worker is collecting product-page evidence.
3. `needs_input`: evidence exists, but a manual field, affiliate link, or creative review is pending.
4. `completed`: every required gate passed and the item can enter owner decision.
5. `blocked`: collection or validation failed safely.

## Visual review boundary

Product URL Intake can preserve the product image URL and detect whether an image is missing. It does not claim that the image is clean or commercially usable. That decision belongs to Creative Review, which can later choose `keep`, `improve`, `replace`, or `block`.

## Worker boundary

`ProductDashboardWorker` polls the private authenticated queue only when explicitly enabled. It performs one controlled intake per item and returns evidence to the dashboard. It does not publish, advertise, alter the supplied URL, or spend provider budget.

The Codex automation **Analisar fila de produtos** checks this queue hourly. Empty runs make no changes. Submitted items can therefore wait up to one hour before the first collection result appears.

Run the proof with:

```powershell
python demo_product_dashboard_worker.py
```
