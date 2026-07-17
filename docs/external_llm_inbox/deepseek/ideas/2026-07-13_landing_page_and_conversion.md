# Idea Proposal: Landing Page & Conversion Optimization Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que projeta, gera e otimiza landing pages para ofertas de afiliado, produtos proprios e captura de leads — com variantes de headline, CTA, layout e prova social, testadas em MOCK antes de qualquer publicacao real.

## Why It Fits The AI Content Factory

A AGENTS.md menciona Next Step #6: "Landing page e compliance — dominio, privacidade, termos, disclosure e eventos de conversao". Hoje a fabrica produz conteudo que leva a lugar nenhum — nao existe uma landing page para onde o clique do Telegram ou do video deve ir. O Affiliate Deals Department gera ofertas com links de afiliado, mas nao ha uma pagina intermediaria da marca que agregue valor, capture dados e aumente conversao.

## User Value

- Shin nao precisa criar landing pages manualmente — o departamento gera HTML estatico + copy otimizado para cada oferta.
- Teste A/B de headline e CTA: 3 variantes sao geradas, Shin escolhe qual publicar.
- Pagina de obrigado (pos-compra) e pagina de lead magnet sao geradas junto com a landing page principal.
- Todas as paginas ja saem com: disclosure de afiliado, politica de privacidade, opt-out e tag de analytics MOCK.

## Proposed Workflow

```
ReceivedTask{page_type, offer, target_audience, conversion_goal, brand_assets}
  -> Pipeline stages (action=CREATE_LP):
     1. BRIEF_ASSEMBLY             (consolidar oferta, publico, objetivo, tom de voz)
     2. HEADLINE_VARIATION         (gerar 3 headlines + subheadlines com diferentes enfoques)
     3. COPY_WRITING               (escrever corpo: dor, solucao, beneficios, prova social, CTA)
     4. COMPLIANCE_CHECK           (disclosure afiliado, LGPD, termos, nao enganoso)
     5. LAYOUT_GENERATION          (montar HTML responsivo com secoes: hero, beneficios, depoimento, FAQ, CTA)
     6. VARIANT_CREATION           (gerar 3 variantes de layout: A=longa, B=curta, C=video)
     7. PAGE_PACKAGE               (consolidar: HTML, assets, analytics setup, AB_test_plan)
```

## Required Employees

1. **LandingPageOptimizerEmployee** — herda ProductionEmployee, gerencia pipeline de LP.
   - Hooks: `_check_reject()` rejeita se `page_type` desconhecido ou `offer` vazio; `_build_pipeline()` monta LandingPagePipeline; `_build_output_from_stages()` extrai `page_package`.

2. **ConversionCopyWriter** — helper interno especializado em copy de conversao (headline, sub, bullet points, PS, CTA).

## Required Capabilities

Todas ja existentes:
- `TEXT_GENERATION` (headlines, copy, FAQ, depoimentos)
- `IMAGE_EDITING` (otimizar imagens para web, gerar alt text)
- `DOCUMENT_GENERATION` (pagina HTML, relatorio)
- `STORAGE` (salvar paginas geradas)
- `SOCIAL_MEDIA` (meta tags para compartilhamento: OG tags)

## Risks And Compliance

- **Disclosure de afiliado obrigatorio**: toda pagina de oferta de afiliado deve conter disclosure visivel (nao no rodape, mas antes do CTA). Herdado do ComplianceCheck do Affiliate Deals Department.
- **LGPD**: formularios de lead capture devem ter checkbox de consentimento e link para politica de privacidade.
- **Nao enganoso**: headlines nao podem prometer resultados especificos ("ganhe R$ 10000 por mes") sem qualificacao ("resultados variam").
- **Direitos autorais**: imagens e depoimentos gerados devem ser marcados como "simulados" ou "ilustrativos".
- **Dominio proprio**: as paginas devem usar subdominio da marca, nunca enganar o usuario sobre qual site esta visitando.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. LandingPageOptimizerEmployee com hooks padrao.
3. Snapshot `LandingPageSnapshot` (pages_created, variants_per_page, compliance_passed, ab_tests_planned).
4. 4 tipos de pagina: "ofertas" (afiliado), "lead_magnet" (captura de email), "vendas" (produto), "obrigado" (pos-conversao).
5. Template HTML responsivo basico gerado como string (sem framework externo).
6. Demo com 30+ assertions: brief, headline variacao, copy, compliance, layout, variantes, pacote final.
7. Saida: 3 arquivos HTML (variantes A, B, C) + 1 README com plano de A/B testing.

## Later Integrations

- Deploy automatico via Cloudflare Pages ou Vercel
- Formulario de lead capture com webhook para Email Marketing Department
- Google Analytics 4 / Tag Manager tracking
- Heatmap (Hotjar, Microsoft Clarity) setup basico
- Teste A/B real com divisao de trafego (Google Optimize ou Vercel Edge Functions)

## Open Questions For Shin/Codex

1. As landing pages devem ser servidas em qual dominio/subdominio? (ex: ofertas.achadosbaratos.com.br)
2. Shin quer integracao com formulario de lead capture desde o MVP ou apenas pagina estatica?
3. Os depoimentos e provas sociais devem ser gerados (MOCK) ou Shin fornece depoimentos reais?
4. Deve existir uma landing page para cada oferta de afiliado ou apenas para ofertas selecionadas pelo Product Research / Creative Review?
5. A responsividade deve suportar mobile-first desde o MVP?

## Sources

- Landing page best practices: https://unbounce.com/landing-page-articles/
- LGPD para formularios: https://www.gov.br/cidadania/pt-br/composicao/orgaos/secretaria-nacional-do-consumidor/protecao-de-dados-pessoais
- FTC affiliate disclosure guidelines: https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
- OG tags spec: https://ogp.me/
