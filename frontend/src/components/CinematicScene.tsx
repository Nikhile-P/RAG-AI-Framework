"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

// ─── SVG: Neural Routing Diagram ─────────────────────────────────────────────
// Shows intelligent query routing across RAG / Web / Local pathways

function NeuralRoutingViz({ accent }: { accent: string }) {
  const cols = { i: 80, h1: 300, h2: 510, o: 720 };
  const inputs  = [130, 220, 320, 420];
  const hidden1 = [175, 295, 415];
  const hidden2 = [175, 295, 415];
  const outputs = [175, 295, 415];
  const activeI = 2, activeH = 1, activeO = 0; // active path: input[2]→h1[1]→h2[1]→output[0]

  // Build all inactive connections as thin white lines
  const inactiveConns: [number, number, number, number][] = [];
  inputs.forEach((iy, ii) =>
    hidden1.forEach((hy, hi) => { if (!(ii === activeI && hi === activeH)) inactiveConns.push([cols.i, iy, cols.h1, hy]); })
  );
  hidden1.forEach((h1y, h1i) =>
    hidden2.forEach((h2y, h2i) => { if (!(h1i === activeH && h2i === activeH)) inactiveConns.push([cols.h1, h1y, cols.h2, h2y]); })
  );
  hidden2.forEach((h2y, h2i) =>
    outputs.forEach((oy, oi) => { if (!(h2i === activeH && oi === activeO)) inactiveConns.push([cols.h2, h2y, cols.o, oy]); })
  );

  const glowId = "ng_glow";
  const pathGlowId = "ng_pathglow";

  return (
    <svg viewBox="0 0 860 560" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
      <defs>
        <filter id={glowId} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id={pathGlowId} x="-20%" y="-50%" width="140%" height="200%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Inactive connections */}
      {inactiveConns.map(([x1, y1, x2, y2], i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="white" strokeWidth="0.8" strokeOpacity="0.08" />
      ))}

      {/* Active routing path — animated flowing dash */}
      <path
        d={`M${cols.i},${inputs[activeI]} C${(cols.i+cols.h1)/2},${inputs[activeI]} ${(cols.i+cols.h1)/2},${hidden1[activeH]} ${cols.h1},${hidden1[activeH]}`}
        stroke={accent} strokeWidth="1.8" strokeDasharray="10 5"
        filter={`url(#${pathGlowId})`}
        className="neural-dash"
      />
      <path
        d={`M${cols.h1},${hidden1[activeH]} C${(cols.h1+cols.h2)/2},${hidden1[activeH]} ${(cols.h1+cols.h2)/2},${hidden2[activeH]} ${cols.h2},${hidden2[activeH]}`}
        stroke={accent} strokeWidth="1.8" strokeDasharray="10 5"
        filter={`url(#${pathGlowId})`}
        className="neural-dash"
        style={{ animationDelay: "0.4s" }}
      />
      <path
        d={`M${cols.h2},${hidden2[activeH]} C${(cols.h2+cols.o)/2},${hidden2[activeH]} ${(cols.h2+cols.o)/2},${outputs[activeO]} ${cols.o},${outputs[activeO]}`}
        stroke={accent} strokeWidth="1.8" strokeDasharray="10 5"
        filter={`url(#${pathGlowId})`}
        className="neural-dash"
        style={{ animationDelay: "0.8s" }}
      />

      {/* Input nodes */}
      {inputs.map((y, i) => (
        <g key={`in${i}`}>
          <circle cx={cols.i} cy={y} r={i === activeI ? 16 : 12}
            fill={i === activeI ? `${accent}20` : "rgba(255,255,255,0.03)"}
            stroke={i === activeI ? accent : "rgba(255,255,255,0.18)"}
            strokeWidth={i === activeI ? 1.8 : 1}
            filter={i === activeI ? `url(#${glowId})` : undefined}
            className={i === activeI ? "node-pulse" : undefined}
          />
          <text x={cols.i - 26} y={y + 4} fontSize="10" fill="rgba(255,255,255,0.3)" textAnchor="end" fontFamily="system-ui">
            {["Query", "Context", "Intent", "History"][i]}
          </text>
        </g>
      ))}

      {/* Hidden layer 1 */}
      {hidden1.map((y, i) => (
        <circle key={`h1${i}`} cx={cols.h1} cy={y} r={i === activeH ? 14 : 11}
          fill={i === activeH ? `${accent}15` : "rgba(255,255,255,0.03)"}
          stroke={i === activeH ? `${accent}80` : "rgba(255,255,255,0.12)"}
          strokeWidth={i === activeH ? 1.5 : 1}
        />
      ))}

      {/* Layer label */}
      <text x={cols.h1} y={520} fontSize="9" fill="rgba(255,255,255,0.2)" textAnchor="middle" fontFamily="system-ui" letterSpacing="1">ROUTER</text>

      {/* Hidden layer 2 */}
      {hidden2.map((y, i) => (
        <circle key={`h2${i}`} cx={cols.h2} cy={y} r={i === activeH ? 14 : 11}
          fill={i === activeH ? `${accent}15` : "rgba(255,255,255,0.03)"}
          stroke={i === activeH ? `${accent}80` : "rgba(255,255,255,0.12)"}
          strokeWidth={i === activeH ? 1.5 : 1}
        />
      ))}
      <text x={cols.h2} y={520} fontSize="9" fill="rgba(255,255,255,0.2)" textAnchor="middle" fontFamily="system-ui" letterSpacing="1">SCORER</text>

      {/* Output nodes with labels */}
      {[["RAG Search", true], ["Web Fallback", false], ["Local Model", false]].map(([label, active], i) => (
        <g key={`out${i}`}>
          <rect x={cols.o - 4} y={outputs[i] - 18} width={126} height={36} rx={10}
            fill={active ? `${accent}18` : "rgba(255,255,255,0.03)"}
            stroke={active ? accent : "rgba(255,255,255,0.1)"}
            strokeWidth={active ? 1.5 : 0.8}
            filter={active ? `url(#${glowId})` : undefined}
          />
          <text x={cols.o + 59} y={outputs[i] + 5} fontSize="11" fill={active ? accent : "rgba(255,255,255,0.35)"}
            textAnchor="middle" fontFamily="system-ui" fontWeight={active ? "600" : "400"}>
            {label as string}
          </text>
        </g>
      ))}

      {/* Column header labels */}
      {[["INPUT", cols.i], ["HIDDEN ×2", cols.h1 + 105], ["OUTPUT", cols.o + 59]].map(([lbl, x]) => (
        <text key={lbl as string} x={x as number} y={60} fontSize="9" fill="rgba(255,255,255,0.15)"
          textAnchor="middle" fontFamily="system-ui" letterSpacing="2">
          {lbl as string}
        </text>
      ))}
    </svg>
  );
}

// ─── SVG: Vector Space Visualization ─────────────────────────────────────────
// Shows semantic document clusters + search query finding nearest neighbors

function VectorSearchViz({ accent }: { accent: string }) {
  // Document clusters (pre-computed positions for determinism)
  const clusters = [
    { label: "Strategy", color: "#22D3EE", dots: [[160,140],[190,110],[210,165],[175,190],[140,155],[220,130],[195,200]] },
    { label: "Hardware", color: "#60A5FA", dots: [[480,120],[510,150],[455,165],[490,190],[530,135],[465,200],[520,180]] },
    { label: "Financial", color: "#34D399", dots: [[300,330],[340,305],[275,345],[330,380],[360,345],[285,370],[310,300]] },
    { label: "Enterprise", color: "#A78BFA", dots: [[580,330],[620,300],[560,360],[610,380],[640,345],[580,300],[625,365]] },
  ];

  // Query point + nearest neighbors in cluster 0
  const query = { x: 250, y: 230 };
  const neighbors = [[190,110],[160,140],[175,190]] as [number,number][];

  const glowId = "vs_glow";

  return (
    <svg viewBox="0 0 800 520" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
      <defs>
        <filter id={glowId} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Axis grid — very subtle */}
      {[120,220,320,420].map(y => <line key={`gy${y}`} x1="40" y1={y} x2="760" y2={y} stroke="white" strokeOpacity="0.04" strokeWidth="1" />)}
      {[140,260,380,500,620,740].map(x => <line key={`gx${x}`} x1={x} y1="60" x2={x} y2="480" stroke="white" strokeOpacity="0.04" strokeWidth="1" />)}

      {/* Neighbor connection lines */}
      {neighbors.map(([nx,ny], i) => (
        <line key={`nb${i}`} x1={query.x} y1={query.y} x2={nx} y2={ny}
          stroke={accent} strokeWidth="1" strokeOpacity="0.4" strokeDasharray="4 3" />
      ))}

      {/* Cluster dots */}
      {clusters.map(cl =>
        cl.dots.map(([x, y], j) => (
          <circle key={`${cl.label}${j}`} cx={x} cy={y} r={4}
            fill={cl.color} fillOpacity={neighbors.some(([nx,ny])=>nx===x&&ny===y) ? 0.9 : 0.55}
          />
        ))
      )}

      {/* Highlighted neighbors */}
      {neighbors.map(([nx, ny], i) => (
        <circle key={`nhr${i}`} cx={nx} cy={ny} r={8}
          fill="none" stroke={accent} strokeWidth="1.2" strokeOpacity="0.6" />
      ))}

      {/* Search query point */}
      <circle cx={query.x} cy={query.y} r={10} fill={accent} fillOpacity="0.25"
        stroke={accent} strokeWidth="2" filter={`url(#${glowId})`} className="query-ring" />
      <circle cx={query.x} cy={query.y} r={5} fill={accent} />
      <text x={query.x} y={query.y - 18} fontSize="10" fill={accent} textAnchor="middle"
        fontFamily="system-ui" fontWeight="600">Search Query</text>

      {/* Cluster labels */}
      {clusters.map(cl => (
        <text key={cl.label}
          x={cl.dots.reduce((s,[x])=>s+x,0)/cl.dots.length}
          y={cl.dots.reduce((s,[,y])=>s+y,0)/cl.dots.length + 24}
          fontSize="9.5" fill={cl.color} fillOpacity="0.7"
          textAnchor="middle" fontFamily="system-ui" letterSpacing="0.5">
          {cl.label}
        </text>
      ))}

      {/* Axis labels */}
      <text x="400" y="505" fontSize="9" fill="rgba(255,255,255,0.18)" textAnchor="middle" fontFamily="system-ui" letterSpacing="2">SEMANTIC DIMENSION 1</text>
      <text x="16" y="280" fontSize="9" fill="rgba(255,255,255,0.18)" textAnchor="middle" fontFamily="system-ui" letterSpacing="2" transform="rotate(-90,16,280)">DIM 2</text>

      {/* Corner badge */}
      <rect x="570" y="420" width="175" height="60" rx="8" fill="rgba(0,0,0,0.4)" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
      <text x="658" y="443" fontSize="9" fill={accent} textAnchor="middle" fontFamily="system-ui" fontWeight="600" letterSpacing="1">CHROMADB · MiniLM-L6</text>
      <text x="658" y="462" fontSize="9" fill="rgba(255,255,255,0.3)" textAnchor="middle" fontFamily="system-ui">Dense retrieval · 384-dim</text>
    </svg>
  );
}

// ─── SVG: Enterprise Architecture Diagram ─────────────────────────────────────
// Hub-and-spoke: Lenovo Platform at centre, platform components in orbit

function EnterpriseArchViz({ accent }: { accent: string }) {
  const cx = 440, cy = 290;
  const inner = 155, outer = 270;

  // Inner orbit — core platform
  const innerNodes = [
    { label: "ChromaDB", angle: -90, color: "#34D399", icon: "⬡" },
    { label: "LangGraph", angle: 30,  color: "#60A5FA", icon: "⟳" },
    { label: "FastAPI",   angle: 150, color: "#F97316", icon: "⚡" },
  ];

  // Outer orbit — integrations
  const outerNodes = [
    { label: "Qwen 2.5",  angle: -120, color: "#E2231A" },
    { label: "Tavily",    angle: -30,  color: "#22D3EE" },
    { label: "Next.js",   angle:  60,  color: "#A78BFA" },
    { label: "Ollama",    angle:  150, color: "#FBBF24" },
    { label: "SSO/Auth",  angle: -150, color: "#34D399" },
  ];

  const pos = (angle: number, r: number) => ({
    x: cx + r * Math.cos((angle * Math.PI) / 180),
    y: cy + r * Math.sin((angle * Math.PI) / 180),
  });

  const glowId = "ea_glow";

  return (
    <svg viewBox="0 0 880 580" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full">
      <defs>
        <filter id={glowId} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="8" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="ea_nodeglow" x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* Orbital rings */}
      <circle cx={cx} cy={cy} r={inner} stroke="white" strokeOpacity="0.05" strokeWidth="1" strokeDasharray="4 6" />
      <circle cx={cx} cy={cy} r={outer} stroke="white" strokeOpacity="0.04" strokeWidth="1" strokeDasharray="3 7" />

      {/* Outer connection lines */}
      {outerNodes.map(n => {
        const p = pos(n.angle, outer);
        return <line key={n.label} x1={cx} y1={cy} x2={p.x} y2={p.y}
          stroke={n.color} strokeWidth="0.8" strokeOpacity="0.2" strokeDasharray="6 5"
          className="arch-dash" />;
      })}

      {/* Inner connection lines */}
      {innerNodes.map(n => {
        const p = pos(n.angle, inner);
        return <line key={n.label} x1={cx} y1={cy} x2={p.x} y2={p.y}
          stroke={n.color} strokeWidth="1.4" strokeOpacity="0.5" strokeDasharray="8 4"
          className="arch-dash" />;
      })}

      {/* Outer nodes */}
      {outerNodes.map(n => {
        const p = pos(n.angle, outer);
        const labelOffset = p.y < cy ? -20 : 22;
        return (
          <g key={n.label}>
            <circle cx={p.x} cy={p.y} r={18} fill={`${n.color}12`} stroke={n.color} strokeWidth="1" strokeOpacity="0.6" />
            <text x={p.x} y={p.y + labelOffset + (p.y < cy ? 0 : 4)} fontSize="9.5" fill={n.color}
              fillOpacity="0.7" textAnchor="middle" fontFamily="system-ui">{n.label}</text>
          </g>
        );
      })}

      {/* Inner nodes */}
      {innerNodes.map(n => {
        const p = pos(n.angle, inner);
        const labelOffset = p.y < cy ? -22 : 24;
        return (
          <g key={n.label} filter="url(#ea_nodeglow)">
            <circle cx={p.x} cy={p.y} r={24} fill={`${n.color}18`} stroke={n.color} strokeWidth="1.5" strokeOpacity="0.8" />
            <text x={p.x} y={p.y + 5} fontSize="13" fill={n.color} textAnchor="middle">{n.icon}</text>
            <text x={p.x} y={p.y + labelOffset + (p.y < cy ? 0 : 5)} fontSize="9.5" fill={n.color}
              fillOpacity="0.85" textAnchor="middle" fontFamily="system-ui" fontWeight="600">{n.label}</text>
          </g>
        );
      })}

      {/* Central node — Lenovo Hub */}
      <circle cx={cx} cy={cy} r={58} fill={`${accent}15`} stroke={accent} strokeWidth="1.5" filter={`url(#${glowId})`} className="hub-pulse" />
      <circle cx={cx} cy={cy} r={44} fill={`${accent}10`} stroke={`${accent}40`} strokeWidth="1" />
      <text x={cx} y={cy - 8} fontSize="13" fill="white" textAnchor="middle" fontFamily="system-ui" fontWeight="700">Lenovo</text>
      <text x={cx} y={cy + 10} fontSize="13" fill={accent} textAnchor="middle" fontFamily="system-ui" fontWeight="700">.LABS</text>
      <text x={cx} y={cy + 26} fontSize="8" fill={accent} fillOpacity="0.6" textAnchor="middle" fontFamily="system-ui" letterSpacing="1.5">PLATFORM</text>
    </svg>
  );
}

// ─── Scene configuration ──────────────────────────────────────────────────────

type Variant = "neural" | "datacenter" | "cosmos";

const CFG = {
  neural: {
    accent:    "#22D3EE",
    label:     "SEARCH · ROUTING · ENGINE",
    headline:  "Right source,\nevery time.",
    base:      "#000C18",
    glow:      "radial-gradient(ellipse 60% 70% at 20% 55%, rgba(0,170,220,0.28) 0%, transparent 65%)",
    glow2:     "radial-gradient(ellipse 40% 50% at 75% 35%, rgba(30,90,200,0.16) 0%, transparent 60%)",
    orb1Color: "rgba(0,180,220,0.22)",
    orb2Color: "rgba(20,70,180,0.14)",
    Viz: NeuralRoutingViz,
  },
  datacenter: {
    accent:    "#E2231A",
    label:     "DOCUMENT · STORE · SEARCH",
    headline:  "All your docs,\nsearchable.",
    base:      "#0E0000",
    glow:      "radial-gradient(ellipse 60% 70% at 75% 50%, rgba(210,25,18,0.26) 0%, transparent 65%)",
    glow2:     "radial-gradient(ellipse 40% 50% at 20% 60%, rgba(150,12,8,0.16) 0%, transparent 60%)",
    orb1Color: "rgba(200,20,15,0.20)",
    orb2Color: "rgba(120,8,6,0.14)",
    Viz: VectorSearchViz,
  },
  cosmos: {
    accent:    "#A78BFA",
    label:     "LENOVO · RESEARCH · PLATFORM",
    headline:  "The full\nstack.",
    base:      "#040010",
    glow:      "radial-gradient(ellipse 60% 70% at 50% 40%, rgba(115,55,235,0.26) 0%, transparent 65%)",
    glow2:     "radial-gradient(ellipse 40% 50% at 80% 65%, rgba(195,45,160,0.15) 0%, transparent 60%)",
    orb1Color: "rgba(110,50,225,0.20)",
    orb2Color: "rgba(185,40,155,0.13)",
    Viz: EnterpriseArchViz,
  },
} as const;

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CinematicScene({ variant }: { variant: Variant }) {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });

  // Four depth layers — perfectly smooth direct mapping, no springs
  const bgY    = useTransform(scrollYProgress, [0, 1], ["-120px", "120px"]);  // slowest
  const vizY   = useTransform(scrollYProgress, [0, 1], ["-70px",  "70px"]);   // mid-depth
  const textY  = useTransform(scrollYProgress, [0, 1], ["60px",  "-60px"]);   // fastest (counter)
  // Cinematic zoom: bg breathes in as you enter, pulls back as you exit
  const bgScale = useTransform(scrollYProgress, [0, 0.45, 1], [1.14, 1.04, 0.92]);
  // Haze layer drifts opposite to bg for extra perceived depth
  const hazeY  = useTransform(scrollYProgress, [0, 1], ["-22px",  "22px"]);

  const sceneOp = useTransform(scrollYProgress, [0, 0.08, 0.92, 1], [0, 1, 1, 0]);
  const textOp  = useTransform(scrollYProgress, [0.04, 0.20, 0.80, 0.96], [0, 1, 1, 0]);
  const hazeOp  = useTransform(scrollYProgress, [0, 0.14, 0.86, 1], [0, 0.55, 0.55, 0]);

  const c = CFG[variant];

  return (
    <section
      ref={ref}
      className="relative w-full overflow-hidden select-none"
      style={{ height: "88vh", minHeight: "600px" }}
    >
      {/* ── LAYER 0: Background gradient + CSS orbs (slowest parallax + zoom) ── */}
      <motion.div className="absolute inset-0 will-change-transform" style={{ y: bgY, scale: bgScale, opacity: sceneOp }}>
        <div className="absolute inset-0" style={{ backgroundColor: c.base }} />
        <div className="absolute inset-0" style={{ background: c.glow }} />
        <div className="absolute inset-0" style={{ background: c.glow2 }} />

        {/* Ambient orbs — pure CSS animation, zero JS cost */}
        <div className="orb-drift-1 absolute rounded-full pointer-events-none" style={{
          width: "36vw", height: "36vw", left: "3%", top: "8%",
          background: `radial-gradient(circle, ${c.orb1Color} 0%, transparent 65%)`,
          filter: "blur(55px)",
        }} />
        <div className="orb-drift-2 absolute rounded-full pointer-events-none" style={{
          width: "28vw", height: "28vw", right: "5%", bottom: "8%",
          background: `radial-gradient(circle, ${c.orb2Color} 0%, transparent 65%)`,
          filter: "blur(70px)",
        }} />

        {/* Cinematic edge vignette */}
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse 80% 70% at 50% 50%, transparent 28%, rgba(0,0,0,0.88) 100%)",
        }} />
        {/* Top / bottom dissolve */}
        <div className="absolute inset-x-0 top-0 h-48 bg-gradient-to-b from-black to-transparent" />
        <div className="absolute inset-x-0 bottom-0 h-48 bg-gradient-to-t from-black to-transparent" />
      </motion.div>

      {/* ── LAYER 0.5: Depth haze — moves counter to bg, adds perceived depth ── */}
      <motion.div
        className="absolute inset-0 pointer-events-none will-change-transform"
        style={{ y: hazeY, opacity: hazeOp }}
      >
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse 55% 55% at 50% 50%, rgba(255,255,255,0.018) 0%, transparent 65%)",
        }} />
      </motion.div>

      {/* ── LAYER 1: SVG Visualization (mid-depth parallax + right side) ── */}
      <motion.div
        className="absolute inset-y-0 right-0 will-change-transform hidden md:block"
        style={{
          y: vizY,
          opacity: sceneOp,
          width: "58%",
          // Mask left edge so viz fades into text area gracefully
          WebkitMaskImage: "linear-gradient(to right, transparent 0%, black 25%, black 100%)",
          maskImage: "linear-gradient(to right, transparent 0%, black 25%, black 100%)",
        }}
      >
        <div className="w-full h-full flex items-center justify-center p-8 opacity-70">
          <c.Viz accent={c.accent} />
        </div>
      </motion.div>

      {/* ── LAYER 2: Text content (fastest / counter-parallax) ── */}
      <div className="absolute inset-0 flex items-center z-20 pointer-events-none">
        <motion.div
          style={{ y: textY, opacity: textOp }}
          className="will-change-transform px-10 md:px-16 lg:px-20 w-full md:max-w-[48%]"
        >
          {/* Eyebrow label */}
          <p
            className="text-[10px] font-bold tracking-[0.3em] uppercase mb-6"
            style={{ color: c.accent, opacity: 0.65 }}
          >
            {c.label}
          </p>

          {/* Headline — each word on its own line, properly contained */}
          <h2
            className="font-extrabold tracking-tight leading-[0.98] mb-8"
            style={{
              fontSize: "clamp(2.4rem, 4.2vw, 4.4rem)",
              background: `linear-gradient(155deg, #ffffff 30%, ${c.accent}90 100%)`,
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
              wordBreak: "keep-all",
            }}
          >
            {c.headline.split("\n").map((line, i) => (
              <span key={i} className="block">{line}</span>
            ))}
          </h2>

          {/* Accent rule */}
          <motion.div
            style={{
              height: "1px",
              background: `linear-gradient(90deg, ${c.accent} 0%, transparent 100%)`,
            }}
            initial={{ width: 0, opacity: 0 }}
            whileInView={{ width: 130, opacity: 0.5 }}
            transition={{ duration: 1.0, ease: [0.22, 1, 0.36, 1] }}
            viewport={{ once: false, margin: "-15%" }}
          />
        </motion.div>
      </div>
    </section>
  );
}
