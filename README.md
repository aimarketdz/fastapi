# AI Social Media Agent - Pulse AI Studio

> Powered by FastAPI + OpenAI | Deployed on Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)

---

## Description

A production-ready AI agent API for automating social media content creation and publishing.
Built for integration with **n8n**, **Make.com**, and direct Facebook/Instagram Graph API publishing.

**Live API:** https://fastapi-production-1a56.up.railway.app/  
**Swagger Docs:** https://fastapi-production-1a56.up.railway.app/docs

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root - API status |
| POST | `/generate-post` | Generate AI social media post |
| POST | `/publish-now` | Publish directly to Facebook/Instagram |
| POST | `/schedule-post` | Schedule a post for later |
| POST | `/webhook/n8n` | Webhook for n8n / Make.com |
| GET | `/health` | Health check + env vars status |

---

## Quick Start

### Generate a Post (Demo Mode)
```bash
curl -X POST https://fastapi-production-1a56.up.railway.app/generate-post \
  -H 'Content-Type: application/json' \
  -d '{"topic": "AI in marketing", "platform": "facebook", "language": "ar", "tone": "engaging"}'
```

### Publish to Facebook
```bash
curl -X POST https://fastapi-production-1a56.up.railway.app/publish-now \
  -H 'Content-Type: application/json' \
  -d '{"text": "Your post text", "platform": "facebook", "page_id": "YOUR_PAGE_ID", "access_token": "YOUR_TOKEN"}'
```

---

## Environment Variables

Set these in Railway > Variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes (for AI) | OpenAI API key for post generation |
| `FB_PAGE_ID` | Yes (for publish) | Facebook Page ID |
| `FB_ACCESS_TOKEN` | Yes (for publish) | Facebook Page Access Token |

> Without `OPENAI_API_KEY`, the API runs in **Demo Mode** (returns placeholder text).

---

## n8n / Make.com Integration

Use the webhook endpoint to trigger actions from automation platforms:

```json
POST /webhook/n8n
{
  "action": "generate_and_publish",
  "data": {"topic": "your topic"},
  "source": "n8n"
}
```

---

## Tech Stack

- **FastAPI** - Python web framework
- **Uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **OpenAI GPT-4o-mini** - AI post generation
- **Railway** - Cloud deployment

---

## Local Development

```bash
git clone https://github.com/aimarketdz/fastapi.git
cd fastapi
pip install -r requirements.txt
uvicorn main:app --reload
```

---

Built by **Pulse AI Studio** | Algeria
