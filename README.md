# Backend — Weather Voice Agent Webhook

FastAPI service that handles weather lookups and coat-reminder SMS for the **Retell AI** voice agent. It implements the same logic as the importable n8n workflow in `n8n-weather-workflow.json`.

Use this backend when you want a self-hosted webhook instead of n8n Cloud, or when developing and testing the weather/SMS logic locally.

---

## How It Works

### Call flow

```
Caller dials Retell number
        │
        ▼
Retell voice agent (STT + LLM + TTS)
        │
        │  LLM calls custom function check_weather(city)
        ▼
POST /webhook/weather-check  ← this backend (or n8n)
        │
        ├──► OpenWeatherMap API  (current temp + conditions)
        │
        ├──► IF temp < COLD_THRESHOLD_F (default 50°F)
        │         AND caller phone in payload
        │         AND Twilio configured
        │         └──► Twilio SMS coat reminder to caller
        │
        └──► JSON response with spoken "message" field
                    │
                    ▼
             Retell reads message to caller
```

Retell owns the voice conversation. This backend only runs when the agent invokes the `check_weather` function — it does not handle audio or telephony directly.

### Cold-weather logic

1. Extract `city` from the Retell payload (`args.city`).
2. Fetch weather from OpenWeatherMap (imperial units).
3. Compare temperature to `COLD_THRESHOLD_F` (default 50°F).
4. Build a natural-language `message` for Retell to speak.
5. If cold **and** the payload includes the caller's phone (`call.from_number`), send an SMS via Twilio.
6. Return JSON including `temperature_f`, `description`, `city`, `is_cold`, and `message`.

Web calls in Retell have no phone number — the voice response still mentions bringing a coat, but SMS is skipped.

### n8n alternative

The same webhook contract is available as an n8n workflow. Import `n8n-weather-workflow.json` into n8n Cloud and point Retell at the n8n production webhook URL instead of this server.

| Approach | Pros |
|----------|------|
| **n8n Cloud** | No code to deploy; visual workflow editor |
| **This FastAPI backend** | Local dev, unit tests, Docker, full control |

Both paths use identical request/response shapes. See [`../docs/retell-agent-config.md`](../docs/retell-agent-config.md) for Retell agent setup.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, route registration
│   ├── config.py            # Settings from .env (Pydantic)
│   ├── models/
│   │   └── weather.py       # WeatherResponse schema
│   ├── routers/
│   │   ├── health.py        # GET /api/health
│   │   └── weather.py       # POST /webhook/weather-check
│   └── services/
│       ├── weather.py       # OpenWeatherMap fetch + message builder
│       ├── sms.py           # Twilio coat-reminder SMS
│       └── retell.py        # Extract city + caller phone from payload
├── tests/
│   ├── test_weather.py
│   └── test_webhook.py
├── n8n-weather-workflow.json
├── docker-compose.yml       # API + n8n for local stack
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Setup

### Local development

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # fill in API keys
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENWEATHER_API_KEY` | Yes | OpenWeatherMap API key |
| `COLD_THRESHOLD_F` | No | Cold threshold in °F (default `50`) |
| `TWILIO_ACCOUNT_SID` | For SMS | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | For SMS | Twilio auth token |
| `TWILIO_FROM_NUMBER` | For SMS | Twilio sender number (E.164) |
| `CORS_ORIGINS` | No | JSON list of allowed origins (default `["http://localhost:3000"]`) |

---

## Run

### Uvicorn (development)

```bash
uvicorn app.main:app --reload --port 8000
```

Webhook URL: `http://localhost:8000/webhook/weather-check`

### Docker

```bash
docker compose up --build
```

Starts:

- **API** on port `8000`
- **n8n** on port `5678` (optional; uses the same `.env` for workflow credentials)

#### n8n public webhook URL (important)

By default n8n generates webhook URLs as `http://localhost:5678/...`, which **external services like Retell cannot reach**. Set your public base URL in `.env` before starting Docker:

```env
WEBHOOK_URL=http://YOUR_PUBLIC_IP:5678/
N8N_EDITOR_BASE_URL=http://YOUR_PUBLIC_IP:5678/
```

Or with ngrok:

```bash
ngrok http 5678
```

```env
WEBHOOK_URL=https://xxxx.ngrok-free.app/
N8N_EDITOR_BASE_URL=https://xxxx.ngrok-free.app/
```

Restart n8n after changing these values:

```bash
docker compose up -d --force-recreate n8n
```

In the n8n Webhook node, the **Production URL** should now show your public address, e.g. `http://YOUR_PUBLIC_IP:5678/webhook/weather-check`. Copy that exact URL into Retell's `check_weather` function (no trailing slash).

### Expose for Retell

**Option A — n8n (Docker):** expose port `5678`, set `WEBHOOK_URL` as above, activate the workflow, use the n8n Production webhook URL in Retell.

**Option B — FastAPI only:** Retell must reach your webhook over HTTPS. Use ngrok or deploy to a public host:

```bash
ngrok http 8000
# Set Retell check_weather URL to: https://xxxx.ngrok.io/webhook/weather-check
```

No trailing slash on the webhook URL — Retell may send GET instead of POST if one is appended.

---

## API

### `GET /`

Returns the app name.

### `GET /api/health`

Health check: `{"status": "ok"}`

### `POST /webhook/weather-check`

Retell custom function endpoint.

**Request** (Retell → backend):

```json
{
  "name": "check_weather",
  "args": { "city": "London" },
  "call": {
    "call_id": "...",
    "direction": "inbound",
    "from_number": "+15559876543",
    "to_number": "+15551234567"
  }
}
```

**Response** (backend → Retell):

```json
{
  "temperature_f": 45,
  "description": "light rain",
  "city": "London",
  "is_cold": true,
  "message": "It's 45°F and light rain in London. It's cold — I've texted you a coat reminder."
}
```

Retell speaks the `message` field. When `is_cold` is false, the message ends with "No coat needed today!" instead.

---

## Tests

```bash
pytest
```

Optional end-to-end webhook script (from repo root):

```bash
bash ../scripts/test-webhook.sh
```

---

## Retell configuration

Configure the Retell agent with a custom function named `check_weather` pointing at this webhook. Full copy-paste config (system prompt, JSON schema, speak settings) is in [`../docs/retell-agent-config.md`](../docs/retell-agent-config.md).

Key Retell quirks:

- Prompt must say the LLM **MUST call check_weather** or it may answer without the function.
- Function timeout is ~10s — keep OpenWeatherMap + Twilio fast.
- Web Call is useful for testing voice without a phone number (SMS skipped).

---

## Comparison with `alternative/backend/`

| | `backend/` (this) | `alternative/backend/` |
|--|-------------------|------------------------|
| Voice platform | Retell AI | Deepgram Voice Agent API |
| Telephony | Retell phone number | Twilio → WebSocket media stream |
| Integration style | HTTP webhook on function call | In-process function dispatch during call |
| Default port | 8000 | 8001 |
| SMS on cold | Yes (Twilio) | Yes (Twilio) + optional email fallback |

See [`../alternative/backend/README.md`](../alternative/backend/README.md) for the Deepgram-based alternative.
