import streamlit as st
import os
import ast

# ============================================================
# HYPER-DYNAMIC LANDING PAGE
# ============================================================

# --- Parse live stats from router.log ---
total_queries = 0
avg_relevance = 0.0
log_path = os.path.join(os.path.dirname(__file__), '..', 'router.log')
try:
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = [l.strip() for l in f if l.strip()]
        total_queries = len(lines)
        relevances = []
        for line in lines:
            try:
                entry = ast.literal_eval(line)
                rel = entry.get('details', {}).get('relevance', 0)
                if rel:
                    relevances.append(float(rel))
            except Exception:
                continue
        avg_relevance = sum(relevances) / len(relevances) if relevances else 0
except Exception:
    pass

data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
file_count = len([f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))]) if os.path.exists(data_dir) else 0

# === FULL-PAGE CSS ===
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700;800&display=swap');

/* ── Base Reset ── */
.stApp {{
    background: #000000 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    overflow-x: hidden;
    color: #e2e8f0;
}}
[data-testid="stSidebar"] {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
}}
.stDeployButton, footer, #MainMenu {{ display: none !important; }}

/* ── Hyper-Dynamic Mesh Background ── */
.mesh-bg {{
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: -1;
    background-color: #030305;
    background-image: 
        radial-gradient(at 0% 0%, hsla(189,100%,25%,0.15) 0px, transparent 50%),
        radial-gradient(at 50% 0%, hsla(350,100%,35%,0.1) 0px, transparent 50%),
        radial-gradient(at 100% 0%, hsla(220,100%,30%,0.15) 0px, transparent 50%),
        radial-gradient(at 0% 100%, hsla(350,100%,35%,0.1) 0px, transparent 50%),
        radial-gradient(at 50% 100%, hsla(189,100%,25%,0.15) 0px, transparent 50%),
        radial-gradient(at 100% 100%, hsla(220,100%,30%,0.1) 0px, transparent 50%);
    background-size: 200% 200%;
    animation: meshFlow 20s ease infinite alternate;
}}
@keyframes meshFlow {{
    0% {{ background-position: 0% 0%; }}
    50% {{ background-position: 100% 100%; }}
    100% {{ background-position: 0% 100%; }}
}}

.bg-orbs {{
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    overflow: hidden;
    z-index: -1;
}}
.orb {{
    position: absolute;
    border-radius: 50%;
    filter: blur(120px);
    opacity: 0.5;
    animation: floatOrb 25s infinite ease-in-out alternate;
}}
.orb-1 {{ width: 60vw; height: 60vw; background: rgba(6, 182, 212, 0.15); top: -20%; left: -20%; animation-delay: 0s; }}
.orb-2 {{ width: 70vw; height: 70vw; background: rgba(226, 35, 26, 0.15); bottom: -30%; right: -20%; animation-delay: -5s; }}
.orb-3 {{ width: 50vw; height: 50vw; background: rgba(59, 130, 246, 0.15); top: 30%; left: 30%; animation-delay: -10s; }}

@keyframes floatOrb {{
    0% {{ transform: translate(0, 0) scale(1) rotate(0deg); }}
    50% {{ transform: translate(10%, 15%) scale(1.2) rotate(180deg); }}
    100% {{ transform: translate(-5%, -10%) scale(0.9) rotate(360deg); }}
}}

/* ── Nav ── */
.hyper-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem 4rem;
    background: rgba(3,3,5,0.4);
    backdrop-filter: blur(30px);
    -webkit-backdrop-filter: blur(30px);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    position: sticky;
    top: 0;
    z-index: 100;
}}
.logo-container {{ display: flex; align-items: center; gap: 12px; }}
.logo-text {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: white;
}}
.logo-text span {{ color: #E2231A; }}

/* ── Hero ── */
.hyper-hero {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 8rem 2rem 5rem;
    position: relative;
}}
.hero-badge {{
    display: inline-block;
    padding: 8px 24px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
    backdrop-filter: blur(20px);
    animation: slideDown 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}}
.hero-badge span {{ color: #06b6d4; margin-right: 8px; animation: pulseDot 2s infinite; }}
@keyframes pulseDot {{ 0%, 100% {{opacity:1;}} 50% {{opacity:0.3;}} }}

@keyframes slideDown {{ from {{opacity: 0; transform: translateY(-30px);}} to {{opacity: 1; transform: translateY(0);}} }}
@keyframes slideUp {{ from {{opacity: 0; transform: translateY(40px);}} to {{opacity: 1; transform: translateY(0);}} }}

.hyper-hero h1 {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: clamp(3.5rem, 7vw, 6.5rem);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -3px;
    margin-bottom: 1.5rem;
    animation: slideUp 1s cubic-bezier(0.16, 1, 0.3, 1);
}}
.text-gradient {{
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.text-shimmer {{
    background: linear-gradient(90deg, #E2231A, #ff4757, #ff6b81, #E2231A);
    background-size: 300% auto;
    color: transparent;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shimmer 4s linear infinite;
}}
@keyframes shimmer {{ to {{ background-position: 300% center; }} }}

.hyper-hero p {{
    font-size: 1.25rem;
    color: #94a3b8;
    max-width: 700px;
    line-height: 1.8;
    margin: 0 auto 3rem;
    animation: slideUp 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s backwards;
}}

/* ── Scroll Reveal Animations ── */
.scroll-reveal {{
    animation: revealElement linear both;
    animation-timeline: view();
    animation-range: entry 10% cover 30%;
}}
@keyframes revealElement {{
    from {{ opacity: 0; transform: translateY(50px) scale(0.95); }}
    to {{ opacity: 1; transform: translateY(0) scale(1); }}
}}

/* ── Stats ── */
.hyper-stats {{
    display: flex;
    justify-content: center;
    gap: 5rem;
    flex-wrap: wrap;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
    padding: 3rem 0;
    width: 100%;
    border-top: 1px solid rgba(255,255,255,0.04);
    border-bottom: 1px solid rgba(255,255,255,0.04);
    position: relative;
}}
.hyper-stats::before {{
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: url('data:image/svg+xml;utf8,<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" fill="none"/><line x1="0" y1="0" x2="100" y2="100" stroke="rgba(255,255,255,0.02)" stroke-width="0.5"/><line x1="100" y1="0" x2="0" y2="100" stroke="rgba(255,255,255,0.02)" stroke-width="0.5"/></svg>');
    background-size: 40px 40px; pointer-events: none; opacity: 0.5;
}}
.stat-box {{ text-align: center; position: relative; z-index: 2; }}
.stat-num {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3.5rem;
    font-weight: 800;
    color: #fff;
    margin-bottom: 0.2rem;
    line-height: 1;
    text-shadow: 0 0 40px rgba(255,255,255,0.2);
}}
.stat-name {{
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #94a3b8;
    font-weight: 700;
}}

/* ── Bento Grid Cards (Peak Glassmorphism) ── */
.bento-wrapper {{
    max-width: 1300px;
    margin: 6rem auto;
    padding: 0 2rem;
}}
.bento-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
}}
.hyper-card {{
    background: rgba(15, 23, 42, 0.4);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 32px;
    padding: 3rem;
    position: relative;
    overflow: hidden;
    transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 20px 40px rgba(0,0,0,0.5);
}}
.hyper-card:hover {{
    transform: translateY(-15px) scale(1.02);
    border-color: rgba(255,255,255,0.2);
    background: rgba(30, 41, 59, 0.6);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 40px 80px rgba(0,0,0,0.8), 0 0 40px var(--accent-glow);
}}

/* Dynamic Hover Glow Array */
.hyper-card::before {{
    content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 50% 0%, var(--accent-glow) 0%, transparent 70%);
    opacity: 0; transition: opacity 0.6s ease; pointer-events: none; mix-blend-mode: screen;
}}
.hyper-card:hover::before {{ opacity: 0.5; }}

/* Bottom animated border */
.hyper-card::after {{
    content: ''; position: absolute; bottom: 0; left: 0; width: 100%; height: 3px;
    background: var(--accent); transform: scaleX(0); transform-origin: left; transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}}
.hyper-card:hover::after {{ transform: scaleX(1); }}

.card-icon-wrapper {{
    width: 70px; height: 70px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    font-size: 2.2rem;
    margin-bottom: 2rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 8px 32px rgba(0,0,0,0.3);
    color: var(--accent);
    transition: transform 0.6s ease;
}}
.hyper-card:hover .card-icon-wrapper {{ transform: scale(1.1) rotate(5deg); }}

.hc-title {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.6rem;
    font-weight: 800;
    color: #fff;
    margin-bottom: 1rem;
    letter-spacing: -0.5px;
}}
.hc-desc {{
    font-size: 1.05rem;
    color: #94a3b8;
    line-height: 1.7;
    margin-bottom: 2rem;
}}
.hc-badge {{
    position: absolute;
    top: 2rem; right: 2rem;
    padding: 6px 16px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 100px;
    color: #fff;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    backdrop-filter: blur(10px);
}}
.hc-badge.live {{ color: #10b981; border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.15); box-shadow: 0 0 20px rgba(16, 185, 129, 0.2); }}
.hc-badge.deployed {{ color: #3b82f6; border-color: rgba(59, 130, 246, 0.4); background: rgba(59, 130, 246, 0.15); box-shadow: 0 0 20px rgba(59, 130, 246, 0.2); }}

/* ── Infinite Marquee ── */
.marquee-container {{
    width: 100%; overflow: hidden; padding: 5rem 0;
    background: rgba(0,0,0,0.5);
    border-top: 1px solid rgba(255,255,255,0.03);
    border-bottom: 1px solid rgba(255,255,255,0.03);
    position: relative; margin-top: 4rem;
}}
.marquee-container::before, .marquee-container::after {{
    content: ''; position: absolute; top: 0; width: 250px; height: 100%; z-index: 2;
}}
.marquee-container::before {{ left: 0; background: linear-gradient(to right, #000, transparent); }}
.marquee-container::after {{ right: 0; background: linear-gradient(to left, #000, transparent); }}
.marquee-content {{
    display: flex; width: max-content; animation: scroll 40s linear infinite;
}}
.marquee-item {{
    font-family: 'Space Grotesk', sans-serif;
    font-size: 3rem; font-weight: 800;
    color: transparent;
    -webkit-text-stroke: 1px rgba(255,255,255,0.15);
    padding: 0 3rem; text-transform: uppercase;
    transition: all 0.4s ease;
}}
.marquee-item:hover {{
    -webkit-text-stroke: 1px #fff; color: #fff; text-shadow: 0 0 30px rgba(255,255,255,0.6);
    transform: scale(1.1);
}}
@keyframes scroll {{ to {{ transform: translateX(-50%); }} }}

/* ── Streamlit Button Overrides ── */
.btn-wrapper {{
    max-width: 900px; margin: 0 auto 4rem; padding: 0 2rem;
    animation: slideUp 1s cubic-bezier(0.16, 1, 0.3, 1) 0.4s backwards;
}}
div.stButton > button, div.stLinkButton > a {{
    width: 100% !important; padding: 1.4rem 2.5rem !important;
    border-radius: 100px !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 800 !important;
    font-size: 1.1rem !important; text-transform: uppercase !important; letter-spacing: 1.5px !important;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}
div.stButton > button[kind="primary"] {{ background: #fff !important; color: #000 !important; border: none !important; }}
div.stButton > button[kind="primary"]:hover {{
    transform: scale(1.05) translateY(-4px) !important;
    box-shadow: 0 20px 40px rgba(255,255,255,0.3) !important;
}}
div.stButton > button[kind="secondary"], div.stLinkButton > a {{
    background: rgba(255,255,255,0.02) !important; color: #fff !important;
    border: 1px solid rgba(255,255,255,0.15) !important; text-decoration: none !important; text-align: center;
    backdrop-filter: blur(10px) !important;
}}
div.stButton > button[kind="secondary"]:hover, div.stLinkButton > a:hover {{
    background: rgba(255,255,255,0.1) !important; border-color: rgba(255,255,255,0.3) !important;
    transform: scale(1.05) translateY(-4px) !important; box-shadow: 0 20px 40px rgba(0,0,0,0.5) !important;
}}

/* Footer */
.ultra-footer {{ text-align: center; padding: 5rem 2rem; color: #64748b; font-size: 1rem; }}
.ultra-footer strong {{ color: #fff; font-weight: 700; letter-spacing: 1px; }}
</style>

<!-- Background -->
<div class="mesh-bg"></div>
<div class="bg-orbs">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
</div>

<!-- Nav -->
<div class="hyper-nav">
    <div class="logo-container">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="24" height="24" rx="6" fill="#E2231A"/>
            <path d="M7 12l4 4 6-8" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="logo-text">Lenovo<span>AI</span></div>
    </div>
    <div style="display:flex; gap:32px; font-size:0.9rem; font-weight:700; color:#94a3b8;">
        <span style="color:#fff;">Overview</span>
        <span>Platform</span>
        <span>Architecture</span>
    </div>
</div>

<!-- Hero -->
<div class="hyper-hero">
    <div class="hero-badge"><span>●</span> Next-Gen Enterprise Intelligence</div>
    <h1>
        <span class="text-gradient">Agentic AI for</span><br/>
        <span class="text-shimmer">Strategic Research</span>
    </h1>
    <p>A hyper-responsive, production-ready platform integrating LangGraph autonomous routing, dynamic RAG document retrieval, and deep analytics.</p>
</div>
""", unsafe_allow_html=True)

# Streamlit Buttons (wrapped in a styled container)
st.markdown("<div class='btn-wrapper'>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("Launch Workspace", type="primary"):
        st.switch_page("appt.py")
with c2:
    if st.button("System Health", type="secondary"):
        st.switch_page("pages/health.py")
with c3:
    st.link_button("Analytics Dashboard", "https://ai-industry-insights.preview.emergentagent.com/")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(f"""
<!-- Stats -->
<div class="hyper-stats">
<div class="stat-box">
<div class="stat-num">{total_queries}</div>
<div class="stat-name">Queries Processed</div>
</div>
<div class="stat-box">
<div class="stat-num">{file_count}</div>
<div class="stat-name">Source Docs</div>
</div>
<div class="stat-box">
<div class="stat-num">{avg_relevance:.0%}</div>
<div class="stat-name">Avg Relevance</div>
</div>
<div class="stat-box">
<div class="stat-num">3</div>
<div class="stat-name">Agent Tools</div>
</div>
</div>

<!-- Bento Grid -->
<div class="bento-wrapper">
<div class="bento-grid">
<div class="hyper-card" style="--accent: #06b6d4;">
<div class="hc-badge live">Live</div>
<div class="card-icon-wrapper">🔍</div>
<div class="hc-title">Research Workspace</div>
<div class="hc-desc">Full-stack chat interface with multi-tool agent routing. Auto-switches between internal ChromaDB search and live Tavily web intelligence.</div>
</div>

<div class="hyper-card" style="--accent: #E2231A;">
<div class="hc-badge live">Live</div>
<div class="card-icon-wrapper">📈</div>
<div class="hc-title">Telemetry Engine</div>
<div class="hc-desc">Real-time observability. Visualizes query routing decisions, confidence distributions, and live agent activity streams from production logs.</div>
</div>

<div class="hyper-card" style="--accent: #3b82f6;">
<div class="hc-badge deployed">Deployed</div>
<div class="card-icon-wrapper">📊</div>
<div class="hc-title">Executive Analytics</div>
<div class="hc-desc">Interactive React SPA dashboard featuring ROI calculations, Fortune 500 AI adoption metrics, and dynamic industry case studies.</div>
</div>
</div>
</div>

<!-- Marquee -->
<div class="marquee-container">
<div class="marquee-content">
<div class="marquee-item">LangGraph</div>
<div class="marquee-item">ChromaDB</div>
<div class="marquee-item">React</div>
<div class="marquee-item">FastAPI</div>
<div class="marquee-item">Ollama</div>
<div class="marquee-item">Streamlit</div>
<div class="marquee-item">Tavily</div>
<!-- Duplicate for infinite scroll loop -->
<div class="marquee-item">LangGraph</div>
<div class="marquee-item">ChromaDB</div>
<div class="marquee-item">React</div>
<div class="marquee-item">FastAPI</div>
<div class="marquee-item">Ollama</div>
<div class="marquee-item">Streamlit</div>
<div class="marquee-item">Tavily</div>
</div>
</div>

<div class="ultra-footer">
Designed & Engineered by <strong>Lenovo AI Engineering</strong><br/>
<span style="opacity: 0.6; display: inline-block; margin-top: 8px;">Enterprise Agentic Research Intelligence · 2026</span>
</div>
""", unsafe_allow_html=True)
