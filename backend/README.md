# MentorFlow Backend

FastAPI backend for an educational programming assistant.

## Features

- Student-level middleware: Beginner, Intermediate, Advanced
- Conversation summary and context management
- LangChain-first agent flow for routing, tool execution, and response generation
- OpenAI-compatible chat endpoint support through LangChain `ChatOpenAI`
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

The default `.env.example` is configured for Metis OpenAI wrapper. Use the host
that matches where the app is running:

```env
OPENAI_API_KEY=your_metis_api_key_here
MENTORFLOW_BASE_URL=https://api.metisai.ir/openai/v1
MENTORFLOW_MODEL=gpt-4o-mini
MENTORFLOW_REQUIRE_LLM=true
```

For environments that are blocked by sanctioned providers, such as Colab or
Kaggle, use:

```env
MENTORFLOW_BASE_URL=https://api.tapsage.com/openai/v1
```

If the key is not set or the provider rejects the request, MentorFlow uses a
local LangChain fallback chain only when `MENTORFLOW_REQUIRE_LLM=false`.
With the default `MENTORFLOW_REQUIRE_LLM=true`, provider errors are shown
instead of returning a canned answer.

## API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Generate a quiz about React Context API","level":"Beginner","session_id":"demo"}'
```
