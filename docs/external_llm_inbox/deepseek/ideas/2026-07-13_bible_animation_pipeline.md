# Idea Proposal: Bible Animation Pipeline

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Produzir animacoes curtas (3-8 min) de passagens biblicas usando a fabrica: roteiro fiel ao texto, dublagem com vozes distintas por personagem (ElevenLabs), cenarios e personagens ilustrados, edicao multiplas passagens em um unico video tematico e revisao de qualidade antes da publicacao.

## Why It Fits The AI Content Factory

A fabrica possui todos os departamentos necessarios: Script (roteiro), Audio (dublagem com ElevenLabs/Kokoro), Image (cenarios/personagens), Video (animacao/edicao), Creative Review (qualidade). Nenhum adaptador novo e necessario — apenas configuracao de pipeline diferente. E um dos nichos mais consistentes do YouTube brasileiro com audiencia fiel e baixa concorrencia em qualidade.

## User Value

- Shin nao precisa contratar ilustrador, dublador ou editor — a fabrica produz o video completo.
- Cada passagem pode ser vendida individualmente como asset ou compilada em um "filme" tematico (ex: A Vida de Jesus em 30 minutos).
- Canal no YouTube de animacao biblica gera receita por anuncios + possivel venda de colecao completa no Hotmart.
- Conteudo evergreen: passagens biblicas nunca perdem relevancia.

## Proposed Workflow

```
Brief (passagem, tom, duracao_alvo)
  -> Script Department:
      1. RESEARCH_AND_OUTLINE     (extrair passagem, contexto historico, personagens envolvidos)
      2. DIALOGUE_WRITING         (escrever dialogo fiel ao texto, adaptado para audiovisual)
      3. NARRATION_SCRIPT         (escrever narracao de ligacao entre falas)
      4. STAGE_DIRECTIONS         (descrever cenas, expressoes, movimentos para o departamento visual)

  -> Audio Department (para cada personagem):
      5. VOICE_CASTING            (mapear voz ElevenLabs para cada personagem: grave, suave, infantil, etc.)
      6. DIALOGUE_RECORDING       (gerar audio por linha com pausas e entonacao)
      7. NARRATION_RECORDING      (gerar voz do narrador)
      8. SOUND_DESIGN             (efeitos sonoros: vento, passos, agua, multidão — MOCK)

  -> Image Department:
      9. CHARACTER_DESIGN         (ilustrar cada personagem com consistencia visual)
      10. SCENE_BACKGROUNDS       (ilustrar cenarios: deserto, templo, monte, casa)
      11. PROPS_AND_OBJECTS       (ilustrar objetos: cajado, cruz, peixes, moedas)

  -> Video Department:
      12. SCENE_ASSEMBLY          (montar cada cena com personagens + fundo + animacao basica)
      13. TIMELINE_SYNC           (sincronizar labia com audio de cada personagem)
      14. TRANSITIONS             (adicionar transicoes entre cenas)
      15. SUBTITLE_EMBED          (inserir legendas da passagem)

  -> Video Editor Employee (novo ou extensao do Video):
      16. MULTI_PASSAGE_COMPILE   (unir varias passagens em um video tematico longo)
      17. COLOR_GRADING           (padronizar cor entre cenas)
      18. FINAL_RENDER            (renderizar MP4 com qualidade final)

  -> Creative Review Department:
      19. THEOLOGICAL_REVIEW      (verificar fidelidade a passagem)
      20. VISUAL_QUALITY_CHECK    (verificar consistencia de personagens, iluminacao, audio)
      21. COMPLIANCE_SCAN         (marcar como "conteudo religioso", publico infantil?)

  -> Output: MP4 final + miniatura + descricao SEO + playlist por tema
```

## Required Employees

Os departamentos existentes cobrem 90% do fluxo. Duas adicoes tornariam o pipeline mais robusto:

1. **VideoEditorEmployee (especializado em compilacao)** — extensao do VideoDepartment para editar multiplas cenas em um unico video coeso. Herda ProductionEmployee.
2. **ScriptureResearchAdapter** (futuro) — adapter MOCK/REAL que consulta API de biblia aberta para garantir fidelidade textual.

Capacidades necessarias (todas existentes): `TEXT_GENERATION`, `SPEECH_GENERATION`, `IMAGE_GENERATION`, `VIDEO_EDITING`, `AUDIO_PROCESSING`, `STORAGE`.

## Estrutura de Producao (Passo a Passo)

### Fase 1: MVP (1 passagem, MOCK)
1. Escolher 1 passagem (ex: "A Pesca Maravilhosa" - Lucas 5:1-11)
2. ScriptWriterEmployee gera roteiro de 3 min com 4 personagens (Jesus, Pedro, Tiago, Joao) + narrador
3. AudioEngineerEmployee gera 4 vozes diferentes MOCK (ou Kokoro com tons variados)
4. ImageDesignerEmployee gera 4 personagens + 2 cenarios (mar, barco)
5. VideoEditorEmployee monta cena com fade, legenda e musica de fundo MOCK
6. CreativeReviewEmployee aprova ou sugere correcoes

### Fase 2: Serie Tematica (5+ passagens)
1. Repetir Fase 1 para 5 passagens da vida de Jesus
2. VideoEditorEmployee compila em unico video de 20 min com aberturas e transicoes
3. SEOContentOptimizerEmployee gera titulo, descricao, tags
4. SocialMediaPublisherEmployee prepara posts para YouTube + Instagram

### Fase 3: Canal + Produto Hotmart
1. 30 episodios de 5-8 min cada
2. Compilado "A Vida de Jesus" (2 horas) vendido no Hotmart por R$ 29-47
3. Miniaturas padronizadas geradas pelo ImageDepartment
4. LandingPageOptimizerEmployee cria pagina de vendas
5. Traffico organico via SEO + postagens semanais

## Risks And Compliance

- **Fidelidade teologica**: o roteiro deve ser baseado em texto biblico, nao em interpretacao pessoal. Usar API de biblia aberta como fonte.
- **Publico infantil**: se o publico for infantil, aplicar regras de COPPA/LGPD para dados de criancas. YouTube exige marcacao "feito para criancas".
- **Direitos autorais**: a Biblia em si e dominio publico (traducoes modernas podem ter direitos). Usar traducao Joao Ferreira de Almeida (dominio publico).
- **Sensibilidade religiosa**: evitar interpretacoes controversas ou denominacionais. Manter-se no texto canonico.
- **ElevenLabs em REAL**: orcar custo de TTS por minuto de dialogo. 5 min de video com 4 vozes = ~20 min de TTS.

## Custo Estimado (REAL vs MOCK)

| Item | MOCK | REAL (por video de 5 min) |
|---|---|---|
| Roteiro | Gratuito | Gratuito |
| Voz (ElevenLabs TTS) | Kokoro gratis | ~$0.30 (4 vozes x 1.25 min cada) |
| Ilustracao | Gerada deterministicamente | Provider pago ~$0.10 |
| Animacao | FFmpeg basico | FFmpeg local gratis |
| Musica | MOCK | Suno API ~$0.05 |
| **Total por video** | **$0** | **~$0.45** |

## Open Questions For Shin/Codex

1. Shin quer uma biblia especifica (Ave Maria, Almeida, NVI) ou qualquer traducao de dominio publico?
2. Qual o estilo visual: realista, cartoon infantil, arte classica?
3. Deve ter versao em ingles para alcance global?
4. O personagem de Jesus deve ter rosto visivel ou mantido em silhueta (sensibilidade cultural)?

## Sources

- Bible API (dominio publico): https://bible-api.com/
- Biblia Almeida (dominio publico): https://www.bibliaonline.com.br/aa
- Channel examples: https://www.youtube.com/@CanaldaBiblia (estilo existente)
- ElevenLabs pricing: https://elevenlabs.io/pricing
- YouTube COPPA rules: https://support.google.com/youtube/answer/9527654
