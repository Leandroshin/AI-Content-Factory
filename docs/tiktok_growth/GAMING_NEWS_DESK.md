# Gaming News Desk

Updated on 2026-07-11.

## Mission

Monitor selected games and discover promising releases without forcing a daily
video. No relevant news means no brief.

The Codex automation `radar-diario-de-noticias-de-games` runs every day at
09:00 local time against this workspace. It researches and prepares drafts but
cannot publish or spend provider budget.

## Initial watchlist

### GTA VI

- Rockstar GTA VI page: `https://www.rockstargames.com/VI/`
- Rockstar Newswire GTA VI tag:
  `https://www.rockstargames.com/newswire?tag_id=666`
- Third-party channels may discover a topic, but release dates, trailers,
  platforms and product claims require primary-source verification.

### Meccha Chameleon

- Steam app ID: `4704690`
- Steam community/news is the first product source.
- Monitor updates, player-created formats, patches and verified momentum.

### Discovery lane

- Steam news and notable new releases;
- publisher showcases and official trailers;
- Google Trends Brazil and TikTok Creative Center as demand signals;
- reputable games reporting for discovery and corroboration.

New games enter the permanent watchlist only after repeated evidence or owner
approval. A one-day spike may become one video without becoming a channel
identity.

## Connected workflow

1. Scheduled research collects normalized `GamingNewsItem` records.
2. `GamingNewsDesk` rejects duplicates, old items, rumors, weak sources and
   items without factual key points.
3. Qualified items become `GrowthCandidate` records.
4. `AudienceGrowthPlanner` scores them and waits for owner approval.
5. Approved `ContentBrief` records run through Script, Audio, Image and Video.
6. The package requires subtitles and creates a YouTube Shorts variant.
7. Avatar is optional; use it only when it improves trust and does not delay a
   time-sensitive story.
8. Publishing stays manual until official channel credentials and scopes are
   configured.

## Avatar policy

Use three production levels:

- **Fast news:** voice, subtitles, licensed/official-reference visuals and
  motion graphics. No avatar.
- **Explainer:** short avatar intro/outro plus visual evidence in the body.
- **Series/evergreen:** persistent presenter identity after visual tests prove
  that it improves retention.

This avoids paying for an avatar on every low-value story and keeps the news
cycle fast.
