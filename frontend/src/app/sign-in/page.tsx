"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Phone, ArrowRight, RefreshCw, ShieldCheck, ChevronLeft } from "lucide-react";

const API = "http://localhost:8000";
const ease = [0.22, 1, 0.36, 1] as const;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function saveSession(identifier: string) {
  const name = identifier.includes("@")
    ? identifier.split("@")[0]
    : identifier.replace(/\D/g, "").slice(-4).padStart(4, "*");
  localStorage.setItem("lenovo_ai_auth", JSON.stringify({ email: identifier, name, ts: Date.now() }));
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

const COUNTRY_CODES = [
  { flag: "🇮🇳", code: "+91",  name: "India"  },
  { flag: "🇺🇸", code: "+1",   name: "US"     },
  { flag: "🇬🇧", code: "+44",  name: "UK"     },
  { flag: "🇸🇬", code: "+65",  name: "Singapore" },
  { flag: "🇦🇺", code: "+61",  name: "Australia" },
  { flag: "🇩🇪", code: "+49",  name: "Germany" },
];

// ─── OTP input ────────────────────────────────────────────────────────────────

function OtpInput({ value, onChange, disabled }: { value: string[]; onChange: (v: string[]) => void; disabled?: boolean }) {
  const refs = useRef<(HTMLInputElement | null)[]>([]);

  const focus = (i: number) => setTimeout(() => refs.current[i]?.focus(), 0);

  const handleChange = (i: number, raw: string) => {
    if (!/^\d*$/.test(raw)) return;
    const next = [...value];
    next[i] = raw.slice(-1);
    onChange(next);
    if (raw && i < 5) focus(i + 1);
  };

  const handleKey = (i: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !value[i] && i > 0) { const n = [...value]; n[i - 1] = ""; onChange(n); focus(i - 1); }
    if (e.key === "ArrowLeft"  && i > 0) focus(i - 1);
    if (e.key === "ArrowRight" && i < 5) focus(i + 1);
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const d = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, 6);
    if (d.length === 6) { onChange(d.split("")); focus(5); }
    e.preventDefault();
  };

  return (
    <div className="flex gap-2.5 justify-center" onPaste={handlePaste}>
      {value.map((d, i) => (
        <input
          key={i}
          ref={el => { refs.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={d}
          disabled={disabled}
          onChange={e => handleChange(i, e.target.value)}
          onKeyDown={e => handleKey(i, e)}
          className="w-12 h-14 text-center text-xl font-bold text-white rounded-xl outline-none transition-all duration-200 disabled:opacity-40"
          style={{
            background: d ? "rgba(34,211,238,0.08)" : "rgba(255,255,255,0.04)",
            border: `1.5px solid ${d ? "rgba(34,211,238,0.45)" : "rgba(255,255,255,0.09)"}`,
            caretColor: "#22D3EE",
          }}
        />
      ))}
    </div>
  );
}

// ─── Background ───────────────────────────────────────────────────────────────

function Bg() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden">
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff04_1px,transparent_1px),linear-gradient(to_bottom,#ffffff04_1px,transparent_1px)] bg-[size:56px_56px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_50%,transparent_100%)]" />
      <div className="hero-orb-1 absolute rounded-full" style={{ width:"55vw", height:"55vw", left:"-15%", top:"-20%", background:"radial-gradient(circle,rgba(6,182,212,0.09) 0%,transparent 65%)", filter:"blur(90px)" }} />
      <div className="hero-orb-2 absolute rounded-full" style={{ width:"50vw", height:"50vw", right:"-10%", bottom:"-15%", background:"radial-gradient(circle,rgba(226,35,26,0.09) 0%,transparent 65%)", filter:"blur(100px)" }} />
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function SignInPage() {
  const router = useRouter();

  // Tabs
  const [mode,   setMode]   = useState<"email" | "phone">("email");

  // Email path
  const [email,  setEmail]  = useState("");

  // Phone path
  const [country, setCountry] = useState(COUNTRY_CODES[0]);
  const [phone,   setPhone]   = useState("");

  // OTP
  const [otp,    setOtp]    = useState(["", "", "", "", "", ""]);
  const [devCode, setDevCode] = useState<string | null>(null);

  // UI state
  const [step,    setStep]   = useState<"input" | "otp" | "done">("input");
  const [busy,    setBusy]   = useState(false);
  const [error,   setError]  = useState("");
  const [cooldown, setCooldown] = useState(0);

  // Redirect if already signed in
  useEffect(() => {
    try { if (localStorage.getItem("lenovo_ai_auth")) router.replace("/workspace"); } catch {}
  }, [router]);

  // Resend cooldown tick
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  const identifier = mode === "email"
    ? email.trim().toLowerCase()
    : `${country.code}${phone.trim()}`;

  const verify = async (digits: string[] = otp) => {
    const code = digits.join("");
    if (code.length < 6) { setError("Enter all 6 digits."); return; }
    setBusy(true); setError("");
    try {
      const res = await fetch(`${API}/api/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, code }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Verification failed.");
      saveSession(identifier);
      setStep("done");
      setTimeout(() => router.replace("/workspace"), 1400);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Wrong code."));
      setBusy(false);
    }
  };

  const handleOtpChange = (next: string[]) => {
    setOtp(next);
    setError("");
    if (step === "otp" && next.every(d => d !== "") && !busy) {
      void verify(next);
    }
  };

  const sendCode = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (mode === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Enter a valid email address."); return;
    }
    if (mode === "phone" && phone.trim().length < 7) {
      setError("Enter a valid phone number."); return;
    }
    setBusy(true); setError("");
    try {
      const res = await fetch(`${API}/api/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ identifier, mode }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Failed to send code.");
      setDevCode(data.dev_code ?? null);   // show if backend returns it (no SMTP/Twilio configured)
      setStep("otp");
      setCooldown(30);
      setOtp(["", "", "", "", "", ""]);
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not send code. Is the backend running?"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-black flex flex-col items-center justify-center p-6">
      <Bg />

      {/* Brand */}
      <motion.div initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease }}
        className="relative z-10 mb-10">
        <Link href="/" className="flex items-center gap-3 group">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#E2231A" />
            <path d="M10 16L16 10L22 16" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M16 10V22" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
          </svg>
          <span className="font-bold text-[18px] text-white group-hover:text-white/70 transition-colors">Lenovo.LABS</span>
        </Link>
      </motion.div>

      {/* Card */}
      <motion.div initial={{ opacity: 0, y: 24, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease }}
        className="relative z-10 w-full max-w-[420px] rounded-2xl overflow-hidden"
        style={{ background: "rgba(8,8,14,0.92)", border: "1px solid rgba(255,255,255,0.08)", backdropFilter: "blur(32px)", boxShadow: "0 32px 80px rgba(0,0,0,0.55)" }}
      >
        <div className="h-px w-full" style={{ background: "linear-gradient(90deg,transparent,rgba(34,211,238,0.35),rgba(226,35,26,0.25),transparent)" }} />

        <div className="p-8">
          <AnimatePresence mode="wait">

            {/* ── Step 1: Identifier input ── */}
            {step === "input" && (
              <motion.div key="input" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.28, ease }}>

                <h1 className="text-[22px] font-extrabold text-white mb-1.5">Sign in</h1>
                <p className="text-[13px] text-white/35 mb-6">We&apos;ll send a 6-digit code to verify it&apos;s you.</p>

                {/* Email / Phone toggle */}
                <div className="flex gap-1 p-1 rounded-xl mb-5" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)" }}>
                  {(["email", "phone"] as const).map(t => (
                    <button key={t} onClick={() => { setMode(t); setError(""); }}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-[12px] font-bold transition-all duration-200"
                      style={{
                        background: mode === t ? "rgba(255,255,255,0.09)" : "transparent",
                        color: mode === t ? "white" : "rgba(255,255,255,0.35)",
                      }}
                    >
                      {t === "email" ? <Mail size={13} /> : <Phone size={13} />}
                      {t === "email" ? "Email" : "Phone"}
                    </button>
                  ))}
                </div>

                <form onSubmit={sendCode} className="space-y-4">
                  {mode === "email" ? (
                    <input type="email" autoFocus placeholder="you@company.com"
                      value={email} onChange={e => { setEmail(e.target.value); setError(""); }}
                      className="w-full rounded-xl px-4 py-3.5 text-[14px] text-white placeholder:text-white/20 outline-none transition-all duration-200"
                      style={{ background: "rgba(255,255,255,0.04)", border: `1.5px solid ${error ? "rgba(226,35,26,0.5)" : "rgba(255,255,255,0.09)"}` }}
                      onFocus={e => { if (!error) e.currentTarget.style.border = "1.5px solid rgba(34,211,238,0.35)"; }}
                      onBlur={e => { if (!error) e.currentTarget.style.border = "1.5px solid rgba(255,255,255,0.09)"; }}
                    />
                  ) : (
                    <div className="flex gap-2">
                      {/* Country selector */}
                      <div className="relative">
                        <select
                          value={country.code}
                          onChange={e => setCountry(COUNTRY_CODES.find(c => c.code === e.target.value)!)}
                          className="h-full rounded-xl px-3 py-3.5 text-[13px] text-white/80 outline-none appearance-none pr-7 transition-all duration-200"
                          style={{ background: "rgba(255,255,255,0.06)", border: "1.5px solid rgba(255,255,255,0.09)", minWidth: 88 }}
                        >
                          {COUNTRY_CODES.map(c => (
                            <option key={c.code} value={c.code} style={{ background: "#0a0a12" }}>
                              {c.flag} {c.code}
                            </option>
                          ))}
                        </select>
                      </div>
                      <input type="tel" autoFocus placeholder="Phone number"
                        value={phone} onChange={e => { setPhone(e.target.value.replace(/\D/g, "")); setError(""); }}
                        className="flex-1 rounded-xl px-4 py-3.5 text-[14px] text-white placeholder:text-white/20 outline-none transition-all duration-200"
                        style={{ background: "rgba(255,255,255,0.04)", border: `1.5px solid ${error ? "rgba(226,35,26,0.5)" : "rgba(255,255,255,0.09)"}` }}
                        onFocus={e => { if (!error) e.currentTarget.style.border = "1.5px solid rgba(34,211,238,0.35)"; }}
                        onBlur={e => { if (!error) e.currentTarget.style.border = "1.5px solid rgba(255,255,255,0.09)"; }}
                      />
                    </div>
                  )}

                  {error && <p className="text-[11px] text-red-400 pl-1">{error}</p>}

                  <button type="submit" disabled={busy}
                    className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold text-[14px] text-white transition-all duration-200 disabled:opacity-50"
                    style={{ background: "#E2231A" }}
                  >
                    {busy ? <RefreshCw size={15} className="animate-spin" /> : <>Send code <ArrowRight size={15} /></>}
                  </button>
                </form>
              </motion.div>
            )}

            {/* ── Step 2: OTP entry ── */}
            {step === "otp" && (
              <motion.div key="otp" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.28, ease }}>

                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
                  style={{ background: "rgba(34,211,238,0.10)", border: "1px solid rgba(34,211,238,0.22)" }}>
                  <ShieldCheck size={18} className="text-cyan-400" />
                </div>
                <h1 className="text-[22px] font-extrabold text-white mb-1.5">Enter the code</h1>
                <p className="text-[13px] text-white/35 mb-6">
                  Sent to <span className="text-white/65 font-semibold">{identifier}</span>
                </p>

                {/* Dev mode banner — shown when backend has no email/SMS configured */}
                {devCode && (
                  <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl mb-5"
                    style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.22)" }}
                  >
                    <span className="text-yellow-400 text-[11px] font-bold tracking-wide flex-shrink-0">DEV</span>
                    <span className="text-[12px] text-white/50">No email/SMS configured —</span>
                    <span className="font-mono text-[18px] font-extrabold text-yellow-300 tracking-[4px] ml-auto">{devCode}</span>
                  </motion.div>
                )}

                <OtpInput value={otp} onChange={handleOtpChange} disabled={busy} />

                {error && (
                  <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                    className="text-[11px] text-red-400 text-center mt-3">{error}
                  </motion.p>
                )}

                <button onClick={() => void verify()} disabled={busy || otp.some(d => !d)}
                  className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-bold text-[14px] text-white transition-all duration-200 mt-5 disabled:opacity-40"
                  style={{ background: "#E2231A" }}
                >
                  {busy ? <RefreshCw size={15} className="animate-spin" /> : <>Verify <ArrowRight size={15} /></>}
                </button>

                <div className="flex items-center justify-between mt-4">
                  <button onClick={() => { setStep("input"); setOtp(["","","","","",""]); setError(""); setDevCode(null); }}
                    className="flex items-center gap-1 text-[11px] text-white/30 hover:text-white/55 transition-colors">
                    <ChevronLeft size={12} /> Change {mode === "email" ? "email" : "number"}
                  </button>
                  <button onClick={() => sendCode()} disabled={cooldown > 0}
                    className="text-[11px] text-white/30 hover:text-white/55 disabled:opacity-35 transition-colors">
                    {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend code"}
                  </button>
                </div>
              </motion.div>
            )}

            {/* ── Step 3: Done ── */}
            {step === "done" && (
              <motion.div key="done" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.35, ease }}
                className="py-6 flex flex-col items-center text-center"
              >
                <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.45, ease: [0.34, 1.56, 0.64, 1] }}
                  className="w-14 h-14 rounded-full flex items-center justify-center mb-5"
                  style={{ background: "rgba(52,211,153,0.12)", border: "1.5px solid rgba(52,211,153,0.35)" }}
                >
                  <ShieldCheck size={26} className="text-emerald-400" />
                </motion.div>
                <h2 className="text-[20px] font-extrabold text-white mb-2">You&apos;re in</h2>
                <p className="text-[13px] text-white/35">Taking you to the workspace…</p>
                <div className="mt-5 flex gap-1.5">
                  {[0, 1, 2].map(i => (
                    <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-emerald-400"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.2 }} />
                  ))}
                </div>
              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </motion.div>

      <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6, delay: 0.4 }}
        className="relative z-10 mt-7 text-[11px] text-white/15 text-center">
        Lenovo Research Workspace · Internal use only
      </motion.p>
    </div>
  );
}
