from dotenv import load_dotenv
import anthropic
import json
import os

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def parse_rocket_params(user_message: str) -> dict:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="""You are a rocketry parameter parser. Extract rocket simulation parameters from natural language.

Return ONLY a JSON object with these fields:
- mass: float (kg, rocket dry mass)
- inclination: float (degrees from horizontal, launch angle)
- name: string (descriptive name based on the parameters)

Examples:
- "simulate a 20kg rocket at 50 degrees" → {"mass": 20.0, "inclination": 50.0, "name": "20kg Rocket at 50°"}
- "launch a 5 pound rocket straight up" → {"mass": 2.27, "inclination": 90.0, "name": "Lightweight Rocket"}
- "heavy rocket at 75 degrees" → {"mass": 20.0, "inclination": 75.0, "name": "Heavy Rocket at 75°"}

Rules:
- ALWAYS extract numbers explicitly stated by the user
- Convert lbs to kg (1 lb = 0.453592 kg)
- "straight up" or "vertical" = 90 degrees
- Default mass: 15.0 kg only if not specified
- Default inclination: 84.0 only if not specified
- Return only valid JSON, no explanation.""",
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text.strip()
    print(f"CLAUDE RAW RESPONSE: {raw}")
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        params = json.loads(raw)
    except json.JSONDecodeError:
        params = {"name": "Custom Rocket", "mass": 15.0, "inclination": 84.0}

    params["mass"] = max(1.0, min(float(params.get("mass", 15.0)), 50.0))
    params["inclination"] = max(45.0, min(float(params.get("inclination", 84.0)), 90.0))
    params.setdefault("name", "Custom Rocket")
    return params
