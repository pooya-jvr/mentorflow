from __future__ import annotations

import re
from typing import Dict
from urllib.parse import quote_plus

import httpx

from app.schemas.chat import StudentContext


LEVEL_STYLE = {
    "Beginner": "با زبان ساده، مثال ملموس، قدم هاي کوچک و بدون فرض دانش قبلي.",
    "Intermediate": "با تمرکز بر الگوها، trade-off ها، تمرين عملي و اصطلاحات فني متعادل.",
    "Advanced": "با جزئيات معماري، edge case ها، lifecycle، performance و نکات production.",
}


def generate_quiz(topic: str, level: str, context: StudentContext) -> str:
    difficulty = {
        "Beginner": "مفهومي و کوتاه",
        "Intermediate": "ترکيبي از مفهوم و کدنویسی",
        "Advanced": "سناريو محور و شامل بهينه سازي",
    }[level]
    return f"""کوییز {difficulty} درباره {topic}

1. {topic} چه مسئله‌ای را حل می‌کند؟
2. یک مثال واقعی بنویسید که در آن استفاده از {topic} مناسب باشد.
3. خروجی یا رفتار این قطعه کد را توضیح دهید:

```ts
const value = createLearningStep("{topic}");
console.log(value.nextAction);
```

4. یک اشتباه رایج هنگام کار با {topic} چیست؟
5. تمرین عملی: یک نمونه کوچک بسازید و دلیل انتخاب‌های خود را در 3 جمله توضیح دهید.

پاسخ‌ها را با سطح {level} می‌سنجم: {LEVEL_STYLE[level]}"""


def generate_code(topic: str, level: str, context: StudentContext) -> str:
    if "fastapi" in topic.lower() or "crud" in topic.lower():
        detail = "Dependency Injection و validation" if level != "Beginner" else "ساختار ساده و قابل خواندن"
        return f"""نمونه FastAPI CRUD با تمرکز بر {detail}

```py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
items = {{}}

class Item(BaseModel):
    title: str
    done: bool = False

@app.post("/items/{{item_id}}")
def create_item(item_id: int, item: Item):
    items[item_id] = item
    return item

@app.get("/items/{{item_id}}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

@app.put("/items/{{item_id}}")
def update_item(item_id: int, item: Item):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    items[item_id] = item
    return item

@app.delete("/items/{{item_id}}")
def delete_item(item_id: int):
    items.pop(item_id, None)
    return {{"deleted": True}}
```

گام بعدی: برای production، دیتابیس، migration و تست endpoint ها را اضافه کنید."""

    return f"""نمونه آموزشی برای {topic}

```ts
type LearningStep = {{
  topic: string;
  goal: string;
  exercise: string;
}};

const step: LearningStep = {{
  topic: "{topic}",
  goal: "درک کاربرد اصلی و ساخت یک نمونه کوچک",
  exercise: "یک مثال بساز و سپس یک محدودیت آن را توضیح بده",
}};

console.log(step);
```

برای سطح {level}: {LEVEL_STYLE[level]}"""


async def review_github_repository(message: str, level: str) -> tuple[str, Dict[str, str]]:
    url = extract_github_url(message)
    if not url:
        return "لطفا لینک repository GitHub را بفرستید تا بتوانم ساختار، README و فایل‌های اصلی را بررسی کنم.", {}

    owner_repo = parse_owner_repo(url)
    metadata = {"repository": owner_repo}
    api_url = f"https://api.github.com/repos/{owner_repo}"

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            repo = (await client.get(api_url)).json()
            contents = (await client.get(f"{api_url}/contents")).json()
    except httpx.HTTPError:
        return fallback_github_review(owner_repo, level), metadata

    if not isinstance(repo, dict) or "full_name" not in repo:
        return fallback_github_review(owner_repo, level), metadata

    files = [item.get("name", "") for item in contents if isinstance(item, dict)]
    readme_score = "README.md" in files or "readme.md" in [f.lower() for f in files]
    tests = any("test" in f.lower() for f in files)
    docker = any(f.lower().startswith("docker") for f in files)

    response = f"""بررسی repository: {repo.get("full_name")}

نقاط قوت:
- زبان اصلی: {repo.get("language") or "نامشخص"}
- ستاره‌ها: {repo.get("stargazers_count", 0)}
- توضیح پروژه: {repo.get("description") or "توضیحی ثبت نشده است"}

بازخورد فنی:
- README: {"موجود است" if readme_score else "بهتر است README کامل اضافه شود"}
- تست‌ها: {"نشانه‌هایی از تست در ریشه دیده شد" if tests else "پیشنهاد می‌شود پوشه tests یا تست‌های CI اضافه شود"}
- اجرا و استقرار: {"Docker دیده شد" if docker else "Dockerfile یا راهنمای اجرا می‌تواند پروژه را حرفه‌ای‌تر کند"}

پیشنهادهای سطح {level}:
- ساختار پوشه‌ها را در README توضیح دهید.
- یک مسیر نصب، اجرای local و اجرای تست‌ها اضافه کنید.
- برای هر feature مهم، حداقل یک تست رفتاری بنویسید."""
    return response, metadata


def create_learning_roadmap(topic: str, level: str, context: StudentContext) -> str:
    known = ", ".join(context.technologies) or "هنوز مشخص نشده"
    depth = {
        "Beginner": "با پروژه‌های کوچک و مفاهیم پایه شروع کن.",
        "Intermediate": "روی معماری، تست و integration تمرکز کن.",
        "Advanced": "روی scaling، observability و تصمیم‌های production تمرکز کن.",
    }[level]
    return f"""مسیر یادگیری شخصی‌سازی‌شده برای {topic}

وضعیت فعلی: سطح {level}، تکنولوژی‌های مورد علاقه: {known}

هفته 1: مبانی و واژگان اصلی
- مفاهیم پایه {topic}
- ساخت 2 تمرین کوچک

هفته 2: پیاده‌سازی عملی
- ساخت یک پروژه mini
- نوشتن تست برای مسیرهای اصلی

هفته 3: ابزارها و best practice
- بررسی مستندات رسمی
- refactor و بهبود ساختار پروژه

هفته 4: پروژه نهایی
- طراحی یک پروژه قابل نمایش در GitHub
- README، demo و checklist کیفیت

راهنمای سطح شما: {depth}"""


def find_youtube_videos(topic: str, level: str) -> str:
    query = quote_plus(f"{topic} tutorial {level}")
    return f"""برای ویدئوهای آموزشی {topic} این مسیرها را پیشنهاد می‌کنم:

- جستجوی YouTube: https://www.youtube.com/results?search_query={query}
- اولویت انتخاب: ویدئوهای جدیدتر، پروژه‌محور، دارای repository و فصل‌بندی شده
- تمرین بعد از دیدن ویدئو: یک نمونه کوچک بسازید و 3 نکته یادگرفته‌شده را بنویسید."""


def context7_docs(topic: str) -> str:
    query = quote_plus(topic)
    return f"""برای مستندات به‌روز {topic}:

- Context7: https://context7.com/search?q={query}
- مستندات رسمی را با مثال local مقایسه کنید.
- هنگام استفاده، نسخه package و تاریخ مستندات را یادداشت کنید."""


def general_tutor(topic: str, level: str, context: StudentContext) -> str:
    if level == "Advanced":
        return f"""{topic}

در سطح پیشرفته، بهتر است آن را از زاویه چرخه اجرا، محدودیت‌ها و اثرش روی معماری ببینیم. اول مسئله‌ای را که حل می‌کند مشخص کنید، بعد هزینه‌هایش را بسنجید: performance، خوانایی، testability و رفتار در edge case ها.

تمرین: یک مثال واقعی از پروژه خودتان انتخاب کنید و توضیح دهید چرا این ابزار از جایگزین‌هایش مناسب‌تر است."""
    if level == "Intermediate":
        return f"""{topic}

این مفهوم را به عنوان یک ابزار حل مسئله ببینید. کاربرد اصلی، مثال عملی، و اشتباهات رایج را کنار هم یاد بگیرید تا فقط تعریف حفظ نکنید.

تمرین: یک مثال کوچک بسازید، سپس آن را refactor کنید و دلیل refactor را بنویسید."""
    return f"""{topic}

توضیح ساده: این موضوع یک ابزار یا مفهوم است که کمک می‌کند برنامه‌تان منظم‌تر و قابل کنترل‌تر شود. بهترین راه یادگیری این است که یک مثال خیلی کوچک بسازید و فقط روی یک ایده تمرکز کنید.

تمرین: یک نمونه 10 خطی بسازید و با کلمات خودتان بگویید هر خط چه کاری انجام می‌دهد."""


def fallback_github_review(owner_repo: str, level: str) -> str:
    return f"""به GitHub API وصل نشدم، اما این checklist بررسی برای {owner_repo} آماده است:

- README شامل هدف پروژه، نصب، اجرا، تست و اسکرین‌شات باشد.
- ساختار پوشه‌ها روشن و قابل حدس باشد.
- فایل‌های env نمونه مثل .env.example اضافه شوند.
- تست و CI برای مسیرهای اصلی وجود داشته باشد.
- issue ها و commit message ها قابل پیگیری باشند.

برای سطح {level}، بعد از رفع موارد بالا سراغ معماری، security و performance بروید."""


def extract_github_url(message: str) -> str:
    match = re.search(r"https?://github\.com/[\w.-]+/[\w.-]+", message)
    return match.group(0) if match else ""


def parse_owner_repo(url: str) -> str:
    parts = url.rstrip("/").split("github.com/")[-1].split("/")
    return "/".join(parts[:2])
