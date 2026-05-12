"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Bot, Cpu, Database, Network, Shield, Zap, Activity } from "lucide-react";
import { motion, useScroll, useTransform } from "framer-motion";
import CinematicScene from "@/components/CinematicScene";

// ─── Cinematic Image Band ─────────────────────────────────────────────────────
// Full-width immersive parallax depth section — 4 independent motion layers
// creating a genuine 3D scene-flow effect on scroll.

type BandTheme = "signal" | "vault" | "cosmos";

const BAND_CFG: Record<BandTheme, {
  accent: string; label: string; headline: string; sub: string;
  gradient1: string; gradient2: string; gridColor: string;
  orb1: string; orb2: string;
}> = {
  signal: {
    accent:    "#22D3EE",
    label:     "DOCUMENT · SEARCH · ENGINE",
    headline:  "Your documents,\nsurfaced instantly.",
    sub:       "Searches thousands of pages in under 50ms. Returns the actual relevant passages, not just file names.",
    gradient1: "radial-gradient(ellipse 130% 90% at 35% 55%, rgba(6,182,212,0.25) 0%, rgba(14,60,160,0.18) 45%, transparent 72%)",
    gradient2: "radial-gradient(ellipse 80% 60% at 75% 35%, rgba(30,100,220,0.14) 0%, transparent 55%)",
    gridColor: "#0ea5e9",
    orb1:      "rgba(6,182,212,0.22)",
    orb2:      "rgba(20,80,200,0.14)",
  },
  vault: {
    accent:    "#E2231A",
    label:     "LOCAL · MODEL · INFERENCE",
    headline:  "Runs on your\nmachine, offline.",
    sub:       "Qwen 2.5 3B via Ollama — no internet needed for inference. Zero API costs, nothing leaves your machine.",
    gradient1: "radial-gradient(ellipse 130% 90% at 65% 50%, rgba(220,35,26,0.24) 0%, rgba(140,10,8,0.16) 45%, transparent 72%)",
    gradient2: "radial-gradient(ellipse 80% 60% at 20% 60%, rgba(160,12,8,0.14) 0%, transparent 55%)",
    gridColor: "#ef4444",
    orb1:      "rgba(220,35,26,0.20)",
    orb2:      "rgba(140,10,6,0.13)",
  },
  cosmos: {
    accent:    "#A78BFA",
    label:     "QUERY · PLANNING · LOOP",
    headline:  "Thinks it through,\nthen answers.",
    sub:       "Does not just keyword-match — breaks the question down, decides what to look up, and pulls from multiple sources to form a complete answer.",
    gradient1: "radial-gradient(ellipse 130% 90% at 50% 45%, rgba(124,58,237,0.24) 0%, rgba(76,29,149,0.16) 45%, transparent 72%)",
    gradient2: "radial-gradient(ellipse 80% 60% at 80% 65%, rgba(192,38,211,0.14) 0%, transparent 55%)",
    gridColor: "#8b5cf6",
    orb1:      "rgba(124,58,237,0.20)",
    orb2:      "rgba(192,38,211,0.13)",
  },
};

function CinematicImageBand({ theme }: { theme: BandTheme }) {
  const ref   = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });

  // Four independent depth layers — each moves at a distinct rate
  const bg1Y  = useTransform(scrollYProgress, [0, 1], ["-90px",  "90px"]);
  const bg2Y  = useTransform(scrollYProgress, [0, 1], ["-52px",  "52px"]);
  const orbY  = useTransform(scrollYProgress, [0, 1], ["-30px",  "30px"]);
  const txtY  = useTransform(scrollYProgress, [0, 1], [ "56px", "-56px"]);

  // Zoom breathes the deepest layer (cinematic focus pull)
  const bg1Scale = useTransform(scrollYProgress, [0, 0.45, 1], [1.18, 1.05, 0.92]);
  const bg2Scale = useTransform(scrollYProgress, [0, 0.5,  1], [1.10, 1.04, 0.97]);

  // Opacity fades section in + out at extremes
  const sectionOp = useTransform(scrollYProgress, [0, 0.10, 0.90, 1], [0, 1, 1, 0]);
  const textOp    = useTransform(scrollYProgress, [0.04, 0.22, 0.78, 0.96], [0, 1, 1, 0]);
  const textScale = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0.90, 1, 1, 0.94]);

  const c = BAND_CFG[theme];
  const gridId = `grid-${theme}`;

  return (
    <section ref={ref} className="relative w-full overflow-hidden select-none" style={{ height: "72vh", minHeight: "520px" }}>

      {/* ── DEPTH LAYER 1: Gradient base + SVG grid (deepest, most zoom) ── */}
      <motion.div className="absolute inset-0 will-change-transform" style={{ y: bg1Y, scale: bg1Scale, opacity: sectionOp }}>
        <div className="absolute inset-0 bg-black" />
        <div className="absolute inset-0" style={{ background: c.gradient1 }} />
        <div className="absolute inset-0" style={{ background: c.gradient2 }} />
        {/* Perspective grid — infinity vanishing point */}
        <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="xMidYMid slice">
          <defs>
            <pattern id={gridId} width="72" height="72" patternUnits="userSpaceOnUse">
              <path d="M72 0L0 0 0 72" fill="none" stroke={c.gridColor} strokeWidth="0.5" strokeOpacity="0.10" />
            </pattern>
            <radialGradient id={`mask-${theme}`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="white" stopOpacity="0.6" />
              <stop offset="70%" stopColor="white" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="100%" height="100%" fill={`url(#${gridId})`} mask={`url(#mask-${theme})`} />
        </svg>
        {/* Hard vignette edge */}
        <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse 88% 80% at 50% 50%, transparent 22%, rgba(0,0,0,0.90) 100%)" }} />
        <div className="absolute inset-x-0 top-0 h-52 bg-gradient-to-b from-black to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-52 bg-gradient-to-t from-black to-transparent" />
      </motion.div>

      {/* ── DEPTH LAYER 2: Ambient orbs (mid-depth, less zoom) ── */}
      <motion.div className="absolute inset-0 will-change-transform pointer-events-none" style={{ y: bg2Y, scale: bg2Scale, opacity: sectionOp }}>
        <div className="orb-drift-1 absolute rounded-full" style={{
          width: "48vw", height: "48vw", left: "4%", top: "5%",
          background: `radial-gradient(circle, ${c.orb1} 0%, transparent 65%)`,
          filter: "blur(40px)",
        }} />
        <div className="orb-drift-2 absolute rounded-full" style={{
          width: "36vw", height: "36vw", right: "6%", bottom: "8%",
          background: `radial-gradient(circle, ${c.orb2} 0%, transparent 65%)`,
          filter: "blur(50px)",
        }} />
      </motion.div>

      {/* ── DEPTH LAYER 3: Floating accent line (mid-foreground) ── */}
      <motion.div className="absolute inset-0 pointer-events-none" style={{ y: orbY, opacity: sectionOp }}>
        <div className="absolute" style={{
          left: "50%", top: "50%", transform: "translate(-50%,-50%)",
          width: "min(700px, 90vw)", height: "1px",
          background: `linear-gradient(90deg, transparent, ${c.accent}45, transparent)`,
        }} />
        <div className="absolute" style={{
          left: "50%", top: "50%", transform: "translate(-50%,-50%) translateY(2px)",
          width: "min(300px, 55vw)", height: "1px",
          background: `linear-gradient(90deg, transparent, ${c.accent}20, transparent)`,
        }} />
      </motion.div>

      {/* ── DEPTH LAYER 4: Text — counter-parallax (foreground) ── */}
      <div className="absolute inset-0 flex items-center justify-center z-20">
        <motion.div style={{ y: txtY, opacity: textOp, scale: textScale }} className="text-center px-8 will-change-transform">
          <p className="text-[9px] font-bold tracking-[0.38em] uppercase mb-5" style={{ color: c.accent, opacity: 0.65 }}>
            {c.label}
          </p>
          <h2 className="font-extrabold tracking-tight leading-[1.04]"
            style={{
              fontSize: "clamp(2.4rem, 4.8vw, 5.2rem)",
              background: `linear-gradient(155deg, #ffffff 28%, ${c.accent}85 100%)`,
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
            }}
          >
            {c.headline.split("\n").map((l, i) => <span key={i} className="block">{l}</span>)}
          </h2>
          <motion.p
            initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: false, margin: "-15%" }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
            className="text-white/30 mt-5 mx-auto leading-relaxed"
            style={{ maxWidth: "min(560px, 90vw)", fontSize: "clamp(0.85rem, 1.4vw, 1.05rem)" }}
          >
            {c.sub}
          </motion.p>
          {/* Accent rule */}
          <motion.div
            initial={{ width: 0, opacity: 0 }} whileInView={{ width: 100, opacity: 0.5 }}
            viewport={{ once: false, margin: "-20%" }}
            transition={{ duration: 1.0, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto mt-7"
            style={{ height: "1px", background: `linear-gradient(90deg, transparent, ${c.accent}, transparent)` }}
          />
        </motion.div>
      </div>
    </section>
  );
}

// ─── Motion variants ──────────────────────────────────────────────────────────
// Each card gets a direction that communicates its position on screen

const fadeLeft  = { hidden: { opacity: 0, x: -52, rotateX: 9, filter: "blur(4px)" }, visible: { opacity: 1, x: 0, rotateX: 0, filter: "blur(0px)" } };
const fadeRight = { hidden: { opacity: 0, x:  52, rotateX: 9, filter: "blur(4px)" }, visible: { opacity: 1, x: 0, rotateX: 0, filter: "blur(0px)" } };
const fadeUp    = { hidden: { opacity: 0, y:  44, rotateX: 12, filter: "blur(3px)" }, visible: { opacity: 1, y: 0, rotateX: 0, filter: "blur(0px)" } };

const easeOut = { ease: [0.22, 1, 0.36, 1] as const, duration: 0.75 };

// ─── Section label ────────────────────────────────────────────────────────────

function SectionLabel({ children }: { children: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={easeOut}
      className="flex items-center gap-3 mb-8"
    >
      <div className="h-px flex-1 bg-white/[0.06]" />
      <span className="text-[10px] font-bold tracking-[0.28em] uppercase text-white/25">{children}</span>
      <div className="h-px flex-1 bg-white/[0.06]" />
    </motion.div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function LandingPage() {
  const gridRef    = useRef<HTMLDivElement>(null);
  const heroRef    = useRef<HTMLElement>(null);

  // Hero camera-dolly — content recedes as user scrolls past
  const { scrollYProgress: heroProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const heroScale = useTransform(heroProgress, [0, 1], [1, 0.93]);
  const heroY     = useTransform(heroProgress, [0, 1], [0, -72]);
  const heroOp    = useTransform(heroProgress, [0, 0.68], [1, 0]);

  useEffect(() => {
    // Throttle DOM writes to requestAnimationFrame (60fps max)
    // getBoundingClientRect() batched inside rAF avoids forced-layout thrashing
    let rafId = 0;
    let cx = 0, cy = 0;

    const flush = () => {
      const cards = document.querySelectorAll(".bento-card") as NodeListOf<HTMLElement>;
      cards.forEach(card => {
        const r = card.getBoundingClientRect();
        card.style.setProperty("--mouse-x", `${cx - r.left}px`);
        card.style.setProperty("--mouse-y", `${cy - r.top}px`);
      });
    };

    const onMove = (e: MouseEvent) => {
      cx = e.clientX;
      cy = e.clientY;
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(flush);
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    return () => {
      window.removeEventListener("mousemove", onMove);
      cancelAnimationFrame(rafId);
    };
  }, []);

  return (
    <div className="relative min-h-screen bg-black text-slate-200 overflow-x-hidden selection:bg-red-500/20">

      {/* Static dot-grid background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff06_1px,transparent_1px),linear-gradient(to_bottom,#ffffff06_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_55%,transparent_100%)]" />
      </div>

      {/* ══ NAV ════════════════════════════════════════════════════════════ */}
      <motion.nav
        initial={{ y: -24, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-50 flex justify-between items-center px-8 md:px-16 py-5 bg-black/75 backdrop-blur-2xl border-b border-white/[0.05] sticky top-0"
      >
        <Link href="/" className="flex items-center gap-3 group">
          <svg width="30" height="30" viewBox="0 0 32 32" fill="none" className="group-hover:scale-110 transition-transform duration-300">
            <rect width="32" height="32" rx="8" fill="#E2231A" />
            <path d="M10 16L16 10L22 16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M16 10V22" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
          <div className="flex flex-col leading-tight">
            <span className="font-extrabold text-[18px] tracking-tight text-white group-hover:text-red-400 transition-colors duration-300">Lenovo.LABS</span>
            <span className="text-[9px] text-white/25 font-bold uppercase tracking-[0.22em]">Research Workspace</span>
          </div>
        </Link>

        <div className="flex gap-3 md:gap-5 items-center">
          <Link href="/analytics" className="hidden md:flex items-center gap-1.5 text-[13px] font-semibold text-white/45 hover:text-cyan-400 transition-colors duration-200">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>
            Analytics
          </Link>
          <Link href="/health" className="hidden md:flex items-center gap-1.5 text-[13px] font-semibold text-white/45 hover:text-emerald-400 transition-colors duration-200">
            <Activity size={13} /> Telemetry
          </Link>
          <Link href="/workspace"
            className="text-[13px] font-bold text-white bg-red-600 hover:bg-red-500 px-5 py-2.5 rounded-full transition-all duration-200 shadow-[0_4px_20px_rgba(226,35,26,0.3)] hover:shadow-[0_4px_28px_rgba(226,35,26,0.45)] hover:-translate-y-px">
            Launch Workspace
          </Link>
        </div>
      </motion.nav>

      {/* ══ HERO ═══════════════════════════════════════════════════════════ */}
      <section ref={heroRef} className="relative z-10 flex flex-col items-center text-center px-6 pt-28 pb-24 overflow-hidden">
        {/* CSS-animated ambient orbs — anchored, do not participate in dolly */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="hero-orb-1 absolute rounded-full" style={{
            width: "65vw", height: "65vw", left: "-16%", top: "-18%",
            background: "radial-gradient(circle, rgba(0,180,220,0.11) 0%, transparent 65%)",
            filter: "blur(40px)",
          }} />
          <div className="hero-orb-2 absolute rounded-full" style={{
            width: "55vw", height: "55vw", right: "-12%", bottom: "-22%",
            background: "radial-gradient(circle, rgba(220,30,20,0.10) 0%, transparent 65%)",
            filter: "blur(50px)",
          }} />
        </div>

        {/* Camera-dolly wrapper — content recedes at 1.4× scroll speed */}
        <motion.div
          style={{ scale: heroScale, y: heroY, opacity: heroOp }}
          className="relative z-10 flex flex-col items-center text-center w-full will-change-transform"
        >

        {/* Live badge */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 inline-flex items-center gap-2.5 px-5 py-2 bg-white/[0.04] border border-white/10 rounded-full text-[11px] font-bold text-white/60 mb-10 backdrop-blur-xl"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-60" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-cyan-400" />
          </span>
          Running locally · Lenovo
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 28 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.78, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 font-extrabold tracking-tight leading-[1.04] max-w-5xl mx-auto mb-7"
          style={{ fontSize: "clamp(2.8rem, 7.5vw, 6rem)" }}
        >
          <span className="text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-white/38">
            Ask anything.
          </span>
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-red-700">
            Get real answers.
          </span>
        </motion.h1>

        {/* Sub */}
        <motion.p
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.26, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 text-[17px] md:text-xl text-white/38 max-w-2xl mx-auto mb-12 leading-relaxed"
        >
          Searches your Lenovo documents, falls back to the web when needed. Runs on your machine — nothing goes to the cloud.
        </motion.p>

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.34, ease: [0.22, 1, 0.36, 1] }}
          className="relative z-10 flex flex-col sm:flex-row flex-wrap justify-center gap-3"
        >
          <Link href="/workspace" className="group inline-flex items-center justify-center gap-2.5 bg-red-600 text-white px-7 py-3.5 rounded-full font-bold text-[15px] hover:bg-red-500 hover:-translate-y-0.5 transition-all duration-200 shadow-[0_8px_32px_rgba(226,35,26,0.32)]">
            Enter Workspace <ArrowRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link href="/analytics" className="inline-flex items-center justify-center gap-2.5 bg-white/[0.05] text-white/75 px-7 py-3.5 rounded-full font-bold text-[15px] border border-white/8 hover:bg-white/10 hover:text-white hover:-translate-y-0.5 transition-all duration-200">
            View Analytics
          </Link>
          <Link href="/health" className="inline-flex items-center justify-center gap-2.5 bg-white/[0.05] text-white/75 px-7 py-3.5 rounded-full font-bold text-[15px] border border-white/8 hover:bg-white/10 hover:text-white hover:-translate-y-0.5 transition-all duration-200">
            Live Telemetry
          </Link>
        </motion.div>

        </motion.div>{/* /camera-dolly */}
      </section>

      {/* ══ STATS TICKER ═══════════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.45 }}
        className="relative z-10 border-y border-white/[0.05] bg-black/50 py-4"
      >
        <div className="max-w-5xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-3">
          {[
            { icon: <Zap size={14} className="text-yellow-400" />, text: "Sub-50ms query routing" },
            { icon: <Database size={14} className="text-cyan-400" />, text: "Semantic document search" },
            { icon: <Bot size={14} className="text-red-400" />, text: "Qwen 2.5 · runs on-device" },
          ].map(({ icon, text }) => (
            <div key={text} className="flex items-center gap-2 text-[10px] font-bold text-white/25 tracking-[0.2em] uppercase">
              {icon} {text}
            </div>
          ))}
        </div>
      </motion.div>

      {/* ══ SCENE 1 — Neural ═══════════════════════════════════════════════ */}
      <CinematicScene variant="neural" />

      {/* Full-width cinematic depth band — RAG / retrieval story */}
      <CinematicImageBand theme="signal" />

      {/* ══ BENTO GROUP A — Routing architecture ═══════════════════════════ */}
      <div ref={gridRef} className="relative z-10 max-w-[1320px] mx-auto px-6 py-16" style={{ perspective: "1200px" }}>
        <SectionLabel>How it works</SectionLabel>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-12 gap-5"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          transition={{ staggerChildren: 0.12 }}
        >
          {/* Large card — slides from left */}
          <motion.div
            variants={fadeLeft}
            transition={{ ...easeOut }}
            className="col-span-1 md:col-span-8"
          >
            <Link href="/workspace" className="bento-card flex flex-col justify-end min-h-[380px] group">
              {/* Background highlight glow on hover */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[28px]"
                style={{ background: "radial-gradient(ellipse 70% 60% at 20% 80%, rgba(226,35,26,0.08) 0%, transparent 70%)" }} />
              <div className="relative z-10">
                <div className="bg-white/[0.04] text-red-500 w-14 h-14 rounded-2xl flex items-center justify-center mb-7 border border-white/[0.06] group-hover:scale-105 group-hover:border-red-500/30 transition-all duration-300">
                  <Network size={26} />
                </div>
                <h2 className="text-[28px] md:text-3xl font-extrabold text-white mb-3 tracking-tight group-hover:text-red-400 transition-colors duration-300">Smart query routing</h2>
                <p className="text-[15px] text-white/38 max-w-lg leading-relaxed">
                  Every question gets routed automatically — to your local documents, the on-device model, or a live web search — in under 50ms.
                </p>
                <div className="mt-6 inline-flex items-center gap-2 text-[12px] font-bold text-red-500/70 group-hover:text-red-400 transition-colors">
                  Open Workspace <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
                </div>
              </div>
            </Link>
          </motion.div>

          {/* Small card — slides from right */}
          <motion.div
            variants={fadeRight}
            transition={{ ...easeOut, delay: 0.06 }}
            className="col-span-1 md:col-span-4"
          >
            <div className="bento-card flex flex-col min-h-[380px] group">
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[28px]"
                style={{ background: "radial-gradient(ellipse 70% 60% at 80% 20%, rgba(6,182,212,0.07) 0%, transparent 70%)" }} />
              <div className="relative z-10 flex flex-col h-full">
                <div className="bg-white/[0.04] text-cyan-500 w-14 h-14 rounded-2xl flex items-center justify-center mb-7 border border-white/[0.06] group-hover:scale-105 group-hover:border-cyan-500/30 transition-all duration-300">
                  <Cpu size={24} />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3 group-hover:text-cyan-400 transition-colors duration-300">Runs on your machine</h3>
                <p className="text-[15px] text-white/38 leading-relaxed flex-1">Qwen 2.5 3B through Ollama — fully local. No API calls, no usage costs, your files never leave the device.</p>

                {/* Animated utilisation bar */}
                <div className="mt-auto pt-6 space-y-2">
                  {[["Model Load", "85%", "bg-cyan-500"], ["Memory", "62%", "bg-blue-500"], ["Throughput", "91%", "bg-teal-500"]].map(([lbl, val, cls]) => (
                    <div key={lbl as string}>
                      <div className="flex justify-between text-[10px] text-white/25 mb-1">
                        <span>{lbl as string}</span><span>{val as string}</span>
                      </div>
                      <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                        <motion.div
                          className={`h-full ${cls as string} rounded-full`}
                          initial={{ width: "0%" }}
                          whileInView={{ width: val as string }}
                          transition={{ duration: 1.1, delay: 0.4, ease: [0.22, 1, 0.36, 1] }}
                          viewport={{ once: true }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* ══ SCENE 2 — Datacenter ═══════════════════════════════════════════ */}
      <CinematicScene variant="datacenter" />

      {/* Full-width cinematic depth band — edge inference / data sovereignty */}
      <CinematicImageBand theme="vault" />

      {/* ══ BENTO GROUP B — Integrated capabilities ═════════════════════════ */}
      <div className="relative z-10 max-w-[1320px] mx-auto px-6 py-16" style={{ perspective: "1200px" }}>
        <SectionLabel>What&apos;s included</SectionLabel>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-5"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          transition={{ staggerChildren: 0.11 }}
        >
          {[
            {
              icon: <Database size={22} />,
              accent: "#34D399",
              hoverGrad: "rgba(52,211,153,0.07)",
              title: "Document memory",
              desc: "Indexes everything in data/ using MiniLM embeddings. Finds the most relevant passages even when you do not know exactly what to search for.",
              tag: "Vector DB",
            },
            {
              icon: <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>,
              accent: "#60A5FA",
              hoverGrad: "rgba(96,165,250,0.07)",
              title: "Analytics dashboard",
              desc: "Charts covering global market data, platform performance, and what the industry is actually doing with this stuff.",
              tag: "Analytics",
              href: "/analytics",
            },
            {
              icon: <Shield size={22} />,
              accent: "#A78BFA",
              hoverGrad: "rgba(167,139,250,0.07)",
              title: "Access control",
              desc: "Email-based OTP login. Session stored locally — no backend auth server needed for the demo.",
              tag: "Auth",
              href: "/workspace",
            },
          ].map(({ icon, accent, hoverGrad, title, desc, tag, href }, i) => {
            const inner = (
              <div className="bento-card flex flex-col min-h-[300px] group relative">
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[28px]"
                  style={{ background: `radial-gradient(ellipse 70% 60% at 50% 50%, ${hoverGrad} 0%, transparent 70%)` }} />
                <div className="relative z-10 flex flex-col h-full">
                  {/* Tag */}
                  <div className="self-start mb-6 px-2.5 py-1 rounded-full text-[9px] font-bold tracking-[0.18em] uppercase"
                    style={{ color: accent, background: `${accent}12`, border: `1px solid ${accent}25` }}>
                    {tag}
                  </div>
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-5 border transition-all duration-300 group-hover:scale-105"
                    style={{ color: accent, background: `${accent}10`, borderColor: `${accent}20` }}>
                    {icon}
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3 transition-colors duration-300"
                    style={{ ["--hover-color" as string]: accent }}
                    onMouseEnter={e => (e.currentTarget.style.color = accent)}
                    onMouseLeave={e => (e.currentTarget.style.color = "white")}
                  >{title}</h3>
                  <p className="text-[14px] text-white/38 leading-relaxed">{desc}</p>

                  {href && (
                    <div className="mt-auto pt-5 flex items-center gap-1.5 text-[11px] font-bold transition-colors duration-200"
                      style={{ color: `${accent}70` }}>
                      Explore <ArrowRight size={11} />
                    </div>
                  )}
                </div>
              </div>
            );

            return (
              <motion.div
                key={title}
                variants={fadeUp}
                transition={{ ...easeOut, delay: i * 0.1 }}
              >
                {href ? <Link href={href}>{inner}</Link> : inner}
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      {/* ══ SCENE 3 — Cosmos ═══════════════════════════════════════════════ */}
      <CinematicScene variant="cosmos" />

      {/* Full-width cinematic depth band — agentic multi-step reasoning */}
      <CinematicImageBand theme="cosmos" />

      {/* ══ FOOTER MARQUEE ═════════════════════════════════════════════════ */}
      <div className="relative z-10 border-t border-white/[0.04] bg-black py-10 overflow-hidden">
        <div className="flex whitespace-nowrap" style={{ animation: "marquee 38s linear infinite" }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex items-center gap-10 px-8">
              {["Next.js 16", "FastAPI", "ChromaDB", "Qwen 2.5", "Ollama", "Tailwind v4", "Tavily", "Framer Motion"].map(t => (
                <span key={t} className="inline-flex items-center gap-10">
                  <span className="text-[12px] font-bold text-white/12 tracking-[0.28em]">{t}</span>
                  <span className="text-white/6">✦</span>
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
