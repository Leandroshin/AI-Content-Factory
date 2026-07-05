# Guia visual de uso - Fila de Ofertas

Este arquivo e o guia separado para entender como voce usaria a fila no dia a dia.
Nao e material de impressao. A ideia e servir como um roteiro visual/operacional:
onde clicar, o que conferir e qual resultado esperar.

## Como abrir

Modo preview:

1. Rode `python demo_affiliate_approval_dashboard.py`.
2. Abra `output/affiliate_approval_dashboard/index.html`.
3. Use os botoes para entender o fluxo visual. Neste modo, as acoes ficam na propria tela.

Modo servidor local:

1. Rode `python -m core.content_factory.affiliate_dashboard_server --seed-demo`.
2. Abra `http://127.0.0.1:8787`.
3. Clique em uma oferta na tabela ou no card da fila.
4. Use `Aprovar`, `Rejeitar` e `Publicar`. Neste modo, as acoes passam pelo backend local e ficam salvas em `.ai_company/affiliate_dashboard/queue.json`.

## Exemplo de uso diario

### Quadro 1 - Escolher a oferta

Clique em uma oferta com bom score e status `Pendente`.

O que olhar:

- Nome do produto.
- Marketplace.
- Score da oferta.
- Status do criativo.
- Status do Telegram.

### Quadro 2 - Revisar antes de aprovar

No painel da direita, confira a mensagem pronta.

O que precisa estar certo:

- Preco atual.
- Preco antigo, quando existir.
- Cupom, se existir.
- Link de afiliado.
- Aviso de afiliado.
- Clareza da copy.
- Criativo marcado como `use_as_is` ou equivalente.

### Quadro 3 - Tomar decisao

Use `Aprovar` quando produto, imagem, preco, link e texto estiverem bons.

Use `Rejeitar` quando:

- A imagem estiver ruim ou poluida.
- O preco nao parecer uma oferta real.
- O link afiliado estiver ausente.
- A copy prometer demais.
- O produto parecer fraco para o publico.

### Quadro 4 - Publicar

Depois de aprovado, use `Publicar`.

Resultado esperado:

- O status do Telegram muda para publicado.
- A oferta sai da fila de pendentes.
- O historico registra a decisao.

## O que digitar quando houver entrada manual

A tela de entrada manual ainda vai ser ligada ao backend. Quando ela existir, o
preenchimento esperado sera:

| Campo | Exemplo | Observacao |
|---|---|---|
| URL do produto | `https://www.amazon.com.br/...` | Link original do produto. |
| Marketplace | `Amazon`, `Mercado Livre`, `Shopee` | Ajuda a escolher regras de avaliacao. |
| Link afiliado | `https://amzn.to/...` | Obrigatorio para publicar. |
| Preco atual | `327.22` | Usar numero limpo, sem `R$`. |
| Preco antigo | `499.90` | Opcional, mas ajuda no score. |
| Cupom | `TUDOPRIME` | Opcional. |
| Imagem | URL ou arquivo | O Creative Review decide se usa como esta. |
| Observacao | `Oferta Prime, estoque baixo` | Contexto util para a copy. |

## Regra simples

Produto forte e criativo limpo pode seguir rapido.

Produto bom com imagem ruim volta para Creative Review/Image antes de publicar.

Produto sem link afiliado nao publica.
