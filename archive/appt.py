import streamlit as st
import re
import requests
import time
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv

# ==========================================
# 1. UI CONFIGURATION & THEME ENGINE
# ==========================================
try:
    st.set_page_config(
        page_title="Lenovo Research Workspace",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except st.errors.StreamlitAPIException:
    pass  # Already configured by platform.py

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# --- DYNAMIC CSS VARIABLES ---
theme_vars = """
    :root {
        --bg-main: #0E1117;
        --bg-card: rgba(22, 27, 34, 0.72);
        --bg-input: rgba(28, 34, 43, 0.84);
        --text-main: #F0F6FC;
        --text-muted: #8B949E;
        --border-color: rgba(138, 154, 173, 0.24);
        --accent-red: #E2231A;
        --shadow-color: rgba(0, 0, 0, 0.32);
        --sidebar-bg: rgba(13, 16, 23, 0.78);
        --bg-gradient-a: rgba(11, 16, 24, 1);
        --bg-gradient-b: rgba(30, 15, 16, 1);
        --bg-gradient-c: rgba(18, 26, 36, 1);
        --surface-glass: rgba(255, 255, 255, 0.04);
        --surface-glass-strong: rgba(255, 255, 255, 0.07);
        --pill-radius: 999px;
        --panel-radius: 24px;
        --panel-blur: 14px;
        --suggestion-bg: rgba(255, 255, 255, 0.05);
        --suggestion-bg-hover: rgba(255, 255, 255, 0.09);
        --suggestion-border: rgba(210, 221, 236, 0.22);
        --suggestion-text: #EAF2FF;
        --suggestion-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
        --suggestion-shadow-breathe: 0 14px 28px rgba(226, 35, 26, 0.22);
        --motion-smooth: cubic-bezier(0.22, 0.61, 0.36, 1);
        --motion-fast: 180ms;
        --motion-mid: 340ms;
        --motion-slow: 640ms;
    }
""" if st.session_state.theme == "dark" else """
    :root {
        --bg-main: #EEF3F8;
        --bg-card: rgba(255, 255, 255, 0.84);
        --bg-input: rgba(255, 255, 255, 0.93);
        --text-main: #0F172A;
        --text-muted: #64748B;
        --border-color: rgba(97, 119, 147, 0.24);
        --accent-red: #E2231A;
        --shadow-color: rgba(15, 23, 42, 0.12);
        --sidebar-bg: rgba(248, 250, 252, 0.78);
        --bg-gradient-a: rgba(238, 244, 251, 1);
        --bg-gradient-b: rgba(255, 244, 242, 1);
        --bg-gradient-c: rgba(234, 243, 255, 1);
        --surface-glass: rgba(255, 255, 255, 0.52);
        --surface-glass-strong: rgba(255, 255, 255, 0.68);
        --pill-radius: 999px;
        --panel-radius: 24px;
        --panel-blur: 16px;
        --suggestion-bg: rgba(255, 255, 255, 0.74);
        --suggestion-bg-hover: rgba(255, 255, 255, 0.9);
        --suggestion-border: rgba(131, 154, 184, 0.42);
        --suggestion-text: #1E293B;
        --suggestion-shadow: 0 8px 24px rgba(24, 44, 78, 0.12);
        --suggestion-shadow-breathe: 0 12px 30px rgba(226, 35, 26, 0.16);
        --motion-smooth: cubic-bezier(0.22, 0.61, 0.36, 1);
        --motion-fast: 180ms;
        --motion-mid: 340ms;
        --motion-slow: 640ms;
    }
"""

css_injection = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    __THEME_VARS__

    /* 🌐 GLOBAL RESETS & PERFECT CENTERING */
    html, body, [class*="css"], .stApp {{
        font-family: 'Inter', sans-serif !important;
        background-color: var(--bg-main) !important;
        background-image:
            radial-gradient(circle at 8% 10%, rgba(226, 35, 26, 0.08), transparent 32%),
            radial-gradient(circle at 92% 4%, rgba(88, 166, 255, 0.09), transparent 36%),
            linear-gradient(135deg, var(--bg-gradient-a), var(--bg-gradient-b) 46%, var(--bg-gradient-c));
        color: var(--text-main) !important;
        transition: background-color var(--motion-mid) var(--motion-smooth), color var(--motion-mid) var(--motion-smooth);
        text-rendering: optimizeLegibility;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    
    h1, h2, h3, p, span, div, li, .stMarkdown {{ color: var(--text-main) !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    #MainMenu, footer {{ display: none !important; }}
    
    .block-container {{ padding-top: 1rem !important; padding-bottom: 120px !important; max-width: 900px !important; margin: 0 auto; }}

    /* 🌊 FLUENT LIQUID ANIMATIONS */
    @keyframes gradient-pan {{ 0% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} 100% {{ background-position: 0% 50%; }} }}
    @keyframes float-avatar {{ 0%, 100% {{ transform: translateY(0px); box-shadow: 0 10px 20px rgba(226,35,26,0.3); }} 50% {{ transform: translateY(-8px); box-shadow: 0 15px 30px rgba(226,35,26,0.5); }} }}
    @keyframes pop-in {{ 0% {{ opacity: 0; transform: translateY(20px); }} 100% {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes card-breathe {{
        0%, 100% {{ transform: translate3d(0, 0, 0) scale(1); box-shadow: var(--suggestion-shadow); }}
        50% {{ transform: translate3d(0, -1px, 0) scale(1.004); box-shadow: var(--suggestion-shadow-breathe); }}
    }}
    @keyframes glass-drift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    @keyframes lenovo-breathe {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.004); }}
    }}

    @keyframes input-glow {{
        0%, 100% {{ box-shadow: 0 10px 26px var(--shadow-color); }}
        50% {{ box-shadow: 0 14px 34px rgba(88, 166, 255, 0.18); }}
    }}

    /* 🤖 ELEGANT HEADER BOX */
    .bot-header-box {{
        display: flex; align-items: center; justify-content: center; gap: 1.5rem;
        background: linear-gradient(155deg, var(--bg-card), var(--surface-glass));
        background-size: 180% 180%;
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        padding: 1.5rem; border-radius: var(--panel-radius);
        border: 1px solid var(--border-color); box-shadow: 0 8px 24px var(--shadow-color);
        margin: 0 auto 3rem auto; max-width: 750px; transition: all var(--motion-mid) var(--motion-smooth);
        animation: pop-in var(--motion-slow) var(--motion-smooth) forwards, glass-drift 18s ease-in-out infinite;
        will-change: transform;
    }}
    .bot-avatar-circle {{
        background: linear-gradient(135deg, #E2231A, #FF4B4B); width: 60px; height: 60px;
        border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2rem;
        animation: float-avatar 4s ease-in-out infinite;
    }}
    .bot-info h1 {{ margin: 0; font-size: 1.6rem; font-weight: 700; letter-spacing: -0.5px; color: var(--text-main) !important; }}
    .bot-info p {{ margin: 4px 0 0 0; font-size: 0.85rem; color: var(--text-muted) !important; display: flex; align-items: center; gap: 8px; }}
    .status-dot {{ width: 8px; height: 8px; background: #4ADE80; border-radius: 50%; display: inline-block; box-shadow: 0 0 10px #4ADE80; }}

    .lenovo-brand-wrap {{
        margin-top: -6px;
        margin-bottom: 10px;
        padding: 0;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: flex-start;
        gap: 6px;
        background: transparent;
        border-radius: 0;
        box-shadow: none;
        border: none;
    }}
    .lenovo-logo-image {{
        width: 194px;
        max-width: 100%;
        height: auto;
        display: block;
        border-radius: 0;
        animation: none;
        transform-origin: left center;
        filter: none;
    }}
    .lenovo-subtitle {{
        color: var(--text-muted) !important;
        font-size: 0.69rem;
        font-weight: 600;
        letter-spacing: 1.35px;
        text-transform: uppercase;
        line-height: 1;
        margin-left: 2px;
        opacity: 0.88;
    }}

    /* ⚡ MAIN QUERY CARDS (Minimalist Breathing Design) */
    .quick-actions-title {{
        text-align: center; font-size: 0.75rem; font-weight: 700; letter-spacing: 4px;
        text-transform: uppercase; margin-bottom: 1.35rem; color: var(--text-muted) !important; opacity: 0.78;
    }}
    
    div.element-container:has(.suggestion-anchor) + div.element-container button {{
        background: linear-gradient(150deg, var(--suggestion-bg), var(--surface-glass-strong)) !important;
        background-size: 180% 180% !important;
        border: 1.5px solid var(--suggestion-border) !important;
        color: var(--suggestion-text) !important;
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        border-radius: var(--panel-radius) !important; 
        padding: 1.1rem 1.2rem !important; 
        width: 100% !important;
        min-height: 82px !important; 
        transition: all var(--motion-mid) var(--motion-smooth) !important;
        animation: card-breathe 7.5s var(--motion-smooth) infinite, glass-drift 22s ease-in-out infinite;
        box-shadow: var(--suggestion-shadow) !important;
        will-change: transform, box-shadow;
        transform: translateZ(0);
        position: relative;
        overflow: hidden;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, transparent 18%, rgba(255, 255, 255, 0.12) 45%, transparent 72%);
        transform: translateX(-130%);
        transition: transform 900ms var(--motion-smooth);
        pointer-events: none;
    }}
    /* Deep nuke for Streamlit's hidden inner button elements */
    div.element-container:has(.suggestion-anchor) + div.element-container button > div,
    div.element-container:has(.suggestion-anchor) + div.element-container button > div > div {{
        background: transparent !important; background-color: transparent !important;
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button p,
    div.element-container:has(.suggestion-anchor) + div.element-container button span,
    div.element-container:has(.suggestion-anchor) + div.element-container button * {{
        color: var(--suggestion-text) !important; -webkit-text-fill-color: var(--suggestion-text) !important;
        font-weight: 600 !important; font-size: 0.95rem !important; margin: 0 !important; background: transparent !important;
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button:hover {{
        background: linear-gradient(150deg, var(--suggestion-bg-hover), var(--surface-glass-strong)) !important;
        transform: translate3d(0, -6px, 0) scale(1.02) !important;
        border-color: var(--accent-red) !important;
        box-shadow: 0 16px 32px rgba(226, 35, 26, 0.22) !important;
        animation: none !important;
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button:hover::before {{
        transform: translateX(130%);
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button:active {{
        transform: translate3d(0, 0, 0) scale(0.995) !important;
    }}
    div.element-container:has(.suggestion-anchor) + div.element-container button:hover p {{ color: var(--accent-red) !important; -webkit-text-fill-color: var(--accent-red) !important; }}

    /* ⌨️ FLOATING INPUT BOX (NUKING THE BLACK BACKGROUND GLOBALLY) */
    [data-testid="stBottom"], [data-testid="stBottom"] > div, .stAppBottomBlock {{
        background: transparent !important; background-color: transparent !important; border: none !important;
    }}
    [data-testid="stChatInput"] {{
        background: linear-gradient(160deg, var(--bg-input), var(--surface-glass-strong)) !important;
        background-size: 170% 170% !important;
        border: 1px solid var(--border-color) !important;
        backdrop-filter: blur(calc(var(--panel-blur) + 2px));
        -webkit-backdrop-filter: blur(calc(var(--panel-blur) + 2px));
        border-radius: var(--pill-radius) !important; padding: 0.7rem 1.2rem !important; margin: 0 auto 25px auto !important;
        box-shadow: 0 10px 30px var(--shadow-color) !important; transition: all var(--motion-mid) var(--motion-smooth); max-width: 900px !important;
        animation: glass-drift 24s ease-in-out infinite, input-glow 6.5s ease-in-out infinite;
        position: relative;
        overflow: hidden;
    }}
    [data-testid="stChatInput"]::before {{
        content: "";
        position: absolute;
        inset: 0;
        border-radius: inherit;
        padding: 1px;
        background: linear-gradient(120deg, rgba(226, 35, 26, 0.35), rgba(88, 166, 255, 0.28), rgba(226, 35, 26, 0.35));
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        opacity: 0.55;
        pointer-events: none;
    }}
    /* Deep Nuke inside chat input */
    [data-testid="stChatInput"] > div, [data-testid="stChatInput"] > div > div {{ background: transparent !important; background-color: transparent !important; }}
    [data-testid="stChatInput"] * {{ background: transparent !important; color: var(--text-main) !important; -webkit-text-fill-color: var(--text-main) !important; }}
    [data-testid="stChatInput"] svg {{ fill: var(--text-main) !important; }}
    [data-testid="stChatInput"]:focus-within {{ border-color: var(--accent-red) !important; transform: translateY(-3px); box-shadow: 0 16px 36px rgba(226, 35, 26, 0.2) !important;}}

    /* 🌙 FLOATING TOP-RIGHT THEME TOGGLE */
    div.element-container:has(.theme-toggle-anchor) + div.element-container {{
        position: fixed !important;
        top: 8px;
        right: 16px;
        z-index: 9999;
        margin: 0 !important;
    }}
    div.element-container:has(.theme-toggle-anchor) + div.element-container button {{
        width: 48px !important; 
        height: 48px !important; 
        min-width: 48px !important; 
        min-height: 48px !important;
        border-radius: var(--pill-radius) !important; 
        padding: 0 !important; 
        margin: 0 !important;
        display: flex !important; 
        align-items: center !important; 
        justify-content: center !important;
        font-size: 1.4rem !important; 
        background: linear-gradient(160deg, var(--bg-card), var(--surface-glass-strong)) !important;
        border: 1.5px solid var(--border-color) !important; 
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        transition: all var(--motion-mid) var(--motion-smooth) !important; 
        outline: none !important;
        box-shadow: 0 8px 24px var(--shadow-color) !important;
        position: relative;
        overflow: hidden;
        color: var(--text-main) !important;
    }}
    
    div.element-container:has(.theme-toggle-anchor) + div.element-container button::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, transparent, rgba(226, 35, 26, 0.08), transparent);
        opacity: 0;
        transition: opacity var(--motion-mid) var(--motion-smooth);
        pointer-events: none;
    }}
    
    div.element-container:has(.theme-toggle-anchor) + div.element-container button:hover {{
        transform: scale(1.1) rotate(-5deg);
        border-color: var(--accent-red) !important;
        box-shadow: 0 12px 32px rgba(226, 35, 26, 0.28) !important;
        background: linear-gradient(160deg, var(--bg-card), var(--surface-glass-strong)) !important;
        color: var(--text-main) !important;
    }}
    
    div.element-container:has(.theme-toggle-anchor) + div.element-container button:hover::before {{
        opacity: 1;
    }}
    
    div.element-container:has(.theme-toggle-anchor) + div.element-container button:active {{
        transform: scale(0.95);
    }}

    @media (max-width: 900px) {{
        div.element-container:has(.theme-toggle-anchor) + div.element-container {{
            top: 8px;
            right: 10px;
        }}
    }}

    button:focus-visible {{
        outline: 2px solid var(--accent-red) !important;
        outline-offset: 2px !important;
    }}

    /* Tooltip styling */
    div[data-testid="stTooltipContent"] {{
        background-color: var(--bg-input) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
    }}

    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation: none !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }}
    }}

    /* 🧼 THE "2ND LAYOUT" SIDEBAR ARCHITECTURE */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--sidebar-bg), var(--surface-glass)) !important;
        backdrop-filter: blur(calc(var(--panel-blur) + 3px));
        -webkit-backdrop-filter: blur(calc(var(--panel-blur) + 3px));
        border-right: 1px solid var(--border-color) !important;
        padding-top: 0.2rem !important;
    }}
    
    /* New Chat Button */
    div.element-container:has(.new-session-anchor) + div.element-container button {{
        border: 1px solid var(--border-color) !important;
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass)) !important;
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        justify-content: center !important; text-align: center !important; border-radius: var(--pill-radius) !important; 
        width: 100% !important; transition: all 0.2s ease !important; padding: 0.6rem !important;
    }}
    div.element-container:has(.new-session-anchor) + div.element-container button p {{ color: var(--text-main) !important; font-weight: 500 !important; font-size: 0.95rem !important;}}
    div.element-container:has(.new-session-anchor) + div.element-container button:hover {{ border-color: var(--text-muted) !important; background: rgba(150,150,150,0.05) !important; }}
    
    /* Recent Session Buttons */
    div.element-container:has(.sidebar-chat-anchor) + div.element-container button {{
        text-align: left !important; justify-content: flex-start !important; padding: 0.5rem 1rem !important;
        border-radius: var(--pill-radius) !important; transition: all 0.2s ease !important;
        background: transparent !important; border: 1px solid transparent !important; width: 100% !important;
    }}
    div.element-container:has(.sidebar-chat-anchor) + div.element-container button p {{ color: var(--text-muted) !important; font-weight: 500 !important; font-size: 0.9rem !important;}}
    div.element-container:has(.sidebar-chat-anchor) + div.element-container button:hover {{
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass)) !important;
        border-color: var(--border-color) !important;
    }}
    div.element-container:has(.sidebar-chat-anchor) + div.element-container button:hover p {{ color: var(--text-main) !important; }}
    
    /* Clear Workspace Pill */
    div.element-container:has(.reset-anchor) + div.element-container button {{
        width: 100% !important; margin: 15px auto !important; border-radius: var(--pill-radius) !important;
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass)) !important;
        border: 1px solid var(--border-color) !important; transition: all 0.2s ease !important; justify-content: center !important; padding: 0.6rem !important;
    }}
    div.element-container:has(.reset-anchor) + div.element-container button p {{ color: var(--text-muted) !important; font-weight: 600 !important; font-size: 0.85rem !important;}}
    div.element-container:has(.reset-anchor) + div.element-container button:hover {{ border-color: #EF4444 !important; background: rgba(239,68,68,0.1) !important; }}
    div.element-container:has(.reset-anchor) + div.element-container button:hover p {{ color: #EF4444 !important; }}

    /* Sign Out Button */
    div.element-container:has(.signout-anchor) + div.element-container button {{
        width: 100% !important; margin: 10px auto !important; border-radius: var(--pill-radius) !important;
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass)) !important;
        border: 1px solid var(--border-color) !important; transition: all 0.2s ease !important; justify-content: center !important; padding: 0.5rem !important;
    }}
    div.element-container:has(.signout-anchor) + div.element-container button p {{ color: var(--text-main) !important; font-weight: 600 !important; font-size: 0.85rem !important;}}
    div.element-container:has(.signout-anchor) + div.element-container button:hover {{ border-color: var(--accent-red) !important; background: rgba(226,35,26,0.1) !important; }}
    div.element-container:has(.signout-anchor) + div.element-container button:hover p {{ color: var(--accent-red) !important; }}

    /* Source Pill Button Styling */
    div.element-container:has(.source-pill-anchor) + div.element-container button {{
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass-strong)) !important;
        border: 1px solid rgba(226, 35, 26, 0.25) !important;
        border-radius: var(--pill-radius) !important;
        color: var(--text-main) !important;
        transition: all var(--motion-mid) var(--motion-smooth) !important;
        padding: 0.5rem 0.8rem !important;
    }}
    div.element-container:has(.source-pill-anchor) + div.element-container button p {{
        color: var(--text-main) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }}
    div.element-container:has(.source-pill-anchor) + div.element-container button:hover {{
        transform: translateY(-2px) scale(1.02);
        border-color: var(--accent-red) !important;
        box-shadow: 0 8px 24px rgba(226, 35, 26, 0.15) !important;
        background: linear-gradient(145deg, var(--bg-card), rgba(226, 35, 26, 0.08)) !important;
    }}

    /* Modal Dialog & Download Button */
    div[data-testid="stDialog"] > div {{
        background-color: var(--bg-main) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: var(--panel-radius) !important;
    }}
    div.element-container:has(.modal-download-anchor) + div.element-container button {{
        background: linear-gradient(145deg, var(--accent-red), #FF4B4B) !important;
        border: none !important;
        border-radius: var(--pill-radius) !important;
        color: white !important;
        transition: all 0.2s ease !important;
    }}
    div.element-container:has(.modal-download-anchor) + div.element-container button p {{
        color: white !important;
        font-weight: 600 !important;
    }}
    div.element-container:has(.modal-download-anchor) + div.element-container button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(226, 35, 26, 0.4) !important;
    }}

    hr {{ border-color: rgba(150,150,150,0.15) !important; margin: 1.5rem 0 !important; }}

    /* Chat Message Bubbles */
    [data-testid="chat-message-user"], [data-testid="chat-message-assistant"] {{
        background: linear-gradient(155deg, var(--bg-card), var(--surface-glass)) !important;
        border: 1px solid var(--border-color) !important;
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        border-radius: var(--panel-radius) !important; padding: 1.5rem !important; margin: 1.5rem 0 !important;
        box-shadow: 0 4px 12px var(--shadow-color) !important;
    }}
    [data-testid="chat-message-assistant"] {{ border-left: 4px solid var(--accent-red) !important; }}

    /* Constrain markdown heading sizes inside chat area */
    .stMainBlockContainer h1 {{ font-size: 1.4rem !important; font-weight: 700 !important; margin: 0.6rem 0 !important; }}
    .stMainBlockContainer h2 {{ font-size: 1.15rem !important; font-weight: 600 !important; margin: 0.5rem 0 !important; }}
    .stMainBlockContainer h3 {{ font-size: 1rem !important; font-weight: 600 !important; margin: 0.4rem 0 !important; }}
    .stMainBlockContainer p, .stMainBlockContainer li {{ font-size: 0.95rem !important; line-height: 1.6 !important; }}
    .stMainBlockContainer ul, .stMainBlockContainer ol {{ padding-left: 1.2rem !important; margin: 0.3rem 0 !important; }}

    /* 🗂️ SOURCE NAVIGATOR SECTION */
    .source-navigator-container {{
        margin-top: 1.5rem;
        padding: 1.2rem;
        background: linear-gradient(160deg, rgba(226, 35, 26, 0.08), rgba(88, 166, 255, 0.06)) !important;
        border: 1px solid rgba(226, 35, 26, 0.2) !important;
        border-radius: var(--panel-radius);
        backdrop-filter: blur(var(--panel-blur));
        -webkit-backdrop-filter: blur(var(--panel-blur));
        box-shadow: 0 8px 24px rgba(226, 35, 26, 0.08) !important;
    }}

    .source-navigator-title {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--accent-red);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 6px;
    }}

    .source-navigator-pills {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
        align-items: center;
    }}

    .source-pill {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.6rem 1rem;
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass-strong)) !important;
        border: 1px solid rgba(226, 35, 26, 0.25) !important;
        border-radius: var(--pill-radius);
        cursor: pointer;
        transition: all var(--motion-mid) var(--motion-smooth);
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--text-main) !important;
        white-space: nowrap;
        position: relative;
        overflow: hidden;
    }}

    .source-pill::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(226, 35, 26, 0.1), rgba(88, 166, 255, 0.05));
        opacity: 0;
        transition: opacity var(--motion-mid) var(--motion-smooth);
        pointer-events: none;
    }}

    .source-pill:hover {{
        transform: translateY(-2px) scale(1.06);
        border-color: var(--accent-red) !important;
        box-shadow: 0 12px 28px rgba(226, 35, 26, 0.22) !important;
        background: linear-gradient(145deg, var(--bg-card), rgba(226, 35, 26, 0.1)) !important;
    }}

    .source-pill:hover::before {{
        opacity: 1;
    }}

    .source-icon {{
        font-size: 1rem;
        flex-shrink: 0;
    }}

    .source-filename {{
        position: relative;
        z-index: 1;
    }}

    /* Pulse animation for new sources */
    @keyframes source-pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(226, 35, 26, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(226, 35, 26, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(226, 35, 26, 0); }}
    }}

    .source-pill.new {{
        animation: source-pulse 2s ease-out;
    }}

    /* File type badges */
    .source-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background: rgba(226, 35, 26, 0.15);
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--accent-red);
    }}

    /* 🎬 ENHANCED ANIMATIONS FOR LIVELY UI */
    @keyframes card-entrance {{
        0% {{
            opacity: 0;
            transform: translateY(12px) scale(0.98);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
    }}

    @keyframes shimmer-glow {{
        0% {{
            text-shadow: 0 0 8px rgba(226, 35, 26, 0);
        }}
        50% {{
            text-shadow: 0 0 16px rgba(226, 35, 26, 0.3);
        }}
        100% {{
            text-shadow: 0 0 8px rgba(226, 35, 26, 0);
        }}
    }}

    [data-testid="chat-message-assistant"] {{
        animation: card-entrance 0.5s var(--motion-smooth);
    }}

    /* Status indicator pulse */
    @keyframes status-pulse {{
        0%, 100% {{
            box-shadow: 0 0 0 0 rgba(226, 35, 26, 0.7);
        }}
        50% {{
            box-shadow: 0 0 0 8px rgba(226, 35, 26, 0);
        }}
    }}

    .status-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #4ADE80;
        margin-right: 6px;
        animation: status-pulse 2s infinite;
    }}

    /* Enhanced input focus glow */
    [data-testid="stChatInputContainer"] {{
        animation: subtle-drift 20s ease-in-out infinite;
    }}

    @keyframes subtle-drift {{
        0%, 100% {{
            transform: translateY(0px);
        }}
        50% {{
            transform: translateY(-2px);
        }}
    }}

    /* Hover gradient reveal for buttons */
    div.element-container:has(.suggestion-anchor) + div.element-container button {{
        position: relative;
        overflow: hidden;
    }}

    div.element-container:has(.suggestion-anchor) + div.element-container button::after {{
        content: "";
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, rgba(226, 35, 26, 0), rgba(226, 35, 26, 0.1), rgba(226, 35, 26, 0));
        transition: left var(--motion-mid) var(--motion-smooth);
        pointer-events: none;
    }}

    div.element-container:has(.suggestion-anchor) + div.element-container button:hover::after {{
        left: 100%;
    }}

    /* Message text enhancement */
    [data-testid="chat-message-user"] p, [data-testid="chat-message-assistant"] p {{
        font-size: 0.95rem;
        line-height: 1.7;
        letter-spacing: 0.3px;
    }}

    /* Sidebar smooth transitions */
    [data-testid="stSidebar"] {{
        transition: all var(--motion-slow) var(--motion-smooth);
    }}

    /* 🎭 CUSTOM AVATAR STYLING */
    .bot-avatar-circle {{
        width: 48px;
        height: 48px;
        border-radius: var(--pill-radius);
        background: linear-gradient(135deg, var(--accent-red), #FF5555);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        box-shadow: 0 12px 28px rgba(226, 35, 26, 0.25);
        border: 2px solid rgba(226, 35, 26, 0.3);
        flex-shrink: 0;
        animation: bot-float 4s ease-in-out infinite;
    }}

    @keyframes bot-float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-4px); }}
    }}

    /* Enhanced chat message styling with avatar support */
    [data-testid="chat-message-user"] {{
        margin-left: auto;
        margin-right: 0;
    }}

    [data-testid="chat-message-user"]::before {{
        content: "";
        display: inline-block;
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #58A6FF, #79C0FF);
        border-radius: var(--pill-radius);
        margin-right: 8px;
        flex-shrink: 0;
    }}

    /* 🎭 CUSTOM AVATAR STYLING */
    .bot-avatar-circle {{
        width: 48px;
        height: 48px;
        border-radius: var(--pill-radius);
        background: linear-gradient(135deg, var(--accent-red), #FF5555);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        box-shadow: 0 12px 28px rgba(226, 35, 26, 0.25);
        border: 2px solid rgba(226, 35, 26, 0.3);
        flex-shrink: 0;
        animation: bot-float 4s ease-in-out infinite;
    }}

    @keyframes bot-float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-4px); }}
    }}

    /* Enhanced chat message styling with avatar support */
    [data-testid="chat-message-user"] {{
        margin-left: auto;
        margin-right: 0;
    }}

    [data-testid="chat-message-user"]::before {{
        content: "";
        display: inline-block;
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #58A6FF, #79C0FF);
        border-radius: var(--pill-radius);
        margin-right: 8px;
        flex-shrink: 0;
    }}

    /* Avatar SVG styling */
    svg[data-testid="avatar"] {{
        filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.15));
    }}

    /* Professional emoji avatar styling */
    [data-testid="stChatMessageContainer"] [data-testid="stChatMessage"] {{
        align-items: flex-start;
    }}

    /* User avatar circle */
    [data-testid="chat-message-user"] [data-testid="stMarkdownContainer"]::before {{
        content: "👤";
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        margin-right: 12px;
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.2), rgba(121, 192, 255, 0.1));
        border: 1.5px solid rgba(88, 166, 255, 0.3);
        border-radius: var(--pill-radius);
        font-size: 1.2rem;
        flex-shrink: 0;
    }}

    /* Assistant avatar circle */
    [data-testid="chat-message-assistant"] [data-testid="stMarkdownContainer"]::before {{
        content: "🔴";
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        margin-right: 12px;
        background: linear-gradient(135deg, rgba(226, 35, 26, 0.2), rgba(255, 68, 68, 0.1));
        border: 1.5px solid rgba(226, 35, 26, 0.3);
        border-radius: var(--pill-radius);
        font-size: 1rem;
        flex-shrink: 0;
        filter: drop-shadow(0 4px 8px rgba(226, 35, 26, 0.15));
    }}

    /* SSO Gateway Theme */
    .sso-panel {{
        margin: 3.5rem auto 1rem auto;
        max-width: 760px;
        background: linear-gradient(160deg, var(--bg-card), var(--surface-glass-strong));
        border: 1px solid var(--border-color);
        border-radius: 22px;
        padding: 1.9rem;
        backdrop-filter: blur(calc(var(--panel-blur) + 1px));
        -webkit-backdrop-filter: blur(calc(var(--panel-blur) + 1px));
        box-shadow: 0 16px 40px var(--shadow-color);
        animation: pop-in var(--motion-slow) var(--motion-smooth), glass-drift 16s ease-in-out infinite;
    }}
    .sso-panel-badge {{
        display: inline-flex;
        padding: 0.34rem 0.74rem;
        border-radius: var(--pill-radius);
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: var(--accent-red);
        border: 1px solid rgba(226, 35, 26, 0.35);
        background: rgba(226, 35, 26, 0.08);
        margin-bottom: 0.8rem;
    }}
    .sso-title {{
        margin: 0 0 0.42rem 0;
        color: var(--text-main);
        font-size: 1.45rem;
        letter-spacing: -0.3px;
    }}
    .sso-subtitle {{
        margin: 0;
        color: var(--text-muted);
        font-size: 0.95rem;
    }}
    div.element-container:has(.sso-toggle-anchor) + div.element-container {{
        max-width: 760px;
        margin: 0 auto 0.6rem auto !important;
        background: linear-gradient(145deg, var(--bg-card), var(--surface-glass));
        border: 1px solid var(--border-color);
        border-radius: var(--pill-radius);
        padding: 0.45rem 0.9rem;
        box-shadow: 0 8px 24px var(--shadow-color);
    }}
    div.element-container:has(.sso-signin-anchor) + div.element-container button {{
        border-radius: var(--pill-radius) !important;
        border: 1px solid rgba(226, 35, 26, 0.35) !important;
        background: linear-gradient(135deg, rgba(226, 35, 26, 0.95), rgba(255, 92, 92, 0.95)) !important;
        color: #fff !important;
        font-weight: 700 !important;
        letter-spacing: 0.2px;
        transition: transform var(--motion-mid) var(--motion-smooth), box-shadow var(--motion-mid) var(--motion-smooth) !important;
        box-shadow: 0 14px 30px rgba(226, 35, 26, 0.28) !important;
    }}
    div.element-container:has(.sso-signin-anchor) + div.element-container button:hover {{
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 18px 36px rgba(226, 35, 26, 0.32) !important;
    }}

</style>
""".replace("__THEME_VARS__", theme_vars)

st.markdown(css_injection, unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def get_file_icon(filename: str) -> str:
    """Return a modern SVG icon based on file extension"""
    ext = filename.split('.')[-1].lower()
    
    icons = {
        'txt': '📋',
        'md': '📝',
        'csv': '📊',
        'json': '⚙️',
        'docx': '📄',
        'doc': '📄',
        'pdf': '📕',
        'xlsx': '📈',
        'xls': '📊',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️'
    }
    
    return icons.get(ext, '📁')

def get_assistant_avatar_svg() -> str:
    """Return a modern professional assistant avatar SVG"""
    return """
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="avatar-gradient" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" style="stop-color:#E2231A;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#FF4444;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="16" cy="16" r="15" fill="url(#avatar-gradient)" opacity="0.12" stroke="url(#avatar-gradient)" stroke-width="1.5"/>
        <circle cx="16" cy="12" r="4" fill="url(#avatar-gradient)"/>
        <path d="M10 22C10 19.2 12.7 17 16 17C19.3 17 22 19.2 22 22" stroke="url(#avatar-gradient)" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """

def get_user_avatar_svg() -> str:
    """Return a modern professional user avatar SVG"""
    return """
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="user-gradient" x1="0" y1="0" x2="32" y2="32">
                <stop offset="0%" style="stop-color:#58A6FF;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#79C0FF;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="16" cy="16" r="15" fill="url(#user-gradient)" opacity="0.12" stroke="url(#user-gradient)" stroke-width="1.5"/>
        <circle cx="16" cy="11" r="4" fill="url(#user-gradient)"/>
        <path d="M9 23C9 20 12 18 16 18C20 18 23 20 23 23" stroke="url(#user-gradient)" stroke-width="2" stroke-linecap="round"/>
    </svg>
    """

def render_custom_avatar(avatar_type: str) -> str:
    """Render custom avatar with modern styling"""
    if avatar_type == "assistant":
        return get_assistant_avatar_svg()
    return get_user_avatar_svg()

def extract_sources_from_answer(answer: str) -> list:
    """Extract source filenames from the answer using regex patterns"""
    sources = set()
    
    # Pattern 1: "Source: filename.ext" or "Source: filename"
    pattern1 = r'[Ss]ource[s]?:\s*([A-Za-z0-9_\-\.]+(?:\.[A-Za-z0-9]+)?)'
    
    # Pattern 2: **filename.ext** or filename.ext in backticks
    pattern2 = r'\*\*([A-Za-z0-9_\-\.]+\.[A-Za-z0-9]+)\*\*'
    pattern3 = r'`([A-Za-z0-9_\-\.]+\.[A-Za-z0-9]+)`'
    
    # Pattern 4: (filename.ext) or [filename.ext]
    pattern4 = r'[\(\[]([A-Za-z0-9_\-\.]+\.[A-Za-z0-9]+)[\)\]]'
    
    # Pattern 5: Lenovo_*.txt style files
    pattern5 = r'(Lenovo_[A-Za-z0-9_\-\.]+(?:\.[A-Za-z0-9]+)?)'
    
    for pattern in [pattern1, pattern2, pattern3, pattern4, pattern5]:
        matches = re.findall(pattern, answer)
        sources.update(matches)
    
    return sorted(list(sources))


# ==========================================
# PRODUCTION-READY UTILITIES
# ==========================================

class QueryCache:
    """Simple LRU cache for query results to reduce redundant processing."""
    def __init__(self, max_size: int = 50, ttl_seconds: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> dict | None:
        """Get cached result if exists and not expired."""
        if key not in self.cache:
            return None
        
        timestamp = self.timestamps.get(key, 0)
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            del self.timestamps[key]
            return None
        
        return self.cache[key]
    
    def put(self, key: str, value: dict) -> None:
        """Store result in cache with LRU eviction."""
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear entire cache."""
        self.cache.clear()
        self.timestamps.clear()


def sanitize_query(query: str) -> str | None:
    """Validate and sanitize user query for security and quality."""
    if not query or not isinstance(query, str):
        return None
    
    query = query.strip()
    
    # Length validation
    if len(query) < 3 or len(query) > 1000:
        return None
    
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query)
    
    # Prevent SQL injection-like patterns
    dangerous_patterns = [r'DROP\s+', r'DELETE\s+', r'TRUNCATE\s+', r'INSERT\s+']
    for pattern in dangerous_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            return None
    
    return query


def validate_response(answer: str, confidence: str, evidence_count: int) -> bool:
    """Validate response meets minimum quality standards."""
    if not answer or not isinstance(answer, str):
        return False
    
    if len(answer.strip()) < 20:
        return False
    
    if confidence not in ["High", "Medium", "Low"]:
        return False
    
    if evidence_count < 0:
        return False
    
    # Check for error indicators
    error_phrases = ["error", "failed", "unable to", "cannot process"]
    if sum(phrase in answer.lower() for phrase in error_phrases) > 2:
        return False
    
    return True


def create_cache_key(query: str, mode: str, history_len: int) -> str:
    """Create deterministic cache key for query."""
    key_parts = [query, mode, str(history_len)]
    key_str = "|".join(key_parts)
    # Use hash for shorter key
    import hashlib
    return hashlib.sha256(key_str.encode()).hexdigest()[:16]

def render_source_navigator(sources: list) -> str:
    """Generate HTML for the source navigator component"""
    # This function is retained for backwards-compatibility but the app will
    # prefer interactive rendering via `show_sources_interactive` below.
    if not sources:
        return ""

    pills_html = ""
    for source in sources:
        icon = get_file_icon(source)
        display_name = source.replace('Lenovo_', '').replace('.txt', '').replace('_', ' ')
        if len(display_name) > 25:
            display_name = display_name[:22] + "..."
        pills_html += f'<div class="source-pill" title="{source}"><span class="source-icon">{icon}</span><span class="source-filename">{display_name}</span></div>'

    html = f'''<div class="source-navigator-container"><div class="source-navigator-title">🔗 Enterprise Sources</div><div class="source-navigator-pills">{pills_html}</div></div>'''
    return html


def resolve_source_path(source_name: str) -> str:
    """Try to resolve a source filename to an actual workspace file path.

    Returns the relative path if found, otherwise returns empty string.
    """
    candidates = []
    # If metadata already contains a relative path, check it first
    candidates.append(source_name)
    # common data folder
    candidates.append(os.path.join("data", source_name))
    candidates.append(os.path.join("vector_db", source_name))
    # try with/without underscores and common txt extension
    if not source_name.lower().endswith('.txt'):
        candidates.append(source_name + '.txt')
        candidates.append(os.path.join('data', source_name + '.txt'))

    for c in candidates:
        try:
            if os.path.exists(c):
                return c.replace('\\', '/')
        except Exception:
            continue
    return ""


def choose_assistant_mode() -> tuple[str, dict]:
    """Return the single broad-context assistant mode used by the simplified UI."""
    mode_name = "Adaptive Fusion"
    return mode_name, get_wide_context_mode_config()


def show_sources_interactive(sources: list, base_key: str = "") -> None:
    """Render interactive source pills - detects local files vs web URLs and handles accordingly.

    Features: Theme-aware styling, responsive layout, proper formatting, error handling.
    base_key should be unique per assistant message to avoid widget key collisions.
    """
    if not sources:
        return
    
    # Separate web URLs from local files
    web_urls = [s for s in sources if isinstance(s, str) and s.startswith('http')]
    local_files = [s for s in sources if not isinstance(s, str) or not s.startswith('http')]
    
    # Display web URLs
    if web_urls:
        show_web_sources(web_urls, base_key)
    
    # Display local files
    if local_files:
        show_local_sources(local_files, base_key)


def show_web_sources(urls: list, base_key: str = "") -> None:
    """Display web source URLs with theme-aware styling and proper formatting."""
    
    html_content = f"""<div style="margin-top: 16px; padding: 12px; background-color: var(--surface-glass); border: 1px solid var(--border-color); border-radius: 8px;">
<div style="font-size: 0.75rem; font-weight: 700; color: var(--text-main); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px;">
🔗 Sources Consulted
</div>
<div style="display: flex; flex-direction: column; gap: 8px;">"""
    
    # Clean URLs properly
    import urllib.parse
    import re
    
    for i, url in enumerate(urls[:8]):  # Limit to 8 sources
        # Remove trailing punctuation that might have been grabbed by regex
        clean_url = re.sub(r'[.,;:\)\}\]]+$', '', url.strip())
        
        if not clean_url.startswith('http'):
            clean_url = 'https://' + clean_url
            
        try:
            parsed = urllib.parse.urlparse(clean_url)
            domain = parsed.netloc.replace('www.', '')
            display_url = f"{domain}"
            if len(display_url) > 40:
                display_url = display_url[:37] + "..."
        except Exception:
            display_url = clean_url[:50] + "..." if len(clean_url) > 50 else clean_url
            
        # Add each link to HTML block
        html_content += f"""<a href="{clean_url}" target="_blank" style="
display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px;
background-color: var(--surface-glass-strong); border: 1px solid var(--border-color);
border-radius: 6px; color: var(--accent-red); text-decoration: none;
font-size: 0.85rem; font-weight: 500; transition: all 0.2s ease;
" onmouseover="this.style.backgroundColor='var(--suggestion-bg-hover)'; this.style.transform='translateY(-2px)';" 
onmouseout="this.style.backgroundColor='var(--surface-glass-strong)'; this.style.transform='translateY(0)';">
<span style="font-size: 1rem;">↗️</span>
<span title="{clean_url}" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px;">
{display_url}
</span>
</a>"""
        
    html_content += "</div></div>"
    
    # Render all at once
    st.markdown(html_content, unsafe_allow_html=True)


def _get_mime_type(filepath: str) -> str:
    """Return appropriate MIME type based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    mime_map = {
        '.txt': 'text/plain', '.md': 'text/markdown', '.csv': 'text/csv',
        '.json': 'application/json', '.pdf': 'application/pdf',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return mime_map.get(ext, 'application/octet-stream')


def _is_text_file(filepath: str) -> bool:
    """Check if a file can be previewed as text."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in {'.txt', '.md', '.csv', '.json'}


def show_local_sources(sources: list, base_key: str = "") -> None:
    """Display local file sources with inline preview and reliable download.
    
    Download buttons are placed OUTSIDE the expander so they persist across
    Streamlit reruns and never collapse.
    """
    st.markdown(
        '<div class="source-navigator-title" style="background-color: var(--surface-glass); border: 1px solid var(--border-color); color: var(--text-main); padding: 8px 12px; border-radius: 8px; margin-top: 16px; margin-bottom: 8px;">📄 Referenced Files</div>',
        unsafe_allow_html=True
    )
    
    for i, src in enumerate(sources):
        display_name = src.replace('Lenovo_', '').replace('.txt', '').replace('_', ' ').strip()
        if len(display_name) > 40:
            display_name = display_name[:37] + '...'
        icon = get_file_icon(src)
        resolved = resolve_source_path(src)
        
        if not resolved:
            st.warning(f"⚠️ Source file not found: {src}")
            continue
        
        try:
            # Always read binary for download (works for ALL file types)
            with open(resolved, 'rb') as fh:
                file_bytes = fh.read()
            
            file_size = len(file_bytes)
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size // 1024} KB"
            else:
                size_str = f"{file_size / (1024*1024):.1f} MB"
            
            filename = os.path.basename(resolved)
            mime = _get_mime_type(resolved)
            
            # --- Download button OUTSIDE the expander (top-level, never conditional) ---
            dl_col, label_col = st.columns([1, 3])
            with dl_col:
                st.download_button(
                    label=f"📥 {filename}",
                    data=file_bytes,
                    file_name=filename,
                    mime=mime,
                    key=f"dl_{base_key}_{i}",
                    use_container_width=True
                )
            with label_col:
                st.markdown(f"<div style='padding-top: 8px; font-size: 0.85rem; color: var(--text-muted);'>{icon} {display_name} — {size_str}</div>", unsafe_allow_html=True)
            
            # --- Preview inside expander (collapsible, optional) ---
            if _is_text_file(resolved):
                with st.expander(f"👁️ Preview contents", expanded=False):
                    try:
                        text_content = file_bytes.decode('utf-8', errors='ignore')
                        MAX_PREVIEW = 3000
                        preview = text_content[:MAX_PREVIEW]
                        if len(text_content) > MAX_PREVIEW:
                            preview += f"\n\n... [{len(text_content) - MAX_PREVIEW:,} more characters] ..."
                        
                        import html as html_mod
                        safe = html_mod.escape(preview)
                        st.markdown(
                            f"<div style='background-color: var(--bg-input); padding: 16px; border-radius: 8px; max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.5; color: var(--text-main); border: 1px solid var(--border-color);'><pre style='white-space: pre-wrap; margin: 0; font-family: inherit;'>{safe}</pre></div>",
                            unsafe_allow_html=True
                        )
                    except Exception:
                        st.info("📄 Text preview unavailable.")
                    st.caption(f"✓ Source: `{resolved}`")
            else:
                ext = os.path.splitext(resolved)[1].lower()
                type_labels = {'.pdf': '📕 PDF', '.docx': '📘 Word', '.xlsx': '📊 Excel'}
                label = type_labels.get(ext, f'📎 {ext}')
                st.caption(f"{label} — click download above to open")
                
        except Exception as e:
            st.error(f"❌ Error reading {src}: {str(e)[:150]}")
    # No enclosing div markdown because it breaks streamlit component flow
# ==========================================
# 3. SESSION STATE & BACKGROUND AGENT INIT
# ==========================================
API_URL = "http://localhost:8000/chat"
API_TIMEOUT_SECONDS = float(os.getenv("API_TIMEOUT_SECONDS", "1.2"))
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "5"))
RETRIEVER_FETCH_K = int(os.getenv("RETRIEVER_FETCH_K", "16"))
RETRIEVER_LAMBDA = float(os.getenv("RETRIEVER_LAMBDA", "0.42"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "0.68"))
MAX_EVIDENCE_SNIPPETS = int(os.getenv("MAX_EVIDENCE_SNIPPETS", "5"))
LOCAL_HISTORY_MESSAGES = int(os.getenv("LOCAL_HISTORY_MESSAGES", "6"))
LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:3b")
ENABLE_WEB_FALLBACK = os.getenv("ENABLE_WEB_FALLBACK", "true").lower() == "true"
USE_FASTAPI_GATEWAY = os.getenv("USE_FASTAPI_GATEWAY", "false").lower() == "true"

MODE_PROFILES = {
    "Ultra Fast": {
        "api_timeout": 0.8,
        "history_messages": 3,
        "relevance_threshold": 0.73,
        "retriever_k": 3,
        "allow_deep_fallback": False,
    },
    "Balanced": {
        "api_timeout": 1.2,
        "history_messages": 6,
        "relevance_threshold": 0.66,
        "retriever_k": 5,
        "allow_deep_fallback": True,
    },
    "Deep Dive": {
        "api_timeout": 2.0,
        "history_messages": 10,
        "relevance_threshold": 0.58,
        "retriever_k": 8,
        "allow_deep_fallback": True,
    },
    "Adaptive Fusion": {
        "api_timeout": 1.4,
        "history_messages": 8,
        "relevance_threshold": 0.64,
        "retriever_k": 6,
        "allow_deep_fallback": True,
    },
}

if "sessions" not in st.session_state:
    st.session_state.sessions = {"Chat 1": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "Chat 1"
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 1
if "process_query" not in st.session_state:
    st.session_state.process_query = False
if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False
if "query_cache" not in st.session_state:
    st.session_state.query_cache = QueryCache(max_size=50, ttl_seconds=300)
if "query_metrics" not in st.session_state:
    st.session_state.query_metrics = {
        "last_latency_s": None,
        "last_path": "N/A",
        "last_mode": "N/A",
        "last_confidence": "N/A",
        "last_relevance": None,
        "last_evidence_count": 0,
        "last_escalations": 0,
        "total_queries": 0,
        "avg_latency_s": None,
    }
    if "router_log" not in st.session_state:
        st.session_state.router_log = []
if "response_mode" not in st.session_state:
    st.session_state.response_mode = "Adaptive Fusion"


def get_mode_config(selected_mode: str) -> dict:
    profile = MODE_PROFILES.get(selected_mode, MODE_PROFILES["Adaptive Fusion"])
    return {
        "api_timeout": profile["api_timeout"],
        "history_messages": profile["history_messages"],
        "relevance_threshold": profile["relevance_threshold"],
        "retriever_k": profile["retriever_k"],
        "allow_deep_fallback": profile["allow_deep_fallback"],
    }


def get_wide_context_mode_config() -> dict:
    """Single broad-context configuration used by the simplified UI."""
    return {
        "api_timeout": 2.2,
        "history_messages": 12,
        "relevance_threshold": 0.45,
        "retriever_k": 10,
        "allow_deep_fallback": True,
    }


def is_realtime_market_query(query_text: str) -> bool:
    q = query_text.lower()
    realtime_terms = [
        "current stock price",
        "stock price",
        "live price",
        "today price",
        "real-time",
        "realtime",
        "market cap",
        "share price",
        "trading",
        "bitcoin price",
        "cryptocurrency price",
        "crypto price",
        "ethereum price",
        "gold price",
        "oil price",
        "forex",
        "currency exchange",
        "price today",
        "current price",
    ]
    return any(term in q for term in realtime_terms)


def is_external_query(query_text: str) -> bool:
    """Heuristic for questions that should not be forced through the internal corpus."""
    q = query_text.lower()
    external_terms = [
        "current stock price",
        "stock price",
        "live price",
        "today price",
        "bitcoin",
        "cryptocurrency",
        "crypto",
        "ethereum",
        "gold price",
        "oil price",
        "latest",
        "news",
        "weather",
        "forecast",
        "exchange rate",
        "sports",
        "score",
        "market",
        "quote",
        "external",
        "public",
        "as of today",
        "right now",
        "currently",
        "today",
        "yesterday",
        "tomorrow",
        "nasdaq",
        "s&p",
        "dow jones"
    ]
    return is_realtime_market_query(query_text) or any(term in q for term in external_terms)


def update_query_metrics(elapsed: float, path: str, mode: str, quality: dict):
    qm = st.session_state.query_metrics
    qm["last_latency_s"] = elapsed
    qm["last_path"] = path
    qm["last_mode"] = mode
    qm["last_confidence"] = quality.get("confidence", "N/A")
    qm["last_relevance"] = quality.get("relevance")
    qm["last_evidence_count"] = quality.get("evidence_count", 0)
    qm["last_escalations"] = quality.get("escalations", 0)
    qm["total_queries"] = qm.get("total_queries", 0) + 1
    prev_avg = qm.get("avg_latency_s")
    if prev_avg is None:
        qm["avg_latency_s"] = elapsed
    else:
        count = qm["total_queries"]
        qm["avg_latency_s"] = ((prev_avg * (count - 1)) + elapsed) / count

def get_chat_name(session_id):
    msgs = st.session_state.sessions[session_id]
    if not msgs: return "New Chat"
    return msgs[0]["content"][:22] + "..." if len(msgs[0]["content"]) > 22 else msgs[0]["content"]

def trigger_query(txt):
    st.session_state.sessions[st.session_state.current_session].append({"role": "user", "content": txt})
    st.session_state.process_query = True


def build_conversation_context(active_history: list, max_turns: int = 4) -> str:
    """Build a compact context block from the most recent turns for follow-up handling."""
    if not active_history:
        return ""

    turns = active_history[-max_turns:]
    lines = []
    for turn in turns:
        role = turn.get("role", "user").upper()
        content = str(turn.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)

# ----------------------
# Authentication / SSO
# ----------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "sso_in_progress" not in st.session_state:
    st.session_state.sso_in_progress = False
if "sso_error" not in st.session_state:
    st.session_state.sso_error = ""

def _validate_lenovo_identity(email: str) -> bool:
    return bool(email and email.lower().endswith("@lenovo.com"))


def mock_sso_login(display_name: str, email: str, role: str):
    """Mock SSO gateway for local development with enterprise-domain checks."""
    st.session_state.sso_error = ""
    if not display_name.strip():
        st.session_state.sso_error = "Display name is required."
        return
    if not _validate_lenovo_identity(email):
        st.session_state.sso_error = "Use a valid Lenovo corporate email (@lenovo.com)."
        return

    st.session_state.user = {
        "name": display_name.strip(),
        "email": email.strip().lower(),
        "role": role,
        "login_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    ensure_agent_ready()
    st.rerun()


def logout_user():
    st.session_state.user = None
    st.session_state.sso_in_progress = False
    st.session_state.sso_error = ""
    st.rerun()


def render_sso_gate() -> bool:
    """Render auth interface; return True only when user is authenticated."""
    if st.session_state.user:
        return True

    st.markdown(
        """
        <div class="sso-panel">
            <div class="sso-panel-badge">Secure Access</div>
            <h2 class="sso-title">Enterprise SSO Gateway</h2>
            <p class="sso-subtitle">Authenticate with corporate identity before accessing Lenovo Research Workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sso-toggle-anchor"></div>', unsafe_allow_html=True)
    sso_enabled = st.toggle("Enable Enterprise Sign In", value=True, key="sso_toggle")

    if not sso_enabled:
        st.info("Enable the sign-in toggle to continue.")
        st.stop()

    with st.form("mock_sso_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            display_name = st.text_input("Display Name", value="Alice Lenovo")
            role = st.selectbox("Access Role", ["researcher", "analyst", "manager", "admin"], index=0)
        with c2:
            email = st.text_input("Corporate Email", value="alice@lenovo.com")
            st.caption("Local mock SSO. Replace with OIDC callback/token exchange in production.")

        st.markdown('<div class="sso-signin-anchor"></div>', unsafe_allow_html=True)
        submit = st.form_submit_button("Sign in with Enterprise SSO", use_container_width=True)
        if submit:
            mock_sso_login(display_name, email, role)

    if st.session_state.sso_error:
        st.error(st.session_state.sso_error)

    st.stop()
    return False



# ==========================================
# 3. CORE AI AGENT (Fallback / Local Mode)
# ==========================================
@st.cache_resource
def initialize_agent():
    load_dotenv()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory="vector_db", embedding_function=embeddings)
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": max(RETRIEVER_K, 8),
            "fetch_k": max(RETRIEVER_FETCH_K, 24),
            "lambda_mult": RETRIEVER_LAMBDA,
        },
    )
    custom_doc_prompt = PromptTemplate.from_template("Source: {source}\n\n{page_content}")
    internal_tool = create_retriever_tool(
        retriever,
        name="lenovo_internal",
        description="Primary internal enterprise corpus for Lenovo. Always use this first.",
        document_prompt=custom_doc_prompt
    )
    web_tool = TavilySearch(max_results=1)
    llm = ChatOllama(
        model=LOCAL_MODEL_NAME,
        temperature=0,
        num_predict=320,
        num_ctx=3072,
    )
    system_prompt = f"""You are Lenovo's Internal Research Assistant for enterprise users.

Mission:
- Answer from internal files first using `lenovo_internal`.
- Use web search only when internal docs do not cover the request.

Rules:
- Never invent data. If missing, say so explicitly.
- Prefer concise executive summaries, followed by key bullet points.
- Include file-level provenance and pinpointed evidence in every answer.
- Always format source citations clearly as "Source: filename.ext"

Response format:
1) Executive Summary
2) Key Findings
3) Pinpointed Evidence (quote short exact snippets with Source: filename.ext)
4) Sources (list each unique file)

For Pinpointed Evidence, quote short exact snippets and attach Source: filename.ext after each snippet.
For Sources section, use format: "Source: filename.ext" on separate lines or comma-separated.
Enterprise traceability is critical - always cite your sources clearly.
Keep Key Findings to 4-6 bullets, and limit Pinpointed Evidence to at most {MAX_EVIDENCE_SNIPPETS} snippets.
"""
    tools = [internal_tool, web_tool] if ENABLE_WEB_FALLBACK else [internal_tool]
    agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    return {"agent": agent, "llm": llm, "retriever": retriever, "embeddings": embeddings, "web_tool": web_tool}


def ensure_agent_ready():
    """Initialize and cache agent once per session after function is defined."""
    if (not st.session_state.get("agent_initialized", False)) or ("runtime" not in st.session_state):
        runtime = initialize_agent()
        st.session_state.runtime = runtime
        st.session_state.agent = runtime["agent"]
        st.session_state.agent_initialized = True


def build_turbo_rag_answer(query_text: str, runtime: dict, mode_cfg: dict, active_history=None) -> dict:
    """Fast path with strict grounding and quality metadata for route orchestration."""
    context_block = build_conversation_context(active_history or [], max_turns=4)
    contextual_query = query_text
    if context_block:
        contextual_query = (
            f"Conversation context:\n{context_block}\n\n"
            f"Current user question: {query_text}\n\n"
            "Answer the current question only, but use the conversation context to resolve pronouns, follow-ups, and references."
        )

    docs = runtime["retriever"].invoke(contextual_query)
    retriever_k = int(mode_cfg.get("retriever_k", RETRIEVER_K))
    relevance_threshold = float(mode_cfg.get("relevance_threshold", RELEVANCE_THRESHOLD))
    
    # Filter by similarity threshold to reduce hallucinations and irrelevant answers
    if not docs:
        answer = (
            "**Closest Internal View**\n\n"
            "I could not retrieve direct matching passages for this query, so I cannot state exact figures. "
            "Please refine the question with a specific indexed document/topic for a fully grounded answer."
        )
        return {
            "answer": answer,
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.0,
            "needs_escalation": True,
        }
    
    # Use semantic similarity for relevance filtering
    try:
        embeddings_fn = runtime.get("embeddings")
        scored_docs = []
        if embeddings_fn:
            query_emb = embeddings_fn.embed_query(query_text)
            for doc in docs[: max(retriever_k * 3, 9)]:
                doc_snippet = doc.page_content[:500]
                doc_emb = embeddings_fn.embed_query(doc_snippet)
                # Simple cosine similarity approximation
                sim = sum(q * d for q, d in zip(query_emb, doc_emb)) / (
                    (sum(q**2 for q in query_emb)**0.5) * (sum(d**2 for d in doc_emb)**0.5) + 1e-9
                )
                if sim >= relevance_threshold:
                    scored_docs.append((doc, sim))
            docs = [d[0] for d in sorted(scored_docs, key=lambda x: x[1], reverse=True)[:retriever_k]]
            # If strict threshold filtered everything, fall back to top semantic matches instead of dead-ending.
            if not docs:
                relaxed = []
                for doc in runtime["retriever"].invoke(contextual_query)[: max(retriever_k, 5)]:
                    snippet = doc.page_content[:500]
                    emb = embeddings_fn.embed_query(snippet)
                    sim = sum(q * d for q, d in zip(query_emb, emb)) / (
                        (sum(q**2 for q in query_emb)**0.5) * (sum(d**2 for d in emb)**0.5) + 1e-9
                    )
                    relaxed.append((doc, sim))
                docs = [d[0] for d in sorted(relaxed, key=lambda x: x[1], reverse=True)[:retriever_k]]
                scored_docs = relaxed
        else:
            docs = docs[:retriever_k]
    except Exception:
        scored_docs = []
        docs = docs[:retriever_k]
    
    if not docs or len(docs) == 0:
        answer = (
            "**Closest Internal View**\n\n"
            "Direct evidence is limited for this query in the indexed corpus. "
            "I can still provide nearby internal context if you want a proxy insight summary."
        )
        return {
            "answer": answer,
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.0,
            "needs_escalation": True,
        }
    
    # Build context with source attribution
    context_blocks = []
    sources = []
    for idx, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        snippet = d.page_content.strip().replace("\n", " ")[:380]
        sources.append(src)
        context_blocks.append(f"[{idx}] Source: {src}\nEvidence: {snippet}")

    context_text = "\n\n".join(context_blocks)
    unique_sources = sorted(set(sources))

    prompt = f"""You are Lenovo's Enterprise Research Assistant providing evidence-based answers for manager review.

STRICT REQUIREMENTS:
1. Answer ONLY based on the evidence provided below.
2. Do NOT invent, assume, or extrapolate beyond evidence.
3. If evidence is insufficient, say so explicitly.
4. ALWAYS cite the source file (e.g., Source: filename.txt) for every claim.
5. Be concise, precise, and suitable for executive presentation.
6. Never output the literal headings "Insufficient Evidence" or "Insufficient Data".
7. If direct evidence for the exact ask is limited, provide the closest internal proxy insight and label it clearly.

QUESTION: {query_text}

EVIDENCE FROM LENOVO SYSTEMS:
{context_text}

RESPONSE STRUCTURE (required):
**Summary:** [1-3 sentences directly answering the question based on evidence]

**Key Findings:**
• Finding 1 (Source: filename)
• Finding 2 (Source: filename)  
• Finding 3 (Source: filename)
[Maximum {MAX_EVIDENCE_SNIPPETS} findings]

**Evidence Confidence:** [High | Medium | Low] - Assess based on relevance and completeness of retrieved documents.

**Sources Consulted:** {', '.join(unique_sources)}
"""
    
    llm_resp = runtime["llm"].invoke(prompt)
    answer = llm_resp.content if hasattr(llm_resp, "content") else str(llm_resp)
    # Log LLM interaction for diagnostics
    try:
        log_llm_interaction(st.session_state.current_session, query_text, prompt, answer, tool_name="TurboRAG")
    except Exception:
        pass

    # Ensure sources are appended if missing; only expose resolved workspace files
    resolved_sources = [s for s in unique_sources if resolve_source_path(s)]
    if resolved_sources and "Source:" not in answer and "Sources Consulted:" not in answer:
        answer += f"\n\n**Sources Consulted:** {', '.join(resolved_sources)}"

    avg_relevance = 0.0
    if scored_docs:
        top = scored_docs[: max(1, min(len(scored_docs), retriever_k))]
        avg_relevance = sum(score for _, score in top) / len(top)
    else:
        avg_relevance = 0.5 if docs else 0.0

    confidence = "High" if avg_relevance >= 0.76 else "Medium" if avg_relevance >= 0.62 else "Low"
    needs_escalation = confidence == "Low"

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": resolved_sources,
        "evidence_count": len(docs),
        "relevance": avg_relevance,
        "needs_escalation": needs_escalation,
        "contextual_query": contextual_query,
    }


def run_deep_agent_answer(active_history: list, runtime: dict, mode_cfg: dict) -> str:
    # Preserve full conversational context for follow-up handling.
    history_messages = int(mode_cfg.get("history_messages", LOCAL_HISTORY_MESSAGES))
    window = active_history[-history_messages:]
    hist = []
    for m in window:
        # keep full content; agent may rely on earlier assistant replies as context
        if m["role"] == "user":
            hist.append(HumanMessage(content=m["content"]))
        else:
            hist.append(AIMessage(content=m["content"]))
    # Pass messages as full history to the react agent
    contextual_query = build_conversation_context(active_history, max_turns=6)
    try:
        res = runtime["agent"].invoke({"messages": hist})
        # Agent returns dict with messages list; normalize defensively
        if isinstance(res, dict) and res.get("messages"):
            deep_answer = res["messages"][-1].content
        else:
            deep_answer = str(res)

        try:
            log_llm_interaction(st.session_state.current_session, contextual_query, contextual_query, deep_answer, tool_name="DeepAgent")
        except Exception:
            pass
        return deep_answer
    except Exception as e:
        # fallback: invoke llm directly with joined history
        joined = build_conversation_context(window, max_turns=history_messages)
        try:
            resp = runtime["llm"].invoke(joined)
            # Log deep-fallback LLM interaction
            try:
                log_llm_interaction(st.session_state.current_session, joined, joined, resp.content if hasattr(resp, "content") else str(resp), tool_name="DeepFallbackLLM")
            except Exception:
                pass
            return resp.content if hasattr(resp, "content") else str(resp)
        except Exception:
            return ""


def log_routing_decision(session_id: str, query: str, chosen_path: str, mode: str, details: dict) -> None:
    """Record routing decisions for later inspection and debugging."""
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session": session_id,
        "query": query,
        "path": chosen_path,
        "mode": mode,
        "details": details,
    }
    st.session_state.router_log.append(entry)
    # Also write to a lightweight log file for persistence across reloads
    try:
        with open("router.log", "a", encoding="utf-8") as lf:
            lf.write(str(entry) + "\n")
    except Exception:
        pass


def log_llm_interaction(session_id: str, query: str, prompt: str, response: str, tool_name: str = "LLM") -> None:
    """Lightweight logging of prompts and LLM responses for diagnosis."""
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session": session_id,
        "query": query,
        "tool": tool_name,
        "prompt_snippet": prompt[:1000],
        "response_snippet": (response[:2000] if isinstance(response, str) else str(response))
    }
    try:
        st.session_state.router_log.append({"llm_interaction": entry})
    except Exception:
        pass
    try:
        with open("llm_interactions.log", "a", encoding="utf-8") as lf:
            lf.write(str(entry) + "\n")
    except Exception:
        pass


def build_proxy_internal_summary(query_text: str, runtime: dict, mode_cfg: dict) -> dict:
    """Guaranteed fallback: summarize nearest indexed evidence without hard failure wording."""
    docs = runtime["retriever"].invoke(query_text)[: max(3, int(mode_cfg.get("retriever_k", 5)))]
    if not docs:
        return {
            "answer": (
                "**Internal Snapshot**\n\n"
                "No close passages were retrieved for this question from current indexed files. "
                "Try a document-specific prompt (for example: strategy, deployment guide, server comparison)."
            ),
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.0,
        }

    blocks = []
    sources = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        txt = d.page_content.strip().replace("\n", " ")[:260]
        sources.append(src)
        blocks.append(f"- {txt} (Source: {src})")

    unique_sources = sorted(set(sources))
    resolved_sources = [s for s in unique_sources if resolve_source_path(s)]
    answer = (
        "**Internal Snapshot**\n\n"
        "Direct exact evidence is limited, so this is the closest indexed internal context:\n\n"
        + "\n".join(blocks[:MAX_EVIDENCE_SNIPPETS])
        + (f"\n\n**Sources Consulted:** {', '.join(resolved_sources)}" if resolved_sources else "")
    )
    # Log proxy summary generation
    try:
        log_llm_interaction(st.session_state.current_session, query_text, "proxy_internal_summary", answer, tool_name="ProxySummary")
    except Exception:
        pass
    return {
        "answer": answer,
        "confidence": "Medium" if len(resolved_sources) >= 2 else "Low",
        "sources": resolved_sources,
        "evidence_count": len(docs),
        "relevance": 0.55,
        "contextual_query": query_text,
    }


def build_web_answer(query_text: str, runtime: dict, mode_cfg: dict, active_history: list | None = None) -> dict:
    """Direct web-search path for external/live questions with enhanced relevance & synthesis.
    
    Features:
    - Retry logic for reliability
    - Advanced synthesis prompts for factual extraction
    - Quality-based confidence scoring
    - Source deduplication and ranking
    - Production-grade error handling
    """
    web_tool = runtime.get("web_tool")
    if not web_tool:
        return {
            "answer": "**Web Search Unavailable**\n\nThe web search tool is not available in this session. Please try again later.",
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.0,
        }

    context_block = build_conversation_context(active_history or [], max_turns=4)
    web_query = query_text if not context_block else f"{query_text}\n\nConversation context:\n{context_block}"

    # Retry logic for resilience (max 2 attempts)
    raw_web_text = ""
    retry_count = 2
    for attempt in range(retry_count):
        try:
            web_result = web_tool.invoke(web_query)
            if isinstance(web_result, str):
                raw_web_text = web_result.strip()
            else:
                raw_web_text = str(web_result).strip()
            
            if raw_web_text and len(raw_web_text) > 50:  # Valid result
                break
        except Exception as exc:
            if attempt == retry_count - 1:
                error_msg = str(exc)[:100]
                return {
                    "answer": f"**Web Search Temporarily Unavailable**\n\nCould not retrieve web results at this moment. Error: {error_msg}",
                    "confidence": "Low",
                    "sources": [],
                    "evidence_count": 0,
                    "relevance": 0.0,
                }

    if not raw_web_text or len(raw_web_text) < 50:
        return {
            "answer": "**No Search Results Found**\n\nThe web search did not return relevant results for this query. Try rephrasing your question with more specific terms.",
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.0,
        }

    # Enhanced synthesis prompt with structured output
    prompt = f"""You are a professional research assistant for enterprise organizations.

Your task: Extract and synthesize key facts from web search results to directly answer the user's question.

**IMPORTANT RULES:**
- Use ONLY information present in the search results
- Be specific with numbers, dates, and metrics
- Structure your response clearly
- Cite sources when possible
- If results are insufficient, be honest about limitations

**RESPONSE FORMAT:**
**Direct Answer:** [1-2 sentence direct answer to the question]

**Key Facts:**
- [Specific fact with details]
- [Supporting data/metrics]
- [Additional relevant context]

**Additional Context:** [Any important caveats or nuance]

---

USER QUESTION: {query_text}

WEB SEARCH RESULTS:
{raw_web_text}

Now provide your response:
"""

    try:
        llm_resp = runtime["llm"].invoke(prompt)
        answer = llm_resp.content if hasattr(llm_resp, "content") else str(llm_resp)
    except Exception as e:
        return {
            "answer": f"**Analysis Failed**\n\nCould not analyze search results: {str(e)[:80]}",
            "confidence": "Low",
            "sources": [],
            "evidence_count": 0,
            "relevance": 0.3,
        }

    try:
        log_llm_interaction(st.session_state.current_session, query_text, prompt[:800], answer, tool_name="WebSearch")
    except Exception:
        pass

    # Extract URLs with improved regex and deduplication
    sources = []
    url_pattern = r'https?://(?:www\.)?[^\s)\]}>,"\']+'
    for token in re.findall(url_pattern, raw_web_text):
        clean_url = token.rstrip('.,;:)')
        if len(clean_url) > 10 and clean_url not in sources:
            sources.append(clean_url)
    
    # Limit and deduplicate sources
    unique_sources = sorted(set(sources))[:8]
    
    # Quality-based confidence scoring
    has_structure = any(marker in answer for marker in ["**Direct Answer:**", "**Key Facts:", "**Key Findings:", "**Summary:"])
    fact_count = answer.count('- ') + answer.count('• ') + answer.count('* ')
    answer_length = len(answer.strip())
    
    # Confidence calculation
    if has_structure and len(unique_sources) >= 2 and fact_count >= 2 and answer_length > 150:
        confidence = "High"
        relevance = 0.85
    elif (len(unique_sources) >= 1 and answer_length > 100 and fact_count >= 1):
        confidence = "Medium"
        relevance = 0.65
    else:
        confidence = "Low"
        relevance = 0.40

    # Don't append sources to final_answer - they're displayed via show_web_sources() with theme-aware styling
    # Only add confidence marker
    final_answer = answer
    if "Evidence Confidence:" not in final_answer:
        final_answer += f"\n\n**Evidence Confidence:** {confidence}"

    return {
        "answer": final_answer,
        "confidence": confidence,
        "sources": unique_sources,
        "evidence_count": len(unique_sources) + fact_count,
        "relevance": relevance,
        "contextual_query": web_query,
    }


def normalize_response_format(raw_answer: str, sources: list, confidence: str) -> str:
    """Enforce consistent executive-ready format across all modes.
    
    NOTE: Web URLs are displayed via show_web_sources() with proper theme styling.
    Only local file sources are appended to text for internal references.
    """
    if not raw_answer:
        return "**Response Error** — Unable to generate response. Please try again."
    
    # If response already has structure markers, trust it; otherwise wrap it
    if "**Summary:**" in raw_answer or "**Findings:**" in raw_answer or "**Direct Answer:**" in raw_answer:
        pass  # Already formatted
    else:
        # Wrap unstructured responses
        raw_answer = f"**Summary:** {raw_answer[:180]}...\n\n{raw_answer}"
    
    # Ensure confidence is always appended
    if "Evidence Confidence:" not in raw_answer:
        raw_answer += f"\n\n**Evidence Confidence:** {confidence}"
    
    # Only add local file sources to text; web URLs will be displayed separately via show_web_sources()
    local_files = [s for s in sources if s and not str(s).startswith('http')]
    if local_files and "Source:" not in raw_answer and "Sources Consulted:" not in raw_answer:
        raw_answer += f"\n\n**Sources Consulted:** {', '.join(local_files)}"
    
    return raw_answer


def validate_response_quality(answer: str, confidence: str, evidence_count: int, mode: str) -> bool:
    """Check response meets minimum quality gates for production."""
    # Minimum content length
    if len(answer.strip()) < 40:
        return False
    
    # Must have confidence level
    if confidence not in ["High", "Medium", "Low"]:
        return False
    
    # High confidence should have evidence
    if confidence == "High" and evidence_count == 0:
        return False
    
    # Avoid hard-fail wording in final output
    forbidden_phrases = ["cannot", "unable to", "don't have", "not available"]
    if any(phrase in answer.lower() for phrase in forbidden_phrases) and evidence_count > 0:
        # If we have evidence but say we can't answer, fix it
        return False
    
    return True


def route_answer(active_history: list, runtime: dict, selected_mode: str) -> tuple[str, str, dict]:
    latest_query = active_history[-1]["content"] if active_history else ""
    mode_cfg = get_wide_context_mode_config()
    escalations = 0
    
    # Production: Validate and sanitize query
    sanitized_query = sanitize_query(latest_query)
    if not sanitized_query:
        return "Invalid query. Please try a different question.", "InvalidQuery", {
            "confidence": "Low", "relevance": 0.0, "evidence_count": 0,
            "escalations": 0, "sources": []
        }
    
    # Check cache first
    cache_key = create_cache_key(sanitized_query, selected_mode, len(active_history))
    cached_result = st.session_state.query_cache.get(cache_key)
    if cached_result:
        log_routing_decision(st.session_state.current_session, sanitized_query, "Cache Hit", selected_mode, {"cached": True})
        return cached_result["answer"], "Cache", cached_result["quality"]
    
    # Check if query is external/live first; if so, use web search directly
    if is_external_query(sanitized_query) and ENABLE_WEB_FALLBACK:
        web_result = build_web_answer(sanitized_query, runtime, mode_cfg, active_history)
        formatted = web_result.get("answer", "")
        quality = {
            "confidence": web_result.get("confidence", "Low"),
            "relevance": web_result.get("relevance", 0.0),
            "evidence_count": web_result.get("evidence_count", 0),
            "escalations": 0,
            "sources": web_result.get("sources", []),
        }
        # Validate response quality
        if validate_response(formatted, quality["confidence"], quality["evidence_count"]):
            st.session_state.query_cache.put(cache_key, {"answer": formatted, "quality": quality})
        log_routing_decision(st.session_state.current_session, sanitized_query, "Web Search", selected_mode, quality)
        return formatted, "Web Search", quality

    turbo = build_turbo_rag_answer(sanitized_query, runtime, mode_cfg, active_history)
    quality = {
        "confidence": turbo["confidence"],
        "relevance": turbo["relevance"],
        "evidence_count": turbo["evidence_count"],
        "escalations": escalations,
        "sources": turbo.get("sources", []),
    }

    if mode_cfg.get("allow_deep_fallback") and turbo["needs_escalation"]:
        escalations += 1
        deep_answer = run_deep_agent_answer(active_history, runtime, mode_cfg)
        deep_sources = extract_sources_from_answer(deep_answer)
        deep_sources = [s for s in deep_sources if resolve_source_path(s)]
        if deep_sources:
            # Normalize deep answer and return formatted output with resolved sources
            formatted_deep = normalize_response_format(deep_answer, deep_sources, "High")
            quality.update({
                "confidence": "High",
                "relevance": max(quality["relevance"], 0.74),
                "evidence_count": max(quality["evidence_count"], len(deep_sources)),
                "escalations": escalations,
                "sources": deep_sources,
            })
            if validate_response(formatted_deep, quality["confidence"], quality["evidence_count"]):
                st.session_state.query_cache.put(cache_key, {"answer": formatted_deep, "quality": quality})
            log_routing_decision(st.session_state.current_session, sanitized_query, "Turbo RAG -> Deep Agent", selected_mode, quality)
            return formatted_deep, "Turbo RAG -> Deep Agent", quality

        proxy = build_proxy_internal_summary(sanitized_query, runtime, mode_cfg)
        formatted = normalize_response_format(proxy["answer"], proxy["sources"], proxy["confidence"])
        quality.update({
            "confidence": proxy["confidence"],
            "relevance": max(quality["relevance"], proxy["relevance"]),
            "evidence_count": max(quality["evidence_count"], proxy["evidence_count"]),
            "escalations": escalations,
            "sources": proxy.get("sources", []),
        })
        if validate_response(formatted, quality["confidence"], quality["evidence_count"]):
            st.session_state.query_cache.put(cache_key, {"answer": formatted, "quality": quality})
        log_routing_decision(st.session_state.current_session, sanitized_query, "Turbo RAG -> Deep Agent -> Proxy Summary", selected_mode, quality)
        return formatted, "Turbo RAG -> Deep Agent -> Proxy Summary", quality

    quality["escalations"] = escalations
    formatted = normalize_response_format(turbo["answer"], turbo["sources"], turbo["confidence"])
    if validate_response(formatted, quality["confidence"], quality["evidence_count"]):
        st.session_state.query_cache.put(cache_key, {"answer": formatted, "quality": quality})
    log_routing_decision(st.session_state.current_session, sanitized_query, "Turbo RAG", selected_mode, quality)
    return formatted, "Turbo RAG", quality


# Pre-initialize on app load so first user query does not pay init cost.
ensure_agent_ready()

# Require SSO authentication before showing workspace.
render_sso_gate()

# ==========================================
# 4. THE PERFECT SIDEBAR (Locked Red Text)
# ==========================================
with st.sidebar:
    # 1. THE FLAWLESS RED LOGO
    st.markdown(
        """
        <div class="lenovo-brand-wrap">
            <img class="lenovo-logo-image" src="https://upload.wikimedia.org/wikipedia/commons/b/b8/Lenovo_logo_2015.svg" alt="Lenovo">
            <div class="lenovo-subtitle">Agentic AI Framework</div>
        </div>
        """, unsafe_allow_html=True
    )

    # 2. NEW CHAT BUTTON
    st.markdown('<div class="new-session-anchor"></div>', unsafe_allow_html=True)
    if st.button("➕ New Chat", use_container_width=True, key="new_s"):
        st.session_state.chat_counter += 1
        new_id = f"Chat {st.session_state.chat_counter}"
        st.session_state.sessions[new_id] = []
        st.session_state.current_session = new_id
        st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Auth status
    user = st.session_state.get("user")
    if user:
        st.markdown(
            f"""
            <div style='font-size: 0.85rem; color: var(--text-main); line-height: 1.8;'>
                <div style='font-weight: 700; margin-bottom: 6px;'>Authenticated User</div>
                <div><span style='color:var(--text-muted);'>Name:</span> <b>{user.get("name", "-")}</b></div>
                <div><span style='color:var(--text-muted);'>Email:</span> <b>{user.get("email", "-")}</b></div>
                <div><span style='color:var(--text-muted);'>Role:</span> <b>{user.get("role", "-")}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="signout-anchor"></div>', unsafe_allow_html=True)
        if st.button("Sign Out", use_container_width=True, key="logout_btn"):
            logout_user()
        st.markdown("<hr>", unsafe_allow_html=True)


    # 3. RECENT SESSIONS
    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; color: var(--text-main); text-transform: uppercase; margin-bottom: 1rem;'>Recent Sessions</div>", unsafe_allow_html=True)
    for sid in list(st.session_state.sessions.keys()):
        st.markdown('<div class="sidebar-chat-anchor"></div>', unsafe_allow_html=True)
        icon = "🔵" if sid == st.session_state.current_session else "💬"
        if st.button(f"{icon} {get_chat_name(sid)}", key=sid, use_container_width=True):
            st.session_state.current_session = sid
            st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    
    # 4. SYSTEM TELEMETRY & PERFORMANCE MODES
    st.markdown("<div style='color: var(--text-main); font-size: 1rem; font-weight: 700; margin-bottom: 12px;'>Response Intelligence Mode</div>", unsafe_allow_html=True)
    selected_mode, mode_cfg = choose_assistant_mode()
    st.markdown(
        "<div style='padding:0.55rem 0.8rem; border-radius:12px; background: rgba(226,35,26,0.08); border: 1px solid rgba(226,35,26,0.22); font-weight:700; color: var(--text-main);'>"
        "Wide Context Mode: Adaptive Fusion + broad retrieval + web fallback"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='color: var(--text-main); font-size: 1rem; font-weight: 700; margin-bottom: 12px; margin-top: 12px;'>System Telemetry</div>", unsafe_allow_html=True)
    
    # Perfectly aligned cyan dot and status text
    st.markdown("""
        <div style="display: flex; align-items: center; font-size: 0.75rem; font-weight: 600; color: var(--text-main); margin-bottom: 15px; text-transform: uppercase;">
            <div style="width: 8px; height: 8px; background-color: #00E5FF; border-radius: 50%; box-shadow: 0 0 6px #00E5FF; margin-right: 8px;"></div>
            STATUS: ONLINE | LOCAL HOST
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='font-size: 0.85rem; color: var(--text-main); line-height: 2;'>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Architecture:</span> <b>Agentic AI + RAG</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Engine:</span> <b>{LOCAL_MODEL_NAME}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Store:</span> <b>ChromaDB</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Retriever:</span> <b>MMR (k={mode_cfg.get("retriever_k")})</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Mode:</span> <b>Wide Context</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Relevance Gate:</span> <b>{mode_cfg.get("relevance_threshold"):.2f}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Oracle:</span> <b>{'Tavily Web (On)' if ENABLE_WEB_FALLBACK else 'Disabled for Speed'}</b></div>
        </div>
    """, unsafe_allow_html=True)

    metrics = st.session_state.get("query_metrics", {})
    last_latency = metrics.get("last_latency_s")
    avg_latency = metrics.get("avg_latency_s")
    confidence = metrics.get("last_confidence", "N/A")
    
    # Color-coded confidence indicator
    conf_color = "#4ADE80" if confidence == "High" else "#FBBF24" if confidence == "Medium" else "#EF4444"
    conf_bg = "rgba(74, 222, 128, 0.1)" if confidence == "High" else "rgba(251, 191, 36, 0.1)" if confidence == "Medium" else "rgba(239, 68, 68, 0.1)"
    
    st.markdown(
        f"""
        <div style='margin-top: 12px; font-size: 0.8rem; color: var(--text-main); line-height: 1.85;'>
            <div style='font-weight:700; margin-bottom:8px;'>Runtime Metrics</div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Mode:</span> <b>{metrics.get("last_mode", "N/A")}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Execution Path:</span> <b>{metrics.get("last_path", "N/A")}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Last Latency:</span> <b>{f"{last_latency:.2f}s" if isinstance(last_latency, float) else "N/A"}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Avg Latency:</span> <b>{f"{avg_latency:.2f}s" if isinstance(avg_latency, float) else "N/A"}</b></div>
            <div style='display:flex; justify-content:space-between; padding:6px 8px; background:{conf_bg}; border-radius:6px; margin: 4px 0;'>
                <span style='color:var(--text-muted);'>Confidence:</span> 
                <b style='color:{conf_color};'>{confidence}</b>
            </div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Evidence Docs:</span> <b>{metrics.get("last_evidence_count", 0)}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Escalations:</span> <b>{metrics.get("last_escalations", 0)}</b></div>
            <div style='display:flex; justify-content:space-between;'><span style='color:var(--text-muted);'>Total Queries:</span> <b>{metrics.get("total_queries", 0)}</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("<hr>", unsafe_allow_html=True)

    # 5. ARCHITECTURE FLOW
    st.markdown("<div style='color: var(--text-main); font-size: 1rem; font-weight: 700; margin-bottom: 15px;'>Architecture Flow</div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='font-size: 0.85rem; color: var(--text-main); line-height: 1.9; padding-left: 5px; font-weight: 500;'>
            1. Query Ingestion<br>
            2. ReAct Agent Initiation<br>
            3. Vector Retrieval<br>
            4. Web Search Fallback<br>
            5. Output Generation
        </div>
    """, unsafe_allow_html=True)

    # 6. RESET WORKSPACE
    st.markdown('<div style="height: 30px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="reset-anchor"></div>', unsafe_allow_html=True)
    if st.button("■ Clear Workspace", use_container_width=True, key="c_wk"):
        st.session_state.sessions = {"Chat 1": []}
        st.session_state.current_session = "Chat 1"
        st.rerun()

# ==========================================
# 5. MAIN CONTENT RAG INTERFACE
# ==========================================
# Top-right theme toggle with callback (no rerun to preserve agent context)
def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

st.markdown('<div class="theme-toggle-anchor"></div>', unsafe_allow_html=True)
st.button("🌙" if st.session_state.theme == "light" else "☀️", key="t_sw", help="Quick theme switch", on_click=toggle_theme)

active_history = st.session_state.sessions[st.session_state.current_session]

if not active_history:
    st.markdown("""
        <div class="bot-header-box">
            <div class="bot-avatar-circle">
                <svg width="42" height="42" viewBox="0 0 42 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <filter id="shadow-bot" x="-50%" y="-50%" width="200%" height="200%">
                            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.3"/>
                        </filter>
                    </defs>
                    <circle cx="21" cy="14" r="5" fill="white" filter="url(#shadow-bot)"/>
                    <path d="M12 28C12 24 15.6 21 21 21C26.4 21 30 24 30 28" stroke="white" stroke-width="2.5" stroke-linecap="round" filter="url(#shadow-bot)"/>
                    <circle cx="21" cy="21" r="19" fill="none" stroke="white" stroke-width="1.5" opacity="0.3"/>
                </svg>
            </div>
            <div class="bot-info">
                <h1>Lenovo Research Agent</h1>
                <p><span class="status-dot"></span> Secure Local Connection</p>
            </div>
        </div>
        <div class='quick-actions-title'>Suggested Queries</div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="suggestion-anchor"></div>', unsafe_allow_html=True)
        st.button("📊 AI Adoption in Government Sector", on_click=trigger_query, args=("Analyze AI adoption in Government from the CIO playbook.",), use_container_width=True)
        st.markdown('<div class="suggestion-anchor"></div>', unsafe_allow_html=True)
        st.button("⚙️ SR670 V2 Hardware Specifications", on_click=trigger_query, args=("Summarize SR670 V2 hardware specs.",), use_container_width=True)
    with c2:
        st.markdown('<div class="suggestion-anchor"></div>', unsafe_allow_html=True)
        st.button("⚖️ Compare Servers: Lenovo vs Dell", on_click=trigger_query, args=("Compare Lenovo vs Dell servers.",), use_container_width=True)
        st.markdown('<div class="suggestion-anchor"></div>', unsafe_allow_html=True)
        st.button("📈 Analyze Lenovo Group Stock Price", on_click=trigger_query, args=("What is the current stock price of Lenovo Group?",), use_container_width=True)

# Chat Input & Rendering
if prompt := st.chat_input("Ask a complex enterprise query..."):
    st.session_state.sessions[st.session_state.current_session].append({"role": "user", "content": prompt})
    st.session_state.process_query = True
for idx, msg in enumerate(active_history):
    role = msg["role"]
    
    # Render with custom SVG avatars
    if role == "user":
        st.markdown(f'''
            <div style="display: flex; gap: 12px; margin: 16px 0; align-items: flex-start;">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" style="flex-shrink: 0; margin-top: 4px;">
                    <defs>
                        <linearGradient id="user-grad" x1="0" y1="0" x2="36" y2="36">
                            <stop offset="0%" style="stop-color:#58A6FF;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#79C0FF;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle cx="18" cy="18" r="17" fill="url(#user-grad)" opacity="0.12" stroke="url(#user-grad)" stroke-width="1.5"/>
                    <circle cx="18" cy="12" r="4" fill="url(#user-grad)"/>
                    <path d="M10 24C10 20.5 13 18 18 18C23 18 26 20.5 26 24" stroke="url(#user-grad)" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <div style="flex: 1;">
                    <div style="color: var(--text-muted); font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">You</div>
        ''', unsafe_allow_html=True)
        st.markdown(msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:  # assistant
        st.markdown(f'''
            <div style="display: flex; gap: 12px; margin: 16px 0; align-items: flex-start;">
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none" style="flex-shrink: 0; margin-top: 4px;">
                    <defs>
                        <linearGradient id="assist-grad" x1="0" y1="0" x2="36" y2="36">
                            <stop offset="0%" style="stop-color:#E2231A;stop-opacity:1" />
                            <stop offset="100%" style="stop-color:#FF4444;stop-opacity:1" />
                        </linearGradient>
                    </defs>
                    <circle cx="18" cy="18" r="17" fill="url(#assist-grad)" opacity="0.12" stroke="url(#assist-grad)" stroke-width="1.5"/>
                    <circle cx="18" cy="12" r="4" fill="url(#assist-grad)"/>
                    <path d="M10 24C10 20.5 13 18 18 18C23 18 26 20.5 26 24" stroke="url(#assist-grad)" stroke-width="2" stroke-linecap="round"/>
                </svg>
                <div style="flex: 1;">
                    <div style="color: var(--accent-red); font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Lenovo Agent</div>
        ''', unsafe_allow_html=True)
        st.markdown(msg["content"])
        
        # Show interactive source navigator for assistant messages
        sources = msg.get("sources") or extract_sources_from_answer(msg["content"])
        if sources:
            base_key = f"{st.session_state.current_session}_{idx}"
            show_sources_interactive(sources, base_key=base_key)
        
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.process_query:
    with st.status("Analyzing Query...", expanded=True):
        start_ts = time.perf_counter()
        mode = "Adaptive Fusion"
        mode_cfg = get_wide_context_mode_config()
        execution_path = "Local Router"
        quality = {
            "confidence": "N/A",
            "relevance": None,
            "evidence_count": 0,
            "escalations": 0,
        }
        try:
            if USE_FASTAPI_GATEWAY:
                payload = {"messages": [{"role": m["role"], "content": m["content"]} for m in active_history]}
                response = requests.post(API_URL, json=payload, timeout=mode_cfg["api_timeout"])
                response.raise_for_status()
                ans = response.json()["response"]
                execution_path = "FastAPI Gateway"
                srcs = extract_sources_from_answer(ans)
                quality = {
                    "confidence": "Medium" if srcs else "Low",
                    "relevance": 0.65 if srcs else 0.45,
                    "evidence_count": len(srcs),
                    "escalations": 0,
                }
                if not srcs:
                    raise RuntimeError("FastAPI response not sufficiently grounded")
            else:
                raise RuntimeError("Bypass FastAPI and use local router")
        except Exception:
            ensure_agent_ready()
            runtime = st.session_state.runtime
            ans, execution_path, quality = route_answer(active_history, runtime, mode)

        elapsed = time.perf_counter() - start_ts
        update_query_metrics(elapsed, execution_path, mode, quality)

    # Render assistant response with custom SVG avatar
    st.markdown('''
        <div style="display: flex; gap: 12px; margin: 16px 0; align-items: flex-start;">
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none" style="flex-shrink: 0; margin-top: 4px;">
                <defs>
                    <linearGradient id="assist-grad-new" x1="0" y1="0" x2="36" y2="36">
                        <stop offset="0%" style="stop-color:#E2231A;stop-opacity:1" />
                        <stop offset="100%" style="stop-color:#FF4444;stop-opacity:1" />
                    </linearGradient>
                </defs>
                <circle cx="18" cy="18" r="17" fill="url(#assist-grad-new)" opacity="0.12" stroke="url(#assist-grad-new)" stroke-width="1.5"/>
                <circle cx="18" cy="12" r="4" fill="url(#assist-grad-new)"/>
                <path d="M10 24C10 20.5 13 18 18 18C23 18 26 20.5 26 24" stroke="url(#assist-grad-new)" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <div style="flex: 1;">
                <div style="color: var(--accent-red); font-size: 0.75rem; font-weight: 600; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px;">Lenovo Agent</div>
    ''', unsafe_allow_html=True)

    st.markdown(ans)

    sources = extract_sources_from_answer(ans)
    if sources:
        base_key = f"{st.session_state.current_session}_{len(active_history)}"
        show_sources_interactive(sources, base_key=base_key)

    # Professional quality badge for manager presentation
    conf = quality.get("confidence", "N/A")
    conf_color = "#4ADE80" if conf == "High" else "#FBBF24" if conf == "Medium" else "#EF4444"
    conf_bg = "rgba(74, 222, 128, 0.08)" if conf == "High" else "rgba(251, 191, 36, 0.08)" if conf == "Medium" else "rgba(239, 68, 68, 0.08)"
    evid = quality.get("evidence_count", 0)
    rel = quality.get("relevance")
    rel_str = f"{rel:.2f}" if isinstance(rel, float) else "N/A"
    
    st.markdown(f"""
        <div style='margin-top: 12px; padding: 8px 12px; background: {conf_bg}; border-radius: 8px; border-left: 3px solid {conf_color};'>
            <div style='font-size: 0.75rem; font-weight: 600; color: {conf_color}; text-transform: uppercase; letter-spacing: 0.5px;'>
                Quality Assessment
            </div>
            <div style='font-size: 0.8rem; color: var(--text-main); margin-top: 6px; line-height: 1.6;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-muted);'>Confidence:</span>
                    <b style='color: {conf_color};'>{conf}</b>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-muted);'>Evidence:</span>
                    <b>{evid} document(s)</b>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: var(--text-muted);'>Relevance Score:</span>
                    <b>{rel_str}</b>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.session_state.sessions[st.session_state.current_session].append({
        "role": "assistant",
        "content": ans,
        "sources": quality.get("sources", []),
        "path": execution_path,
        "confidence": quality.get("confidence"),
    })
    st.session_state.process_query = False
    st.rerun()