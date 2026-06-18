"use client";

import { FormEvent, useMemo, useState } from "react";
import { BookOpen, Code2, Github, GraduationCap, Loader2, Map, Send, Video } from "lucide-react";

type Level = "Beginner" | "Intermediate" | "Advanced";

type StudentContext = {
  technologies: string[];
  current_roadmap?: string | null;
  studied_topics: string[];
};

type ChatResponse = {
  response: string;
  tool_used: string;
  level: Level;
  summary: string;
  context: StudentContext;
  metadata: Record<string, string>;
};

type Message = {
  role: "user" | "assistant";
  content: string;
  tool?: string;
  mode?: string;
};

const suggestions = [
  { icon: BookOpen, text: "Generate a quiz about React Context API" },
  { icon: Code2, text: "Generate a FastAPI CRUD example" },
  { icon: Github, text: "Review this repository: https://github.com/vercel/ai" },
  { icon: Map, text: "Create a roadmap for becoming a Backend Developer" },
  { icon: Video, text: "Find videos for FastAPI Authentication" },
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "سلام، من MentorFlow هستم. سطح خودت را انتخاب کن و درباره کوییز، کد، roadmap یا بررسی GitHub از من بپرس.",
      tool: "general_tutor",
    },
  ]);
  const [input, setInput] = useState("");
  const [level, setLevel] = useState<Level>("Beginner");
  const [context, setContext] = useState<StudentContext>({ technologies: [], studied_topics: [] });
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionId = useMemo(() => `mentorflow-${Date.now()}`, []);

  async function sendMessage(value = input) {
    const clean = value.trim();
    if (!clean || loading) return;

    setMessages((current) => [...current, { role: "user", content: clean }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: clean, level, session_id: sessionId, context }),
      });

      if (!res.ok) throw new Error("Backend request failed");
      const data = (await res.json()) as ChatResponse;
      setContext(data.context);
      setSummary(data.summary);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.response,
          tool: data.tool_used,
          mode: data.metadata?.mode,
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: "اتصال به backend برقرار نشد. مطمئن شوید FastAPI روی http://localhost:8000 اجرا شده است.",
          tool: "system",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    sendMessage();
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <GraduationCap size={28} />
          <div>
            <h1>MentorFlow</h1>
            <span>دستیار یادگیری برنامه‌نویسی</span>
          </div>
        </div>

        <div className="panel">
          <label>سطح دانشجو</label>
          <div className="segments">
            {(["Beginner", "Intermediate", "Advanced"] as Level[]).map((item) => (
              <button key={item} className={level === item ? "active" : ""} onClick={() => setLevel(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="panel">
          <label>Context</label>
          <div className="chips">
            {context.technologies.length ? context.technologies.map((tech) => <span key={tech}>{tech}</span>) : <span>هنوز تکنولوژی ثبت نشده</span>}
          </div>
          <p>{context.current_roadmap ? `Roadmap: ${context.current_roadmap}` : "Roadmap فعال مشخص نشده"}</p>
        </div>

        <div className="panel">
          <label>Summary</label>
          <p>{summary || "بعد از طولانی شدن مکالمه، خلاصه اینجا نمایش داده می‌شود."}</p>
        </div>
      </aside>

      <section className="chat">
        <div className="messages">
          {messages.map((message, index) => (
            <article key={index} className={`message ${message.role}`}>
              <div className="messageMeta">
                {message.role === "assistant" ? [message.tool, message.mode].filter(Boolean).join(" / ") : "You"}
              </div>
              <p>{message.content}</p>
            </article>
          ))}
          {loading && (
            <article className="message assistant loading">
              <Loader2 className="spin" size={18} />
              <span>در حال ساخت پاسخ آموزشی...</span>
            </article>
          )}
        </div>

        <div className="suggestions">
          {suggestions.map(({ icon: Icon, text }) => (
            <button key={text} onClick={() => sendMessage(text)} title={text}>
              <Icon size={18} />
              <span>{text}</span>
            </button>
          ))}
        </div>

        <form className="composer" onSubmit={onSubmit}>
          <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="مثلا: What is useEffect?" />
          <button type="submit" disabled={loading || !input.trim()} title="Send">
            <Send size={20} />
          </button>
        </form>
      </section>
    </main>
  );
}
