# MentorFlow

MentorFlow is an educational programming assistant with a FastAPI backend and a Next.js chat UI.

## Implemented Requirements

- LangChain-first agent flow for routing, tool execution, and response generation
- OpenAI-compatible provider support through LangChain `ChatOpenAI`
- Student level middleware for Beginner, Intermediate and Advanced responses
- Conversation summary middleware after long conversations
- Context management for student level, technologies, current roadmap and studied topics
- GitHub review through GitHub API with offline fallback
- Bonus YouTube search and Context7 documentation tools
- Professional chat interface with level controls, context panel and prompt shortcuts

## Run Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# set OPENAI_API_KEY, MENTORFLOW_BASE_URL and MENTORFLOW_MODEL in ../.env
uvicorn app.main:app --reload --port 8000
```

The included `.env.example` is ready for Metis OpenAI wrapper. Use the host that
matches where the app runs:

```env
OPENAI_API_KEY=your_metis_api_key_here
MENTORFLOW_BASE_URL=https://api.metisai.ir/openai/v1
MENTORFLOW_MODEL=gpt-4o-mini
MENTORFLOW_REQUIRE_LLM=true
MENTORFLOW_LLM_ROUTER=false
```

For environments blocked by sanctioned providers, such as Colab or Kaggle:

```env
MENTORFLOW_BASE_URL=https://api.tapsage.com/openai/v1
```

`MENTORFLOW_REQUIRE_LLM=true` prevents silent template fallback when a provider
key is configured. If the AI provider has no credit, rejects the model, or is
unreachable, the API returns a clear provider error instead of a canned answer.
`MENTORFLOW_LLM_ROUTER=false` is recommended for Metis direct wrappers because
the docs note that direct model connections do not expose the full platform
features such as function calling. The final answer still comes from the LLM.

## Run Frontend

Requires Node.js 18.18 or newer.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Demo Prompts

- `Generate a quiz about React Context API`
- `Generate a FastAPI CRUD example`
- `Review this repository: https://github.com/vercel/ai`
- `Create a roadmap for becoming a Backend Developer`
- `Find videos for FastAPI Authentication`
- `Latest documentation for LangChain`

## Project Delivery Notes

For final submission, publish this folder to GitHub and record a short screen capture showing the chat UI, student level switcher, quiz generation, code generation, GitHub review and roadmap creation.
