import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx

# Load env vars
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
    raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be set")

app = FastAPI(title="Twitch PFP API", version="1.0")

# ✅ Allow only your domains
origins = [
    "https://ttvthreads.vercel.app",
    "http://ttvthreads.vercel.app",
    "https://www.ttvthreads.vercel.app",
    "http://www.ttvthreads.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# -----------------------
# 🔒 Token caching system
# -----------------------
twitch_token = None
token_expiration = 0

async def get_app_access_token():
    global twitch_token, token_expiration
    if twitch_token and time.time() < token_expiration - 60:  # refresh 1 min early
        return twitch_token

    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get Twitch token")
        data = resp.json()
        twitch_token = data["access_token"]
        token_expiration = time.time() + data.get("expires_in", 3600)
        return twitch_token

# -----------------------
# 🩺 Health check
# -----------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# -----------------------
# ⚡ Fast GET endpoint
# -----------------------
@app.get("/pfp/{username}")
async def get_pfp(username: str):
    token = await get_app_access_token()
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params={"login": username})
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch user data")

        data = resp.json()
        if not data.get("data"):
            raise HTTPException(status_code=404, detail="User not found")

        return {"pfp_url": data["data"][0]["profile_image_url"]}
