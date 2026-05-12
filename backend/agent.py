import os
import re
import time
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────
RETRIEVER_K       = int(os.getenv("RETRIEVER_K", "8"))
RETRIEVER_FETCH_K = int(os.getenv("RETRIEVER_FETCH_K", "24"))
RETRIEVER_LAMBDA  = float(os.getenv("RETRIEVER_LAMBDA", "0.42"))
MAX_EVIDENCE      = int(os.getenv("MAX_EVIDENCE_SNIPPETS", "5"))
HISTORY_TURNS     = int(os.getenv("LOCAL_HISTORY_MESSAGES", "6"))
LOCAL_MODEL       = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:3b")
ENABLE_WEB        = os.getenv("ENABLE_WEB_FALLBACK", "true").lower() == "true"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

global_runtime = None

# ── Query routing ──────────────────────────────────────────────────────────────
_EXTERNAL_TERMS = {
    "stock price", "share price", "live price", "market cap", "trading",
    "bitcoin", "cryptocurrency", "crypto", "ethereum", "gold price", "oil price",
    "exchange rate", "forex", "nse", "bse", "nasdaq", "nyse",
    "ipl", "cricket", "score", "match", "live score", "scorecard",
    "football", "soccer", "tennis", "nba", "nfl", "nhl", "f1", "formula 1",
    "olympics", "world cup", "tournament", "fixture", "result",
    "news", "latest", "weather", "right now", "as of today",
    "currently", "today", "yesterday", "tomorrow", "sports", "market", "quote",
}

def is_external_query(query_text: str) -> bool:
    q = query_text.lower()
    return any(term in q for term in _EXTERNAL_TERMS)

def sanitize_query(query: str) -> str | None:
    if not query or not isinstance(query, str):
        return None
    query = query.strip()
    if len(query) < 3 or len(query) > 1000:
        return None
    query = re.sub(r"\s+", " ", query)
    if re.search(r"\b(DROP|DELETE|TRUNCATE|INSERT)\s+", query, re.IGNORECASE):
        return None
    return query

# ── Source utilities ───────────────────────────────────────────────────────────
def resolve_source_path(name: str) -> str:
    candidates = [name, os.path.join(BASE_DIR, "documents", name)]
    if not name.lower().endswith(".txt"):
        candidates.append(os.path.join(BASE_DIR, "documents", name + ".txt"))
    for c in candidates:
        if os.path.exists(c):
            return c.replace("\\", "/")
    return ""

def _read_file_preview(path: str, max_chars: int = 2000) -> str:
    try:
        if path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            text = ""
            for page in PdfReader(path).pages:
                text += (page.extract_text() or "") + "\n"
                if len(text) >= max_chars:
                    break
            return text[:max_chars].strip()
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(max_chars)
    except Exception:
        return ""

_URL_LIKE = re.compile(
    r"^(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:[/\w.@?=%&_~:,;!-]*)?$"
)

def build_source_details(sources: list) -> list:
    details = []
    for s in (sources or []):
        if not s or not isinstance(s, str):
            continue
        item: dict = {"name": s}
        try:
            if s.startswith("http://") or s.startswith("https://"):
                item.update({"type": "url", "url": s})
            else:
                p = resolve_source_path(s)
                if p:
                    item.update({"type": "file", "path": p, "preview": _read_file_preview(p)})
                elif _URL_LIKE.match(s):
                    item.update({"type": "url", "url": "https://" + s.lstrip("/")})
                else:
                    item.update({"type": "unknown", "raw": s})
        except Exception:
            item.update({"type": "unknown", "raw": s})
        details.append(item)
    return details

def extract_sources_from_answer(answer: str) -> list:
    seen: set[str] = set()
    for line in answer.split("\n"):
        if "Source:" not in line:
            continue
        raw = line.split("Source:")[1].split(",")[0].split("\n")[0]
        raw = raw.strip().strip(")]*\"'").strip()
        raw = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", raw).strip()
        if raw and not raw.startswith("http") and len(raw) < 120:
            seen.add(raw)
    return list(seen)

def log_routing_decision(session_id: str, query: str, path: str, details: dict) -> None:
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session": session_id,
        "query": query,
        "path": path,
        "details": details,
    }
    try:
        with open(os.path.join(BASE_DIR, "router.log"), "a", encoding="utf-8") as lf:
            lf.write(str(entry) + "\n")
    except Exception:
        pass

# ── Agent initialization ───────────────────────────────────────────────────────
def initialize_agent():
    global global_runtime

    # If we already have a working runtime with an LLM, return it directly
    if global_runtime and global_runtime.get("llm") is not None:
        return global_runtime

    load_dotenv()

    # Build retriever (always works — no Ollama needed)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(
        persist_directory=os.path.join(BASE_DIR, "vector_db"),
        embedding_function=embeddings,
    )
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_FETCH_K, "lambda_mult": RETRIEVER_LAMBDA},
    )
    internal_tool = create_retriever_tool(
        retriever,
        name="lenovo_internal",
        description="Lenovo's internal enterprise document corpus. Always search here first for Lenovo-related queries.",
        document_prompt=PromptTemplate.from_template("Source: {source}\n\n{page_content}"),
    )

    # Web tool (optional)
    web_tool = global_runtime.get("web_tool") if global_runtime else None
    if web_tool is None and ENABLE_WEB:
        try:
            web_tool = TavilySearch(max_results=4)
        except Exception:
            pass

    # Try to connect to Ollama — retry-friendly (doesn't cache failure)
    llm = None
    ollama_error = None
    try:
        llm = ChatOllama(model=LOCAL_MODEL, temperature=0.1, num_predict=512, num_ctx=4096)
        llm.invoke("ping")  # verify Ollama is alive
    except Exception as e:
        ollama_error = str(e)
        llm = None

    agent_prompt = (
        "You are a senior enterprise research analyst at Lenovo. "
        "Use the lenovo_internal tool to search the document corpus, then write a clear, well-reasoned answer. "
        "Write in natural professional prose — as an expert would in an executive briefing. "
        "Cite every claim with its source document using (Source: filename). "
        "Never fabricate data. If the documents do not cover the question, say so directly."
    )
    agent = create_react_agent(model=llm, tools=[internal_tool], prompt=agent_prompt) if llm else None

    # Only permanently cache if LLM is available; otherwise allow retry on next request
    runtime = {"agent": agent, "llm": llm, "retriever": retriever, "web_tool": web_tool, "ollama_error": ollama_error}
    if llm is not None:
        global_runtime = runtime
    else:
        # Cache retriever/web_tool but NOT as the final runtime so LLM is retried next call
        global_runtime = None

    return runtime

# ── Internal RAG fallback (when agent is unavailable) ─────────────────────────
def _rag_fallback(query: str, runtime: dict) -> dict:
    docs = runtime["retriever"].invoke(query)[:RETRIEVER_K]
    if not docs:
        return {
            "answer": (
                "The internal document corpus was searched but no relevant content was found for this query. "
                "Try rephrasing with a specific product name, document title, or topic area."
            ),
            "confidence": "Medium",
            "sources": [],
        }

    sources, blocks = [], []
    for i, d in enumerate(docs, 1):
        src = d.metadata.get("source", "internal")
        snippet = d.page_content.strip().replace("\n", " ")[:400]
        sources.append(src)
        blocks.append(f"[{i}] {snippet} (Source: {src})")

    unique_sources = sorted(set(sources))
    llm = runtime.get("llm")

    if llm:
        prompt = (
            "You are a Lenovo enterprise research analyst. "
            "Using only the document excerpts below, write a clear, well-reasoned answer. "
            "Cite the source document for every point you make. "
            "Write naturally — not as a list of bullet points. "
            "If the excerpts do not address the question, say so honestly.\n\n"
            "Documents:\n" + "\n\n".join(blocks) + f"\n\nQuestion: {query}\n\nAnswer:"
        )
        try:
            resp = llm.invoke(prompt)
            ans = resp.content if hasattr(resp, "content") else str(resp)
            if ans and len(ans.strip()) > 20:
                confidence = "High" if len(unique_sources) >= 2 else "Medium"
                return {"answer": ans, "confidence": confidence, "sources": unique_sources}
        except Exception:
            pass

    # No LLM — return the raw excerpts clearly labelled
    answer = (
        "The most relevant passages from internal documents are included below.\n\n"
        + "\n\n".join(blocks[:MAX_EVIDENCE])
    )
    return {"answer": answer, "confidence": "Medium", "sources": unique_sources}

# ── Web search answer ──────────────────────────────────────────────────────────
_WEB_ERROR_SIGNALS = {
    "error", "exception", "maximum allowed length", "rate limit",
    "invalid query", "bad request",
}

def _tavily_fetch(web_tool, query: str) -> str:
    try:
        result = web_tool.invoke(query.strip()[:200])
        raw = result.strip() if isinstance(result, str) else str(result).strip()
        if any(sig in raw.lower()[:300] for sig in _WEB_ERROR_SIGNALS):
            return ""
        return raw
    except Exception:
        return ""

def build_web_answer(query_text: str, runtime: dict) -> dict:
    web_tool = runtime.get("web_tool")
    if not web_tool:
        return {
            "answer": "Live web search is not available in this session. Please verify your Tavily API key.",
            "confidence": "Medium", "sources": [], "source_details": [],
        }

    raw = ""
    for attempt in [query_text, " ".join(query_text.split()[:10]), " ".join(query_text.split()[:5])]:
        raw = _tavily_fetch(web_tool, attempt)
        if raw:
            break

    url_pattern = r"https?://[^\s)\]}>\"'\s]+"
    seen_urls: dict[str, None] = {}
    for t in re.findall(url_pattern, raw):
        clean = re.sub(r"[.,;:)\]}>]+$", "", t)
        if clean:
            seen_urls[clean] = None
    sources = list(seen_urls)[:5]

    if not raw:
        q = query_text.lower()
        hint = (
            "For real-time stock data, check Google Finance, Yahoo Finance, or Bloomberg."
            if any(w in q for w in ("stock", "price", "share"))
            else "Try a dedicated platform for the most current information on this topic."
        )
        return {
            "answer": f"Live web data was unavailable for this query. {hint}",
            "confidence": "Medium", "sources": [], "source_details": [],
        }

    llm = runtime.get("llm")
    if llm:
        prompt = (
            "You are a precise research analyst. Based on the search results below, "
            "answer the question in 3-5 sentences of natural, professional prose. "
            "Include specific figures, dates, or facts where present. "
            "Mention the source at the end.\n\n"
            f"Question: {query_text}\n\nSearch Results:\n{raw[:2500]}\n\nAnswer:"
        )
        try:
            resp = llm.invoke(prompt)
            answer = resp.content if hasattr(resp, "content") else str(resp)
            if answer and len(answer.strip()) > 20:
                return {
                    "answer": answer, "confidence": "Medium",
                    "sources": sources, "source_details": build_source_details(sources),
                }
        except Exception:
            pass

    # LLM unavailable — extract key figure from raw text
    price_match = None
    for pat in (r"(?:INR|₹)\s?\d[\d,]*(?:\.\d{1,4})?", r"\$\s?\d[\d,]*(?:\.\d{1,4})?"):
        m = re.search(pat, raw)
        if m:
            price_match = m.group(0)
            break

    if price_match:
        answer = (
            f"Based on live search data, the current value is approximately {price_match}. "
            "Verify directly on your preferred financial platform, as prices update in real time."
        )
    else:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", raw) if len(s.strip()) > 25]
        answer = " ".join(sentences[:3]) if sentences else raw[:300]

    return {
        "answer": answer, "confidence": "Medium",
        "sources": sources, "source_details": build_source_details(sources),
    }

# ── Entry point ────────────────────────────────────────────────────────────────
def route_answer(active_history: list, session_id: str = "default") -> dict:
    runtime = initialize_agent()
    latest_query = active_history[-1]["content"] if active_history else ""
    query = sanitize_query(latest_query)

    if not query:
        return {"answer": "Please enter a valid query.", "confidence": "Medium", "sources": [], "source_details": []}

    # ── Surface clear Ollama-not-running message ──────────────────────────────
    if runtime.get("llm") is None:
        ollama_err = runtime.get("ollama_error", "")
        msg = (
            "⚠️ **Ollama is not running or the model is not loaded.**\n\n"
            "To fix this:\n"
            "1. Open a new terminal\n"
            "2. Run: `ollama serve`\n"
            f"3. Then run: `ollama pull {LOCAL_MODEL}`\n"
            "4. Retry your question.\n\n"
            + (f"_Technical detail: {ollama_err}_" if ollama_err else "")
        )
        return {"answer": msg, "confidence": "Low", "sources": [], "source_details": []}

    # ── Web path ───────────────────────────────────────────────────────────────
    if is_external_query(query) and ENABLE_WEB:
        result = build_web_answer(query, runtime)
        log_routing_decision(session_id, query, "Web Search", {"confidence": result.get("confidence")})
        return result

    # ── Internal agent path ────────────────────────────────────────────────────
    hist = []
    for m in active_history[-HISTORY_TURNS:]:
        hist.append(HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"]))

    ans, srcs, confidence = "", [], "Medium"

    if runtime.get("agent"):
        try:
            res = runtime["agent"].invoke({"messages": hist})
            ans = res["messages"][-1].content
            srcs = extract_sources_from_answer(ans)
            confidence = "High" if srcs else "Medium"
        except Exception as e:
            print(f"[Agent] invoke error: {e}")
            ans = ""

    if not ans or len(ans.strip()) < 20:
        fallback = _rag_fallback(query, runtime)
        ans, srcs, confidence = fallback["answer"], fallback.get("sources", []), fallback.get("confidence", "Medium")

    # Last-resort source sweep via retriever metadata
    if not srcs:
        try:
            docs = runtime["retriever"].invoke(query)[:5]
            srcs = sorted({d.metadata.get("source", "") for d in docs if d.metadata.get("source")})
        except Exception:
            pass

    if ans and len(ans.strip()) > 30 and confidence == "Low":
        confidence = "Medium"

    log_routing_decision(session_id, query, "Internal Agent", {"confidence": confidence})
    return {
        "answer": ans, "confidence": confidence,
        "sources": srcs, "source_details": build_source_details(srcs),
    }
