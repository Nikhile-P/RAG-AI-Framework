import os
import ast
import sys
import asyncio
import random
import traceback
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# Ensure the current directory (backend) is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
app = FastAPI(title="Lenovo Research Workspace API", version="1.0")

# Wildcard origin cannot be combined with credentials per CORS spec; Next.js rewrites are same-origin for /api.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared Directories
DATA_DIR = os.path.join(BASE_DIR, "documents")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(BASE_DIR, "router.log")

# ── OTP store ─────────────────────────────────────────────────────────────────
# In-memory dict keyed by lowercased email/phone → {code, expires, mode}
_otp_store: dict[str, dict] = {}

def _gen_code() -> str:
    return str(random.randint(100000, 999999))

def _send_email(to: str, code: str) -> bool:
    user = os.getenv("GMAIL_USER", "")
    pwd  = os.getenv("GMAIL_APP_PASSWORD", "")
    if not user or not pwd:
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your access code"
        msg["From"]    = user
        msg["To"]      = to
        body = (
            f"<p style='font-family:sans-serif;font-size:28px;letter-spacing:6px;"
            f"font-weight:700;color:#1a1a1a'>{code}</p>"
            f"<p style='font-family:sans-serif;font-size:13px;color:#888'>"
            f"Expires in 10 minutes. Only works once.</p>"
        )
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(user, pwd)
            s.sendmail(user, to, msg.as_string())
        return True
    except Exception as e:
        print(f"[OTP] Email send failed: {e}")
        return False

def _send_sms(phone: str, code: str) -> bool:
    sid   = os.getenv("TWILIO_SID", "")
    token = os.getenv("TWILIO_TOKEN", "")
    frm   = os.getenv("TWILIO_FROM", "")
    if not (sid and token and frm):
        return False
    try:
        from twilio.rest import Client
        Client(sid, token).messages.create(
            body=f"Your access code: {code} (expires in 10 min)",
            from_=frm, to=phone,
        )
        return True
    except Exception as e:
        print(f"[OTP] SMS send failed: {e}")
        return False

# ==========================================
# 2. MODELS
# ==========================================
class ChatRequest(BaseModel):
    message: str
    chat_history: List[dict] = []

class OtpRequest(BaseModel):
    identifier: str      # email address or phone number
    mode: str = "email"  # "email" or "phone"

class VerifyRequest(BaseModel):
    identifier: str
    code: str

# ==========================================
# 3. ENDPOINTS
# ==========================================

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.get("/api/telemetry")
def get_telemetry():
    """Returns the parsed router.log data for the health dashboard."""
    total_queries = 0
    avg_relevance = 0.0
    logs = []
    
    # Default stats if file is empty or missing
    routing_counts = {"Turbo RAG": 0, "Deep Agent": 0, "Web Search": 0, "Direct Answer": 0}
    confidence_counts = {"High (0.8+)": 0, "Medium (0.5-0.8)": 0, "Low (<0.5)": 0}
    file_count = 0
    
    try:
        if os.path.exists(DATA_DIR):
            file_count = len([f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))])
            
        if os.path.exists(LOG_FILE):
            import collections
            with open(LOG_FILE, 'rb') as f:
                # Efficiently read last 1000 lines
                f.seek(0, os.SEEK_END)
                size = f.tell()
                f.seek(max(0, size - 1024 * 100), os.SEEK_SET) # last 100KB
                chunk = f.read().decode('utf-8', errors='ignore')
                lines = chunk.splitlines()[-1000:]
            
            total_queries = len(lines)
            relevances = []
            latencies = []
            confidences = []
            
            for line in lines:
                try:
                    entry = ast.literal_eval(line)
                    if isinstance(entry, dict):
                        logs.append(entry)
                        
                        # Accuracy/Relevance
                        rel = entry.get('details', {}).get('confidence', 0)
                        if rel == "High": relevances.append(0.95)
                        elif rel == "Medium": relevances.append(0.65)
                        elif rel == "Low": relevances.append(0.30)
                        
                        # Latency
                        lat = entry.get('latency', 0)
                        if lat: latencies.append(lat)
                        
                        # Confidence
                        if rel == "High": confidences.append(0.92)
                        elif rel == "Medium": confidences.append(0.68)
                        elif rel == "Low": confidences.append(0.35)
                except Exception:
                    continue
            
            avg_relevance = sum(relevances) / len(relevances) if relevances else 0.0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            for entry in logs:
                route = entry.get("path", "")
                if route in routing_counts:
                    routing_counts[route] += 1
                elif "Agent" in route:
                    routing_counts["Deep Agent"] += 1
                elif "Search" in route:
                    routing_counts["Web Search"] += 1
                    
                # Map string or float confidence to counts
                raw_conf = entry.get("details", {}).get("confidence") or entry.get("details", {}).get("relevance", 0)
                if isinstance(raw_conf, str):
                    if raw_conf == "High": confidence_counts["High (0.8+)"] += 1
                    elif raw_conf == "Medium": confidence_counts["Medium (0.5-0.8)"] += 1
                    else: confidence_counts["Low (<0.5)"] += 1
                else:
                    try:
                        conf = float(raw_conf)
                        if conf >= 0.76: confidence_counts["High (0.8+)"] += 1
                        elif conf >= 0.5: confidence_counts["Medium (0.5-0.8)"] += 1
                        else: confidence_counts["Low (<0.5)"] += 1
                    except (ValueError, TypeError):
                        confidence_counts["Medium (0.5-0.8)"] += 1

        return {
            "total_queries": total_queries,
            "avg_relevance": avg_relevance,
            "avg_latency": f"{avg_latency:.2f}s",
            "avg_confidence": f"{avg_confidence*100:.1f}%",
            "context_param": f"{file_count * 10} tokens",
            "file_count": file_count,
            "routing": routing_counts,
            "confidence_stats": confidence_counts,
            "recent_logs": logs[-15:] # Return last 15 logs
        }
    except Exception as e:
        # Return fallback instead of 500 error
        return {
            "total_queries": 0,
            "avg_relevance": 0.0,
            "file_count": 0,
            "routing_counts": routing_counts,
            "confidence_counts": confidence_counts,
            "recent_logs": [],
            "error": str(e)
        }

@app.post("/api/send-otp")
def send_otp(req: OtpRequest):
    identifier = req.identifier.strip().lower()
    if not identifier:
        raise HTTPException(400, "Email or phone number required.")

    code = _gen_code()
    _otp_store[identifier] = {
        "code":    code,
        "expires": datetime.now() + timedelta(minutes=10),
        "mode":    req.mode,
    }

    sent = False
    if req.mode == "email":
        sent = _send_email(identifier, code)
    elif req.mode == "phone":
        sent = _send_sms(identifier, code)

    # Always print so the developer can see it in uvicorn logs
    print(f"[OTP] {req.mode.upper()} → {identifier} : {code}")

    return {
        "ok":       True,
        "sent":     sent,
        # Return code directly when no delivery service is configured (dev mode)
        "dev_code": code if not sent else None,
    }


@app.post("/api/verify-otp")
def verify_otp(req: VerifyRequest):
    identifier = req.identifier.strip().lower()
    code       = req.code.strip()

    entry = _otp_store.get(identifier)
    if not entry:
        raise HTTPException(400, "No code found for this address — request a new one.")
    if datetime.now() > entry["expires"]:
        del _otp_store[identifier]
        raise HTTPException(400, "Code expired — request a new one.")
    if entry["code"] != code:
        raise HTTPException(400, "Wrong code — try again.")

    del _otp_store[identifier]
    return {"ok": True}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads a file to the data directory."""
    try:
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # We will add chunking logic here later
        return {"filename": file.filename, "status": "Uploaded successfully", "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Chat endpoint backed by LangGraph."""
    try:
        from agent import route_answer

        payload = req.chat_history + [{"role": "user", "content": req.message}]
        # Heavy sync work (vector DB + LLM): avoid blocking the asyncio event loop
        result = await asyncio.to_thread(route_answer, payload)
        return result
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[Chat] ERROR:\n{tb}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n\n{tb}")

@app.on_event("startup")
async def startup_event():
    """Pre-initialize agent and vector store to avoid cold-start latency."""
    print("[Server] Pre-initializing research agent...")
    try:
        from agent import initialize_agent
        asyncio.create_task(asyncio.to_thread(initialize_agent))
    except Exception as e:
        print(f"[Server] Startup init warning: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)