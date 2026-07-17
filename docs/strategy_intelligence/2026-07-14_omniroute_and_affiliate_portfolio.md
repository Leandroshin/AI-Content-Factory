# OmniRoute, sincronizacao visual e portfolio de afiliados

Atualizado em 2026-07-14.

## Decisao sobre OmniRoute

O OmniRoute `3.8.48` foi instalado de forma isolada em `C:\Users\Shin\Tools\OmniRoute`, sem dependencia no `core/` e sem alterar Codex ou OpenCode. O smoke local confirmou:

- Node `24.15.0` suportado;
- SQLite nativo reparado;
- servidor limitado a `127.0.0.1:20128`;
- dashboard local respondendo;
- API e health recusando chamadas sem autenticacao;
- nenhum provider, conta ou segredo da fabrica conectado;
- nenhuma chamada de modelo ou custo realizado.

O gateway esta **aprovado apenas para avaliacao e futuro roteamento de providers oficiais**. Ele nao cria tokens. Cada modelo continua sujeito a quota, disponibilidade, politica e preco do provider de origem.

O provider `OpenCode Free` usado no tutorial nao foi ativado. O catalogo da propria versao auditada marca os modelos keyless mostrados no video com `tos: avoid`; isso contradiz a ideia de uso gratuito irrestrito e impede integracao de producao.

Regras permanentes:

1. Somente API keys ou OAuth documentados e permitidos pelo provider.
2. Proibidos cookies de sessao extraidos, rotacao anti-ban, pools de contas e providers classificados como `avoid`.
3. Loopback, autenticacao, storage isolado, budget e auditoria obrigatorios.
4. OmniRoute pode rotear texto/codigo, mas nao substitui voz, imagem ou video profissional.
5. Integracao com a fabrica so vira adapter depois de um provider oficial passar por custo, privacidade, licenca, qualidade e smoke controlado.

## Padrao editorial aprendido

Nome interno: **Narration-to-Evidence Visual Sync**.

Cada frase do roteiro vira um beat com tempo, intencao e evidencia visual. Quando a narracao citar uma ferramenta, o video mostra a pagina, o comando, o resultado ou a interface correspondente. Quando citar um produto, mostra o produto real. Quando citar uma metrica, mostra a fonte ou grafico legivel. B-roll generico serve apenas como transicao ou contexto.

Gate de qualidade:

- reprovar slideshow de imagens sem relacao direta com a fala;
- reprovar captura sem URL/proveniencia em alegacoes factuais;
- trocar o enquadramento ou elemento visual em ate seis segundos quando houver valor editorial;
- esconder IDs, tokens, emails, dados pessoais e detalhes tecnicos sem utilidade publica;
- revisar contact sheet, overflow, oclusao e preview antes de entregar.

O contrato `EditorialBeat` agora registra `visual_purpose` e `matches_narration`; o validador bloqueia beats marcados como incompatíveis.

## Portfolio de afiliados

O video sobre plataformas e uma fonte de hipotese, nao uma ordem. A experiencia do criador favorece trafego pago internacional e pode nao refletir nossa fase sem verba, nossos canais ou nossa capacidade de aprovacao.

Direcao adotada:

- trilho principal: ofertas digitais/CPA com economia suficiente por venda;
- trilho complementar: Amazon, Mercado Livre e Shopee para organico, utilidade de audiencia e aprendizado operacional;
- primeiro teste: uma oferta acessivel na Digistore24, sem trafego pago;
- expansao: Braip e ClickBank; depois candidaturas em redes com revisao manual;
- nenhuma escala antes de medir cliques, checkout, venda aprovada, reembolso, comissao liquida e custo.

Essa direcao preserva o que ja foi construido e evita depender de uma unica plataforma ou promessa de renda.
