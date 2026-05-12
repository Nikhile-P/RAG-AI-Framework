"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/components/ThemePreferences";
import {
  ArrowLeft, MessageSquarePlus, MessageCircle, RefreshCw,
  LogOut, Send, Bot, Activity, Settings, Bell, BellOff, Sun, Moon,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type Role = "user" | "assistant";
type SourceDetail = {
  name: string;
  type: "file" | "url" | "unknown";
  path?: string;
  preview?: string;
  url?: string;
};
type Message = {
  role: Role;
  content: string;
  sources?: string[];
  source_details?: SourceDetail[];
  confidence?: "High" | "Medium" | "Low" | string;
  trace?: string;
};
type UserProfile = { name: string; email: string; role: string };

// Auth is now checked only on the client inside useEffect to avoid SSR/client mismatch
function readAuthFromStorage(): { authed: boolean; user: UserProfile | null } {
  try {
    const raw = localStorage.getItem("lenovo_ai_auth");
    if (!raw) return { authed: false, user: null };
    const parsed = JSON.parse(raw) as { email: string; name?: string };
    return {
      authed: true,
      user: {
        name: parsed.name ?? parsed.email.split("@")[0],
        email: parsed.email,
        role: "Researcher",
      },
    };
  } catch {
    return { authed: false, user: null };
  }
}

// ─── Response pre-processor ───────────────────────────────────────────────────
// Cleans LLM output before rendering:
//  • Splits inline bullets run together on one line: "text • text • text"
//  • Strips "Sources Consulted:" and "Evidence Confidence:" lines (shown separately as UI elements)

function preprocessResponse(text: string): string {
  // Split inline bullets run together: "text • text" → each on own line
  text = text.replace(/\s+[•]\s+/g, "\n• ");

  // Strip metadata lines shown separately as UI elements
  text = text.replace(/\*?\*?Sources Consulted:\*?\*?\s*[^\n]*/gi, "");
  text = text.replace(/\*?\*?Evidence Confidence:\*?\*?\s*[^\n]*/gi, "");

  // Strip empty section headers (header followed immediately by another header or end)
  text = text.replace(/\*\*[^*\n]+:\*\*\s*\n(?=\s*\n|\s*\*\*|$)/g, "");

  // Strip "Additional Context:" if body is empty or only whitespace
  text = text.replace(/\*?\*?Additional Context:\*?\*?\s*(\n\s*)+(\n\*\*|$)/g, "\n");

  // Collapse 3+ blank lines to 2
  text = text.replace(/\n{3,}/g, "\n\n");

  return text.trim();
}

// ─── Source helpers ───────────────────────────────────────────────────────────

function getSourceIcon(source: string): string {
  if (source.startsWith("http://") || source.startsWith("https://")) return "🌐";
  const ext = source.split(".").pop()?.toLowerCase() ?? "";
  const m: Record<string, string> = {
    pdf: "📕", txt: "📋", md: "📝", csv: "📊",
    json: "⚙️", docx: "📄", doc: "📄", xlsx: "📈",
  };
  return m[ext] ?? "📁";
}

function formatSource(source: string): string {
  if (source.startsWith("http://") || source.startsWith("https://")) {
    try { return new URL(source).hostname.replace(/^www\./, ""); }
    catch { return source.slice(0, 32) + "…"; }
  }
  return source.length > 40 ? source.slice(0, 38) + "…" : source;
}

// ─── Markdown renderer ────────────────────────────────────────────────────────
// Handles inline bold, italic, code, headings, bullets, numbered lists

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**") && p.length > 4)
      return <strong key={i} className="font-semibold text-white">{p.slice(2, -2)}</strong>;
    if (p.startsWith("*") && p.endsWith("*") && p.length > 2)
      return <em key={i} className="italic text-slate-300">{p.slice(1, -1)}</em>;
    if (p.startsWith("`") && p.endsWith("`") && p.length > 2)
      return <code key={i} className="font-mono text-[12px] bg-white/8 px-1.5 py-0.5 rounded text-red-300">{p.slice(1, -1)}</code>;
    return <span key={i}>{p}</span>;
  });
}

function renderMarkdown(content: string): React.ReactNode {
  return content.split("\n").map((line, i) => {
    const t = line.trim();

    if (!t) return <div key={i} className="h-2" />;

    // ATX heading
    const hMatch = t.match(/^(#{1,3})\s+(.+)/);
    if (hMatch) {
      const cls = hMatch[1].length === 1
        ? "text-[16px] font-bold text-white mt-4 mb-1.5"
        : "text-[14px] font-bold text-white/90 mt-3 mb-1";
      return <p key={i} className={cls}>{renderInline(hMatch[2])}</p>;
    }

    // Short capitalised "Label:" line acting as a section header
    if (/^[A-Z][A-Za-z\s]+:$/.test(t) && t.length < 50)
      return <p key={i} className="text-[14px] font-bold text-white mt-4 mb-1">{t}</p>;

    // Bullet — -, *, or •
    const bMatch = t.match(/^[-•*]\s+(.+)/);
    if (bMatch)
      return (
        <div key={i} className="flex gap-2.5 my-1.5 items-start">
          <div className="w-1.5 h-1.5 rounded-full bg-red-400/60 mt-[7px] flex-shrink-0" />
          <span className="text-[14px] text-slate-200 leading-relaxed">{renderInline(bMatch[1])}</span>
        </div>
      );

    // Numbered list
    const nMatch = t.match(/^(\d+)\.\s+(.+)/);
    if (nMatch)
      return (
        <div key={i} className="flex gap-2.5 my-1.5 items-start">
          <span className="text-[11px] font-bold text-red-400/60 w-4 mt-1 flex-shrink-0">{nMatch[1]}.</span>
          <span className="text-[14px] text-slate-200 leading-relaxed">{renderInline(nMatch[2])}</span>
        </div>
      );

    // Horizontal rule
    if (/^[-*_]{3,}$/.test(t))
      return <hr key={i} className="border-white/[0.08] my-3" />;

    return <p key={i} className="text-[14px] text-slate-200 leading-[1.75] my-0.5">{renderInline(line)}</p>;
  });
}


// ─── Avatars — unique SVG gradient ID per message index ──────────────────────

function AgentAvatar({ idx }: { idx: number }) {
  const id = `agrad-${idx}`;
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" className="flex-shrink-0 mt-1 drop-shadow-lg">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="36" y2="36">
          <stop offset="0%" stopColor="#E2231A" /><stop offset="100%" stopColor="#FF4444" />
        </linearGradient>
      </defs>
      <circle cx="18" cy="18" r="17" fill={`url(#${id})`} fillOpacity="0.13" stroke={`url(#${id})`} strokeWidth="1.5" />
      <circle cx="18" cy="12" r="4" fill={`url(#${id})`} />
      <path d="M10 24C10 20.5 13 18 18 18C23 18 26 20.5 26 24" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function UserAvatar({ idx }: { idx: number }) {
  const id = `ugrad-${idx}`;
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" fill="none" className="flex-shrink-0 mt-1 drop-shadow-lg">
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="36" y2="36">
          <stop offset="0%" stopColor="#3b82f6" /><stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
      <circle cx="18" cy="18" r="17" fill={`url(#${id})`} fillOpacity="0.13" stroke={`url(#${id})`} strokeWidth="1.5" />
      <circle cx="18" cy="12" r="4" fill={`url(#${id})`} />
      <path d="M10 24C10 20.5 13 18 18 18C23 18 26 20.5 26 24" stroke={`url(#${id})`} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

// ─── Sources panel ────────────────────────────────────────────────────────────

function SourcesPanel({ sources, source_details }: { sources?: string[]; source_details?: SourceDetail[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  const looksLikeUrl = (s: string) =>
    s.startsWith("http://") || s.startsWith("https://") || /^[a-z0-9-]+\.[a-z]{2,}(\/|$)/i.test(s);

  const items: SourceDetail[] = (source_details && source_details.length > 0
    ? source_details
    : (sources ?? []).map(s => ({
        name: s,
        type: looksLikeUrl(s) ? "url" as const : "file" as const,
        url: looksLikeUrl(s) ? (s.startsWith("http") ? s : "https://" + s) : undefined,
      }))
  ).map(item =>
    // Promote "unknown" items that look like URLs to url type
    item.type === "unknown" && looksLikeUrl(item.name)
      ? { ...item, type: "url" as const, url: item.name.startsWith("http") ? item.name : "https://" + item.name }
      : item
  );

  if (!items.length) return null;

  return (
    <div className="mt-5 pt-4 border-t border-white/[0.06]">
      <div className="flex items-center gap-1.5 text-[10px] font-bold text-white/20 uppercase tracking-[0.14em] mb-3">
        🔗 Sources Consulted
      </div>
      <div className="flex flex-col gap-2">
        {items.map((s, i) => (
          <div key={i}>
            {s.type === "url" ? (
              // Web link — clickable chip that opens in new tab
              <a
                href={s.url ?? s.name}
                target="_blank"
                rel="noopener noreferrer"
                title={s.url ?? s.name}
                className="inline-flex items-center gap-1.5 bg-white/[0.03] border border-white/8 hover:border-blue-500/40 hover:bg-blue-500/6 rounded-lg px-3 py-1.5 transition-all duration-200 max-w-full"
              >
                <span className="text-[12px]">🌐</span>
                <span className="text-[11px] font-semibold text-blue-300 hover:text-blue-200 truncate max-w-[340px]">
                  {s.name.startsWith("http") ? (() => { try { return new URL(s.name).hostname.replace(/^www\./, ""); } catch { return s.name.slice(0, 48) + "…"; } })() : s.name}
                </span>
                <span className="text-[9px] text-white/20 ml-1 flex-shrink-0">↗</span>
              </a>
            ) : (
              // File source — document card with styled preview
              <div
                className="rounded-xl border border-white/[0.07] overflow-hidden"
                style={{ background: "rgba(15,19,25,0.8)" }}
              >
                {/* Card header — always visible */}
                <button
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  title={s.path ?? s.name}
                  className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/[0.03] transition-colors duration-150"
                >
                  {/* File type badge */}
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-[16px]"
                    style={{ background: "rgba(226,35,26,0.12)", border: "1px solid rgba(226,35,26,0.2)" }}>
                    {getSourceIcon(s.name)}
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <div className="text-[12px] font-semibold text-slate-200 truncate">{formatSource(s.name)}</div>
                    <div className="text-[10px] text-slate-500 mt-0.5">Internal Document</div>
                  </div>
                  {s.preview && (
                    <div className="flex-shrink-0 text-[10px] font-bold text-slate-500 px-2 py-1 rounded-md border border-white/[0.06]">
                      {expanded === i ? "CLOSE" : "PREVIEW"}
                    </div>
                  )}
                </button>

                {/* Expanded document preview */}
                {expanded === i && s.preview && (
                  <div className="border-t border-white/[0.06]">
                    {/* Toolbar */}
                    <div className="flex items-center justify-between px-4 py-2"
                      style={{ background: "rgba(255,255,255,0.02)" }}>
                      <span className="text-[9px] font-bold text-white/20 uppercase tracking-[0.15em]">
                        Document Preview · First 2000 chars
                      </span>
                      <span className="text-[9px] text-white/15">{s.name}</span>
                    </div>
                    {/* Content area */}
                    <div className="max-h-64 overflow-y-auto custom-scrollbar p-4">
                      <div className="space-y-1">
                        {s.preview.split("\n").map((line, li) => {
                          const t = line.trim();
                          if (!t) return <div key={li} className="h-1.5" />;
                          if (/^#{1,3}\s/.test(t))
                            return <p key={li} className="text-[13px] font-bold text-white mt-3 mb-1">{t.replace(/^#+\s/, "")}</p>;
                          if (/^[-•*]\s/.test(t))
                            return (
                              <div key={li} className="flex gap-2 items-start">
                                <div className="w-1.5 h-1.5 rounded-full bg-red-400/50 mt-[5px] flex-shrink-0" />
                                <span className="text-[12px] text-slate-300 leading-relaxed">{t.slice(2)}</span>
                              </div>
                            );
                          return <p key={li} className="text-[12px] text-slate-300 leading-relaxed">{line}</p>;
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Message bubble ───────────────────────────────────────────────────────────

function MessageBubble({ msg, idx }: { msg: Message; idx: number }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-4 items-start ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      {isUser ? <UserAvatar idx={idx} /> : <AgentAvatar idx={idx} />}
      <div
        className={`max-w-[82%] rounded-[22px] px-6 py-5 shadow-2xl ${
          isUser
            ? "bg-[#1C222B] border border-white/[0.06] rounded-tr-sm"
            : "bg-[#0F1319] border border-white/[0.06] border-l-[3px] border-l-red-500 rounded-tl-sm"
        }`}
      >
        {/* Role label */}
        <div className={`text-[10px] font-bold uppercase tracking-[0.15em] mb-3 ${isUser ? "text-slate-500" : "text-red-400"}`}>
          {isUser ? "You" : "Lenovo Agent"}
        </div>

        {/* Rendered content — stripped of duplicate source/confidence lines */}
        <div>{renderMarkdown(preprocessResponse(msg.content))}</div>

        {/* Sources panel */}
        {!isUser && (msg.source_details?.length || msg.sources?.length) ? (
          <SourcesPanel sources={msg.sources} source_details={msg.source_details} />
        ) : null}

        {/* Confidence & Trace badges */}
        {!isUser && (msg.confidence || msg.trace) && (
          <div className="mt-3 flex flex-wrap gap-2">
            {msg.trace && (
              <span className="inline-flex items-center text-[9px] font-bold tracking-[0.15em] uppercase px-2.5 py-1 rounded-full border bg-white/5 border-white/10 text-white/40">
                ⚡ {msg.trace}
              </span>
            )}
            {msg.confidence && (
              <span className={`inline-flex items-center text-[9px] font-bold tracking-[0.15em] uppercase px-2.5 py-1 rounded-full border ${
                msg.confidence === "High"
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                  : msg.confidence === "Medium"
                  ? "bg-yellow-500/10 border-yellow-500/20 text-yellow-400"
                  : "bg-red-500/10 border-red-500/20 text-red-400"
              }`}>
                {msg.confidence} Confidence
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Thinking indicator — Framer Motion stagger, no jitter ───────────────────

function ThinkingBubble() {
  return (
    <div className="flex gap-4 items-start">
      <AgentAvatar idx={-1} />
      <div className="bg-[#0F1319] border border-white/[0.06] border-l-[3px] border-l-red-500 rounded-[22px] rounded-tl-sm px-6 py-5 flex items-center gap-4 shadow-2xl">
        <div className="flex gap-1.5 items-center">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-red-400"
              animate={{ y: [0, -5, 0] }}
              transition={{ duration: 0.65, repeat: Infinity, ease: "easeInOut", delay: i * 0.16 }}
            />
          ))}
        </div>
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.15em]">Routing & Processing</span>
      </div>
    </div>
  );
}

// ─── Empty state with suggestion cards ───────────────────────────────────────

const SUGGESTIONS = [
  { q: "What does the CIO playbook say about government infrastructure adoption?", icon: "🏛️" },
  { q: "Give me the SR670 V2 hardware specs.", icon: "🖥️" },
  { q: "How does Lenovo compare to Dell on enterprise servers?", icon: "⚖️" },
  { q: "What's the current Lenovo stock price?", icon: "📈" },
];

function EmptyState({ onSend }: { onSend: (q: string) => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      className="flex flex-col items-center justify-center py-16 text-center px-4"
    >
      {/* Floating avatar */}
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        className="relative mb-8"
      >
        <div
          className="w-20 h-20 rounded-full flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #1C222B, #0F1319)",
            border: "1px solid rgba(255,255,255,0.07)",
            boxShadow: "0 20px 48px rgba(0,0,0,0.5), 0 0 40px rgba(226,35,26,0.12)",
          }}
        >
          <Bot size={38} className="text-red-500" />
        </div>
        <div className="absolute inset-0 rounded-full border border-red-500/15 blur-[3px]" />
      </motion.div>

      <h2 className="text-[28px] font-extrabold text-white mb-3 tracking-tight">What do you need to know?</h2>
      <p className="text-[14px] text-slate-400 max-w-md leading-relaxed mb-10">
        Ask anything. It searches your Lenovo documents first, then hits the web if needed.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
        {SUGGESTIONS.map(({ q, icon }, i) => (
          <motion.button
            key={i}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1], delay: 0.1 + i * 0.07 }}
            whileHover={{ y: -3, scale: 1.015 }}
            whileTap={{ scale: 0.975 }}
            onClick={() => onSend(q)}
            className="group text-left p-4 rounded-2xl flex items-start gap-3 border border-white/[0.07] hover:border-red-500/30 hover:bg-red-500/[0.04] transition-colors duration-200 cursor-pointer"
            style={{ background: "rgba(255,255,255,0.025)", boxShadow: "0 4px 16px rgba(0,0,0,0.2)" }}
          >
            <span className="text-lg mt-0.5 flex-shrink-0">{icon}</span>
            <span className="text-[13px] font-medium text-slate-300 group-hover:text-white transition-colors leading-relaxed">
              {q}
            </span>
          </motion.button>
        ))}
      </div>
    </motion.div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar({ user, onLogout, sessions, currentId, onSelect, onNewChat, onClear }: {
  user: UserProfile;
  onLogout: () => void;
  sessions: string[];
  currentId: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onClear: () => void;
}) {
  return (
    <div
      className="w-[300px] flex flex-col h-full flex-shrink-0 overflow-y-auto custom-scrollbar"
      style={{
        background: "rgba(10,13,18,0.95)",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        backdropFilter: "blur(20px)",
      }}
    >
      <div className="flex flex-col min-h-full p-6">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3.5 mb-8 group">
          <div
            className="p-2 rounded-xl shadow-[0_0_16px_rgba(226,35,26,0.45)] group-hover:shadow-[0_0_24px_rgba(226,35,26,0.7)] transition-shadow duration-300"
            style={{ background: "#E2231A" }}
          >
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path d="M10 16L16 10L22 16" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M16 10V22" stroke="white" strokeWidth="3" strokeLinecap="round" />
            </svg>
          </div>
          <div className="flex flex-col leading-tight">
            <span className="font-extrabold text-[20px] tracking-tight text-white">
              Lenovo<span className="text-red-500">.</span>LABS
            </span>
            <span className="text-[9px] text-white/25 font-bold uppercase tracking-[0.22em]">Research Workspace</span>
          </div>
        </Link>

        {/* New Chat */}
        <motion.button
          onClick={onNewChat}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          className="flex items-center justify-center gap-2 w-full bg-red-600 hover:bg-red-500 text-white rounded-full py-3.5 px-4 text-[13px] font-bold shadow-[0_8px_20px_rgba(226,35,26,0.3)] mb-3 transition-colors"
        >
          <MessageSquarePlus size={16} /> New Chat
        </motion.button>

        {/* Analytics */}
        <Link
          href="/analytics"
          className="flex items-center justify-center gap-2 w-full bg-white/[0.04] hover:bg-white/8 border border-white/8 hover:border-white/14 rounded-full py-3 px-4 text-[13px] font-bold text-slate-300 hover:text-white mb-8 transition-all duration-200"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400">
            <path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" />
          </svg>
          Enterprise Analytics
        </Link>

        {/* Authenticated user */}
        <div className="mb-6">
          <div className="text-[9px] font-bold text-white/20 uppercase tracking-[0.22em] mb-3 px-1">Authenticated User</div>
          <div className="rounded-2xl p-4 space-y-2 border border-white/[0.04]" style={{ background: "rgba(255,255,255,0.02)" }}>
            {[
              { k: "Name",  v: user.name,  cls: "capitalize" },
              { k: "Email", v: user.email, cls: ""           },
              { k: "Role",  v: user.role,  cls: "capitalize" },
            ].map(({ k, v, cls }) => (
              <div key={k} className="flex justify-between items-center gap-3">
                <span className="text-[12px] text-slate-500 flex-shrink-0">{k}:</span>
                <span className={`text-[12px] font-semibold text-slate-200 text-right truncate ${cls}`}>{v}</span>
              </div>
            ))}
            <button
              onClick={onLogout}
              className="mt-3 w-full flex items-center justify-center gap-1.5 text-red-400 hover:text-red-300 hover:bg-red-500/8 py-2 rounded-xl transition-all text-[11px] font-bold"
            >
              <LogOut size={12} /> Sign Out
            </button>
          </div>
        </div>

        {/* Sessions */}
        <div className="mb-6">
          <div className="text-[9px] font-bold text-white/20 uppercase tracking-[0.22em] mb-3 px-1">Recent Sessions</div>
          <div className="space-y-1">
            {sessions.map(sid => (
              <button
                key={sid}
                onClick={() => onSelect(sid)}
                className={`flex items-center gap-2.5 w-full px-3.5 py-2.5 rounded-xl text-[13px] font-medium text-left transition-all duration-150 ${
                  sid === currentId
                    ? "bg-white/8 text-white border border-white/[0.06]"
                    : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
                }`}
              >
                {sid === currentId
                  ? <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_6px_#3b82f6]" />
                  : <MessageCircle size={14} className="opacity-40" />
                }
                {sid}
              </button>
            ))}
          </div>
        </div>

        {/* System telemetry + clear */}
        <div className="mt-auto pt-4 space-y-4">
          <div className="text-[9px] font-bold text-white/20 uppercase tracking-[0.22em] mb-3 px-1">System Telemetry</div>
          <div className="flex items-center justify-center gap-2 text-[11px] font-bold text-emerald-400 bg-emerald-500/8 py-2.5 rounded-xl border border-emerald-500/15">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_6px_#34d399]" />
            Backend running · port 8000
          </div>

          <button
            onClick={onClear}
            className="flex items-center justify-center gap-2 w-full text-slate-500 hover:text-red-400 hover:bg-red-500/6 border border-transparent hover:border-red-500/15 rounded-full py-2.5 px-4 transition-all text-[12px] font-bold"
          >
            <RefreshCw size={14} /> Clear Workspace
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Preferences panel ────────────────────────────────────────────────────────
// Slide-out panel from the settings gear — theme toggle + N (notify) toggle

function ToggleSwitch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
  return (
    <button
      onClick={onChange}
      role="switch"
      aria-checked={checked}
      className="relative w-11 h-6 rounded-full transition-colors duration-200 flex-shrink-0 focus:outline-none"
      style={{ background: checked ? "#E2231A" : "rgba(0,0,0,0.28)" }}
    >
      <motion.span
        animate={{ x: checked ? 22 : 2 }}
        transition={{ type: "spring", stiffness: 480, damping: 30 }}
        className="absolute top-[2px] w-5 h-5 rounded-full bg-white shadow-md"
        style={{ willChange: "transform" }}
      />
    </button>
  );
}

function PreferencesPanel() {
  const [open, setOpen] = useState(false);
  const [notify, setNotify] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("notif-enabled") !== "false";
  });
  const { theme, toggle: toggleTheme } = useTheme();
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleNotify = () => {
    const next = !notify;
    setNotify(next);
    localStorage.setItem("notif-enabled", String(next));
    if (next && typeof Notification !== "undefined" && Notification.permission === "default") {
      Notification.requestPermission();
    }
  };

  return (
    <div ref={panelRef} className="relative">
      {/* Gear icon trigger */}
      <motion.button
        onClick={() => setOpen(o => !o)}
        whileHover={{ scale: 1.08, rotate: open ? 0 : 30 }}
        whileTap={{ scale: 0.90 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        className="p-2.5 rounded-full border border-white/[0.06] text-slate-400 hover:text-white transition-colors duration-200"
        style={{ background: open ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.04)" }}
        title="Preferences"
        aria-label="Open preferences"
      >
        <Settings size={18} />
      </motion.button>

      {/* Slide-out panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0,  scale: 1    }}
            exit={{    opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="pref-panel absolute top-12 right-0 w-56 rounded-2xl overflow-hidden z-50"
            style={{
              background: "rgba(10,12,18,0.96)",
              border: "1px solid rgba(255,255,255,0.09)",
              backdropFilter: "blur(28px)",
              boxShadow: "0 16px 48px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.03)",
            }}
          >
            {/* Header */}
            <div className="px-4 pt-3.5 pb-2.5 border-b border-white/[0.06]">
              <p className="text-[10px] font-bold tracking-[0.22em] uppercase text-white/25">Preferences</p>
            </div>

            <div className="p-3 space-y-1">

              {/* Theme row */}
              <div className="flex items-center justify-between px-2 py-2.5 rounded-xl hover:bg-white/[0.04] transition-colors">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                    style={{ background: "rgba(251,191,36,0.10)", border: "1px solid rgba(251,191,36,0.18)" }}>
                    {theme === "dark"
                      ? <Moon size={13} className="text-white/50" />
                      : <Sun  size={13} className="text-yellow-400" />
                    }
                  </div>
                  <div>
                    <p className="text-[12px] font-semibold text-white/80 leading-none mb-0.5">
                      {theme === "dark" ? "Dark mode" : "Light mode"}
                    </p>
                    <p className="text-[10px] text-white/30">Appearance</p>
                  </div>
                </div>
                <ToggleSwitch checked={theme === "light"} onChange={toggleTheme} />
              </div>

              {/* N — Notify row */}
              <div className="flex items-center justify-between px-2 py-2.5 rounded-xl hover:bg-white/[0.04] transition-colors">
                <div className="flex items-center gap-2.5">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                    style={{ background: "rgba(34,211,238,0.10)", border: "1px solid rgba(34,211,238,0.18)" }}>
                    {notify
                      ? <Bell    size={13} className="text-cyan-400" />
                      : <BellOff size={13} className="text-white/30" />
                    }
                  </div>
                  <div>
                    <p className="text-[12px] font-semibold text-white/80 leading-none mb-0.5">Notify</p>
                    <p className="text-[10px] text-white/30">Answer alerts</p>
                  </div>
                </div>
                <ToggleSwitch checked={notify} onChange={handleNotify} />
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── Chat area ────────────────────────────────────────────────────────────────

function ChatArea({
  messages,
  setMessages,
}: {
  messages: Message[];
  setMessages: (m: Message[]) => void;
}) {
  const [input, setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef   = useRef<HTMLDivElement>(null);
  const bottomRef   = useRef<HTMLDivElement>(null);
  const inputRef    = useRef<HTMLInputElement>(null);
  const wasAtBottom = useRef(true);

  // Track whether user is near the bottom
  const onScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    wasAtBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 160;
  }, []);

  // Smooth scroll only if user was already near the bottom
  useEffect(() => {
    if (wasAtBottom.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, loading]);

  const send = useCallback(async (override?: string) => {
    const text = (override ?? input).trim();
    if (!text || loading) return;

    const next: Message[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setLoading(true);
    wasAtBottom.current = true; // always scroll for new message

    try {
      const res = await axios.post("/api/chat", {
        message: text,
        chat_history: messages,
      });
      setMessages([
        ...next,
        {
          role: "assistant",
          content: res.data.answer ?? "No response received.",
          sources: res.data.sources ?? [],
          source_details: res.data.source_details ?? [],
          confidence: res.data.confidence ?? undefined,
          trace: res.data.trace ?? undefined,
        },
      ]);
      // Fire OS notification if tab is hidden and user has it enabled
      const notifyOn = localStorage.getItem("notif-enabled") !== "false";
      if (notifyOn && document.hidden && Notification.permission === "granted") {
        new Notification("Lenovo Research Workspace", {
          body: (res.data.answer ?? "Answer ready.").slice(0, 120),
        });
      }
    } catch (err: any) {
      // THIS PRINTS THE EXACT PYTHON BUG ON YOUR SCREEN
      const pythonError = err.response?.data?.detail || err.message || "Unknown Crash";
      const errorMsg = typeof pythonError === 'object' ? JSON.stringify(pythonError) : pythonError;
      
      setMessages([
        ...next,
        {
          role: "assistant",
          content: `**Backend Error Details:** \n\n\`${errorMsg}\` \n\nCheck your FastAPI terminal for the full traceback!`,
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [input, loading, messages, setMessages]);

  return (
    <div
      className="flex-1 flex flex-col h-full relative overflow-hidden"
      style={{ background: "linear-gradient(160deg, #0E1117 0%, #0B0F16 100%)" }}
    >
      {/* Top-right action icons */}
      <div className="absolute top-5 right-6 z-10 flex items-center gap-2.5">
        <Link
          href="/health"
          className="p-2.5 rounded-full bg-white/[0.04] hover:bg-white/8 border border-white/[0.06] text-slate-400 hover:text-white transition-all duration-200"
          title="System Telemetry"
        >
          <Activity size={18} />
        </Link>
        <Link
          href="/"
          className="p-2.5 rounded-full bg-white/[0.04] hover:bg-white/8 border border-white/[0.06] text-slate-400 hover:text-white transition-all duration-200"
          title="Back to Hub"
        >
          <ArrowLeft size={18} />
        </Link>
        <PreferencesPanel />
      </div>

      {/* Scroll area */}
      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto custom-scrollbar px-6 md:px-10 pt-10 pb-44"
      >
        <div className="max-w-3xl mx-auto space-y-8">
          {messages.length === 0 ? (
            <EmptyState onSend={send} />
          ) : (
            <AnimatePresence initial={false}>
              {messages.map((m, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
                >
                  <MessageBubble msg={m} idx={i} />
                </motion.div>
              ))}
            </AnimatePresence>
          )}

          {/* Smooth thinking indicator */}
          <AnimatePresence>
            {loading && (
              <motion.div
                key="thinking"
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              >
                <ThinkingBubble />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Scroll anchor */}
          <div ref={bottomRef} className="h-1" />
        </div>
      </div>

      {/* Floating input bar */}
      <div
        className="absolute bottom-0 left-0 right-0 px-6 md:px-10 pb-6 pt-16 pointer-events-none"
        style={{ background: "linear-gradient(to top, #0E1117 55%, transparent)" }}
      >
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form
            onSubmit={e => { e.preventDefault(); send(); }}
            className="relative flex items-center"
          >
            {/* Gradient border effect */}
            <div
              className="absolute inset-0 rounded-2xl pointer-events-none opacity-35"
              style={{
                padding: "1px",
                background: "linear-gradient(120deg, rgba(226,35,26,0.5), rgba(88,166,255,0.3), rgba(226,35,26,0.5))",
                WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
                WebkitMaskComposite: "xor",
                maskComposite: "exclude",
              }}
            />

            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question…"
              autoFocus
              className="w-full rounded-2xl pl-6 pr-16 py-5 text-[15px] text-white placeholder-slate-600 focus:outline-none transition-all duration-200"
              style={{
                background: "rgba(28,34,43,0.88)",
                border: "1px solid rgba(255,255,255,0.08)",
                backdropFilter: "blur(24px)",
                boxShadow: "0 12px 40px rgba(0,0,0,0.5)",
              }}
              onFocus={e => {
                e.currentTarget.style.borderColor = "rgba(226,35,26,0.4)";
                e.currentTarget.style.boxShadow = "0 12px 40px rgba(0,0,0,0.5), 0 0 0 3px rgba(226,35,26,0.08)";
              }}
              onBlur={e => {
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)";
                e.currentTarget.style.boxShadow = "0 12px 40px rgba(0,0,0,0.5)";
              }}
            />

            <motion.button
              type="submit"
              disabled={!input.trim() || loading}
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.92 }}
              transition={{ type: "spring", stiffness: 450, damping: 28 }}
              className="absolute right-3 p-3 rounded-xl text-white transition-colors shadow-lg disabled:opacity-30"
              style={{ background: input.trim() && !loading ? "#E2231A" : "rgba(255,255,255,0.06)" }}
            >
              <Send size={17} />
            </motion.button>
          </form>

          <p className="text-center mt-3 text-[11px] text-slate-600 tracking-wide">
            Always double-check important answers from primary sources.
          </p>
        </div>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function WorkspacePage() {
  const router = useRouter();
  // Start with null so both server and client render the same loading state
  // Auth is resolved client-side only in useEffect — no hydration mismatch
  const [authed, setAuthed] = useState<boolean | null>(null);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [counter, setCounter] = useState(1);
  const [currentId, setCurrentId] = useState("Chat 1");
  const [sessions, setSessions]   = useState<Record<string, Message[]>>({ "Chat 1": [] });

  // Client-only auth check — runs after hydration, no server/client mismatch
  useEffect(() => {
    const { authed: a, user: u } = readAuthFromStorage();
    if (!a) {
      router.replace("/sign-in");
    } else {
      setAuthed(true);
      setUser(u);
    }
  }, [router]);

  // Show loading spinner while auth state is being resolved
  if (authed !== true || !user) {
    return (
      <div className="min-h-screen bg-black flex flex-col items-center justify-center gap-7">
        <motion.div
          initial={{ scale: 0.75, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="p-4 rounded-[18px]"
          style={{ background: "#E2231A", boxShadow: "0 0 48px rgba(226,35,26,0.45), 0 0 96px rgba(226,35,26,0.15)" }}
        >
          <svg width="34" height="34" viewBox="0 0 32 32" fill="none">
            <path d="M10 16L16 10L22 16" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M16 10V22" stroke="white" strokeWidth="3" strokeLinecap="round" />
          </svg>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-col items-center gap-1.5"
        >
          <span className="font-extrabold text-[20px] text-white tracking-tight">
            Lenovo<span className="text-red-500">.</span>LABS
          </span>
          <span className="text-[10px] text-white/20 font-bold uppercase tracking-[0.26em]">Research Workspace</span>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.38 }}
          className="flex gap-1.5"
        >
          {[0, 1, 2].map(i => (
            <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-white/18"
              animate={{ opacity: [0.18, 0.9, 0.18] }}
              transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.22 }} />
          ))}
        </motion.div>
      </div>
    );
  }

  const msgs = sessions[currentId] ?? [];

  const newChat = () => {
    const id = `Chat ${counter + 1}`;
    setCounter(c => c + 1);
    setSessions(s => ({ ...s, [id]: [] }));
    setCurrentId(id);
  };

  const clearWs = () => {
    setCounter(1);
    setSessions({ "Chat 1": [] });
    setCurrentId("Chat 1");
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-screen bg-[#0A0D12] text-slate-200 font-sans overflow-hidden"
    >
      <Sidebar
        user={user}
        onLogout={() => {
          try { localStorage.removeItem("lenovo_ai_auth"); } catch {}
          router.replace("/sign-in");
        }}
        sessions={Object.keys(sessions)}
        currentId={currentId}
        onSelect={setCurrentId}
        onNewChat={newChat}
        onClear={clearWs}
      />
      <ChatArea
        messages={msgs}
        setMessages={m => setSessions(s => ({ ...s, [currentId]: m }))}
      />
    </motion.div>
  );
}
