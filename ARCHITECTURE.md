# How it works

## Request flow

1. **You ask a question** → Frontend sends it to the backend
2. **Embed the query** → Convert the question into a vector for searching
3. **Search documents** → Find related passages in your document library
4. **Generate response** → Local model synthesizes an answer from the matches
5. **Return result** → Answer shown with sources and confidence level

## Components

**Frontend** (Next.js)
- Chat interface for asking questions
- Email/SMS OTP sign-in
- Live analytics and telemetry dashboards
- Dark/light theme

**Backend** (FastAPI)
- Receives questions and routes them to the right handler
- Searches the vector index
- Talks to Ollama for response generation
- Falls back to web search when documents don't have the answer
- Logs queries for analytics

**Search index** (ChromaDB)
- Stores vector embeddings of your documents
- Makes semantic search fast
- Updated when you run the ingestion script

**Inference** (Ollama + Qwen 2.5 3B)
- 3B parameter model that runs locally
- Fast enough for real-time use
- No API costs, no internet required for inference

## Routing logic

- **High confidence match** → Answer directly from your documents
- **Medium confidence** → Search further before answering
- **Low confidence** → Fall back to web search
- **Simple factual questions** → Answer directly without retrieval

## Tech stack

| Layer     | Technology                    |
|-----------|-------------------------------|
| Frontend  | Next.js · React · TypeScript · Tailwind |
| Backend   | Python · FastAPI              |
| Search    | ChromaDB · MiniLM-L6-v2       |
| Inference | Ollama · Qwen 2.5 3B          |
| Web       | Tavily API                    |
| Auth      | Email / SMS OTP               |
