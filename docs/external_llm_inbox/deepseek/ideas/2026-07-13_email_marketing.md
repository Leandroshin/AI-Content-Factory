# Idea Proposal: Email Marketing Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento que constroi listas de email segmentadas, gera sequencias de nutrição (bem-vindo, oferta, abandono, reengajamento), compõe newsletters a partir de conteudo da fabrica e produz artefatos prontos para envio com copy, assunto e pré-header por segmento.

## Why It Fits The AI Content Factory

A capability `EMAIL` ja existe no sistema mas nenhum departamento a utiliza. Email marketing e um canal de alto ROI, complementar ao Telegram e redes sociais. A fabrica ja gera conteudo (scripts, ofertas de afiliado, videos, imagens) que pode ser reaproveitado como conteudo de email. Alem disso, email permite segmentacao e automacao que nao sao possiveis no Telegram.

## User Value

- Shin pode converter visitantes do site/ landing page em uma lista de emails.
- Cada novo produto ou oferta de afiliado gera automaticamente um email promocional.
- Sequencias automatizadas: novo assinante recebe 3 emails de boas-vindas, depois 1 email semanal de ofertas.
- Shin nao precisa escrever email manualmente — o departamento reutiliza o copy do ScriptDepartment + CTA.

## Proposed Workflow

```
ReceivedTask{email_type, target_segment, content_source, schedule}
  -> Pipeline stages:
     1. SEGMENT_IDENTIFICATION    (identificar segmento: novos, quentes, inativos, afiliados)
     2. CONTENT_ASSEMBLY          (montar corpo do email: headline, copy, CTA, ps, footer)
     3. SUBJECT_LINE_GENERATION   (gerar 3 opcoes de assunto + pre-header)
     4. COMPLIANCE_CHECK          (disclosure de afiliado, opt-out, lei LGPD, nao enganoso)
     5. FORMAT_RENDER             (renderizar versao texto simples + HTML basico)
     6. QUEUE                     (persistir na fila de envio com schedule)
     7. CAMPAIGN_SUMMARY          (resumo: segmento, email_type, schedule_time, variantes)
```

## Required Employees

1. **EmailMarketerEmployee** — herda ProductionEmployee, gerencia pipeline de email marketing.
   - Hooks: `_check_reject()` rejeita se segmento desconhecido ou email_type invalido; `_build_pipeline()` monta EmailMarketingPipeline; `_build_output_from_stages()` extrai `campaign_summary` e `email_variants`.

2. (Futuro) **EmailTemplateRenderer** — helper que monta HTML responsivo usando templates inline.

## Required Capabilities

Todas ja existentes:
- `EMAIL` (ja declarada em core/tools/capabilities.py)
- `TEXT_GENERATION` (assunto, pre-header, copy)
- `DOCUMENT_GENERATION` (versao texto e HTML)
- `STORAGE` (arquivar campanhas enviadas)
- `DATABASE` (gerenciar lista de segmentos)
- `SOCIAL_MEDIA` (cross-promocao: "receba isso por email")

## Risks And Compliance

- **LGPD / Lei Geral de Protecao de Dados**: toda lista de email precisa de consentimento explicito e opt-out visivel. O departamento nunca deve gerar emails para listas compradas ou raspadas.
- **Anti-spam**: o pipeline de compliance deve verificar: opt-out link presente, remetente identificado, assunto nao enganoso, frequencia adequada.
- **Disclosure de afiliado**: emails promocionais de afiliados precisam de disclosure claro, herdado do Affiliate Deals Department.
- **Reputacao de dominio**: enviar muitos emails sem aquecimento de dominio pode prejudicar a entregabilidade. O MVP deve recomendar volume inicial baixo.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. EmailMarketerEmployee com hooks padrao.
3. Snapshot `EmailMarketingSnapshot` (campaigns_created, emails_queued, segments_active, compliance_passed).
4. 3 templates de sequencia pre-definidos: boas-vindas (3 emails), oferta semanal (1 email), promocao sazonal (1 email).
5. Demo com 25+ assertions: segmentacao, montagem de conteudo, assunto, compliance, formatos, fila e resumo.
6. Segmentos MOCK: "novos_assinantes", "compradores_recentes", "inativos_30d", "afiliados_top".

## Later Integrations

- Mailchimp API (envio real, listas, templates)
- SendGrid / Twilio Email API
- AWS SES (para envio transacional)
- Resend (API moderna de email)
- Integracao com Hotmart (gatilho de compra -> email de confirmacao + upsell)
- Integracao com formularios de landing page (captura de lead -> sequencia de boas-vindas)

## Open Questions For Shin/Codex

1. O email deve ser enviado por um adapter existente ou por um novo EmailAdapter com MOCK/REAL?
2. As listas de email devem ser gerenciadas internamente (no PersistenceRuntime) ou integradas a um serviço externo?
3. Shin quer que o departamento gere emails a partir de conteudo existente automaticamente ou apenas sob demanda?
4. Qual o limite de frequencia aceitavel para a lista inicial (1x por semana? 2x?)?

## Sources

- Mailchimp API: https://mailchimp.com/developer/marketing/api/
- SendGrid API: https://docs.sendgrid.com/api-reference
- LGPD simplificada para marketers: https://www.gov.br/cidadania/pt-br/composicao/orgaos/secretaria-nacional-do-consumidor/protecao-de-dados-pessoais
- Resend API: https://resend.com/docs/api-reference/introduction
