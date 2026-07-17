# Idea Proposal: Podcast & Audio Content Department

Status: PROPOSTA - NAO IMPLEMENTADA.

## One-Sentence Idea

Criar um departamento especializado em producao de conteudo audio-first: episodios de podcast com roteiro, vinheta, entrevista simulada (MOCK), capitulos, show notes e distribuicao para plataformas de audio (Spotify, Apple Podcasts, Deezer) — complementar ao AudioEngineerEmployee que foca em TTS para video.

## Why It Fits The AI Content Factory

O AudioEngineerEmployee atual existe apenas para gerar voz (TTS) que alimenta videos. Nao ha producao de conteudo audio autonomo. Podcast e um formato em crescimento no Brasil, com 40% da populacao ouvindo podcasts regularmente. E um canal de autoridade, monetizavel por anuncio, afiliado e conteudo exclusivo, e nao compete com video — complementa.

## User Value

- Shin pode lancar um podcast da marca sem equipamento de audio: roteiro + voz Kokoro + vinheta gerados pela fabrica.
- Cada episodio pode ser "fatia" de um video longo (via Content Repurposing Department) ou episodio original.
- Show notes com links de afiliado gerados automaticamente.
- Spotify for Podcasters permite publicacao gratuita — custo operacional zero no REAL.

## Proposed Workflow

```
ReceivedTask{episode_type, topic, duration_minutes, host_voice, include_music}
  -> Pipeline stages:
     1. EPISODE_STRUCTURE         (definir: intro, blocos, perguntas, cta, encerramento)
     2. SCRIPT_GENERATION         (escrever roteiro do host, com marcas de tempo)
     3. VOICE_RECORDING           (gerar audio do host via KokoroAdapter ou MOCK WAV)
     4. VINHETA_ASSEMBLY          (montar intro/outro com musica MOCK + voz de abertura)
     5. CHAPTER_MARKING           (marcar capitulos com timestamps e titulos)
     6. SHOW_NOTES_ASSEMBLY       (gerar show notes: descricao, links, CTA, disclosure)
     7. EPISODE_PACKAGE           (consolidar: audio MP3 final, capa, show notes, RSS entry)
```

## Required Employees

1. **PodcastProducerEmployee** — herda ProductionEmployee, gerencia pipeline de podcast.
   - Hooks: `_check_reject()` rejeita se `episode_type` desconhecido ou `duration_minutes` fora de 5-60 min; `_build_pipeline()` monta PodcastPipeline; `_build_output_from_stages()` extrai `episode_package`.

2. **ShowNotesWriter** — helper interno que gera notas estruturadas com links, timestamps e disclosures.

## Required Capabilities

Todas ja existentes:
- `SPEECH_GENERATION` (voz do host via KokoroAdapter)
- `AUDIO_PROCESSING` (montar episodio final)
- `AUDIO_EDITING` (cortar, emendar, normalizar volume)
- `TEXT_GENERATION` (roteiro, show notes)
- `DOCUMENT_GENERATION` (RSS entry, show notes em markdown)
- `STORAGE` (salvar episodio MP3 e metadados)

## Risks And Compliance

- **Direitos autorais**: musicas de vinheta DEVEM ser isentas de direitos (biblioteca MOCK ou CC0). O pipeline nunca deve usar musica protegida.
- **Disclosure de afiliado**: se o episodio menciona produtos, o show notes deve conter disclosure claro. Herdado do Affiliate Deals compliance.
- **Consistencia de voz**: se usar Kokoro TTS real, a mesma voz deve ser consistente entre episodios. O pipeline deve registrar qual voz foi usada.
- **Privacidade**: se houver "entrevista simulada", deixar claro que e conteudo gerado, nao uma pessoa real.

## MVP Scope

1. Pipeline deterministico MOCK com 7 stages.
2. PodcastProducerEmployee com hooks padrao.
3. Snapshot `AudioContentSnapshot` (episodes_produced, avg_duration, chapters_per_episode, shows_notes_generated).
4. 3 tipos de episodio: "monologo" (so o host), "entrevista" (host + convidado MOCK), "mesa" (3+ vozes MOCK).
5. Duracao suportada: 5-30 min (shortcast) e 30-60 min (episodio completo).
6. Demo com 30+ assertions: estrutura, script, voz, vinheta, capitulos, show notes e pacote final.
7. Saida: arquivo WAV/MP3 MOCK + show notes .md + RSS entry .xml.

## Later Integrations

- Spotify for Podcasters API (publicacao direta)
- Apple Podcasts Connect API
- Podcast RSS hosting (buzzsprout, anchor, transistor)
- Integracao com ElevenLabs para voz mais natural
- Geracao de transcricao do episodio (via SPEECH_TO_TEXT) para SEO

## Open Questions For Shin/Codex

1. O podcast deve ser um departamento proprio ou uma expansao do AudioDepartment existente?
2. Shin quer um podcast de que nicho? Games, ofertas, tecnologia, todos?
3. A vinheta deve ser gerada por IA (musica sintetica) ou Shin prefere produzir uma unica vez e reusar?
4. Deve existir um calendario de episodios (ex: 1x/semana) integrado ao Content Scheduling Department?

## Sources

- Spotify for Podcasters: https://podcasters.spotify.com/
- Apple Podcasts: https://podcastsconnect.apple.com/
- Podcast no Brasil (dados): https://www.abpod.com.br/pesquisa-podcast-2025 (parcial)
- Musica livre de direitos: https://freemusicarchive.org/ , https://pixabay.com/music/
- RSS spec for podcasts: https://help.apple.com/itc/podcasts_connect/
