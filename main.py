from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sim import run_simulation
import asyncio
import httpx
import os

load_dotenv()

LINQ_API_KEY = os.getenv("LINQ_API_KEY")
LINQ_BASE = "https://api.linqapp.com/api/partner/v3"
BASE_URL = os.getenv("NGROK_BASE_URL")

app = FastAPI()


app.mount("/assets", StaticFiles(directory="assets"), name="assets")


@app.get("/")
def read_root():
    return {"Hello": "World"}


seen_events = set()


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    # based off Linq API docs
    event_id = body.get("event_id")
    if event_id in seen_events:
        return {"ok": True}
    seen_events.add(event_id)

    event_type = body.get("event_type")
    if event_type != "message.received":
        return {"ok": True}

    data = body.get("data", {})
    chat_id = data.get("chat", {}).get("id")
    parts = data.get("parts", [])
    text = " ".join(p["value"] for p in parts if p.get("type") == "text")

    background_tasks.add_task(handle_message, chat_id, text)

    # print(f"chat_id: {chat_id}")
    # print(f"message: {text}")
    # await send_message(chat_id=chat_id, text=f"you said: {text}")

    return {"ok": True}


async def handle_message(chat_id: str, text: str):

    lower = text.lower()

    if "heavy" in lower:
        preset = "2"
    elif "light" in lower:
        preset = "3"
    elif "sim" in lower:
        preset = "1"
    elif "simulate" in lower:
        preset = "simulate"
    else:
        await send_message(chat_id=chat_id, text=f"you said: {text}")
        await send_message(
            chat_id, "Text 'sim', 'heavy', or 'light' to run a simulation!"
        )
        return

    await send_message(chat_id=chat_id, text="running simulation...")
    loop = asyncio.get_event_loop()

    result = await loop.run_in_executor(None, run_simulation, preset)
    reply = (
        f" Apogee: {result['apogee_ft']} ft ({result['apogee_m']} m)\n"
        f" Max Velocity: {result['max_velocity_ms']} m/s\n"
        f" Max Mach: {result['max_mach']}\n"
        f" Time to Apogee: {result['time_to_apogee_s']} s"
    )
    await send_message(chat_id=chat_id, text=reply)


async def send_message(chat_id: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{LINQ_BASE}/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {LINQ_API_KEY}"},
            json={"message": {"parts": [{"type": "text", "value": text}]}},
        )


async def send_image(chat_id: str, image_url: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{LINQ_BASE}/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {LINQ_API_KEY}"},
            json={"message": {"parts": [{"type": "text", "value": image_url}]}},
        )


@app.get("/health")
def health():
    return {"status": "ok"}
