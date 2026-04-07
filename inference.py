import os
import json
import sys
from openai import OpenAI

# =========================
# ENVIRONMENT VARIABLES
# =========================

API_BASE_URL     = os.getenv("API_BASE_URL", "<your-active-endpoint>")
MODEL_NAME       = os.getenv("MODEL_NAME",   "<your-active-model>")
HF_TOKEN         = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# =========================
# OPENAI CLIENT
# =========================

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN or "no-token",
)

# =========================
# TOOL DEFINITIONS
# =========================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Returns temperature in Celsius and condition.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city, e.g. Mumbai"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Search available flights between two cities. Returns flights with prices.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Departure city, e.g. Pune"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Arrival city, e.g. Delhi"
                    }
                },
                "required": ["source", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_ticket",
            "description": "Book a flight ticket by flight number. Returns booking ID on success.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_number": {
                        "type": "string",
                        "description": "Flight number to book, e.g. AI101"
                    }
                },
                "required": ["flight_number"]
            }
        }
    }
]


# =========================
# CALL TOOL VIA ENV API
# =========================

def call_tool(tool_name: str, parameters: dict, base_url: str = "http://localhost:7860") -> dict:
    import urllib.request
    try:
        payload = json.dumps({
            "tool_name":  tool_name,
            "parameters": parameters
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/step",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return result
    except Exception as e:
        return {"error": str(e), "state": {}, "reward": 0, "done": False}


# =========================
# RESET ENVIRONMENT
# =========================

def reset_env(task_id: str, base_url: str = "http://localhost:7860") -> dict:
    import urllib.request
    try:
        payload = json.dumps({"task_id": task_id}).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/reset",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "goal": {}, "remaining_steps": 8}


# =========================
# AGENT LOOP
# =========================

def run_agent(task_id: str = "hard", base_url: str = "http://localhost:7860"):

    print("START", flush=True)

    try:
        state = reset_env(task_id, base_url)
        goal  = state.get("goal", {})

        system_prompt = f"""You are an AI travel planning agent operating inside an OpenEnv tool-orchestration environment.

Your goal: {json.dumps(goal, indent=2)}

You have access to three tools:
- get_weather(city)          — check temperature and conditions
- search_flights(source, destination) — find flights and prices
- book_ticket(flight_number) — book a flight

Rules:
- Only call tools that are relevant to the current goal.
- If a tool returns an error, retry once with the same parameters before giving up.
- For the hard task: first find cities with temperature 20-30 degrees C, then find the cheapest flight under budget, then book it.
- Stop calling tools once the goal is achieved or steps run out.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Complete the goal. Task: {task_id}. Goal: {json.dumps(goal)}"}
        ]

        max_steps    = state.get("remaining_steps", 8)
        total_reward = 0.0
        step_num     = 0
        done         = False

        while not done and step_num < max_steps:
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    max_tokens=512,
                )
            except Exception as e:
                print(f"STEP tool=error params={{}} output={{\"error\": \"{str(e)}\"}} reward=0", flush=True)
                break

            msg = response.choices[0].message

            if msg.tool_calls:
                tool_call  = msg.tool_calls[0]
                tool_name  = tool_call.function.name

                try:
                    parameters = json.loads(tool_call.function.arguments)
                except Exception:
                    parameters = {}

                result       = call_tool(tool_name, parameters, base_url)
                tool_output  = result.get("state", {}).get("last_tool_output", {})
                reward       = result.get("reward", 0)
                done         = result.get("done", False)
                total_reward = result.get("state", {}).get("total_reward", total_reward)
                step_num    += 1

                print(f"STEP tool={tool_name} params={json.dumps(parameters)} "
                      f"output={json.dumps(tool_output)} reward={reward}", flush=True)

                messages.append({"role": "assistant", "content": None, "tool_calls": msg.tool_calls})
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tool_call.id,
                    "content":      json.dumps(tool_output)
                })
            else:
                break

    except Exception as e:
        print(f"STEP tool=error params={{}} output={{\"error\": \"{str(e)}\"}} reward=0", flush=True)
        total_reward = 0.0
        step_num     = 0

    normalized_score = min(total_reward / 10.0, 1.0)

    print(f"END total_reward={total_reward:.2f} normalized_score={normalized_score:.4f}", flush=True)

    return {
        "task_id":          task_id,
        "total_reward":     total_reward,
        "normalized_score": normalized_score,
        "steps":            step_num
    }


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    task    = sys.argv[1] if len(sys.argv) > 1 else "hard"
    env_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:7860"

    result = run_agent(task_id=task, base_url=env_url)
    print(json.dumps(result, indent=2))
