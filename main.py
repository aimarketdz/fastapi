from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import os

app = FastAPI(
    title="AI Social Media Agent",
    description="AI Agent for automating social media posts - Pulse AI Studio",
    version="1.1.0"
)

# --- Helper ---
def is_real_key(key: str) -> bool:
    """Check if an env var is a real key (not empty or placeholder)."""
    if not key:
        return False
    placeholders = ["your_", "placeholder", "xxx", "changeme", "insert", "add_your"]
    key_lower = key.lower()
    return not any(p in key_lower for p in placeholders)

async def call_openai(topic: str, platform: str, language: str, tone: str, api_key: str) -> str:
    """Call OpenAI API to generate a social media post."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": f"You are an expert social media content creator. Write posts in {language}."},
                    {"role": "user", "content": f"Write a {tone} {platform} post about: {topic}. Keep it engaging with emojis and hashtags."}
                ],
                "max_tokens": 500
            },
            timeout=30.0
        )
    result = response.json()
    if "choices" in result:
        return result["choices"][0]["message"]["content"]
    error_msg = result.get("error", {}).get("message", "Unknown OpenAI error")
    raise HTTPException(status_code=502, detail=f"OpenAI error: {error_msg}")

async def post_to_facebook(page_id: str, access_token: str, text: str, scheduled_ts: int = None) -> dict:
    """Post or schedule to Facebook via Graph API."""
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    data = {"message": text, "access_token": access_token}
    if scheduled_ts:
        data["published"] = "false"
        data["scheduled_publish_time"] = str(scheduled_ts)
    async with httpx.AsyncClient() as client:
        res = await client.post(url, data=data, timeout=30.0)
    return res.json()

# --- Models ---
class PostRequest(BaseModel):
    topic: str
    platform: str
    language: str = "ar"
    tone: str = "engaging"

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

class AutoPublishRequest(BaseModel):
    topic: str
    platform: str
    language: str = "ar"
    tone: str = "engaging"
    page_id: str
    access_token: str

class WebhookPayload(BaseModel):
    action: str
    data: dict
    source: Optional[str] = "n8n"

# --- Endpoints ---
@app.get("/")
def root():
    return {
        "status": "AI Social Media Agent is running",
        "version": "1.1.0",
        "endpoints": [
            "/generate-post",
            "/publish-now",
            "/schedule-post",
            "/auto-publish",
            "/webhook/n8n",
            "/health"
        ]
    }

@app.post("/generate-post")
async def generate_post(req: PostRequest):
    """
    Generate a social media post using AI.
    Falls back to demo mode if no valid API key is configured.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    if is_real_key(api_key):
        try:
            generated_text = await call_openai(req.topic, req.platform, req.language, req.tone, api_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to call OpenAI: {str(e)}")
    else:
        generated_text = (
            f"[Demo Mode] Sample post about: {req.topic}\n"
            f"Platform: {req.platform} | Language: {req.language} | Tone: {req.tone}\n\n"
            "Add a valid OPENAI_API_KEY in Railway Variables to enable AI generation."
        )

    return {
        "success": True,
        "topic": req.topic,
        "platform": req.platform,
        "language": req.language,
        "generated_text": generated_text,
        "demo_mode": not is_real_key(api_key),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/publish-now")
async def publish_now(req: PublishRequest):
    """
    Publish a post directly to Facebook/Instagram via Graph API.
    """
    try:
        result = await post_to_facebook(req.page_id, req.access_token, req.text)
        if "id" in result:
            return {"success": True, "post_id": result["id"], "platform": req.platform, "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schedule-post")
async def schedule_post(req: ScheduleRequest):
    """
    Schedule a post for future publishing via Facebook Graph API.
    """
    try:
        scheduled_ts = int(req.scheduled_time.timestamp())
        result = await post_to_facebook(req.page_id, req.access_token, req.text, scheduled_ts)
        if "id" in result:
            return {
                "success": True,
                "post_id": result["id"],
                "scheduled_time": req.scheduled_time.isoformat(),
                "platform": req.platform
            }
        else:
            raise HTTPException(status_code=400, detail=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auto-publish")
async def auto_publish(req: AutoPublishRequest):
    """
    All-in-one: Generate a post with AI then publish it directly to Facebook/Instagram.
    Perfect for n8n/Make.com one-step automation.
    Requires OPENAI_API_KEY, FB page_id and access_token.
    """
    api_key = os.getenv("OPENAI_API_KEY", "")

    # Step 1: Generate text
    if is_real_key(api_key):
        try:
            generated_text = await call_openai(req.topic, req.platform, req.language, req.tone, api_key)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
    else:
        generated_text = (
            f"[Demo] Post about: {req.topic} | {req.platform} | {req.language}\n"
            "Add OPENAI_API_KEY to enable real AI generation."
        )

    # Step 2: Publish to Facebook
    try:
        result = await post_to_facebook(req.page_id, req.access_token, generated_text)
        if "id" in result:
            return {
                "success": True,
                "generated_text": generated_text,
                "post_id": result["id"],
                "platform": req.platform,
                "demo_mode": not is_real_key(api_key),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "generated_text": generated_text,
                "publish_error": result,
                "demo_mode": not is_real_key(api_key),
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        # Return generated text even if publish fails
        return {
            "success": False,
            "generated_text": generated_text,
            "publish_error": str(e),
            "demo_mode": not is_real_key(api_key),
            "timestamp": datetime.now().isoformat()
        }

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
    api_key = os.getenv("OPENAI_API_KEY", "")
    fb_page_id = os.getenv("FB_PAGE_ID", "")
    fb_token = os.getenv("FB_ACCESS_TOKEN", "")

    return {
        "status": "healthy",
        "service": "AI Social Media Agent",
        "version": "1.1.0",
        "timestamp": datetime.now().isoformat(),
        "env_vars": {
            "OPENAI_API_KEY": "configured" if is_real_key(api_key) else "not set (demo mode)",
            "FB_PAGE_ID": "configured" if is_real_key(fb_page_id) else "not set",
            "FB_ACCESS_TOKEN": "configured" if is_real_key(fb_token) else "not set"
        }
    }
