# MentorFlow Backend

FastAPI backend for an educational programming assistant.

## Features

- Student-level middleware: Beginner, Intermediate, Advanced
- Conversation summary and context management
- LangChain response chain with any OpenAI-compatible chat endpoint
- Quiz generator
- Code generator
- GitHub repository review through GitHub API with fallback checklist
- Learning roadmap generator
- Bonus tools: YouTube search links and Context7 documentation search links

## Run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# then set OPENAI_API_KEY in ../.env
uvicorn app.main:app --reload --port 8000
```

The default `.env.example` is configured for Metis AI's OpenAI-compatible Grok
wrapper. Use the host that matches where the app is running:

```env
OPENAI_API_KEY=your_metis_api_key_here
MENTORFLOW_BASE_URL=https://api.metisai.ir/api/v1/wrapper/grok
MENTORFLOW_MODEL=grok-3-beta
```

For environments that are blocked by sanctioned providers, such as Colab or
Kaggle, use:

```env
MENTORFLOW_BASE_URL=https://api.tapsage.com/api/v1/wrapper/grok
```

If the key is not set or the provider rejects the request, MentorFlow uses a
local LangChain fallback chain so the tools still work during development.

## API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Generate a quiz about React Context API","level":"Beginner","session_id":"demo"}'
```
