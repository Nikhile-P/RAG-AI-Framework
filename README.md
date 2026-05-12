# Lenovo Research Workspace

A professional local document research workspace built for enterprise use cases. Ask anything about your internal documents, get real answers grounded in sources.

**Stack:**
- Frontend: Next.js 16 + React 18 + TypeScript
- Backend: FastAPI (Uvicorn)
- Local AI: Ollama (Qwen 2.5 3B)
- Vector DB: ChromaDB with semantic embeddings
- Authentication: OTP (Email/SMS)

## What this project does

- 📄 **Semantic search** - Searches your documents using vector embeddings, not just keywords
- 🔗 **Source grounding** - Answers cite exact documents and passages
- 🔐 **Secure sign-in** - OTP-based authentication (email or SMS)
- 📊 **Analytics dashboard** - Real-time platform metrics and adoption trends
- 🏥 **Health monitoring** - System telemetry, query counts, relevance scores
- 🌐 **Web fallback** - Automatically searches the web for external queries
- 🏠 **Fully local** - Runs completely offline with local Ollama model

## Features showcase

### Landing page
![Landing page](frontend/public/images/readme/home.png)
*Professional interface with one-click workspace access*

### Sign-in
![Sign-in page](frontend/public/images/readme/sign-in.png)
*Secure OTP authentication (email or phone)*

### Analytics dashboard
![Analytics](frontend/public/images/readme/analytics.png)
*Enterprise metrics: market data, adoption trends, productivity gains*

### Health & telemetry
![Health page](frontend/public/images/readme/health.png)
*Real-time system status and performance monitoring*

## Project structure

```text
.
├── backend/              # FastAPI API and query routing
├── frontend/             # Next.js web application
├── documents/            # Documents indexed for retrieval
├── setup/                # Ingestion and dataset prep scripts
├── vector_db/            # ChromaDB persisted index
├── archive/              # Older prototype code
├── tests/                # Saved response samples
└── .github/workflows/    # CI automation
```

## Prerequisites

Install these first:

1. Git
2. Python 3.10+
3. Node.js 20+ and npm
4. Ollama (https://ollama.com)

## Step-by-step setup (beginner friendly)

### 1. Clone the Repository
```bash
git clone https://github.com/Nikhile-P/Lenovo-Research-Workspace.git
cd Lenovo-Research-Workspace
```

### 2. Initialize the Python Virtual Environment
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Backend & Framework Dependencies
Install core runtime modules inside your virtual environment:
```bash
pip install -r backend/requirements.txt
pip install python-dotenv langchain-community langchain-text-splitters langchain-huggingface langchain-core langchain-chroma langchain-ollama langgraph langchain-tavily sentence-transformers pypdf python-docx openpyxl
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 5. Download the Core Inference Model
Pull the highly efficient quantised reasoning model to run offline directly via Ollama:
```bash
ollama pull qwen2.5:3b
```
*Note: Verify Ollama is actively running in the background before continuing.*

### 6. Environment Configuration
Create a `.env` file at the root of the project directory to override defaults or enable advanced fallbacks:

```env
# Optional: Enable live fallback to web intelligence for live dynamic metrics
TAVILY_API_KEY=tvly-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Set model targeting parameters
LOCAL_MODEL_NAME=qwen2.5:3b
ENABLE_WEB_FALLBACK=true

# Fine-tuning local retrieval configurations
RETRIEVER_K=5
RELEVANCE_THRESHOLD=0.68
```

### 7. Populate Document Knowledge Base
Deposit your enterprise target files (`.txt`, `.md`, `.pdf`, `.docx`, `.xlsx`, `.csv`, `.json`) inside the `documents/` folder. Build the initial embedding store by executing:
```bash
python setup/ingest.py
```
*This parses the contents, calculates localized semantic vectors, and writes them securely to the persistent `vector_db/` datastore.*

### 8. Launch the Integrated Microservices
Open two distinct terminal windows.

**Terminal 1 — Local Backend Proxy Engine:**
```bash
# Ensure your virtual environment is active!
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Next.js UI Frontend Server:**
```bash
cd frontend
npm run dev
```

Navigate to **[http://localhost:3000](http://localhost:3000)** in your browser to experience the completely functional production workspace!

---

## 🔒 Security & Privacy Notice
- **Zero Data Leakage**: By default, no file data or embeddings leave your local workspace network interface.
- **Credential Storage**: Keep all operational secrets inside local `.env` configuration scopes. The repository includes strict `.gitignore` rules to prevent unintended API key commits.

---

## 📝 License & Contributions
Distributed under the **MIT License**. See the `LICENSE` file for full terms and conditions. Contributions, improvements, and custom agent logic extensions are warmly welcomed via pull requests.
