from datetime import datetime
import logging
import os
import json
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ValidationError
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from .models import JobExtraction, JobInfo, UserInput
from .db import add_job, create_tables, del_job, get_jobs


_BASE_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _BASE_DIR / "templates"
_STATIC_DIR = _BASE_DIR / "static"



logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI()

load_dotenv()

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

EXTRACTION_SYSTEM = """You extract structured fields from job postings.
Return ONLY valid JSON (no markdown, no prose) with exactly these keys:
- "job_title": string or null if not clearly stated
- "salary": string or null — copy compensation EXACTLY as written in the posting (range, hourly, etc.). If absent, null. Do not invent numbers.
- "job_summary": string — summary of the role. If the posting separates required vs nice-to-have qualifications, use two labeled parts (e.g. "Required: ..." and "Nice to have: ..."). If it does not separate them, use bullet points; do not invent section labels.
Base all role facts (title, comp, requirements, stack) ONLY on the job posting text."""


def _build_extraction_user_message(job_text: str, resume_choice: str | None) -> str:
    parts = [f"Job posting text:\n\n{job_text}"]
    r = (resume_choice or "").strip()
    if r:
        parts.append(
            f"\n\nResume label for this application (for optional fit line only, no file attached): {r}"
        )
    return "".join(parts)


def persist_job_from_user_input(body: UserInput) -> str:
    """Validate business rules, extract fields, save. Returns the summary string."""
    if not (body.job_text or "").strip():
        raise ValueError("job_text cannot be empty")

    extraction_data = extract_job_fields(
        body.job_text,
        resume_choice=body.resume_choice,
    )
    summary = extraction_data.job_summary
    salary = extraction_data.salary
    title = extraction_data.job_title

    url_str = str(body.job_url) if body.job_url else ""
    resume = str(body.resume_choice) if body.resume_choice else ""

    job_to_add = JobInfo(
        datetime.now().isoformat(),
        body.job_text,
        url_str,
        resume,
        title,
        salary,
        summary,
    )
    add_job(job_to_add)
    return summary or ""

def _form_empty(s: str | None) -> str | None:
    t = (s or "").strip()
    return t if t else None


def extract_job_fields(
    job_text: str,
    resume_choice: str | None = None,
) -> JobExtraction:
    api_key = os.environ.get("OPENAI_API_KEY")  # example
    if not api_key:
        logger.error("OPENAI_API_KEY is not set")
        raise HTTPException(
            status_code=503,
            detail="Extraction is not configured on this server",
        )

    try:
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
                        "content": _build_extraction_user_message(job_text, resume_choice),
                    },
                ],
            },
            timeout=120,
        )
        r.raise_for_status()

    except requests.Timeout:
        logger.exception("OpenAI request timed out")
        raise HTTPException(
            status_code=503,
            detail="Extraction service timed out; try again later",
        )
    except requests.RequestException:
        logger.exception("OpenAI request failed")
        raise HTTPException(
            status_code=502,
            detail="Extraction service returned an error",
        )

    raw = r.json()["choices"][0]["message"]["content"].strip()
    try:
        return JobExtraction.model_validate_json(raw)
    except ValidationError:
        try:
            data = json.loads(raw)
            return JobExtraction.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.exception("LLM returned JSON we could not parse into JobExtraction")
            raise HTTPException(
                status_code=502,
                detail="Could not read structured fields from the model response.",
            ) from e

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/log-job")
def log_job_api(body: UserInput):
    try:
        summary = persist_job_from_user_input(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"summary": summary, "ok": True}


@app.get("/log")
def get_log_page(request: Request):
    return templates.TemplateResponse(
        request,
        "log_job.html",
        {
            "error": None,
            "old_url": "",
            "old_text": "",
            "old_resume": "",
        },
    )

@app.post("/log")
def post_log_page(
    request: Request,
    job_text: str = Form(""),
    job_url: str = Form(""),
    resume_choice: str = Form(""),
):
    # Build UserInput (Pydantic validates URL shape when non-empty)
    try:
        body = UserInput(
            job_text=job_text,
            job_url=_form_empty(job_url),
            resume_choice=_form_empty(resume_choice),
        )
    except ValidationError:
        return templates.TemplateResponse(
            request,
            "log_job.html",
            {
                "error": "Invalid input (e.g. Job URL must be a valid http(s) link).",
                "old_url": job_url,
                "old_text": job_text,
                "old_resume": resume_choice,
            },
            status_code=422,
        )


    def _log_form_error(message: str, status_code: int) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "log_job.html",
            {
                "error": message,
                "old_url": job_url,
                "old_text": job_text,
                "old_resume": resume_choice,
            },
            status_code=status_code,
        )

    try:
        persist_job_from_user_input(body)
    except ValueError as e:
        return _log_form_error(str(e), 400)
    except HTTPException as e:
        detail = e.detail
        if isinstance(detail, list):
            detail = "; ".join(str(x) for x in detail)
        elif not isinstance(detail, str):
            detail = str(detail)
        return _log_form_error(detail or "Something went wrong.", e.status_code)
    return RedirectResponse(url="/jobs", status_code=303)



@app.post("/jobs/{job_id}/delete")
def delete_job_row(job_id: int) -> RedirectResponse:
    create_tables()
    n = del_job(job_id)
    if n == 0:
        raise HTTPException(status_code=404, detail="No application with that id.")
    return RedirectResponse(url="/jobs", status_code=303)


@app.get("/jobs")
def index(request: Request):
    create_tables()
    jobs = get_jobs()
    return templates.TemplateResponse(
        request,
        "jobs.html",
        {"jobs": jobs, "messages": []},
    )


