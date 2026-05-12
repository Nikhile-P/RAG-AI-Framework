# How it works

## The basic flow

1. **You ask a question** → Frontend sends it to the backend
2. **Convert to embedding** → Turn your question into a searchable vector
3. **Search documents** → Find related files in your document library
4. **Get LLM response** → Use the local model to synthesize an answer
5. **Show result** → Display answer with sources and confidence

## The pieces

**Frontend** (Next.js)
- Chat interface where you type questions
- Login with email/SMS code
- Live dashboard showing what's happening
- Dark/light theme toggle

**Backend** (FastAPI)
- Receives messages and routes them
- Searches the vector database
- Talks to Ollama for AI responses
- Falls back to web search if documents don't have the answer
- Logs everything for analytics

**Data** (ChromaDB)
- Stores embeddings of all your documents
- Makes searching fast
- Automatically updated when you add files

**AI Model** (Ollama + Qwen 2.5)
- Small 3B model that runs locally
- Fast enough for real-time chat
- No API costs or internet required

## How queries get routed

- **High confidence match** → Answer from your documents
- **Medium confidence** → Do additional searching or reasoning
- **Low confidence** → Fall back to web search for current info
- **Simple questions** → Just answer directly

## Stack summary

- Frontend: Next.js, React, TypeScript, Tailwind
- Backend: Python, FastAPI
- Search: ChromaDB
- Model: Ollama (Qwen 2.5 3B)
- Web: Tavily API (for live search)
- Auth: Email/SMS OTP codes
