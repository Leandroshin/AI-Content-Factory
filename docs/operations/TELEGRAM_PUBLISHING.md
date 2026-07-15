# Publicação controlada no Telegram

O Telegram é o primeiro canal operacional de ofertas. WhatsApp permanece fora
do fluxo automático nesta fase.

## Fluxo

1. O produto entra no painel e passa pela coleta e análise.
2. O owner confirma preço, origem oficial do link afiliado, canal e revisão visual.
3. A fábrica prepara a mensagem exata sem chamar provider pago.
4. O owner marca a confirmação final e coloca a mensagem na fila do Telegram.
5. O pacote expira após duas horas para evitar publicar preço antigo.
6. O worker local reserva uma única mensagem, publica pelo bot e devolve
   `message_id`, horário e resultado ao painel.

Preparar pacote nunca publica. Aprovar uma oportunidade nunca publica. Somente a
confirmação textual `PUBLICAR NO TELEGRAM` cria uma solicitação de envio.

## Formato comercial

A oferta usa foto oficial revisada, título, preço confirmado, link monetizado e
uma identificação curta `#publi` no final. Não é usada a frase longa sobre
comissão. O marcador curto mantém o post limpo sem esconder a natureza
comercial da recomendação.

O comportamento de outros canais serve como referência visual, não como prova
de conformidade. Preço, estoque, cupom e urgência nunca são inventados.

## Segredos locais

`secrets/dashboard.env`:

```text
DASHBOARD_INTAKE_TOKEN=...
SITES_AUTHORIZATION_TOKEN=...
```

`secrets/telegram.env`:

```text
TELEGRAM_BOT_TOKEN=...
```

Os arquivos em `secrets/` não entram no Git. O destino permitido por padrão é
`@achadosbaratosBrasil`.

## Execução manual

```powershell
$env:AI_COMPANY_RUN_TELEGRAM_WORKER='1'
python scripts/run_telegram_publication_worker.py
```

Cada execução consome no máximo uma publicação aprovada. Se ocorrer falha, o
painel registra o erro e exige uma ação explícita de reenviar.
