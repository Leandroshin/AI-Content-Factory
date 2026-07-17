import { auditLearningSource, learningSourceState, upsertLearningSource } from "./store";

const MAX_BODY_BYTES = 950_000;
const MAX_AUDIT_BODY_BYTES = 25_000;
const LANGUAGES = new Set(["pt-BR", "en", "es", "unknown"]);

export async function GET() {
  return Response.json(await learningSourceState());
}

export async function POST(request: Request) {
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) {
    return Response.json({ error: "A transcrição ultrapassa o limite desta entrada" }, { status: 413 });
  }
  try {
    const body = JSON.parse(raw) as Record<string, unknown>;
    const source = youtubeSource(body.sourceUrl);
    const transcript = optionalText(body.transcript, "Transcrição", 900_000);
    if (transcript && transcript.length < 200) throw new Error("A transcrição precisa ter ao menos 200 caracteres");
    const language = enumValue(body.language, LANGUAGES, "Idioma", "pt-BR");
    return Response.json(await upsertLearningSource({
      sourceUrl: source.original,
      canonicalUrl: source.canonical,
      externalId: source.videoId,
      title: optionalText(body.title, "Título", 160),
      ownerNotes: optionalText(body.ownerNotes, "Contexto", 1_200),
      language,
      transcript,
    }), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

export async function PATCH(request: Request) {
  const raw = await request.text();
  if (new TextEncoder().encode(raw).byteLength > MAX_AUDIT_BODY_BYTES) {
    return Response.json({ error: "A auditoria ultrapassa o limite desta entrada" }, { status: 413 });
  }
  try {
    const body = JSON.parse(raw) as Record<string, unknown>;
    if (body.action !== "audit_transcript") throw new Error("Ação inválida");
    return Response.json(await auditLearningSource({
      sourceId: requiredText(body.sourceId, "Fonte", 100),
      claimText: requiredText(body.claimText, "Alegação", 1_500),
      evidenceExcerpt: requiredText(body.evidenceExcerpt, "Trecho de evidência", 12_000),
      evidenceLocator: requiredText(body.evidenceLocator, "Localização", 200),
      candidateStatement: requiredText(body.candidateStatement, "Aprendizado candidato", 1_500),
      applicability: requiredText(body.applicability, "Aplicação", 1_500),
      risks: optionalText(body.risks, "Riscos", 2_500),
    }), { status: 202 });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Dados inválidos" }, { status: 400 });
  }
}

function youtubeSource(value: unknown) {
  if (typeof value !== "string" || !value.trim() || value.length > 1_500) throw new Error("Informe uma URL válida do YouTube");
  const url = new URL(value.trim());
  if (url.protocol !== "https:" || url.username || url.password) throw new Error("A fonte deve usar HTTPS público");
  const host = url.hostname.toLowerCase();
  const allowed = new Set(["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"]);
  if (!allowed.has(host)) throw new Error("Nesta fase, a Caixa de Aprendizado aceita somente vídeos do YouTube");
  let videoId = "";
  if (host === "youtu.be") videoId = url.pathname.split("/").filter(Boolean)[0] ?? "";
  else if (url.pathname === "/watch") videoId = url.searchParams.get("v") ?? "";
  else if (/^\/(shorts|live)\//.test(url.pathname)) videoId = url.pathname.split("/").filter(Boolean)[1] ?? "";
  if (!/^[A-Za-z0-9_-]{11}$/.test(videoId)) throw new Error("Não foi possível identificar o vídeo nessa URL");
  return {
    original: url.toString(),
    canonical: `https://www.youtube.com/watch?v=${videoId}`,
    videoId,
  };
}

function enumValue(value: unknown, allowed: Set<string>, label: string, fallback: string) {
  if (value == null || value === "") return fallback;
  if (typeof value !== "string" || !allowed.has(value)) throw new Error(`${label} inválido`);
  return value;
}

function optionalText(value: unknown, label: string, max: number) {
  if (value == null || value === "") return "";
  if (typeof value !== "string" || value.length > max) throw new Error(`${label} inválido`);
  return value.trim();
}

function requiredText(value: unknown, label: string, max: number) {
  const result = optionalText(value, label, max);
  if (!result) throw new Error(`${label} é obrigatório`);
  return result;
}
