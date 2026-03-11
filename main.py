from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from sim import run_simulation_from_params
from agent import parse_rocket_params
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
    return {"Hello": "Orbit"}


@app.get("/health")
def health():
    return {"status": "ok"}


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
    print(f"HANDLE: chat_id={chat_id}, LINQ_API_KEY set={bool(LINQ_API_KEY)}")

    lower = text.lower()
    keywords = ["sim", "rocket", "launch", "motor", "mass", "kg", "lbs", "simulate"]

    if not any(k in lower for k in keywords):
        await send_message(
            chat_id,
            "Orbit — RocketPy over iMessage\n\nTry: 'simulate a 15kg rocket at 80 degrees'",
        )
        return

    await send_message(chat_id, "Parsing your rocket...")

    try:
        loop = asyncio.get_event_loop()
        params = await loop.run_in_executor(None, parse_rocket_params, text)
    except Exception:
        await send_message(
            chat_id,
            "Couldn't parse that. Try: 'simulate a 15kg rocket at 80 degrees'",
        )
        return

    await send_message(
        chat_id,
        f"Got it!\n\n"
        f"Name: {params['name']}\n"
        f"Mass: {params['mass']} kg\n"
        f"Inclination: {params['inclination']}°\n\n"
        f"Running simulation...",
    )

    try:
        result = await loop.run_in_executor(None, run_simulation_from_params, params)
    except Exception as e:
        print(f"SIM ERROR: {e}")
        await send_message(chat_id, "❌ Simulation failed. Try different parameters.")
        return
    reply = (
        f"🚀 {result['name']}\n\n"
        f"📍 Apogee: {result['apogee_ft']} ft ({result['apogee_m']} m)\n"
        f"⚡ Max Velocity: {result['max_velocity_ms']} m/s\n"
        f"💥 Max Mach: {result['max_mach']}\n"
        f"⏱ Time to Apogee: {result['time_to_apogee_s']} s"
    )
    await send_message(chat_id, reply)
    await send_image(chat_id, result["plot_url"])


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
            json={"message": {"parts": [{"type": "media", "url": image_url}]}},
        )
