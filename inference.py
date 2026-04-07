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

def call_tool(tool_name: str, parameters: dict, base_url: str) -> dict:
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
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "state": {}, "reward": 0, "done": False}


# =========================
# RESET ENVIRONMENT
# =========================

def reset_env(task_id: str, base_url: str) -> dict:
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
# CLAMP SCORE TO (0, 1) EXCLUSIVE
# =========================

def clamp_score(raw_reward: float, min_reward: float = -5.0, max_reward: float = 10.0) -> float:
    """
    Normalise reward to strictly (0, 1) — never exactly 0.0 or 1.0.
    The evaluator rejects scores at the boundaries.
    """
    span = max_reward - min_reward
    normalised = (raw_reward - min_reward) / span if span > 0 else 0.5
    # Clamp to open interval (0.01, 0.99)
    return max(0.01, min(0.99, round(normalised, 4)))


# =========================
# RUN ONE TASK
# =========================

def run_task(task_id: str, base_url: str) -> dict:

    print(f"[START] task={task_id}", flush=True)

    total_reward = 0.0
    step_num     = 0

    try:
        state     = reset_env(task_id, base_url)
        goal      = state.get("goal", {})
        max_steps = state.get("remaining_steps", 8)
        done      = False

        system_prompt = f"""You are an AI travel planning agent.

Your goal: {json.dumps(goal, indent=2)}

Tools available:
- get_weather(city)
- search_flights(source, destination)
- book_ticket(flight_number)

Rules:
- Check weather first to find cities with temperature 20-30 degrees C.
- Then search flights and pick the cheapest under budget.
- For hard task: also book the ticket.
- Retry once on errors.
- Stop when goal is complete or steps run out.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Complete the task. task_id={task_id} goal={json.dumps(goal)}"}
        ]

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
                step_num += 1
                print(f"[STEP] step={step_num} tool=error reward=0", flush=True)
                break

            msg = response.choices[0].message

            if not msg.tool_calls:
                break

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

            print(f"[STEP] step={step_num} tool={tool_name} reward={reward}", flush=True)

            messages.append({"role": "assistant", "content": None, "tool_calls": msg.tool_calls})
            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      json.dumps(tool_output)
            })

    except Exception as e:
        step_num += 1
        print(f"[STEP] step={step_num} tool=error reward=0", flush=True)
        total_reward = 0.0

    # Score must be strictly between 0 and 1
    score = clamp_score(total_reward)

    print(f"[END] task={task_id} score={score:.4f} steps={step_num}", flush=True)

    return {
        "task_id":      task_id,
        "total_reward": total_reward,
        "score":        score,
        "steps":        step_num
    }


# =========================
# ENTRY POINT — runs ALL 3 tasks
# =========================

if __name__ == "__main__":
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:7860"

    # Always run all 3 tasks so the evaluator sees 3 graded results
    results = {}
    for task_id in ["easy", "medium", "hard"]:
        results[task_id] = run_task(task_id, base_url)

    print(json.dumps(results, indent=2))
