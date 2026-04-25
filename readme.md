I will add the url and the screen contents and which resume i'm using.

i will paste them into a google form and click submit
app_entry_form


the app will grab that and get relevant info and append 
it to the app_tracker google sheet along with that day's date.



Deploy / local (from this repo’s root, i.e. the folder with `web_app` and `requirements.txt`):

- **Render (and similar):** Root Directory = empty (use repo root).  
  **Start command:** `gunicorn web_app.app:app -k uvicorn.workers.UvicornWorker` or `uvicorn web_app.app:app --host 0.0.0.0 --port 10000`  
  (Render’s package root is the clone, so the app is `web_app.app`, not `jobapp_tracker.web_app.app` — the package name in imports is `web_app` only.)
- `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000` (if you have a `main` module; this project’s app is `web_app.app`).

`uvicorn web_app.app:app`




Step	What you’re learning
Form / JSON
FastAPI turns HTTP into Python types (Form, Pydantic model, or raw dict).
LLM

One requests.post (or the official client) with a string prompt; you get a string (or JSON) back.
Sheet

Reuse your gspread client; append one row with whatever columns you need (e.g. timestamp, user text, LLM answer).
