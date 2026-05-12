import streamlit as st
import re
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
# 1. DYNAMIC ENTERPRISE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Lenovo Research Agent",
    page_icon="🔴", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Styling */
    html, body, [class*="css"] { 
        font-family: 'Inter', 'Segoe UI', sans-serif; 
        scroll-behavior: smooth;
    }
    
    .stApp { 
        background: linear-gradient(135deg, #0A0A0B 0%, #1A0505 40%, #050A15 100%);
        background-size: 250% 250%;
        animation: ambient-pulse 12s ease-in-out infinite alternate;
        color: #E3E3E3; 
    }
    
    @keyframes ambient-pulse {
        0% { background-position: 0% 50%; }
        100% { background-position: 100% 50%; }
    }
    
    header[data-testid="stHeader"] { background: transparent !important; }
    #MainMenu, footer { visibility: hidden; }
    
    .block-container { 
        padding-top: 2.5rem !important; 
        padding-bottom: 120px !important; 
        max-width: 850px !important; 
    }
    
    /* Fast CSS Animations (Snappy Load) */
    @keyframes slide-fade-up {
        0% { opacity: 0; transform: translateY(15px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    @keyframes gemini-star-pulse {
        0%, 100% { transform: scale(0.85) rotate(0deg); opacity: 0.8; filter: drop-shadow(0 0 5px rgba(226,35,26,0.5)); }
        50% { transform: scale(1.1) rotate(5deg); opacity: 1; filter: drop-shadow(0 0 15px rgba(226,35,26,0.9)); }
    }
    
    /* Landing Page Greeting */
    .greeting-wrapper {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-bottom: -5px;
        animation: slide-fade-up 0.3s ease-out forwards;
    }
    .greeting-primary { font-size: 3.5rem; font-weight: 500; color: #FAFAFA; margin: 0; }
    .greeting-secondary { 
        font-size: 2.2rem; font-weight: 400; color: #8B949E; 
        margin-top: 10px; margin-bottom: 4.5rem; 
        animation: slide-fade-up 0.3s ease-out forwards;
    }
    
    .lenovo-l-anim {
        display: inline-block;
        font-family: 'Arial Black', Impact, sans-serif;
        font-style: italic; font-weight: 900; font-size: 3.5rem;
        background: linear-gradient(135deg, #E2231A, #ff6b6b, #E2231A);
        background-size: 200% 200%;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: gemini-star-pulse 2.5s ease-in-out infinite;
        line-height: 1; margin-right: 8px;
    }

    /* Landing Page Suggestion Cards */
    section[data-testid="stMain"] .stButton > button {
        background-color: rgba(22, 23, 26, 0.6) !important; backdrop-filter: blur(12px);
        color: #E3E3E3 !important; border: 1px solid #2D3136 !important;
        border-radius: 16px !important; padding: 1.5rem !important; height: 130px; 
        text-align: left !important; display: flex !important; justify-content: flex-start !important; align-items: flex-start !important;
        animation: slide-fade-up 0.3s ease-out forwards;
        transition: all 0.2s ease-out !important;
    }
    section[data-testid="stMain"] .stButton > button:hover {
        background-color: rgba(30, 32, 36, 0.95) !important; border: 1px solid #E2231A !important;
        transform: translateY(-4px); box-shadow: 0 8px 25px rgba(226, 35, 26, 0.15); 
    }
    section[data-testid="stMain"] .stButton > button p {
        font-size: 0.95rem; font-weight: 400; line-height: 1.5; color: #D1D5DB; margin: 0;
    }

    /* Chat Messages */
    [data-testid="chat-message-user"], [data-testid="chat-message-assistant"] {
        animation: slide-fade-up 0.3s ease-out forwards;
    }
    [data-testid="chat-message-assistant"] {
        background-color: rgba(20, 21, 24, 0.85) !important; backdrop-filter: blur(10px);
        border: 1px solid #2D3136 !important; border-radius: 16px !important; padding: 1.5rem; margin-top: 0.5rem;
    }
    
    /* Input Box */
    [data-testid="stBottomBlock"] {
        background: linear-gradient(0deg, rgba(10,10,11,1) 40%, rgba(10,10,11,0) 100%) !important;
        padding-bottom: 2rem !important; padding-top: 2rem !important;
    }
    [data-testid="stChatInput"] {
        background-color: rgba(30, 32, 36, 0.95) !important; border-radius: 24px !important; 
        border: 1px solid #333 !important; padding: 0.2rem 0.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    [data-testid="stChatInput"]:focus-within { border-color: #E2231A !important; box-shadow: 0 0 0 1px #E2231A !important; }
    
    /* Expander Styling (For Sources Dropdown) */
    [data-testid="stExpander"] {
        background-color: transparent !important;
        border: 1px solid #2D3136 !important;
        border-radius: 12px !important;
        margin-top: 1.5rem !important;
    }
    
    /* ==========================================
       BULLETPROOF SIDEBAR BUTTON CSS 
       ========================================== */
    [data-testid="stSidebar"] { background-color: #0D0E10 !important; border-right: 1px solid #2D3136; }
    
    /* Default Chat History Buttons (Neutral) */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: transparent !important; border: none !important; color: #A0AAB5 !important;
        text-align: left !important; justify-content: flex-start !important; padding: 0.5rem !important;
        width: 100% !important; border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover { background-color: rgba(255, 255, 255, 0.05) !important; color: #E3E3E3 !important; }
    
    /* 1. New Chat Button (Clean, Subtle Outline) */
    div.element-container:has(.new-chat-anchor) + div.element-container button {
        background-color: transparent !important; color: #A0AAB5 !important;
        border: 1px solid #2D3136 !important; font-weight: 500 !important;
        border-radius: 8px !important; justify-content: center !important; text-align: center !important;
    }
    div.element-container:has(.new-chat-anchor) + div.element-container button:hover { 
        border-color: #E3E3E3 !important; color: #FFFFFF !important; 
    }

    /* 2. Reset Workspace Button (Pill Shape, Red Hover ONLY) */
    div.element-container:has(.reset-anchor) + div.element-container button {
        width: 100% !important; max-width: 180px !important; margin: 15px auto 0 auto !important;
        padding: 0.5rem 1rem !important; border-radius: 20px !important; 
        background-color: transparent !important; border: 1px solid #333 !important; color: #8B949E !important;
        justify-content: center !important; text-align: center !important; white-space: nowrap !important;
        transition: all 0.3s ease !important;
    }
    div.element-container:has(.reset-anchor) + div.element-container button p { margin: 0 !important; line-height: 1 !important; }
    div.element-container:has(.reset-anchor) + div.element-container button:hover {
        background-color: #E2231A !important; color: #FFFFFF !important;
        border-color: #E2231A !important; box-shadow: 0 4px 15px rgba(226, 35, 26, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)
 
# ==========================================
# 2. SESSION STATE MEMORY MANAGER
# ==========================================
if "sessions" not in st.session_state:
    st.session_state.sessions = {"Chat 1": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "Chat 1"
if "chat_counter" not in st.session_state:
    st.session_state.chat_counter = 1
if "process_query" not in st.session_state:
    st.session_state.process_query = False

def get_chat_name(session_id):
    messages = st.session_state.sessions[session_id]
    if not messages: return "New Chat"
    first_msg = messages[0]["content"]
    return first_msg[:28] + "..." if len(first_msg) > 28 else first_msg

def trigger_card_query(query_text):
    st.session_state.sessions[st.session_state.current_session].append({"role": "user", "content": query_text})
    st.session_state.process_query = True

# ==========================================
# 3. CORE AI AGENT (BULLETPROOF RETRIEVAL)
# ==========================================
@st.cache_resource
def initialize_agent():
    load_dotenv()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory="vector_db", embedding_function=embeddings)
    
    retriever = db.as_retriever(search_kwargs={"k": 6})
    
    # 🎯 BULLETPROOF FIX: Removed {page} dependency so it never crashes!
    custom_doc_prompt = PromptTemplate.from_template(
        "Source Document: {source}\n\nContent:\n{page_content}"
    )
    
    internal_tool = create_retriever_tool(
        retriever, 
        name="lenovo_internal", 
        description="CRITICAL: You MUST use this tool FIRST for ANY question regarding Lenovo, ThinkSystem, playbooks, or internal docs. TIP: If your first search fails, search again using highly specific keywords (e.g., 'Government AI adoption') instead of full sentences.",
        document_prompt=custom_doc_prompt 
    )
    
    web_tool = TavilySearch(max_results=3)
    
    llm = ChatOllama(model="qwen2.5:3b", temperature=0) 
    
    # 🎯 THE EXECUTIVE PERSONA PROMPT
    system_instruction = """You are an elite, highly articulate AI Research Consultant for Lenovo Global Technology.
    You process complex queries using an iterative ReAct (Reason + Act) loop.

    YOUR WRITING STYLE (CRITICAL):
    - You must write with the eloquence, depth, and analytical rigor of a flagship AI (like Gemini or GPT-4).
    - Do not just parrot facts like a robot. Synthesize the data into flowing, highly readable, and insightful paragraphs.
    - Provide an executive summary of your findings before diving into the detailed bullet points.
    - Use an authoritative, professional, and engaging tone.

    CRITICAL RULES FOR EXECUTION:
    1. STRICT TOOL ROUTING: 
       - IF the user asks about Lenovo, internal documents, or specific hardware, you MUST use `lenovo_internal` FIRST. 
       - ONLY use `web_search` if `lenovo_internal` returns absolutely nothing, or if searching for a competitor.
       - If you find partial information in the database, do not keep searching in a loop. Output what you found immediately.
    2. ZERO HALLUCINATION: You are strictly forbidden from guessing specs or numbers.
    3. PROFESSIONAL FORMATTING: Use clean, structured sections, bold headers, and polished bullet points. No tables. No HTML.
    4. CITATIONS: When you retrieve data from `lenovo_internal`, look closely at the "Source Document" metadata. You MUST extract the exact document name.

    You MUST append your sources at the very end of your response under the exact heading: ---SOURCES---
    
    Example of the bottom of your output:
    ---SOURCES---
    * CIO Playbook 2026 - WW_V2pdf.pdf
    * https://actual-raw-url.com/page
    """
    
    return create_react_agent(model=llm, tools=[internal_tool, web_tool], prompt=system_instruction)
agent = initialize_agent()

# ==========================================
# 4. TELEMETRY & HISTORY SIDEBAR 
# ==========================================
with st.sidebar:
    st.markdown(
        """
        <div style="margin-top: -15px; margin-bottom: 25px; display: flex; flex-direction: column; align-items: flex-start;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/Lenovo_logo_2015.svg" width="150" alt="Lenovo" style="margin-bottom: 8px;">
            <div style="color: #8B949E; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.5px; line-height: 1.2;">
                Research Agentic Framework | RAG - AI
            </div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="new-chat-anchor"></div>', unsafe_allow_html=True)
    if st.button("➕ New Chat"):
        st.session_state.chat_counter += 1
        new_session_id = f"Chat {st.session_state.chat_counter}"
        st.session_state.sessions[new_session_id] = []
        st.session_state.current_session = new_session_id
        st.rerun()
    
    st.divider()
    st.markdown("<p style='color: #8B949E; font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; margin-bottom: 5px;'>RECENT SESSIONS</p>", unsafe_allow_html=True)
    
    for session_id in list(st.session_state.sessions.keys()):
        chat_name = get_chat_name(session_id)
        icon = "🔵" if session_id == st.session_state.current_session else "💬"
        if st.button(f"{icon} {chat_name}", key=session_id):
            st.session_state.current_session = session_id
            st.rerun()

    st.divider()
    st.markdown("### System Telemetry")
    st.caption("<span style='color: #00E5FF;'>●</span> STATUS: ONLINE | LOCAL HOST", unsafe_allow_html=True)
    st.write("**Architecture:** Agentic AI + RAG")
    st.write("**Engine:** Qwen2.5-3B (Tool Enabled)") 
    st.write("**Store:** ChromaDB")
    st.write("**Oracle:** Tavily Web")
    
    st.divider()
    st.markdown("### Architecture Flow")
    st.caption("1. Query Ingestion\n2. ReAct Agent Initiation\n3. Vector Retrieval\n4. Web Search Fallback\n5. Output Generation")
    
    st.divider()
    
    st.markdown('<div class="reset-anchor"></div>', unsafe_allow_html=True)
    if st.button("■ Reset Workspace"):
        st.session_state.sessions = {"Chat 1": []}
        st.session_state.current_session = "Chat 1"
        st.session_state.chat_counter = 1
        st.session_state.process_query = False
        st.rerun()

# ==========================================
# 5. UI RENDERING & AGENT EXECUTION
# ==========================================

# Robust Gemini-style Message Renderer (Catches ALL source formats)
def render_message(content):
    # This aggressive Regex catches "### SOURCES", "---SOURCES---", "Sources:", etc.
    match = re.search(r'(?i)(?:\n|^)\s*(?:###|---)?\s*SOURCES?:?(?:---|)?\s*(?:\n|$)', content)
    if match:
        main_text = content[:match.start()].strip()
        sources_text = content[match.end():].strip()
        st.markdown(main_text)
        if sources_text: # Only draw the expander if sources were actually listed
            with st.expander("🔗 Sources"):
                st.markdown(sources_text)
    else:
        st.markdown(content)

active_chat_history = st.session_state.sessions[st.session_state.current_session]

if not active_chat_history:
    st.markdown("""
        <div class="greeting-wrapper">
            <span class="lenovo-l-anim">L</span>
            <h1 class="greeting-primary">Hello.</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<h1 class='greeting-secondary'>What shall we research today?</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1: st.button("📊 Compare supported GPUs and PCIe generation on SR670 V2 vs XE9680.", on_click=trigger_card_query, args=("Compare supported GPU count and PCIe generation on Lenovo ThinkSystem SR670 V2 vs Dell PowerEdge XE9680.",), use_container_width=True)
    with col2: st.button("🌐 Analyze the current stock performance of Lenovo Group.", on_click=trigger_card_query, args=("What is the current stock price of Lenovo Group?",), use_container_width=True)
    with col3: st.button("⚙️ Summarize PSU requirements and cooling architecture of SR670 V2.", on_click=trigger_card_query, args=("Summarize power supply wattage requirements and cooling architecture of ThinkSystem SR670 V2 from internal docs.",), use_container_width=True)

if user_input := st.chat_input("Ask a complex research query..."):
    st.session_state.sessions[st.session_state.current_session].append({"role": "user", "content": user_input})
    st.session_state.process_query = True

for msg in active_chat_history:
    avatar_icon = "👤" if msg["role"] == "user" else "🔴"
    with st.chat_message(msg["role"], avatar=avatar_icon):
        if msg["role"] == "assistant":
            render_message(msg["content"])
        else:
            st.markdown(msg["content"])

if st.session_state.process_query:
    with st.chat_message("assistant", avatar="🔴"):
        with st.status("Agent reflecting and gathering data...", expanded=True) as status:
            agent = initialize_agent() 
            
            langgraph_history = [
                HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
                for m in active_chat_history
            ]
            
            # Use .invoke() to return the final dictionary state (avoids generator error)
            final_state = agent.invoke({"messages": langgraph_history})
            status.update(label="Report Generated", state="complete", expanded=False)
            
        final_answer = final_state["messages"][-1].content
        
        # Output the answer natively passing through our Gemini-style interceptor
        render_message(final_answer)
                    
        st.session_state.sessions[st.session_state.current_session].append({"role": "assistant", "content": final_answer})
        st.session_state.process_query = False
        st.rerun()