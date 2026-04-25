Phase 1 — Wire up Jinja2 in FastAPI
Prompt: “In my FastAPI app, import Jinja2Templates from starlette.templating, point it at a templates/ folder next to app.py, and add a GET / route that returns TemplateResponse for index.html with request in the context dict. Show the minimal index.html that only displays a heading.”

Prompt: “Explain why Starlette/FastAPI template responses require {"request": request, ...} in the context, and what breaks if request is missing.”

Phase 2 — Templates, inheritance, and static files
Prompt: “Create base.html with {% block title %}, {% block content %}, and a simple nav. Make index.html use {% extends "base.html" %} and fill the blocks. Mount StaticFiles for a static/ directory and link a styles.css from base.html.”

Prompt: “Add a partial components/flash.html (or a small alert block) and include it with {% include %}. Pass an optional message from Python and use {% if message %} so the banner only shows when there is a message.”

Phase 3 — Pass data from Python (your domain)
Prompt: “On GET /, call create_tables() once at startup (lifespan or startup event) so the DB exists. On GET /jobs, load jobs with get_jobs(), pass them into a template as a list, and render a table. Note: fetchall() returns tuples — either document column order or switch the query to name columns and pass a list of dicts for clearer Jinja access.”

Prompt: “In the list template, loop with {% for job in jobs %}. Show created_at, job_title, salary, and a truncated job_summary using Jinja filters (e.g. | truncate(80)). Add a link column if you store job_url.”

Phase 4 — Form: HTML → server (Jinja’s main job)
Your API today uses JSON on POST /log-job. For Jinja practice you usually want an HTML form that posts to a route that accepts form fields, not raw JSON.

Prompt: “Add a GET /log route that renders log_job.html with a form: optional job_url, required job_text (textarea), optional resume_choice. Use correct name attributes matching what FastAPI will read with Form().”

Prompt: “Add POST /log (or POST /log-job as form) that uses Form(...) parameters for job_text, optional job_url, optional resume_choice. Convert empty job_url to None; if present, validate or cast to HttpUrl like the Pydantic model. Reuse the same extract_job_fields + add_job logic as the JSON endpoint, then redirect with RedirectResponse to /jobs or back to /log with a success message in the query string or flash pattern.”

Prompt: “Optionally keep POST /log-job as JSON for API clients, and POST /log for browser forms — factor shared logic into one function so you don’t duplicate the LLM + DB code.”

Phase 5 — Errors, UX, and Jinja conditionals
Prompt: “If validation fails (empty job_text, bad URL), re-render log_job.html with error and old_values pre-filled in the inputs using value="{{ old_url or '' }}" and textarea body. In Jinja, use {% if error %} to show the error near the form.”

Prompt: “Add a GET /health link in the footer of base.html only in development (pass debug=True in context from an env var) using {% if debug %}.”

Phase 6 — Jinja features worth one exercise each
Prompt: “Use a Jinja macro for a form field row (label + input + error slot) in macros/forms.html and {% import %} it into log_job.html.”

Prompt: “Add a simple | default('—') for missing salary or job_title in the jobs table.”

Order of operations (suggested)
Order	What you practice
1–2
TemplateResponse, request, folder layout
3–4
extends, block, include, static CSS
5–6
Loops, filters, real data from get_jobs
7–9
HTML form + Form() + redirect vs JSON API
10–13
Errors, macros, defaults, small polish
One design note for your project
UserInput uses HttpUrl | None for job_url. Browser forms send strings. Your form-handling route should treat “empty string” as None and validate URL format before calling the same pipeline as log_job. That’s a good, small learning exercise in both FastAPI and Jinja (re-display bad input).

If you want this implemented in the repo for you, switch to Agent mode and say whic