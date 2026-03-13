from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import os

app = FastAPI(
    title="AI Social Media Agent",
    description="AI Agent for automating social media posts - Pulse AI Studio",
    version="1.0.0"
)

# ─── Models ───────────────────────────────────────────

class PostRequest(BaseModel):
    topic: str
    platform: str  # "facebook" | "instagram"
    language: str = "ar"
    tone: str = "engaging"  # engaging | professional | funny

class PublishRequest(BaseModel):
    text: str
    platform: str
    page_id: str
    access_token: str

class ScheduleRequest(BaseModel):
    text: str
    platform: str
    scheduled_time: datetime
    page_id: str
    access_token: str

class WebhookPayload(BaseModel):
    action: str
    data: dict
    source: Optional[str] = "n8n"

# ─── Endpoints ────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "AI Social Media Agent is running",
        "version": "1.0.0",
        "endpoints": ["/generate-post", "/publish-now", "/schedule-post", "/webhook/n8n", "/health"]
    }

@app.post("/generate-post")
async def generate_post(req: PostRequest):
    """
    Generate a social media post using AI.
    Connects to OpenAI or Gemini API.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if api_key:
        # Call OpenAI API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": f"You are an expert social media content creator. Write posts in {req.language}."},
                        {"role": "user", "content": f"Write a {req.tone} {req.platform} post about: {req.topic}. Keep it engaging with emojis and hashtags."}
                    ],
                    "max_tokens": 500
                },
                timeout=30.0
            )
            result = response.json()
            generated_text = result["choices"][0]["message"]["content"]
    else:
        # Demo mode - no API key
        generated_text = f"[Demo Mode] Post about '{req.topic}' for {req.platform} in {req.language}. Add your OPENAI_API_KEY in Railway Variables to enable AI generation."
    
    return {
        "success": True,
        "topic": req.topic,
        "platform": req.platform,
        "language": req.language,
        "generated_text": generated_text,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/publish-now")
async def publish_now(req: PublishRequest):
    """
    Publish a post directly to Facebook/Instagram via Graph API.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{req.page_id}/feed"
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                data={
                    "message": req.text,
                    "access_token": req.access_token
                },
                timeout=30.0
            )
        result = res.json()
        if "id" in result:
            return {"success": True, "post_id": result["id"], "platform": req.platform}
        else:
            raise HTTPException(status_code=400, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule-post")
async def schedule_post(req: ScheduleRequest):
    """
    Schedule a post for future publishing via Facebook Graph API.
    """
    try:
        scheduled_ts = int(req.scheduled_time.timestamp())
        url = f"https://graph.facebook.com/v19.0/{req.page_id}/feed"
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                data={
                    "message": req.text,
                    "published": "false",
                    "scheduled_publish_time": scheduled_ts,
                    "access_token": req.access_token
                },
                timeout=30.0
            )
        result = res.json()
        if "id" in result:
            return {
                "success": True,
                "post_id": result["id"],
                "scheduled_time": req.scheduled_time.isoformat(),
                "platform": req.platform
            }
        else:
            raise HTTPException(status_code=400, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/n8n")
async def n8n_webhook(payload: WebhookPayload):
    """
    Webhook endpoint for n8n or Make.com automations.
    Receives action requests and processes them.
    """
    return {
        "success": True,
        "received_action": payload.action,
        "source": payload.source,
        "data": payload.data,
        "processed_at": datetime.now().isoformat()
    }

@app.get("/health")
def health_check():
    """
    Health check endpoint for Railway monitoring.
    """
    return {
        "status": "healthy",
        "service": "AI Social Media Agent",
        "timestamp": datetime.now().isoformat(),
        "env_vars": {
            "OPENAI_API_KEY": "set" if os.getenv("OPENAI_API_KEY") else "not set",
            "FB_PAGE_ID": "set" if os.getenv("FB_PAGE_ID") else "not set",
        }
    }
