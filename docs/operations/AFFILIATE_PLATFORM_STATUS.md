# Status das plataformas de afiliados

Atualizado em 2026-07-14.

Atualizacao operacional em 2026-07-14: a fabrica agora possui um scorecard
deterministico em `core/departments/affiliate_deals/platforms.py` para decidir
qual plataforma entra primeiro em Product Research. A regra central e: comissao
alta ajuda, mas nao supera falta de cadastro, ausencia de link afiliado,
restricao de trafego, friccao de saque/pagamento ou falta de evidencia da oferta.

Atualizacao sem verba em 2026-07-14: etapas que dependem de saldo/cartao, PayPal,
trafego pago, provider pago ou verificacao financeira ficam pausadas. A fabrica
continua trabalhando em tarefas gratuitas: pesquisa, captura de evidencias,
analise de pagina de venda, organizacao de ofertas, copy em rascunho, aprendizado
por transcricoes e preparacao de painel.

## Amazon Brasil

- Conta do Programa de Associados criada.
- ID de Associado: `achadosba0dae-20`.
- Canal cadastrado: `https://www.instagram.com/achadosbaratosbr2/`.
- Central liberada para gerar links manuais.
- Informacoes fiscais e de recebimento continuam pendentes.
- A Amazon revisara o cadastro depois que um link originar o primeiro pedido.
- Sem pedido originado em 180 dias, a Amazon informa que podera revogar o cadastro.
- AWS nao e o portal de onboarding do Programa de Associados.
- A API de catalogo/Creators API e posterior e nao bloqueia links manuais.

## Mercado Livre

- Aplicativo `Achados Baratos BR` criado.
- Client ID: `7037577034666600`.
- Credencial secreta guardada somente em `secrets/mercado_livre.env`, ignorado pelo Git.
- Fluxo ativo: `Client Credentials`; Authorization Code e Refresh Token desativados.
- Redirect HTTPS: painel privado da fabrica.
- O Client ID e o Client Secret identificam o aplicativo, mas nao substituem o access token OAuth autorizado pelo owner.
- `MercadoLivreCatalogAdapter` esta implementado em modo MOCK/REAL somente leitura para item, busca, multiget e categoria.
- O modo REAL permanece bloqueado ate existir access token OAuth, aprovacao explicita e limite de requests.
- Mensagens, publicacao, publicidade, faturamento, metricas, promocoes, vendas e envios nao serao usados pelo runtime.
- A tela registrou `Leitura e escrita` em comunicacoes pre/pos-venda porque foi a opcao escolhida manualmente para concluir o formulario. O runtime deve bloquear toda escrita e essa permissao deve ser reduzida quando o portal permitir edicao segura.
- Demo de seguranca: 36 verificacoes confirmam GET allowlisted, token no header, redacao de secrets, limites e bloqueio pre-HTTP de toda escrita.

## Regra multiloja

O canal pode reunir lojas diferentes. Cada oferta precisa de evidencia, link afiliado pertencente ao proprietario, preco e validade conferidos, disclosure e aprovacao humana. Links de grupos de terceiros servem como referencia, mas nao transferem comissao para nossa conta.

## Nova estrategia de portfolio

Amazon e Mercado Livre continuam ativos, mas deixam de ser a aposta principal para trafego pago. Eles servem para:

- validar o fluxo de coleta, analise, criativo, link e publicacao;
- produzir achados organicos de utilidade para Telegram e outros canais permitidos;
- medir cliques e primeiras comissoes sem presumir que a economia sera escalavel.

Prioridade de onboarding sem verba:

1. **Digistore24** — conta criada; ID publico deve ser migrado para `smartdealradar`; marketplace internacional e link promocional direto; primeiro candidato para uma oferta digital controlada.
2. **Braip** — conta criada e token local registrado em `secrets/braip.env`; alternativa brasileira com produtos digitais e fisicos; analisar cada termo de afiliacao e material autorizado antes de qualquer producao.
3. **ClickBank** — manter no radar, mas iniciar somente aceitando a exigencia de distribuicao de clientes antes do primeiro pagamento.
4. **MediaScalers e MaxWeb** — enviar candidatura depois de preparar perfil, canais, metodo de trafego e politica de compliance.
5. **BuyGoods** — candidatura posterior; o site atual informa revisao manual e preferencia por historico ou indicacao.

Uma plataforma nao entra em producao apenas por pagar comissao alta. O Product Research deve registrar: modelo CPA/revshare, valor liquido por venda, cookie/atribuicao, saque minimo, prazo e taxa de pagamento, moeda, reembolso/chargeback, paises aceitos, canais permitidos, criativos autorizados, restricoes de marca e evidencia independente da oferta.

## Scorecard operacional

O scorecard inicial classifica:

- **Amazon Brasil** como `start_now` para teste organico e utilidade de audiencia,
  nao como motor principal de trafego pago.
- **Digistore24** como `prepare_next`: conta criada, mas ainda depende de
  pagamento/saque e uma oferta revisada.
- **Braip** como plataforma pronta para pesquisa de oferta: token salvo fora do
  Git, mas sem adapter produtivo ate confirmarmos endpoints oficiais, permissoes
  minimas e uma oferta com termos aprovados.
- **Mercado Livre** como `blocked` ate existir atribuicao/link afiliado oficial
  ou link proprio fornecido manualmente pelo owner.
- **MaxWeb/MediaScalers/BuyGoods** como redes posteriores, porque exigem
  candidatura, historico, regras de trafego e perfil de compliance mais maduro.

Prova tecnica: `demo_affiliate_platform_scorecard.py`.

## Digistore24

- Conta de associado criada.
- ID publico atual: `achadosbaratosbr`; ID recomendado para internacional:
  `smartdealradar`.
- PayPal/pagamento pausado ate existir saldo/cartao para a verificacao de USD
  1,00 ou equivalente.
- Uso inicial recomendado: escolher produtos no Marketplace, copiar o link
  promocional oficial e colar no painel da fabrica para analise.
- API ainda nao deve ser usada para automacao produtiva. A documentacao publica
  precisa ser revisada em ambiente logado e so entra se houver endpoints uteis
  para leitura/metricas sem elevar risco de conta.

## Braip

- Conta criada.
- Token de API salvo somente em `secrets/braip.env`, ignorado pelo Git.
- Uso inicial recomendado: consultar ofertas no portal, pegar link oficial de
  afiliado e testar no fluxo de Produto/Oportunidade.
- Qualquer adapter futuro deve nascer somente leitura por padrao: listar
  produtos/ofertas, ler status permitido e preparar links autorizados. Saque,
  banco virtual, alteracao de produto, checkout, compra, reembolso e acoes
  financeiras ficam fora do runtime.

## Modo sem verba

Enquanto o owner nao liberar orçamento, os funcionarios podem:

- pesquisar marketplaces e salvar paginas de venda;
- registrar comissao, preco, regras de reembolso e canais permitidos;
- preparar rascunhos de copy, criativo e funil;
- alimentar o painel com oportunidades pendentes de aprovacao;
- aprender com transcricoes e transformar boas ideias em propostas isoladas.

Enquanto o modo sem verba estiver ativo, os funcionarios nao podem:

- concluir verificacoes que cobrem cartao/PayPal;
- comprar trafego;
- chamar provider pago de audio, imagem ou video;
- publicar automaticamente;
- usar link afiliado de terceiros como se fosse do projeto;
- criar promessa de receita baseada em print ou video de YouTube.

Prova tecnica: `demo_no_spend_affiliate_plan.py`.
