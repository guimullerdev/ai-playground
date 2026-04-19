import random

WEATHER_TOOL_SCHEMA = {
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The name of the city (e.g. 'London', 'Tokyo')",
            }
        },
        "required": ["city"],
    },
}

_CONDITIONS = ["Sunny", "Cloudy", "Rainy", "Windy", "Partly cloudy", "Stormy", "Foggy"]


def get_weather(city: str) -> dict:
    temp_c = random.randint(5, 35)
    return {
        "ok": True,
        "data": {
            "city": city,
            "temperature_c": temp_c,
            "temperature_f": round(temp_c * 9 / 5 + 32),
            "condition": random.choice(_CONDITIONS),
            "humidity_pct": random.randint(30, 90),
        },
        "error": None,
    }
