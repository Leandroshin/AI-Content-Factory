# Idea Proposal: Science Curiosity Shorts Channel

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um canal de shorts/videos curtos (30-90s) que explicam curiosidades cientificas com animacao visual, narracao envolvente e musica — cada video responde uma pergunta como "Por que o ceu e azul?" ou "Como funciona um ima?" — produzido em serie pela fabrica, 1 video por dia.

## Why It Fits The AI Content Factory

Conteudo educativo e um dos maiores motores de crescimento no YouTube Shorts e Instagram Reels. Cada video e pequeno (produto rapido), o roteiro e deterministico (fatos cientificos), e o formato e ideal para producao em esteira. A fabrica pode produzir 30 videos de uma vez e agendar publicacao diaria. E o tipo de conteudo que pais aprovam para criancas assistirem.

## The New Idea: "Curious Byte"

Um canal que explica 1 curiosidade cientifica por dia em 60 segundos. Narracao calma e didatica (voz feminina suave), animacao clean com fundo escuro e elementos coloridos, musica ambiente relaxante. Cada video termina com "E amanha: Por que os gatos sempre caem em pe?" para criar expectativa.

### Por que funciona:
- Conteudo educativo tem alto compartilhamento (pais compartilham com pais)
- YouTube Shorts tem algoritmo favoravel para canais que publicam diariamente
- Roteiro e facil: livros de curiosidades, Wikipedia, ciencia popular
- Visual clean e mais barato que animacao de personagem — formas geometricas, icones, textos animados
- Pode ser expandido para ingles (alcance global)

## Proposed Workflow (batch de 30 videos)

```
DIA 1: ROTEIRO (Script Department)
  1. TOPIC_LIST_GENERATION    (gerar 30 perguntas de curiosidade cientifica)
  2. FACT_CHECK                (verificar cada resposta em fonte confiavel — MOCK)
  3. SCRIPT_60s               (escrever roteiro de 60s para cada: hook + explicacao + CTA)

DIA 1-2: AUDIO (Audio Department)
  4. NARRATION_BATCH           (gerar 30 narracoes com mesma voz e tom)
  5. SOUND_DESIGN              (efeitos: "ding" para descoberta, "whoosh" para transicao)
  6. BACKGROUND_MUSIC          (1 trilha ambiente de 60s que funciona para todos)

DIA 2-3: VISUAL BASE (Image Department)
  7. COLOR_PALETTE             (definir paleta fixa: fundo escuro #1a1a2e, elementos #e94560, #0f3460)
  8. ICON_TEMPLATES            (criar 5 templates de cena: pergunta, explicacao, exemplo, curiosidade, CTA)
  9. ANIMATION_COMPONENTS      (elementos reutilizaveis: setas, circulos, caixas de texto)

DIA 3-5: VIDEO (Video Department)
  10. SCENE_RENDER_BATCH       (renderizar 5 templates x 30 videos = 150 cenas)
  11. AUDIO_SYNC               (sincronizar narracao com animacao)
  12. SUBTITLE_EMBED           (legendas para cada video)
  13. FINAL_ASSEMBLY           (montar 30 videos de 60s cada)

DIA 5: QUALIDADE (Creative Review)
  14. FACTUAL_ACCURACY         (cada roteiro corresponde ao video?)
  15. AUDIO_VISUAL_CONSISTENCY (tom, volume, cor consistentes?)
  16. ACCESSIBILITY            (legendas corretas, contraste adequado?)

DIA 5: AGENDAMENTO (Content Scheduler)
  17. YOUTUBE_SCHEDULE         (agendar 1 video por dia para os proximos 30 dias)
  18. SHORTS_DESC              (descricao curta com hashtags)
  19. THUMBNAIL_GENERATION     (thumb generico com numero do episodio)
```

## Required Employees

### Existentes:
- ScriptWriterEmployee — 30 scripts de 60s
- AudioEngineerEmployee — narracao em batch
- ImageDesignerEmployee — templates visuais
- VideoEditorEmployee — render batch
- CreativeReviewEmployee — qualidade
- (proposto) ContentSchedulerEmployee — agenda 30 dias
- (proposto) SEOContentOptimizerEmployee — descricao + tags

### Novos:
- **FactCheckAdapter** (futuro) — API de verificacao de fatos cientificos ou Wikipedia
- **BatchVideoRenderer** — helper para renderizar 30 videos de uma vez (extensao do VideoEmployee)

## Vantagem de Producao em Batch

Fazer 30 videos de uma vez reduz o custo medio por video:

| Item | 1 video | 30 videos (batch) | Custo medio cada |
|---|---|---|---|
| Roteiro | 30 min | 90 min (3 roteiros + adaptacao) | 3 min |
| Audio | 3 min TTS | 15 min TTS (mesma voz, tom) | 30s |
| Templates visuais | 45 min | 60 min (criar templates) | 2 min |
| Render | 5 min | 10 min (batch render) | 20s |
| Revisao | 5 min | 15 min (amostragem) | 30s |
| **Tempo total** | **~83 min** | **~190 min** | **~6.3 min/video** |

Com batch, cada video custa ~8% do tempo de produzir individualmente.

## Monetizacao

1. **YouTube Shorts Fund**: pagamento por visualizacao (variavel, ~$0.01-0.03 por 1000 views)
2. **YouTube ads (longos)**: compilar 10 shorts em 1 video de 10 min com anuncio
3. **Hotmart**: ebook "101 Curiosidades Cientificas" ~R$ 17
4. **Brand deal**: marcas educativas, livros, canais de ciencia
5. **Ingles**: traduzir e republicar no canal em ingles (2x audiencia)

## Custo Estimado (batch de 30)

| Item | MOCK | REAL |
|---|---|---|
| Roteiro | $0 | $0 |
| Narracao (30 min total) | $0 (Kokoro) | ElevenLabs ~$0.60 |
| Templates/Icones | $0 (Image MOCK) | Provider ~$1.00 |
| Musica | $0 | Suno ~$0.05 |
| Render | $0 (FFmpeg) | $0 |
| **Total** | **$0** | **~$1.65** |
| **Custo por video** | **$0** | **~$0.055** |

Custo de $0.055 por video e viavel mesmo com baixo CPM do YouTube Shorts.

## Open Questions For Shin/Codex

1. Shin prefere narracao masculina ou feminina? Tom serio, divertido ou misterioso?
2. Os videos devem ter legendas em portugues e ingles (duas versoes)?
3. Deve incluir experimentos caseiros viaveis (ex: "como fazer um vulcao em casa")?
4. Shin quer que o canal tenha rosto (apresentador) ou apenas animacao?
5. Licenca para usar Wikipedia como fonte ou precisa de referencias academicas?

## Sources

- YouTube Shorts Fund: https://support.google.com/youtube/answer/10328928
- Curiosidades cientificas: https://www.britannica.com/ (fonte confiavel)
- Ciencia popular no Brasil: https://www.youtube.com/@CienciaTodoDia (referencia)
- Batch production guide: https://www.descript.com/blog/batch-content-creation
