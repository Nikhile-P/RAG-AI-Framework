import os
import re
import sys
import time
import threading
import traceback
from typing import Any

from langchain.agents import create_agent
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.tools.retriever import create_retriever_tool
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# ── Configuration ──────────────────────────────────────────────────────────────
RETRIEVER_K       = int(os.getenv("RETRIEVER_K", "10"))
RETRIEVER_FETCH_K = int(os.getenv("RETRIEVER_FETCH_K", "30"))
RETRIEVER_LAMBDA  = float(os.getenv("RETRIEVER_LAMBDA", "0.5"))
MAX_EVIDENCE      = int(os.getenv("MAX_EVIDENCE_SNIPPETS", "5"))
HISTORY_TURNS     = int(os.getenv("LOCAL_HISTORY_MESSAGES", "6"))
LOCAL_MODEL       = os.getenv("LOCAL_MODEL_NAME", "qwen2.5:3b")
ENABLE_WEB        = os.getenv("ENABLE_WEB_FALLBACK", "true").lower() == "true"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

global_runtime = None
_runtime_init_lock = threading.Lock()

AGENT_SYSTEM_PROMPT = (
    "You are a senior enterprise research analyst at Lenovo. "
    "Your goal is to provide accurate, data-driven insights by synthesizing Lenovo's internal document corpus and real-time web data.\n\n"
    "### Operational Pattern:\n"
    "1. **Internal Context First**: For any Lenovo-specific query (products like ThinkPad, policies, internal news), always use the 'lenovo_internal' tool first.\n"
    "2. **Web Augmentation**: Use 'tavily_search_results_json' to supplement internal data with current market trends, stock prices, or competitor analysis.\n"
    "3. **Multi-Hop Synthesis**: If the internal search provides partial info, use the web search to fill the gaps. Do not provide two separate answers; synthesize them into one cohesive report.\n\n"
    "### Response Standards:\n"
    "- **Precision**: Use specific numbers, dates, and names from the tools.\n"
    "- **Citations**: Cite every fact. Internal: '(Source: filename.ext)'. Web: '(Source: domain.com)'.\n"
    "- **Transparency**: If tools return conflicting data, highlight the discrepancy and provide a reasoned perspective.\n"
    "- **Formatting**: Use bold text for key insights and ### headers for sections."
)


def _normalize_source(meta_val: Any) -> str:
    if meta_val is None:
        return ""
    return str(meta_val).strip()


def _final_ai_message_text(invoke_result: dict[str, Any]) -> str:
    """Pick last plain assistant reply (skip AIMessages that only schedule tool_calls)."""
    msgs: list[Any] = invoke_result.get("messages") or []
    for m in reversed(msgs):
        if not isinstance(m, AIMessage):
            continue
        tcalls = getattr(m, "tool_calls", None) or []
        raw = getattr(m, "content", "")
        text = _normalize_message_content(raw).strip()
        if not text:
            continue
        if not tcalls:
            return _normalize_message_content(raw)
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            raw = getattr(m, "content", "")
            text = _normalize_message_content(raw).strip()
            if text:
                return _normalize_message_content(raw)
    return ""


def _normalize_message_content(content: Any) -> str:
    """Flatten LangChain message content (str or multimodal blocks) to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
                elif isinstance(block.get("content"), str):
                    parts.append(block["content"])
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _degraded_llm_banner(runtime: dict) -> str:
    err = (runtime.get("ollama_error") or "").strip()
    detail = f"\n\n_Technical detail: {err}_" if err else ""
    return (
        "**Note:** The local LLM (Ollama) is not available. "
        "Showing retrieval-based results below. Start `ollama serve` and ensure the model is pulled for full agent replies."
        + detail
        + "\n\n---\n\n"
    )


# ── Query routing ──────────────────────────────────────────────────────────────
_EXTERNAL_TERMS = {
    "stock price", "share price", "live price", "market cap", "trading", "stock",
    "bitcoin", "cryptocurrency", "crypto", "ethereum", "gold price", "oil price",
    "exchange rate", "forex", "nse", "bse", "nasdaq", "nyse",
    "ipl", "cricket", "score", "match", "live score", "scorecard",
    "football", "soccer", "tennis", "nba", "nfl", "nhl", "f1", "formula 1",
    "olympics", "world cup", "tournament", "fixture", "result",
    "news", "latest", "weather", "right now", "as of today",
    "currently", "today", "yesterday", "tomorrow", "sports", "market", "quote",
    "ceo", "revenue", "fiscal year", "earnings", "headquarters", "founded",
    "competitor", "market share", "announcement", "release date",
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

def log_routing_decision(session_id, query, strategy, details=None, latency=0.0):
    entry = {
        "timestamp": time.time(),
        "session_id": session_id,
        "query": query[:100],
        "path": strategy,
        "details": details or {},
        "latency": latency
    }
    try:
        with open(LOG_FILE, "a") as f:
            f.write(str(entry) + "\n")
    except Exception:
        pass

# ── Agent initialization ───────────────────────────────────────────────────────
def _ensure_vector_runtime() -> dict:
    """Load embeddings + vector store once (expensive). Does not require Ollama."""
    # Repo-root .env works even when uvicorn's cwd is backend/
    load_dotenv(os.path.join(BASE_DIR, ".env"))
    load_dotenv()
    tavily_key = (os.getenv("TAVILY_API_KEY") or "").strip()
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(
        persist_directory=os.path.join(BASE_DIR, "vector_db"),
        embedding_function=embeddings,
    )
    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": RETRIEVER_K, "fetch_k": RETRIEVER_FETCH_K, "lambda_mult": RETRIEVER_LAMBDA},
    )
    web_tool = None
    if ENABLE_WEB and tavily_key:
        try:
            from langchain_tavily import TavilySearch
            web_tool = TavilySearch(
                max_results=5, 
                search_depth="advanced", 
                tavily_api_key=tavily_key
            )
            if hasattr(web_tool, "name"):
                web_tool.name = "tavily_search_results_json"
        except Exception as e:
            print(f"[Web] Tavily init skipped: {e}")
    return {
        "retriever": retriever,
        "web_tool": web_tool,
        "llm": None,
        "agent": None,
        "ollama_error": None,
        "web_status": "Ready" if web_tool else "Disabled",
    }


def _attach_ollama_agent(runtime: dict) -> dict:
    """Attach ChatOllama + tool-calling agent; cheap to retry when Ollama was down."""
    retriever = runtime["retriever"]
    internal_tool = create_retriever_tool(
        retriever,
        name="lenovo_internal",
        description="Lenovo's internal enterprise document corpus. Always search here first for Lenovo-related queries.",
        document_prompt=PromptTemplate.from_template("Source: {source}\n\n{page_content}"),
    )
    llm = None
    ollama_error = None
    try:
        llm = ChatOllama(model=LOCAL_MODEL, temperature=0.1, num_predict=512, num_ctx=4096)
        llm.invoke("ping")
    except Exception as e:
        ollama_error = str(e)
        llm = None

    tools = [internal_tool]
    if runtime.get("web_tool"):
        tools.append(runtime["web_tool"])

    agent = None
    if llm:
        try:
            agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=AGENT_SYSTEM_PROMPT,
            )
        except Exception as e:
            print(f"[Agent] create_agent failed: {e}")
            agent = None
            llm = None
            ollama_error = ollama_error or str(e)

    runtime["llm"] = llm
    runtime["agent"] = agent
    runtime["ollama_error"] = ollama_error
    return runtime


def initialize_agent():
    global global_runtime

    # Serialize init: concurrent /api/chat + Chroma SQLite → "database is locked" otherwise
    with _runtime_init_lock:
        if global_runtime and global_runtime.get("llm") is not None:
            return global_runtime

        if global_runtime is None:
            global_runtime = _ensure_vector_runtime()

        return _attach_ollama_agent(global_runtime)

# ── Internal RAG fallback (when agent is unavailable) ─────────────────────────
def _rag_fallback(query: str, runtime: dict, *, external_without_web: bool = False) -> dict:
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
        src_raw = d.metadata.get("source", "internal")
        src = _normalize_source(src_raw) or "internal"
        snippet = d.page_content.strip().replace("\n", " ")[:400]
        sources.append(src)
        blocks.append(f"[{i}] {snippet} (Source: {src})")

    unique_sources = sorted(set(sources))
    llm = runtime.get("llm")

    if llm:
        timing_note = (
            "This question may call for breaking news or other live web data that is not in the excerpts. "
            "If so, answer strictly from the documents below and clearly state limitations.\n\n"
            if external_without_web
            else ""
        )
        prompt = (
            "You are a Lenovo enterprise research analyst. "
            "Using only the document excerpts below, write a clear, well-reasoned answer. "
            "Cite the source document for every point you make. "
            "Write naturally — not as a list of bullet points. "
            "If the excerpts do not address the question, say so honestly.\n\n"
            + timing_note
            + "Documents:\n" + "\n\n".join(blocks) + f"\n\nQuestion: {query}\n\nAnswer:"
        )
        try:
            resp = llm.invoke(prompt)
            ans = resp.content if hasattr(resp, "content") else str(resp)
            if ans and len(ans.strip()) > 20:
                confidence = "High" if len(unique_sources) >= 2 else "Medium"
                # If the LLM says it can't address the question, lower the confidence
                if "not possible" in ans.lower() or "not address" in ans.lower() or "no information" in ans.lower():
                    confidence = "Low"
                return {"answer": ans, "confidence": confidence, "sources": unique_sources}
        except Exception:
            pass

    # No LLM — return the raw excerpts clearly labelled
    answer = (
        "The most relevant passages from internal documents are included below.\n\n"
        + "\n\n".join(blocks[:MAX_EVIDENCE])
    )
    return {"answer": answer, "confidence": "Medium", "sources": unique_sources}

# ── Web search answer (Optimized with Cache) ──────────────────────────────────
_WEB_CACHE = {}
_CACHE_TTL = 3600 # 1 hour

def _get_cached_web(query: str) -> str | None:
    if query in _WEB_CACHE:
        val, ts = _WEB_CACHE[query]
        if time.time() - ts < _CACHE_TTL:
            return val
    return None

def _set_cached_web(query: str, val: str):
    _WEB_CACHE[query] = (val, time.time())

_WEB_ERROR_SIGNALS = {
    "error", "exception", "maximum allowed length", "rate limit",
    "invalid query", "bad request", "unauthorized", "invalid api", "api key",
    "401", "403", "incorrect api key",
}


def _tavily_payload_to_snippet(payload: Any) -> str | None:
    """Turn Tavily tool output (often a dict from the HTTP API) into plain text."""
    if payload is None:
        return None
    if isinstance(payload, dict):
        if payload.get("error") is not None:
            return None
        chunks: list[str] = []
        ans = payload.get("answer")
        if isinstance(ans, str) and ans.strip():
            chunks.append(ans.strip())
        for row in payload.get("results") or []:
            if not isinstance(row, dict):
                continue
            title = (row.get("title") or "Search Result").strip()
            content = (row.get("content") or row.get("raw_content") or "").strip()
            url = (row.get("url") or "").strip()
            # Clean up content a bit
            content = re.sub(r"\s+", " ", content)[:800]
            line = f"TITLE: {title}\nCONTENT: {content}\nURL: {url}"
            if content:
                chunks.append(line)
        text = "\n\n".join(chunks).strip()
        return text or None
    if isinstance(payload, str):
        t = payload.strip()
        return t or None
    return str(payload).strip() or None


def _rewrite_query_for_web(llm, query: str, history: list) -> str:
    if not llm:
        return query
    prompt = (
        "Given the conversation history and the latest user query, rewrite the query to be optimized for a web search engine (Tavily). "
        "Focus on extracting the core intent, entities, and required real-time information. "
        "Return ONLY the rewritten query text.\n\n"
        f"Query: {query}\n\nRewritten Query:"
    )
    try:
        resp = llm.invoke(prompt)
        text = _normalize_message_content(resp.content if hasattr(resp, "content") else str(resp)).strip()
        return text if text else query
    except Exception:
        return query


def _tavily_fetch(web_tool, query: str) -> str:
    try:
        # Limit query length for API safety
        result = web_tool.invoke(query.strip()[:240])
    except Exception as e:
        print(f"[Web] Tavily invoke failed for '{query}': {e}")
        return ""

    raw = _tavily_payload_to_snippet(result)
    if not raw:
        return ""
    head = raw.lower()[:600]
    if any(sig in head for sig in _WEB_ERROR_SIGNALS):
        return ""
    return raw


def try_complete_web_answer(query_text: str, runtime: dict) -> dict[str, Any] | None:
    """
    Produce an answer when live Tavily web search succeeds.
    Returns None → caller should fall back to internal RAG/agent (no Tavily key, errors, empty results).
    """
    web_tool = runtime.get("web_tool")
    if not web_tool:
        return None

    llm = runtime.get("llm")
    
    # ── Step 1: Optimized Query Rewriting ──
    search_query = _rewrite_query_for_web(llm, query_text, []) if llm else query_text
    
    raw = _get_cached_web(search_query)
    if raw:
        print(f"[Web] Cache hit for '{search_query}'")
    else:
        # Try rewritten query first, then original
        for attempt in [search_query, query_text]:
            raw = _tavily_fetch(web_tool, attempt)
            if raw and len(raw.strip()) >= 40:
                _set_cached_web(search_query, raw)
                break

    if not raw or len(raw.strip()) < 40:
        return None

    url_pattern = r"https?://[^\s)\]}>\"'\s]+"
    seen_urls: dict[str, None] = {}
    for t in re.findall(url_pattern, raw):
        clean = re.sub(r"[.,;:)\]}>]+$", "", t)
        if clean:
            seen_urls[clean] = None
    sources = list(seen_urls)[:5]

    if llm:
        prompt = (
            "You are a precise research analyst. Based on the search results below, "
            "answer the question in 3-5 sentences of natural, professional prose. "
            "Include specific figures, dates, or facts where present. "
            "Mention the source at the end.\n\n"
            f"Question: {query_text}\n\nSearch Results:\n{raw[:3000]}\n\nAnswer:"
        )
        try:
            resp = llm.invoke(prompt)
            answer = resp.content if hasattr(resp, "content") else str(resp)
            if answer and len(answer.strip()) > 20:
                return {
                    "answer": answer, "confidence": "High",
                    "sources": sources, "source_details": build_source_details(sources),
                    "trace": "Web Search (LLM Synthesized)"
                }
        except Exception:
            pass

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
    try:
        return _route_answer_impl(active_history, session_id=session_id)
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[route_answer] FAILED:\n{tb}", file=sys.stderr)
        return {
            "answer": (
                "**Something went wrong on the server while generating a reply.**\n\n"
                "Typical fixes: restart the backend, ensure **Ollama is running**, and wait for the first "
                "request to finish (models and the vector store load on demand).\n\n"
                f"`{type(e).__name__}: {e}`"
            ),
            "confidence": "Low",
            "sources": [],
            "source_details": [],
        }


def _route_answer_impl(active_history: list, session_id: str = "default") -> dict:
    runtime = initialize_agent()
    latest = active_history[-1] if active_history else {}
    latest_query = latest.get("content", "") if isinstance(latest, dict) else ""
    query = sanitize_query(latest_query)

    if not query:
        return {"answer": "Please enter a valid query.", "confidence": "Medium", "sources": [], "source_details": []}

    degraded = runtime.get("llm") is None
    banner = _degraded_llm_banner(runtime) if degraded else ""
    start_time = time.time()
    
    # ── Intelligent Routing ──
    # If it's a known external query, prioritize the web path for real-time accuracy.
    if is_external_query(query) and ENABLE_WEB:
        web_out = try_complete_web_answer(query, runtime)
        if web_out:
            result = dict(web_out)
            if degraded and result.get("answer"):
                result["answer"] = banner + result["answer"]
            log_routing_decision(session_id, query, "Web Search (Fast Path)", {"confidence": result.get("confidence")})
            return result
        # No Tavily / failed search → same seamless path as other questions (internal RAG + agent)
        external_without_web_fallback = True
    else:
        external_without_web_fallback = False

    # ── Internal agent path ────────────────────────────────────────────────────
    hist = []
    for m in active_history[-HISTORY_TURNS:]:
        if not isinstance(m, dict):
            continue
        raw = (m.get("role") or "user").strip().lower()
        content = m.get("content")
        if content is None:
            continue
        text = content if isinstance(content, str) else str(content)
        if raw in ("assistant", "ai", "model", "agent"):
            hist.append(AIMessage(content=text))
        else:
            hist.append(HumanMessage(content=text))

    ans, srcs, confidence = "", [], "Medium"

    if runtime.get("agent"):
        try:
            res = runtime["agent"].invoke({"messages": hist})
            state: dict[str, Any] = (
                res if isinstance(res, dict) else {"messages": list(getattr(res, "messages", []) or [])}
            )
            ans = _final_ai_message_text(state)
            srcs = extract_sources_from_answer(ans)
            confidence = "High" if srcs else "Medium"
        except Exception as e:
            print(f"[Agent] invoke error: {e}")
            ans = ""

    if not ans or len(ans.strip()) < 20:
        fallback = _rag_fallback(
            query, runtime, external_without_web=external_without_web_fallback
        )
        ans = fallback["answer"]
        srcs = fallback.get("sources", [])
        confidence = fallback.get("confidence", "Medium")

    if degraded and ans:
        ans = banner + ans

    # Last-resort source sweep via retriever metadata
    if not srcs:
        try:
            docs = runtime["retriever"].invoke(query)[:5]
            cleaned = {_normalize_source(d.metadata.get("source")) for d in docs if d.metadata.get("source")}
            cleaned.discard("")
            srcs = sorted(cleaned)
        except Exception:
            pass

    if ans and len(ans.strip()) > 30 and confidence == "Low":
        confidence = "Medium"

    log_routing_decision(session_id, query, "Internal Agent", {"confidence": confidence})
    return {
        "answer": ans, "confidence": confidence,
        "sources": srcs, "source_details": build_source_details(srcs),
        "trace": "Agentic Orchestration (Internal + Web)" if runtime.get("web_tool") else "RAG Execution"
    }
