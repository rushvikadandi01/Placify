# Placement Copilot

FastAPI backend foundation for a placement preparation assistant. The API supports student profiles and an AI placement chat endpoint, backed by SQLite.

## Setup

From the project root, install dependencies into your active Python environment:

```powershell
python -m pip install -r requirements.txt
```

The local `.env` sets `DATABASE_URL` for SQLite. To enable LLM responses, copy `.env.example` to `.env` and set `AI_PROVIDER`, `AI_API_KEY`, and `AI_MODEL`. The provider currently uses an OpenAI-compatible chat completions API; set `AI_BASE_URL` when using a compatible provider with a different endpoint. Never put API keys in source files or commit `.env`. Without AI credentials, `/chat` still classifies requests and returns a setup notice.

## Run

```powershell
uvicorn backend.main:app --reload
```

The interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## Test the API

Check the root endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

Create a student profile:

```powershell
$body = @{
    name = "Asha"
    target_role = "Software Engineer"
    programming_language = "Python"
    experience_level = "Beginner"
    hours_per_day = 2
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8000/student `
    -Method Post -ContentType "application/json" -Body $body
```

The student endpoint returns a success message and the created `student_id`.

Send a placement-assistant request:

```powershell
$body = @{ message = "Explain HashMap in Java" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/chat `
    -Method Post -ContentType "application/json" -Body $body
```

The response includes the assistant reply, detected intent, and an optional `conversation_id` echoed from the request.