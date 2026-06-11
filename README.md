# Backend — Weather Voice Agent Webhook

FastAPI webhook that implements the same logic as the n8n workflow. Point Retell's `check_weather` function here (via ngrok) or use the n8n import in `n8n-weather-workflow.json`.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env            # fill in API keys
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Webhook URL: `http://localhost:8000/webhook/weather-check`

For Retell, expose with ngrok:

```bash
ngrok http 8000
# Use https://xxxx.ngrok.io/webhook/weather-check in Retell custom function
```

## Test

```bash
pytest
bash ../scripts/test-webhook.sh
```

## Endpoint

**POST** `/webhook/weather-check`

Retell payload:

```json
{
  "name": "check_weather",
  "args": { "city": "London" }
}
```

Response:

```json
{
  "temperature_f": 45,
  "description": "light rain",
  "city": "London",
  "is_cold": true,
  "message": "It's 45°F and light rain in London. It's cold — I've texted you a coat reminder."
}
```

When `is_cold` is true and the Retell payload includes `call.from_number`, an SMS is sent to the caller via Twilio.
