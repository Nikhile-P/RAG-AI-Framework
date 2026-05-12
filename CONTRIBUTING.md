# Contributing

## Getting started

Clone the repo and set up locally:

```bash
git clone <your-repo-url>
cd lenovo-research-workspace
```

### Backend
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

### Environment setup
Create a `.env` file at the root with your API keys:
```
TAVILY_API_KEY=tvly-...
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

## Running locally

**Terminal 1:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2:**
```bash
cd frontend
npm run dev
```

Then open http://localhost:3000

## Making changes

- Keep commits clear and focused
- Write descriptive commit messages
- Test locally before pushing
- Run `npm run lint` in frontend before committing

## Adding documents

1. Drop files in `documents/`
2. Run `python setup/ingest.py`
3. Restart the backend to see changes

## Questions or issues?

Feel free to open an issue or PR with details about what you're trying to do.
