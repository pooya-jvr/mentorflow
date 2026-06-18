# MentorFlow

MentorFlow is an educational programming assistant with a FastAPI backend and a Next.js chat UI.

## Implemented Requirements

- Agent-style routing for quiz, code, GitHub review, learning roadmap and general tutoring
- LangChain-powered response layer with OpenAI-compatible provider support
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

The included `.env.example` is ready for Metis AI Grok. Use the host that
matches where the app runs:

```env
OPENAI_API_KEY=your_metis_api_key_here
MENTORFLOW_BASE_URL=https://api.metisai.ir/api/v1/wrapper/grok
MENTORFLOW_MODEL=grok-3-beta
```

For environments blocked by sanctioned providers, such as Colab or Kaggle:

```env
MENTORFLOW_BASE_URL=https://api.tapsage.com/api/v1/wrapper/grok
```

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
