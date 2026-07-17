# Auditoria Codex das propostas DeepSeek

Data: 2026-07-14  
Status: analise concluida; nenhuma proposta foi integrada automaticamente.

## Veredito executivo

O material esta bem mais organizado do que um brainstorm comum e vale ser preservado. Entretanto, a premissa de que todas as propostas representam funcoes inexistentes esta incorreta. Varias ideias repetem parcialmente componentes ja comprovados na fabrica. Criar um departamento para cada documento agora aumentaria manutencao sem aumentar receita.

A melhor oportunidade nova e alinhada a vida real de Leandro e o **Diagnostico e Transformacao de Negocios Locais**. O melhor produto isolado para explorar depois e o **Menu SaaS**, mas primeiro como um pequeno produto validavel, nao como a arquitetura completa proposta.

## Classificacao

| Proposta | Veredito | Motivo |
|---|---|---|
| Diagnostico e Transformacao de Negocios Locais | Prioridade alta, apos o fluxo atual | Usa a presenca de Leandro em negocios locais e pode gerar uma proposta paga antes de construir software. Deve nascer como workflow, nao nove departamentos. |
| Menu SaaS | Experimento comercial promissor | Tem problema claro, demonstracao visual e recorrencia. Precisa validar demanda com 3 a 5 clientes antes de construir billing, multiunidade e integracoes. |
| Business Intelligence | Prioridade estrutural, mas bloqueada por dados | Coincide com o roadmap oficial de metricas de negocio. Implementar depois que cliques, vendas, comissao e custo reais existirem. |
| Compliance & Rights | Ampliar componentes existentes | Affiliate compliance, Creative Review, Editorial Quality e HITL ja cobrem partes importantes. O valor esta em um gate transversal, nao em duplicar tudo. |
| Publishing & Scheduling / Social Distribution | Consolidar em um unico fluxo | Telegram real e publishing plans ja existem. Falta calendario e adapters oficiais de outras plataformas. Nao devem virar dois departamentos sobrepostos. |
| Content Calendar | Futuro proximo | Util quando houver cadencia real em mais de um canal. Hoje seria um calendario quase vazio. |
| A/B Testing & Optimization | Esperar metricas | Sem volume, variantes e janela de observacao reais, o resultado seria apenas simulacao. |
| Community Engagement | Esperar audiencia | Boa ideia, mas responder automaticamente antes de existir audiencia e APIs oficiais nao gera valor agora. |
| Email Marketing | Esperar lista e oferta validada | Exige consentimento, opt-out, provider e uma lista real. Nao deve preceder a primeira oferta comprovada. |
| Landing Page & Conversion | Reusar stack de sites | A fabrica ja possui dashboard, Sites e compliance planejado. Deve ser um workflow/template de entrega, nao necessariamente departamento novo. |
| SEO & Organic Discovery | Incorporar como etapa | Cabe nos briefings de Script, Strategy Intelligence e paginas. Um departamento inteiro e prematuro. |
| Trend & Viral Intelligence | Duplicada em grande parte | Gaming News Desk, Audience Growth Planner, Strategy Intelligence e radares diarios ja exercem essa funcao com fontes e gates. |
| Thumbnail & Visual Identity | Especializacao, nao novo departamento | Image Department ja produz thumbnails; Creative Review ja valida formula, contraste e riscos. Falta template de marca, que cabe como perfil/hook. |
| Translation & Localization | Capacidade existente, execucao incompleta | `TRANSLATION` ja existe no CapabilityRegistry e e solicitada por Script/Video. Falta adapter/provider e validacao cultural. |
| Content Repurposing | Parcialmente existente | O Video Department ja tem `LongFormRepurposingValidator`. Falta pipeline produtivo completo; deve ampliar Video/Content Factory sem cortar videos arbitrariamente. |
| Podcast & Audio | Extensao do Audio Department | Audio Department, Kokoro e modelos de audio ja existem. O novo valor seria empacotamento RSS/show notes, nao outro departamento inteiro. |
| Canais de animacao, Biblia e ciencia | Backlog editorial | Sao apostas de conteudo, nao infraestrutura. Escolher no maximo uma depois de o canal atual publicar e medir. |
| Curso de exercicios | Nao priorizar | Envolve saude, seguranca, credenciais e alto risco de recomendacao inadequada. Nao e uma primeira fonte de receita responsavel. |

## Correcao das principais premissas

1. **Kangu nao esta integrado.** O projeto tem webhook Hotmart. A proposta Menu SaaS cita "Hotmart/Kangu integrado", mas nao ha implementacao Kangu no repositorio.
2. **Trend intelligence ja existe.** Gaming News Desk, Audience Growth Planner e Strategy Intelligence cobrem descoberta, deduplicacao, fontes e decisao `no_news`.
3. **Thumbnail nao esta ausente.** Image Department suporta `thumbnail`; Creative Review possui validacao especifica; Video Department tem `thumbnail_awareness`.
4. **Traducao ja e capability.** A lacuna e o executor/provider real e seu controle de qualidade.
5. **Repurposing ja tem contrato editorial.** O que falta e transformar o contrato em pipeline e employee produtivo completo.
6. **Receita projetada nao e evidencia.** MRR, conversoes, CPL e cronogramas do Menu SaaS sao hipoteses. Devem aparecer como metas de experimento, nunca como previsoes.
7. **Publicar alteracoes de preco automaticamente e arriscado.** No Menu SaaS, preco, disponibilidade e alergênicos devem permanecer sob aprovacao do cliente, mesmo com automacao.

## Recomendacao para o Menu SaaS

Nao comecar pelos oito stages, billing, dominio por cliente, iFood e WhatsApp API. O primeiro teste deve ser menor:

1. Escolher um comercio conhecido e obter autorizacao.
2. Receber cardapio real, fotos e precos.
3. Criar um prototipo publico responsivo e um QR code local.
4. Deixar alteracoes manuais e medir se o dono e os clientes acham util.
5. Perguntar quanto pagariam e quais atualizacoes mais solicitam.
6. Somente apos 3 a 5 validacoes decidir entre servico operado, produto SaaS ou descarte.

O prototipo do DeepSeek e util para conversa, mas ainda usa dados ficticios e nao prova demanda, pagamento, suporte ou operacao recorrente.

## Recomendacao para negocios locais

Este e o melhor encaixe com a rotina de extintores porque Leandro ja entra em estabelecimentos e observa processos reais. O MVP nao precisa construir nada para o cliente:

`nome + cidade + consentimento + pesquisa publica + conversa/transcricao -> diagnostico -> perguntas -> 3 alternativas -> prototipo conceitual -> proposta`.

O primeiro teste deve usar caso ficticio ou autorizado. A fabrica deve recomendar inclusive "nao construir software" quando uma configuracao simples do sistema atual resolver.

## Ordem recomendada

1. Terminar o ciclo real da fabrica atual: roteiro -> pre-producao -> providers aprovados -> revisao -> publicacao manual/oficial -> metricas.
2. Colocar um produto/oferta real no fluxo e medir o primeiro resultado.
3. Criar metricas de negocio e o ciclo de aprendizado.
4. Prototipar Diagnostico de Negocios Locais com um caso autorizado.
5. Validar Menu SaaS com um comercio, sem billing automatico.
6. Consolidar compliance e publishing como gates transversais.
7. Somente entao escolher um novo canal editorial ou produto de conteudo.

## Decisao de arquitetura

- Nem toda funcao precisa virar `ProductionEmployee`.
- Pesquisa, planejamento, compliance e aprovacao podem ser workflows/gates usando departamentos existentes.
- Novos departamentos so se justificam quando possuem estado, pipeline e metricas proprias que nao cabem nos atuais.
- As propostas continuam na inbox ate uma decisao explicita do owner e revisao Codex.
