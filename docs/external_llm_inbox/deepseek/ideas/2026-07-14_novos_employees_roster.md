# Roster: Novos Employees para a Fábrica

## Critério de seleção
Ideias para **employees/departamentos que ainda não existem** nem estão cobertos por propostas anteriores. Cada um segue o padrão `ProductionEmployee` → departamento concreto.

---

### 1. Publishing & Scheduling Employee
**One-liner:** Publica o conteúdo pronto no melhor horário para cada plataforma, com formato correto e scheduling.

**Por que não existe:** Temos TelegramAdapter e o conteúdo é produzido, mas a publicação em si não tem um dono — cada plataforma tem regras, limites, formatos.

**O que faz:**
- Recebe o output pronto (vídeo, áudio, texto, imagem)
- Escolhe plataforma + horário por regras determinísticas (ex: TikTok 18h, YouTube 11h)
- Formata legenda, hashtags, menções por plataforma
- Chama o adapter correto (TelegramAdapter hoje; YouTube, Instagram, TikTok no futuro)
- Registra no calendário o que foi publicado e quando

**Capabilities necessárias:** `PUBLISHING`, `SCHEDULING` (novas), mais as existentes `SOCIAL_MEDIA`, `TEXT_GENERATION`

**Riscos:** Publicação real é gateada por HITL + Budget Guard. MOCK sempre publica no log apenas.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 2. Compliance & Rights Employee
**One-liner:** Antes de qualquer publicação, verifica licenças, direitos autorais, LGPD, disclosure de afiliado e termos de uso.

**Por que não existe:** Compliance hoje é parcial dentro do Affiliate Deals (só disclosure). Não há um guardião transversal.

**O que faz:**
- Recebe o pacote pronto (texto + áudio + imagem + vídeo)
- Verifica: música tem licença? Imagem é própria/domínio público? Disclosure de afiliado está visível? LGPD ok?
- Emite parecer: `approved`, `needs_fix` (com instruções), `blocked`
- Bloqueia publicação se `blocked`
- Audit trail de todas as verificações

**Capabilities necessárias:** `COPYRIGHT_CHECK`, `COMPLIANCE_AUDIT` (novas)

**Riscos:** Não substitui advogado. Regras determinísticas + checklist. O que exigir approval humano fica explícito.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 3. Trend & Viral Intelligence Employee
**One-liner:** Alimenta a fábrica com trending topics, hashtags em alta e oportunidades virais antes que esfriem.

**Por que não existe:** Strategy Intelligence foca em padrões de mercado/afiliados. Não há ninguém olhando "o que está bombando agora".

**O que faz:**
- Consulta fontes determinísticas: trending do YouTube/TikTok, Google Trends, X trending topics
- Filtra por nicho relevante (games, ofertas, tecnologia)
- Produz relatório compacto: `topico`, `plataforma`, `volume_estimado`, `janela_oportunidade`
- Entrega ao Script Department como briefing de conteúdo

**Capabilities necessárias:** `TREND_ANALYSIS`, `WEB_RESEARCH` (novas)

**Riscos:** MOCK com dados sintéticos de exemplos reais. REAL exigiria scraping ou APIs pagas.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 4. Translation & Localization Employee
**One-liner:** Traduz e adapta roteiros, legendas e descrições para outros idiomas, mantendo tom e contexto brasileiro.

**Por que não existe:** Todo conteúdo é PT-BR. Não há rota para internacionalização.

**O que faz:**
- Recebe script/texto + formato de saída (legenda, descrição, roteiro dublado)
- Traduz mantendo tom, CTA, hooks culturalmente adaptados
- Gera SRT para legendas, roteiro alternativo para dublagem
- Sinaliza se precisa de revisão humana (expressões regionais, trocadilhos)

**Capabilities necessárias:** `TRANSLATION`, `LOCALIZATION` (novas)

**Riscos:** Qualidade de tradução MOCK é placeholder; REAL exigiria provider de tradução (Google/DeepL) com budget.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 5. Thumbnail & Visual Identity Employee
**One-liner:** Cria thumbnails consistentes por canal/série, com identidade visual, paleta e texto legível.

**Por que não existe:** Image Department faz capas genéricas. Thumbnail de YouTube/Shorts exige técnica específica (contraste, texto grande, expressão, branding).

**O que faz:**
- Recebe metadados do vídeo: título, cena-chave, canal, série
- Aplica template do canal (cores, fontes, logo)
- Gera thumbnail 1280x720 com texto destacado
- Valida: contraste, tamanho de texto, excesso de elementos

**Capabilities necessárias:** `THUMBNAIL_DESIGN` (nova), reusa `IMAGE_EDITING`

**Riscos:** MOCK gera imagem placeholder com texto. REAL exigiria ImageGeneration provider ou template HTML->PNG.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 6. Community Engagement Employee
**One-liner:** Monitora, responde e engaja seguidores nos comentários, mantendo tom da marca e escalando crises.

**Por que não existe:** Ninguém na fábrica fala com a audiência.

**O que faz:**
- Recebe notificações de novos comentários (MOCK: lista simulada)
- Classifica: pergunta, elogio, crítica, spam, crise
- Responde com template do canal + personalização
- Escala para HITL se for crítica/crise
- Relatório semanal: sentimentos, perguntas frequentes, sugestões

**Capabilities necessárias:** `COMMUNITY_MANAGEMENT`, `SENTIMENT_ANALYSIS` (novas)

**Riscos:** Respostas automáticas exigem supervisão. Spam e crises podem exigir humano rapidamente.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 7. A/B Testing & Optimization Employee
**One-liner:** Testa variações de hook, thumbnail, CTA e horário para maximizar desempenho.

**Por que não existe:** Não há ciclo de aprendizado sobre o que funciona melhor.

**O que faz:**
- Recebe conteúdo base + N variantes (hooks, thumbnails, CTAs)
- Agenda publicação sequencial das variantes
- Coleta métricas após 24h (views, CTR, engagement)
- Recomenda vencedora com base em critérios determinísticos
- Alimenta Organizational Memory com aprendizado

**Capabilities necessárias:** `A_B_TESTING`, `PERFORMANCE_ANALYSIS` (novas)

**Riscos:** MOCK simula resultados. REAL exige plataforma real + tempo de espera.

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

### 8. Content Repurposing Employee
**One-liner:** Transforma 1 conteúdo longo em N derivados (Short, quote, carrossel, áudio, tweet) sem refazer do zero.

**Por que não existe:** Hoje cada departamento produz do zero. Não há reaproveitamento inteligente.

**O que faz:**
- Recebe asset raiz (ex: script longo + áudio + vídeo)
- Identifica trechos destacáveis (hooks, melhores falas, momentos)
- Gera: Short vertical, quote card, tweet thread, carrossel de slides, clipe de áudio
- Mantém proveniência: todo derivado aponta para o original

**Capabilities necessárias:** `CONTENT_EXCERPTION`, `FORMAT_ADAPTATION` (novas)

**Riscos:** Qualidade dos trechos é subjetiva. MOCK usa regras de POSIÇÃO (primeiros 15s, melhor trecho central).

**Status:** PROPOSTA - NAO IMPLEMENTADA

---

## Meta-análise (Camada 3 — Auto-crítica)

**O que posso ter deixado passar:**
- Algumas ideias podem exigir capabilities que não existem nem como conceito no CapabilityRegistry — teria que criar do zero
- A sobreposição com ideias de 2026-07-13 existe (ex: Content Repurposing já tinha ideia no INDEX.md) — marquei a que conflita
- Não calculei custo REAL de providers necessários (tradução, análise de sentimento, trends API)
- A ordem de implementação ideal depende de Shin — qual dor é maior agora?

**O que só Shin/Codex decide:**
- Qual ideia merece virar departamento primeiro
- Se alguma capability nova cabe no `CapabilityRegistry` ou é específica demais
- Se a arquitetura `ProductionEmployee` serve para todos ou alguns precisam de adaptação
- Budget para APIs reais de tradução/trends/sentimento

## Caminho crítico (Camada 4)

Se fosse implementar em ordem de dependência:
1. **Compliance & Rights** — barreira de segurança antes de qualquer publicação real
2. **Publishing & Scheduling** — desbloqueia publicação organizada (já temos TelegramAdapter)
3. **Trend & Viral Intelligence** — alimenta o funil de produção com o que está quente
4. **Thumbnail & Visual Identity** — melhora taxa de clique sem custo de provider
5. **A/B Testing** — precisa de Publishing + Métricas para funcionar
6. **Translation** — conteúdo em PT-BR primeiro; internacionalização é escala
7. **Content Repurposing** — precisa de métrica provada antes de valer o esforço
8. **Community Engagement** — depende de ter audiência engajada primeiro
