import json
import random
from typing import Dict, Any

from chaos_engine import ChaosEngine


# =========================
# CHAOS ENGINE INITIALIZATION
# =========================

chaos = ChaosEngine()


# =========================
# LOAD WEATHER DATA
# =========================

with open("weather_data.json") as f:
    BASE_WEATHER_DB = json.load(f)


def generate_dynamic_weather():

    dynamic_weather = {}

    for city, data in BASE_WEATHER_DB.items():

        base_temp = data["temperature"]

        variation = random.randint(-3, 3)

        dynamic_weather[city] = {
            "temperature": base_temp + variation,
            "condition": data["condition"]
        }

    return dynamic_weather


# Initialize dynamic weather once
WEATHER_DB = generate_dynamic_weather()


# =========================
# LOAD FLIGHT DATA
# =========================

with open("flights_data.json") as f:
    FLIGHT_DB = json.load(f)


# =========================
# BASE TOOL CLASS
# =========================

class Tool:

    def __init__(self, name: str):

        self.name = name

    def execute(self, **kwargs) -> Dict[str, Any]:

        raise NotImplementedError


# =========================
# WEATHER TOOL
# =========================

class GetWeatherTool(Tool):

    def __init__(self):

        super().__init__("get_weather")

    def execute(self, city="Delhi"):

        global WEATHER_DB

        city = city.title()

        failure = chaos.inject_failure()

        if city not in WEATHER_DB:

            return {"error": f"No weather data for {city}"}

        if failure == "timeout":

            return {"error": "Weather API timeout"}

        # BUG FIX: was returning {"temperature": "unknown"} which has no
        # "error" key, bypassing env error-guard and crashing int comparison.
        # Now returns a proper error dict so -2 penalty is applied cleanly.
        if failure == "wrong_data":

            return {"error": "Weather API returned corrupted data"}

        return {

            "tool": self.name,

            "city": city,

            **WEATHER_DB[city]

        }


# =========================
# FLIGHT SEARCH TOOL
# =========================

class SearchFlightsTool(Tool):

    def __init__(self):

        super().__init__("search_flights")

    def execute(self, source="Pune", destination="Delhi"):

        route = f"{source.title()}-{destination.title()}"

        failure = chaos.inject_failure()

        if route not in FLIGHT_DB:

            return {"error": "Route not available"}

        if failure == "timeout":

            return {"error": "Flight API timeout"}

        # BUG FIX: was returning {"flights": []} which has no "error" key,
        # but env checks `if not flights: return -2` so this was handled —
        # however returning an error dict is more consistent with the pattern.
        if failure == "wrong_data":

            return {"error": "Flight API returned corrupted data"}

        return {

            "tool": self.name,

            "source": source,

            "destination": destination,

            "flights": FLIGHT_DB[route]

        }


# =========================
# BOOKING TOOL
# =========================

class BookTicketTool(Tool):

    def __init__(self):

        super().__init__("book_ticket")

    def execute(self, flight_number="SG202"):

        failure = chaos.inject_failure()

        if failure == "timeout":

            return {"error": "Booking service unavailable"}

        if failure == "wrong_data":

            return {"error": "Booking API returned corrupted data"}

        if failure == "partial_success":

            # Partial success: booking initiated but not confirmed
            return {

                "tool": self.name,

                "flight_number": flight_number,

                "status": "pending",

                "message": "Booking initiated but not confirmed"

            }

        return {

            "tool": self.name,

            "flight_number": flight_number,

            "status": "booked",

            "booking_id": "BK12345"

        }


# =========================
# TOOL REGISTRY
# =========================

TOOLS = {

    "get_weather": GetWeatherTool(),

    "search_flights": SearchFlightsTool(),

    "book_ticket": BookTicketTool()

}


# =========================
# TOOL ACCESS FUNCTION
# =========================

def get_tool(tool_name: str) -> Tool:

    return TOOLS.get(tool_name)
