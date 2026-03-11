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
- mass: float (kg, rocket dry mass, default 15.0)
- inclination: float (degrees, launch angle, default 84, max 90)
- name: string (a descriptive name for this rocket)

If the user mentions weight in lbs, convert to kg (1 lb = 0.453592 kg).
If parameters are missing, use sensible rocketry defaults.
Return only valid JSON, no explanation.""",
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()
    params = json.loads(raw)

    # Clamp values to safe ranges
    params["mass"] = max(1.0, min(params["mass"], 50.0))
    params["inclination"] = max(45.0, min(params["inclination"], 90.0))

    return params
