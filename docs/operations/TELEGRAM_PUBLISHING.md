# Publicação contínua e controlada no Telegram

O Telegram é o primeiro canal operacional de ofertas. WhatsApp permanece fora
do fluxo automático nesta fase. A operação pode permanecer ativa continuamente,
sem data final, até o owner pausá-la no painel.

## Fluxo manual

1. O produto entra no painel e passa pela coleta e análise.
2. O owner confirma preço, origem oficial do link afiliado, canal e revisão visual.
3. A fábrica prepara a mensagem exata sem chamar provider pago.
4. A fábrica registra um candidato com status `PENDING HUMAN APPROVAL`; nada entra na fila de envio.
5. Em uma ação separada, o owner confere conteúdo, destino, validade e riscos e então coloca o candidato na fila local.
6. O pacote comercial expira após duas horas para evitar publicar preço antigo.
7. Somente com opt-in explícito, o worker local reserva atomicamente uma única mensagem, publica pelo bot e devolve
   `message_id`, horário e resultado ao painel.

Preparar pacote nunca publica. Aprovar uma oportunidade nunca publica. Somente a
confirmação textual `PREPARAR CANDIDATO` cria apenas o candidato. A confirmação
separada `APROVAR PUBLICACAO TELEGRAM` o coloca na fila local, mas não executa o
worker e não envia mensagem.

## Formato comercial

A oferta afiliada usa foto oficial revisada, título, preço confirmado, link monetizado e
uma identificação curta `#publi` no final. Mensagens editoriais sem link afiliado
não recebem marcador comercial. Não é usada a frase longa sobre
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

## Política contínua delegada

O owner pode autorizar uma política permanente e revogável com a confirmação
`ATIVAR AUTOPILOTO TELEGRAM`. Essa autorização não aprova qualquer texto: ela
permite ao worker selecionar somente pacotes comerciais que já passaram pelas
validações determinísticas da fábrica.

Limites iniciais:

- destino fixo: `@achadosbaratosBrasil`;
- operação sem data final, até `PAUSAR AUTOPILOTO TELEGRAM`;
- no máximo 48 reservas por dia, renovadas diariamente no fuso de São Paulo;
- intervalo mínimo de 30 minutos, equivalente a no máximo duas tentativas por hora;
- nesta versão, somente pacotes completos do Mercado Livre;
- URL afiliada, preço confirmado, imagem pública, hash do conteúdo, hash da
  validação, validade e chave de idempotência obrigatórios;
- se não houver pacote elegível, nenhum post é criado ou improvisado;
- a fila manual tem prioridade sobre a delegação automática;
- cada ciclo do worker reserva e processa no máximo uma publicação.

O teto de 48 é diário, não vitalício. Ao mudar o dia, os contadores são zerados e
a operação continua. Ele serve como proteção inicial contra rajadas, repetição e
banimento enquanto ainda não existem métricas suficientes para escolher uma
cadência maior com segurança.

## Automação local

A automação Codex `Publicar ofertas Telegram` acorda o worker a cada 30 minutos.
Ela não fabrica links afiliados, não usa provider pago e termina silenciosamente
quando a fila não possui um pacote válido. Pesquisa e geração oficial de links
monetizados continuam etapas independentes: a operação só distribui o que pode
ser comprovado.
