def detect_tool(message: str) -> str:
    text = message.lower()

    if "youtube" in text or "video" in text or "find videos" in text:
        return "youtube_search"

    if "context7" in text or "latest documentation" in text or "latest docs" in text:
        return "context7_docs"

    if "quiz" in text or "test" in text or "کوییز" in text:
        return "quiz_generator"

    if "github.com" in text or "review repository" in text or "review this repository" in text:
        return "github_review"

    if "roadmap" in text or "learning path" in text or "مسیر یادگیری" in text:
        return "learning_roadmap"

    if "code" in text or "crud" in text or "example" in text or "کد" in text:
        return "code_generator"

    return "general_tutor"
