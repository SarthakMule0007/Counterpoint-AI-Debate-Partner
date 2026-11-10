# Counterpoint — AI Debate Partner

A compact, browser-based debate practice app. Pick a question and your position, make an argument, and get an opposing response plus coaching. The scorecard covers claim clarity, evidence, reasoning, and engagement with counterarguments.

## Run locally

Requires Python 3.9 or newer. No Python packages are required.

```powershell
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Without credentials, the app uses a small local demo partner. Set an API key to enable generated debate responses:

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
python app.py
```

The server calls the OpenAI-compatible Chat Completions API. Set `OPENAI_BASE_URL` to use a compatible endpoint. API credentials stay server-side and are not sent to the browser. The app sends the debate question and conversation transcript to the configured model provider. Keep the server bound to localhost unless you have added appropriate access controls.

## What is included

- `app.py` — standard-library HTTP server, model API client, and local fallback.
- `index.html` — responsive chat interface, debate setup, scorecard, and prompt starters.
- `.env.example` — environment variable reference (copy values into your shell; the app does not load `.env` files).

The scorecard is formative feedback, not an objective measure of truth or a substitute for checking sources. The local fallback does not generate real model-based scores; use the Score round button with an API connection for transcript scoring.
