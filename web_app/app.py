import gunicorn
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, ValidationError
import os
from datetime import datetime
from jobapp_tracker.sheet import append_to_sheet
from jobapp_tracker.web_app.models import UserInput, JobExtraction
import json

app = FastAPI()

load_dotenv()


EXTRACTION_SYSTEM = """You extract structured fields from job postings.
Return ONLY valid JSON (no markdown, no prose) with exactly these keys:
- "job_title": string or null if not clearly stated
- "salary": string or null — copy compensation EXACTLY as written in the posting (range, hourly, etc.). If absent, null. Do not invent numbers.
- "job_summary": string — concise summary of the role. If the posting separates required vs nice-to-have qualifications, use two short labeled parts (e.g. "Required: ..." and "Nice to have: ..."). If it does not separate them, write one coherent summary; do not invent sections.
Base everything ONLY on the user's text."""



def extract_job_fields(job_text: str) -> JobExtraction:
    api_key = os.environ.get("OPENAI_API_KEY")  # example
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY")
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {
                    "role": "user",
                    "content": f"Job posting text:\n\n{job_text}",
                },
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"].strip()
    try:
        return JobExtraction.model_validate_json(raw)
    except ValidationError as e:
        # Fallback: try plain json.loads then validate (if model wraps oddly)
        return JobExtraction.model_validate(json.loads(raw))


# def call_llm(user_text: str) -> str:
#     """Replace with your provider (OpenAI, Anthropic, local Ollama, etc.)."""
#     api_key = os.environ.get("OPENAI_API_KEY")  # example
#     if not api_key:
#         return "[configure OPENAI_API_KEY]"
#     # Example: OpenAI chat completions — adjust model/URL for your stack
#     r = requests.post(
#         "https://api.openai.com/v1/chat/completions",
#         headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
#         json={
#             "model": "gpt-4o-mini",
#             "messages": [
#                 {"role": "system", "content": "Summarize the job in one line for a tracker row."},
#                 {"role": "user", "content": user_text},
#             ],
#         },
#         timeout=60,
#     )
#     r.raise_for_status()
#     data = r.json()
#     return data["choices"][0]["message"]["content"].strip()



@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/log-job")
def log_job(body: UserInput):
    summary = extract_job_fields(body.job_text)
    url_str = str(body.job_url) if body.job_url else ""
    resume = str(body.resume_choice) if body.resume_choice else ""
    append_to_sheet([datetime.now().isoformat(), url_str, resume, summary])
    # sheet.append_row([datetime.utcnow().isoformat(), body.text[:200], summary])
    return {"summary": summary, "ok": True}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
