import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel

# Load environment variables
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

if not TWITCH_CLIENT_ID or not TWITCH_CLIENT_SECRET:
    raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be set in environment variables")

app = FastAPI(title="Twitch PFP API")

# CORS setup
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twitch API token helper
async def get_app_access_token():
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": TWITCH_CLIENT_ID,
        "client_secret": TWITCH_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to get Twitch access token")
        return resp.json()["access_token"]

# Pydantic model for /pfp input
class UserRequest(BaseModel):
    username: str  # could also be id, but username is simpler

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/pfp")
async def get_pfp(data: UserRequest):
    token = await get_app_access_token()
    url = "https://api.twitch.tv/helix/users"
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    params = {"login": data.username}  # using username, you can change to id if you want
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Failed to fetch Twitch user data")
        user_data = resp.json()
        if not user_data.get("data"):
            raise HTTPException(status_code=404, detail="User not found")
        return {"pfp_url": user_data["data"][0]["profile_image_url"]}
