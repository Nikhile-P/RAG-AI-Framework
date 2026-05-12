import streamlit as st
import os
import ast
from datetime import datetime
from collections import Counter

# ============================================================
# SYSTEM HEALTH — Telemetry & Performance Dashboard
# ============================================================

# Navigation (since auto-nav is hidden)
nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 4])
with nav_col1:
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("pages/home.py")
with nav_col2:
    if st.button("🔍 Research", use_container_width=True):
        st.switch_page("appt.py")


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
.stApp { font-family: 'Inter', sans-serif !important; }

.health-hero {
    padding: 1.5rem 0;
    margin-bottom: 1rem;
}
.health-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #f0f0f0;
    margin-bottom: 0.3rem;
}
.health-sub {
    font-size: 0.9rem;
    color: #666;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1rem 0;
}
.m-card {
    background: linear-gradient(155deg, rgba(30,31,34,0.9), rgba(20,20,22,0.95));
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 1.5rem;
    text-align: center;
}
.m-card-val {
    font-size: 2rem;
    font-weight: 800;
}
.m-card-val.red { color: #E2231A; }
.m-card-val.blue { color: #58A6FF; }
.m-card-val.green { color: #3FB950; }
.m-card-val.purple { color: #A371F7; }
.m-card-label {
    font-size: 0.75rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
    margin-top: 6px;
}

/* Log Entry */
.log-entry {
    padding: 10px 14px;
    background: rgba(20,20,22,0.8);
    border: 1px solid rgba(255,255,255,0.04);
    border-radius: 8px;
    margin-bottom: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #aaa;
    display: flex;
    gap: 12px;
    align-items: center;
}
.log-ts { color: #666; min-width: 140px; }
.log-path { font-weight: 600; }
.log-path.rag { color: #3FB950; }
.log-path.web { color: #58A6FF; }
.log-path.deep { color: #A371F7; }
.log-path.proxy { color: #E2231A; }
.log-conf { padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; }
.log-conf.high { background: rgba(63,185,80,0.15); color: #3FB950; }
.log-conf.medium { background: rgba(226,178,50,0.15); color: #E2B232; }
.log-conf.low { background: rgba(226,35,26,0.15); color: #E2231A; }
</style>
""", unsafe_allow_html=True)

# --- Parse Router Log ---
log_path = os.path.join(os.path.dirname(__file__), '..', 'router.log')
entries = []
try:
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(ast.literal_eval(line))
                except Exception:
                    continue
except Exception:
    pass

total = len(entries)
paths = [e.get('path', 'Unknown') for e in entries]
confidences = [e.get('details', {}).get('confidence', 'N/A') for e in entries]
relevances = [float(e.get('details', {}).get('relevance', 0)) for e in entries if e.get('details', {}).get('relevance')]
escalations = sum(1 for e in entries if e.get('details', {}).get('escalations', 0) > 0)
sources_all = []
for e in entries:
    sources_all.extend(e.get('details', {}).get('sources', []))

web_count = sum(1 for p in paths if 'Web Search' in p)
rag_count = sum(1 for p in paths if 'Turbo RAG' in p and 'Web' not in p and 'Deep' not in p)
deep_count = sum(1 for p in paths if 'Deep Agent' in p)
avg_rel = sum(relevances) / len(relevances) if relevances else 0

# --- Header ---
st.markdown("""
<div class="health-hero">
    <div class="health-title">📈 System Health & Telemetry</div>
    <div class="health-sub">Real-time performance metrics from the agent routing engine</div>
</div>
""", unsafe_allow_html=True)

# --- Top Metrics ---
st.markdown(f"""
<div class="metric-grid">
    <div class="m-card">
        <div class="m-card-val red">{total}</div>
        <div class="m-card-label">Total Queries</div>
    </div>
    <div class="m-card">
        <div class="m-card-val blue">{avg_rel:.0%}</div>
        <div class="m-card-label">Avg Relevance</div>
    </div>
    <div class="m-card">
        <div class="m-card-val green">{escalations}</div>
        <div class="m-card-label">Escalations</div>
    </div>
    <div class="m-card">
        <div class="m-card-val purple">{len(set(sources_all))}</div>
        <div class="m-card-label">Unique Sources</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Charts Row ---
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🛣️ Query Routing Distribution")
    route_data = {"Turbo RAG": rag_count, "Deep Agent": deep_count, "Web Search": web_count}
    st.bar_chart(route_data, color="#E2231A", horizontal=True)

with col2:
    st.markdown("#### 🎯 Confidence Breakdown")
    conf_counts = Counter(confidences)
    st.bar_chart(dict(conf_counts), color="#58A6FF")

# --- Source Utilization ---
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 📁 Top Source Documents")
    local_sources = [s for s in sources_all if not s.startswith('http')]
    source_counts = Counter(local_sources).most_common(8)
    if source_counts:
        names = [s[0].replace('Lenovo_', '').replace('.txt', '').replace('_', ' ')[:30] for s in source_counts]
        counts = [s[1] for s in source_counts]
        chart_data = dict(zip(names, counts))
        st.bar_chart(chart_data, color="#3FB950", horizontal=True)
    else:
        st.info("No source data available yet.")

with col4:
    st.markdown("#### 🌐 Web Search Targets")
    web_sources = [s for s in sources_all if s.startswith('http')]
    if web_sources:
        import urllib.parse
        domains = []
        for u in web_sources:
            try:
                domains.append(urllib.parse.urlparse(u).netloc.replace('www.', '')[:30])
            except Exception:
                domains.append(u[:30])
        domain_counts = Counter(domains).most_common(8)
        chart_data = dict(domain_counts)
        st.bar_chart(chart_data, color="#58A6FF", horizontal=True)
    else:
        st.info("No web search data available yet.")

# --- Relevance Over Time ---
st.markdown("#### 📊 Relevance Score Timeline")
if relevances:
    st.line_chart(relevances, color="#E2231A")
else:
    st.info("No relevance data available yet.")

# --- Live Log Tail ---
st.markdown("---")
st.markdown("#### 🔴 Recent Agent Activity")

recent = entries[-15:][::-1]  # Last 15, newest first
for e in recent:
    ts = e.get('ts', '')
    query = e.get('query', '')[:60]
    path = e.get('path', 'Unknown')
    conf = e.get('details', {}).get('confidence', 'N/A')
    rel = e.get('details', {}).get('relevance', 0)
    
    # Color class for path
    if 'Web Search' in path:
        path_cls = 'web'
    elif 'Deep Agent' in path:
        path_cls = 'deep'
    elif 'Proxy' in path:
        path_cls = 'proxy'
    else:
        path_cls = 'rag'
    
    conf_cls = conf.lower() if conf in ['High', 'Medium', 'Low'] else 'medium'
    
    st.markdown(f"""
    <div class="log-entry">
        <span class="log-ts">{ts}</span>
        <span style="flex: 1; color: #ccc;">{query}</span>
        <span class="log-path {path_cls}">{path}</span>
        <span class="log-conf {conf_cls}">{conf}</span>
        <span style="color: #555; min-width: 40px; text-align: right;">{rel:.0%}</span>
    </div>
    """, unsafe_allow_html=True)

# --- Raw Log Viewer ---
with st.expander("🗂️ Full Router Log (raw)"):
    try:
        with open(log_path, 'r') as f:
            st.code(f.read(), language="python")
    except Exception as e:
        st.error(f"Could not read log: {e}")
