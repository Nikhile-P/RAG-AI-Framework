"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, Activity, Server, FileSearch, Zap, AlertCircle, ExternalLink } from "lucide-react";
import { motion, AnimatePresence, useScroll, useTransform } from "framer-motion";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, CartesianGrid,
} from "recharts";
import axios from "axios";

type TelemetryLog = {
  ts?: string;
  query?: string;
  path?: string;
  details?: {
    relevance?: number;
    confidence?: string;
  };
};

type TelemetryResponse = {
  total_queries?: number;
  avg_relevance?: number;
  file_count?: number;
  routing_counts?: Record<string, number>;
  recent_logs?: TelemetryLog[];
};

type ChartTooltipPayload = {
  value?: string | number;
};

type ChartTooltipProps = {
  active?: boolean;
  payload?: ChartTooltipPayload[];
  label?: string;
};

// ─── Shared motion config ──────────────────────────────────────────────────────
const fadeUp = {
  hidden:  { opacity: 0, y: 36, rotateX: 10, filter: "blur(3px)" },
  visible: { opacity: 1, y: 0,  rotateX: 0,  filter: "blur(0px)" },
};
const ease = [0.22, 1, 0.36, 1] as const;

// ─── Recharts custom tooltip ──────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl px-3 py-2 text-xs font-semibold"
      style={{ background: "rgba(8,8,14,0.95)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(16px)" }}>
      <p className="text-white/40 mb-0.5">{label}</p>
      <p className="text-white">{payload[0].value}</p>
    </div>
  );
}

// ─── Parallax section wrapper ──────────────────────────────────────────────────
function ScrollSection({ children, className }: { children: React.ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "center center"] });
  const y = useTransform(scrollYProgress, [0, 1], ["48px", "-16px"]);
  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
}

// ─── Metric card ──────────────────────────────────────────────────────────────
function MetricCard({ icon: Icon, label, value, color, index }: {
  icon: React.ElementType; label: string; value: React.ReactNode; color: string; index: number;
}) {
  return (
    <motion.div
      variants={fadeUp}
      transition={{ duration: 0.65, ease, delay: index * 0.07 }}
      className="relative rounded-2xl p-6 overflow-hidden"
      style={{
        background: "rgba(10,10,14,0.7)",
        border: "1px solid rgba(255,255,255,0.07)",
        backdropFilter: "blur(20px)",
      }}
    >
      <div className="absolute top-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${color}40, transparent)` }} />
      <div className="flex items-center gap-2.5 mb-3">
        <Icon size={15} style={{ color }} />
        <span className="text-[11px] font-bold tracking-[0.15em] uppercase" style={{ color, opacity: 0.75 }}>{label}</span>
      </div>
      <div className="text-4xl font-extrabold text-white tracking-tight">{value}</div>
    </motion.div>
  );
}

// ─── Chart card ──────────────────────────────────────────────────────────────
function ChartCard({ title, children, index }: { title: string; children: React.ReactNode; index: number }) {
  return (
    <motion.div
      variants={fadeUp}
      transition={{ duration: 0.78, ease, delay: index * 0.08 }}
      className="relative rounded-2xl p-6 overflow-hidden"
      style={{
        background: "rgba(10,10,14,0.7)",
        border: "1px solid rgba(255,255,255,0.07)",
        backdropFilter: "blur(20px)",
        minHeight: 320,
      }}
    >
      <div className="absolute top-0 left-0 right-0 h-px"
        style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)" }} />
      <h3 className="text-[13px] font-bold text-white/70 tracking-wide uppercase mb-6">{title}</h3>
      {children}
    </motion.div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────
const POLL_MS = 5000;

export default function HealthPage() {
  const [telemetry,     setTelemetry]     = useState<TelemetryResponse | null>(null);
  const [loading,       setLoading]       = useState(true);
  const [refreshing,    setRefreshing]    = useState(false);
  const [backendOnline, setBackendOnline] = useState(true);
  const [lastUpdated,   setLastUpdated]   = useState<Date | null>(null);
  const [countdown,     setCountdown]     = useState(POLL_MS / 1000);

  // Fetch + set timestamps
  useEffect(() => {
    const doFetch = async () => {
      setRefreshing(true);
      try {
        const res = await axios.get("/api/telemetry", { timeout: 4000 });
        setTelemetry(res.data);
        setBackendOnline(true);
        setLastUpdated(new Date());
      } catch {
        setBackendOnline(false);
      } finally {
        setLoading(false);
        setRefreshing(false);
        setCountdown(POLL_MS / 1000);
      }
    };

    doFetch();
    const pollTimer = setInterval(doFetch, POLL_MS);

    // Countdown ticks every second between polls
    const cdTimer = setInterval(() => {
      setCountdown(c => (c > 1 ? c - 1 : POLL_MS / 1000));
    }, 1000);

    return () => { clearInterval(pollTimer); clearInterval(cdTimer); };
  }, []);

  const {
    total_queries = 0,
    avg_relevance = 0,
    file_count = 0,
    routing_counts = {},
    recent_logs = [],
  } = telemetry ?? {};

  const routingData = Object.entries(routing_counts as Record<string, number>)
    .map(([name, count]) => ({ name, count }));

  const relevanceTimeline = (recent_logs as TelemetryLog[])
    .filter((l): l is TelemetryLog & { details: { relevance: number } } => l.details?.relevance != null)
    .map((l, i) => ({ i, rel: +l.details.relevance.toFixed(3) }));

  const BAR_COLORS = ["#22D3EE", "#FBBF24", "#F87171", "#34D399"];

  // ── Loading ────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="flex flex-col items-center gap-5">
          <div className="relative w-14 h-14">
            <div className="absolute inset-0 rounded-full border-2 border-white/6 border-t-cyan-500 animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <Activity size={18} className="text-cyan-400" />
            </div>
          </div>
          <p className="text-[13px] font-semibold text-white/30 tracking-wide">Fetching telemetry…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-slate-200 overflow-x-hidden">

      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_60%_40%_at_50%_0%,#000_60%,transparent_100%)]" />
        <div className="absolute top-0 left-1/4 w-[50vw] h-[30vh] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(6,182,212,0.06) 0%, transparent 70%)", filter: "blur(60px)" }} />
      </div>

      {/* ── Nav ────────────────────────────────────────────────────────────── */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, ease }}
        className="sticky top-0 z-50 flex justify-between items-center px-8 md:px-14 py-5 bg-black/75 backdrop-blur-2xl border-b border-white/[0.05]"
      >
        <div className="flex items-center gap-4">
          <Link href="/" className="p-2 rounded-full bg-white/5 hover:bg-white/10 text-white/40 hover:text-white transition-all duration-200">
            <ArrowLeft size={18} />
          </Link>
          <div className="w-px h-5 bg-white/8" />
          <Link href="/" className="flex items-center gap-2.5">
            <svg width="24" height="24" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="7" fill="#E2231A" />
              <path d="M10 16L16 10L22 16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M16 10V22" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
            <span className="font-bold text-[15px] text-white">Lenovo.LABS</span>
            <span className="text-white/20">/</span>
            <span className="font-semibold text-[14px] text-white/55">Telemetry</span>
          </Link>
        </div>

        <div className="flex items-center gap-3">
          {/* Backend status + last-updated + countdown */}
          <div className="hidden md:flex items-center gap-2.5">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-[11px] font-bold tracking-wide transition-colors duration-500 ${
              backendOnline
                ? "bg-emerald-500/8 border-emerald-500/20 text-emerald-400"
                : "bg-red-500/8 border-red-500/20 text-red-400"
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${backendOnline ? "bg-emerald-400 animate-pulse" : "bg-red-400"}`} />
              {backendOnline ? "LIVE" : "OFFLINE"}
            </div>

            {backendOnline && lastUpdated && (
              <div className="flex items-center gap-1.5 text-[10px] text-white/25">
                <motion.span
                  key={String(refreshing)}
                  animate={refreshing ? { opacity: [0.4, 1, 0.4] } : { opacity: 1 }}
                  transition={{ duration: 0.9, repeat: refreshing ? Infinity : 0 }}
                  className="font-mono"
                >
                  {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                </motion.span>
                <span className="text-white/15">·</span>
                <span className="font-mono text-white/20">↻{countdown}s</span>
              </div>
            )}
          </div>

          <Link href="/workspace"
            className="text-[13px] font-bold text-white bg-white/8 border border-white/10 px-4 py-2 rounded-full hover:bg-white/14 transition-all duration-200">
            Research Workspace
          </Link>
        </div>
      </motion.nav>

      {/* ── Hero band ──────────────────────────────────────────────────────── */}
      <div className="relative px-8 md:px-14 pt-12 pb-10 border-b border-white/[0.05]">
        <motion.p initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease, delay: 0.05 }}
          className="text-[10px] font-bold tracking-[0.3em] uppercase text-cyan-400/55 mb-3">
          Lenovo Research · System
        </motion.p>
        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease, delay: 0.12 }}
          className="font-extrabold text-white tracking-tight mb-2"
          style={{ fontSize: "clamp(1.8rem, 3.5vw, 3rem)" }}>
          System status
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.22 }}
          className="text-[14px] text-white/30">
          Live query counts, relevance scores, and routing breakdown. Refreshes every 5 seconds.
        </motion.p>
      </div>

      <main className="relative z-10 max-w-7xl mx-auto px-8 md:px-14 py-12 space-y-8">

        {/* ── Metric cards ──────────────────────────────────────────────── */}
        {!backendOnline && (
          <motion.div
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 px-5 py-4 rounded-2xl border border-yellow-500/20 bg-yellow-500/5"
          >
            <AlertCircle size={16} className="text-yellow-400 flex-shrink-0" />
            <div>
              <p className="text-[13px] font-semibold text-yellow-300">Backend offline</p>
              <p className="text-[12px] text-yellow-400/60 mt-0.5">Start the backend server to see live data.</p>
            </div>
          </motion.div>
        )}

        <motion.div
          className="grid grid-cols-2 md:grid-cols-4 gap-4"
          style={{ perspective: "1200px" }}
          initial="hidden"
          animate="visible"
          transition={{ staggerChildren: 0.07 }}
        >
          <MetricCard icon={Server}    label="Total Queries" color="#22D3EE" index={0}
            value={
              <AnimatePresence mode="wait">
                <motion.span key={total_queries}
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                  className="tabular-nums"
                >{total_queries}</motion.span>
              </AnimatePresence>
            } />
          <MetricCard icon={FileSearch} label="Avg Relevance" color="#34D399" index={1}
            value={
              <AnimatePresence mode="wait">
                <motion.span key={avg_relevance.toFixed(2)}
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                  className="tabular-nums"
                >{avg_relevance.toFixed(2)}</motion.span>
              </AnimatePresence>
            } />
          <MetricCard icon={AlertCircle} label="Indexed Files" color="#E2231A" index={2}
            value={
              <AnimatePresence mode="wait">
                <motion.span key={file_count}
                  initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
                  className="tabular-nums"
                >{file_count}</motion.span>
              </AnimatePresence>
            } />
          <MetricCard icon={Zap} label="Live Status" color="#FBBF24" index={3}
            value={
              <span className={`flex items-center gap-2 text-2xl ${backendOnline ? "text-emerald-400" : "text-red-400"}`}>
                <span className={`w-3 h-3 rounded-full flex-shrink-0 ${backendOnline ? "bg-emerald-400 shadow-[0_0_10px_#34d399] animate-pulse" : "bg-red-400"}`} />
                {backendOnline ? "ONLINE" : "OFFLINE"}
              </span>
            } />
        </motion.div>

        {/* ── Charts ────────────────────────────────────────────────────── */}
        <ScrollSection>
        <motion.div
          className="grid grid-cols-1 lg:grid-cols-2 gap-5"
          style={{ perspective: "1200px" }}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-60px" }}
          transition={{ staggerChildren: 0.1 }}
        >
          <ChartCard title="Query Routing Distribution" index={0}>
            {routingData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={routingData} barCategoryGap="35%">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="name" stroke="rgba(255,255,255,0.18)" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis stroke="rgba(255,255,255,0.18)" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)", radius: 6 }} />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {routingData.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % 4]} fillOpacity={0.85} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-white/20 text-sm">No routing data yet</div>
            )}
          </ChartCard>

          <ChartCard title="Relevance Score Timeline" index={1}>
            {relevanceTimeline.length > 1 ? (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={relevanceTimeline}>
                  <defs>
                    <linearGradient id="relGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#34D399" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#34D399" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="i" hide />
                  <YAxis stroke="rgba(255,255,255,0.18)" domain={[0, 1]} tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="monotone" dataKey="rel" stroke="#34D399" strokeWidth={2.5}
                    dot={{ fill: "#0a0a0e", stroke: "#34D399", strokeWidth: 2, r: 3 }}
                    activeDot={{ r: 6, fill: "#34D399", stroke: "rgba(52,211,153,0.3)", strokeWidth: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-48 text-white/20 text-sm">No relevance data yet</div>
            )}
          </ChartCard>
        </motion.div>
        </ScrollSection>

        {/* ── Log table ─────────────────────────────────────────────────── */}
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-40px" }}
          variants={fadeUp}
          transition={{ duration: 0.65, ease }}
          className="relative rounded-2xl overflow-hidden"
          style={{
            background: "rgba(10,10,14,0.7)",
            border: "1px solid rgba(255,255,255,0.07)",
            backdropFilter: "blur(20px)",
          }}
        >
          <div className="absolute top-0 left-0 right-0 h-px"
            style={{ background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)" }} />
          <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.05]">
            <h3 className="text-[13px] font-bold text-white/70 tracking-wide uppercase">Live Routing Logs</h3>
            <div className="flex items-center gap-2 text-[11px] text-white/25">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Auto-refresh 5s
            </div>
          </div>

          <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[10px] font-bold text-white/25 tracking-[0.14em] uppercase">
                  {["Timestamp", "Query Snippet", "Route", "Confidence"].map(h => (
                    <th key={h} className="px-6 py-4 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="text-[13px] divide-y divide-white/[0.04]">
                {recent_logs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-white/20">
                      No routing logs available — run a query in the workspace.
                    </td>
                  </tr>
                ) : (
                  [...(recent_logs as TelemetryLog[])].reverse().map((log, idx: number) => (
                    <tr key={idx} className="hover:bg-white/[0.025] transition-colors duration-150">
                      <td className="px-6 py-4 text-white/25 font-mono text-[11px]">{log.ts}</td>
                      <td className="px-6 py-4 font-medium text-white/70 max-w-[280px] truncate">{log.query}</td>
                      <td className="px-6 py-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide bg-white/5 border border-white/8 text-white/50">
                          {log.path}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide ${
                          log.details?.confidence === "High"
                            ? "bg-emerald-500/12 border border-emerald-500/20 text-emerald-400"
                            : log.details?.confidence === "Medium"
                            ? "bg-yellow-500/12 border border-yellow-500/20 text-yellow-400"
                            : "bg-red-500/12 border border-red-500/20 text-red-400"
                        }`}>
                          {log.details?.confidence ?? "N/A"}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4">
          <p className="text-[11px] text-white/15">Lenovo.LABS · System Telemetry · v2.0</p>
          <Link href="/" className="text-[11px] text-white/20 hover:text-white/40 transition-colors flex items-center gap-1.5">
            Back to Hub <ExternalLink size={10} />
          </Link>
        </div>
      </main>
    </div>
  );
}
