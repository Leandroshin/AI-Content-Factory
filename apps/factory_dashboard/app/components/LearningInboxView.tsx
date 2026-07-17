"use client";

import { BrainCircuit, Check, ExternalLink, Eye, FileCheck2, FileText, FlaskConical, Send, ShieldCheck, Youtube } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import type { LearningSourceItem } from "./types";
import styles from "./dashboard.module.css";

type LearningSourceForm = {
  sourceUrl: string;
  title: string;
  ownerNotes: string;
  language: string;
  transcript: string;
};

type LearningAuditForm = {
  claimText: string;
  evidenceExcerpt: string;
  evidenceLocator: string;
  candidateStatement: string;
  applicability: string;
  risks: string;
};

export function LearningInboxView({ items, busy, onSubmit, onAudit }: {
  items: LearningSourceItem[];
  busy: string | null;
  onSubmit: (input: LearningSourceForm) => Promise<boolean>;
  onAudit: (sourceId: string, input: LearningAuditForm) => Promise<boolean>;
}) {
  const [form, setForm] = useState<LearningSourceForm>({
    sourceUrl: "",
    title: "",
    ownerNotes: "",
    language: "pt-BR",
    transcript: "",
  });

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (await onSubmit(form)) setForm((current) => ({ ...current, sourceUrl: "", title: "", ownerNotes: "", transcript: "" }));
  }

  return <>
    <section className={styles.learningIntro}>
      <div>
        <p className={styles.eyebrow}>CAIXA DE APRENDIZADO</p>
        <h2>Uma fonte entra. O conhecimento só entra depois.</h2>
        <p>Você pode enviar apenas o link ou anexar uma transcrição pronta. Nenhuma fonte vira regra dos funcionários sem evidência, auditoria, experimento e sua aprovação.</p>
      </div>
      <div className={styles.learningSafety}>
        <span><b>US$ 0</b> nesta entrada</span>
        <span><ShieldCheck size={15} /> Provider não chamado</span>
        <span><BrainCircuit size={15} /> Conhecimento bloqueado</span>
      </div>
    </section>

    <div className={styles.learningWorkspace}>
      <form className={`${styles.productForm} ${styles.learningForm}`} onSubmit={submit}>
        <div className={styles.sectionHead}><div><p className={styles.eyebrow}>NOVA FONTE</p><h2>Adicionar vídeo</h2></div><Youtube size={20} /></div>
        <div className={styles.formBody}>
          <label><span>Link do YouTube</span><div><Youtube size={16} /><input required type="url" value={form.sourceUrl} onChange={(event) => setForm({ ...form, sourceUrl: event.target.value })} placeholder="https://www.youtube.com/watch?v=..." /></div></label>
          <label><span>Título <small>opcional</small></span><div><FileText size={16} /><input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="Como você reconhecerá esta fonte" /></div></label>
          <label><span>Por que chamou sua atenção <small>opcional</small></span><textarea value={form.ownerNotes} onChange={(event) => setForm({ ...form, ownerNotes: event.target.value })} placeholder="Ex.: quero descobrir processos, ferramentas e ideias que possam melhorar a fábrica." /></label>
          <label><span>Transcrição <small>opcional, mas acelera a análise</small></span><textarea className={styles.transcriptField} value={form.transcript} onChange={(event) => setForm({ ...form, transcript: event.target.value })} placeholder="Cole aqui a transcrição. Sem ela, o item ficará aguardando transcrição e não será auditado." /></label>
          <label><span>Idioma</span><select value={form.language} onChange={(event) => setForm({ ...form, language: event.target.value })}><option value="pt-BR">Português (Brasil)</option><option value="en">Inglês</option><option value="es">Espanhol</option><option value="unknown">Ainda não sei</option></select></label>
          <button className={styles.submitProduct} disabled={busy === "learning-source"}><Send size={15} />{busy === "learning-source" ? "Registrando..." : form.transcript.trim() ? "Registrar para auditoria" : "Registrar fonte pendente"}</button>
          <p className={styles.formSafety}><ShieldCheck size={14} /> A entrada não baixa o vídeo, não chama API paga, não publica e não ensina automaticamente os funcionários.</p>
        </div>
      </form>

      <section className={`${styles.productQueue} ${styles.learningQueue}`}>
        <div className={styles.sectionHead}><div><p className={styles.eyebrow}>ACOMPANHAMENTO</p><h2>Fontes recebidas</h2></div><span className={styles.learningCount}>{items.length}</span></div>
        {!items.length ? <div className={styles.empty}><BrainCircuit size={28} /><strong>Nenhuma fonte registrada ainda</strong><span>O primeiro vídeo aparecerá aqui com cada portão do aprendizado.</span></div> : <div className={styles.learningList}>{items.map((item) => <LearningSourceCard key={item.id} item={item} busy={busy} onAudit={onAudit} />)}</div>}
      </section>
    </div>
  </>;
}

function LearningSourceCard({ item, busy, onAudit }: {
  item: LearningSourceItem;
  busy: string | null;
  onAudit: (sourceId: string, input: LearningAuditForm) => Promise<boolean>;
}) {
  const [auditOpen, setAuditOpen] = useState(false);
  const [auditForm, setAuditForm] = useState<LearningAuditForm>({
    claimText: "",
    evidenceExcerpt: "",
    evidenceLocator: "",
    candidateStatement: "",
    applicability: "",
    risks: "",
  });
  async function submitAudit(event: React.FormEvent) {
    event.preventDefault();
    if (await onAudit(item.id, auditForm)) setAuditOpen(false);
  }
  const stages = [
    { label: "Fonte", done: true, icon: <Youtube size={12} /> },
    { label: "Transcrição", done: item.transcriptStatus === "attached", icon: <FileText size={12} /> },
    { label: "Evidências", done: item.evidenceStatus !== "pending", icon: <Eye size={12} /> },
    { label: "Auditoria", done: item.auditStatus !== "pending", icon: <ShieldCheck size={12} /> },
    { label: "Conhecimento", done: item.knowledgeStatus !== "blocked", icon: <BrainCircuit size={12} /> },
  ];
  return <article className={styles.learningSourceCard}>
    <div className={styles.learningIdentity}>
      <Image src={item.thumbnailUrl} width={160} height={90} alt="Prévia do vídeo" unoptimized />
      <div><small>YouTube · {item.language}</small><strong>{item.title}</strong><a href={item.canonicalUrl} target="_blank" rel="noreferrer">Abrir fonte <ExternalLink size={11} /></a></div>
      <b className={item.auditStatus === "partial" ? styles.green : item.transcriptStatus === "attached" ? styles.amber : styles.amber}>{item.auditStatus === "partial" ? "Evidência registrada" : item.transcriptStatus === "attached" ? "Pronta para auditoria" : "Aguardando transcrição"}</b>
    </div>
    <div className={styles.learningStages}>{stages.map((stage, index) => <span className={stage.done ? styles.learningStageDone : ""} key={stage.label}><i>{stage.done ? <Check size={11} /> : stage.icon}</i>{stage.label}{index < stages.length - 1 && <em />}</span>)}</div>
    <p className={styles.learningExplanation}>{item.auditPacket ? "Um trecho exato foi vinculado a uma alegação. O resultado continua parcial: falta fonte independente, experimento medido e sua aprovação final." : item.transcriptStatus === "attached" ? "Transcrição recebida. Agora selecione uma alegação e o trecho exato que a sustenta; isso ainda não vira conhecimento oficial." : "A fábrica registrou a fonte, mas ainda não ouviu o vídeo. O próximo passo é obter uma transcrição verificável."}</p>
    {item.ownerNotes && <p className={styles.ownerNotes}>{item.ownerNotes}</p>}
    <div className={styles.learningFacts}>
      <span><FileText size={13} /> {item.transcriptCharacters.toLocaleString("pt-BR")} caracteres</span>
      <span><FlaskConical size={13} /> Experimento não iniciado</span>
      <span><ShieldCheck size={13} /> Publicação bloqueada</span>
      <span>US$ {item.estimatedCostUsd.toFixed(2).replace(".", ",")}</span>
    </div>
    <div className={styles.missingFields}>{item.missingRequirements.map((requirement) => <span key={requirement}>{requirement}</span>)}</div>
    {item.auditPacket ? <section className={styles.auditResult}>
      <div><span>VEREDITO</span><b>Parcial</b></div>
      <div><span>ALEGAÇÃO REGISTRADA</span><strong>{item.auditPacket.claim.text}</strong></div>
      <blockquote>“{item.auditPacket.evidence.excerpt}” <small>{item.auditPacket.evidence.locator}</small></blockquote>
      <p><ShieldCheck size={14} /> {item.auditPacket.audit.rationale}</p>
      <p><BrainCircuit size={14} /> Candidato: {item.auditPacket.knowledgeDraft.statement}</p>
      <footer>Provider não chamado · experimento não iniciado · memória e publicação bloqueadas</footer>
    </section> : item.transcriptStatus === "attached" && <>
      <button type="button" className={styles.auditToggle} onClick={() => setAuditOpen((value) => !value)}><FileCheck2 size={14} /> {auditOpen ? "Fechar auditoria" : "Registrar evidência da transcrição"}</button>
      {auditOpen && <form className={styles.auditForm} onSubmit={submitAudit}>
        <p>Copie da transcrição apenas o trecho que sustenta a alegação. A fábrica confere o texto e o hash antes de registrar.</p>
        <label><span>Alegação da fonte</span><textarea required value={auditForm.claimText} onChange={(event) => setAuditForm({ ...auditForm, claimText: event.target.value })} placeholder="O que exatamente o autor afirma?" /></label>
        <label><span>Trecho exato da transcrição</span><textarea required minLength={40} value={auditForm.evidenceExcerpt} onChange={(event) => setAuditForm({ ...auditForm, evidenceExcerpt: event.target.value })} placeholder="Cole literalmente ao menos 40 caracteres da transcrição registrada." /></label>
        <div className={styles.auditFormGrid}>
          <label><span>Onde está</span><input required value={auditForm.evidenceLocator} onChange={(event) => setAuditForm({ ...auditForm, evidenceLocator: event.target.value })} placeholder="Ex.: 08:42-09:15" /></label>
          <label><span>Aplicação possível</span><input required value={auditForm.applicability} onChange={(event) => setAuditForm({ ...auditForm, applicability: event.target.value })} placeholder="Onde isso ajudaria a fábrica?" /></label>
        </div>
        <label><span>Aprendizado candidato</span><textarea required value={auditForm.candidateStatement} onChange={(event) => setAuditForm({ ...auditForm, candidateStatement: event.target.value })} placeholder="Escreva como hipótese para teste, não como verdade definitiva." /></label>
        <label><span>Riscos ou limites <small>um por linha</small></span><textarea value={auditForm.risks} onChange={(event) => setAuditForm({ ...auditForm, risks: event.target.value })} placeholder="Pode ficar desatualizado\nDepende de validação visual" /></label>
        <button disabled={busy === `learning-audit-${item.id}`}><ShieldCheck size={14} /> {busy === `learning-audit-${item.id}` ? "Conferindo..." : "Registrar como candidato"}</button>
      </form>}
    </>}
  </article>;
}

export type { LearningAuditForm, LearningSourceForm };
