def detect_tool(message: str) -> str:
    text = message.lower()

    if "quiz" in text or "test" in text:
        return "quiz_generator"

    if "github.com" in text or "review repository" in text or "review this repository" in text:
        return "github_review"

    if "roadmap" in text or "learning path" in text:
        return "learning_roadmap"

    if "code" in text or "crud" in text or "example" in text:
        return "code_generator"

    return "general_tutor"