from pydantic import BaseModel, HttpUrl

class UserInput(BaseModel):
    """Incoming job log: link + free-form text."""

    job_url: HttpUrl | None = None  # optional if sometimes there's no posting link
    job_text: str
    resume_choice: str | None = None