---
title: OpenEnv Agent Decision Lab
emoji: 🚀
colorFrom: purple
colorTo: blue
sdk: docker
sdk_version: "latest"
python_version: "3.10"
app_file: app.py
pinned: false
---

# 🚀 OpenEnv Agent Decision Lab

An interactive reinforcement-learning environment where AI agents learn to orchestrate real tools — checking weather, searching flights, and booking tickets — across three difficulty levels, with a built-in chaos engine that injects realistic API failures.

---

## 🌟 Overview

**OpenEnv Agent Decision Lab** is a complete learning platform for studying and training AI agents on tool-use tasks. The environment is fully OpenEnv-compatible and exposes a clean REST API alongside an interactive web dashboard.

Designed for:
- Training language models or RL agents on multi-step tool orchestration
- Benchmarking agent robustness under API failure conditions
- Studying reward shaping and goal-based evaluation patterns

---

## 🚀 Quick Start

### Option 1: HuggingFace Spaces (Recommended) 🌐

1. Visit [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Choose **Docker** as the Space SDK
4. Upload all project files or connect your GitHub repository
5. Your app will be live at `https://{username}-{spacename}.hf.space`

### Option 2: Local Development 💻

```bash
# Clone repository
git clone https://github.com/GitROG09/tool-orchestration-env.git
cd tool-orchestration-env

# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py

# Open in browser
# http://localhost:7860
```

### Option 3: Docker 🐳

```bash
# Build Docker image
docker build -t openenv-lab .

# Run container
docker run -p 7860:7860 openenv-lab

# Access at http://localhost:7860
```

---

## 🎯 Features

### Interactive Web Dashboard
- **Mission selector** — choose easy, medium, or hard task before each episode
- **Live timeline** — structured step-by-step output with reward per action
- **Progress bar** — tracks steps used vs steps remaining in the episode
- **Reward panel** — displays step reward, total reward, and normalised score in real time
- **Baseline runner** — one-click evaluation of the rule-based agent across all three tasks
- **Input validation** — clear alerts and hints guide correct tool parameter entry

### REST API (5 Endpoints)

```
GET  /          — Interactive web dashboard
POST /reset     — Start a new episode for a task
POST /step      — Execute a tool action
GET  /baseline  — Run the baseline agent on all tasks
GET  /grader    — Retrieve grading results for completed episodes
```

### 3 Built-in Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `get_weather` | `city: str` | Returns temperature (°C) and weather condition |
| `search_flights` | `source: str`, `destination: str` | Returns available flights with prices |
| `book_ticket` | `flight_number: str` | Books a flight, returns booking ID on success |

### 3 Difficulty Levels

| Level | Task | Goal | Max Steps | Reward Range |
|-------|------|------|-----------|--------------|
| Easy | Weather Optimisation | Find a city with temperature 20–30°C | 4 | -5 to +5 |
| Medium | Flight Selection | Find the cheapest flight under ₹5,000 to a comfortable city | 6 | -5 to +8 |
| Hard | Full Trip Planning | Check weather + find cheapest flight + book ticket | 8 | -5 to +10 |

### Chaos Engine

Every tool call passes through a configurable chaos engine that randomly injects:

| Failure Mode | Probability | Behaviour |
|-------------|-------------|-----------|
| `normal_execution` | 70% | Tool returns correct data |
| `timeout` | 10% | Tool returns `{"error": "... timeout"}` |
| `wrong_data` | 10% | Tool returns `{"error": "... corrupted data"}` |
| `partial_success` | 10% | Booking returns `status: pending` (not confirmed) |

Agents must handle failures gracefully — every error incurs a −2 reward penalty.

---

## 📊 API Reference

### POST `/reset` — Start Episode

Initialises the environment for the chosen task and resets all state.

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'
```

**Request body:**
```json
{ "task_id": "easy" }
```
`task_id` must be one of `"easy"`, `"medium"`, or `"hard"`.

**Response:**
```json
{
  "success": true,
  "task_id": "easy",
  "step": 0,
  "goal": {
    "type": "weather_selection",
    "temperature_range": [20, 30],
    "candidate_destinations": ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai"]
  },
  "remaining_steps": 4,
  "last_tool_output": null,
  "total_reward": 0.0,
  "normalized_score": 0.0,
  "history": []
}
```

---

### POST `/step` — Execute Tool Action

Runs a single tool call inside the current episode. Must call `/reset` first.

```bash
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "get_weather", "parameters": {"city": "Mumbai"}}'
```

**Request body:**
```json
{
  "tool_name": "get_weather",
  "parameters": { "city": "Mumbai" }
}
```

**Response:**
```json
{
  "success": true,
  "reward": 2.5,
  "done": false,
  "state": {
    "task_id": "easy",
    "step": 1,
    "goal": { ... },
    "remaining_steps": 3,
    "last_tool_output": {
      "tool": "get_weather",
      "city": "Mumbai",
      "temperature": 28,
      "condition": "Humid"
    },
    "total_reward": 2.5,
    "normalized_score": 0.25,
    "history": [ ... ]
  }
}
```

**Error — step called before reset:**
```json
{
  "success": false,
  "error": "No episode started. Call /reset first."
}
```

---

### GET `/baseline` — Run Baseline Agent

Runs the built-in rule-based agent on all three tasks and returns scores.

```bash
curl http://localhost:7860/baseline
```

**Response:**
```json
{
  "easy":   { "task": "easy",   "final_reward": 2.0,  "normalized_score": 0.20, "steps": 4 },
  "medium": { "task": "medium", "final_reward": 7.5,  "normalized_score": 0.75, "steps": 6 },
  "hard":   { "task": "hard",   "final_reward": 10.0, "normalized_score": 1.0,  "steps": 8 }
}
```

---

### GET `/grader` — Get Grading Results

Returns grading results for any episodes that have been completed (reached `done: true`).

```bash
curl http://localhost:7860/grader
```

**Response:**
```json
{
  "success": true,
  "results": {
    "easy": {
      "task_id": "easy",
      "raw_score": 2.5,
      "normalized_score": 0.25,
      "grade": "D"
    }
  }
}
```

**Grade thresholds:**

| Grade | Normalised Score |
|-------|-----------------|
| A | ≥ 0.90 |
| B | ≥ 0.80 |
| C | ≥ 0.70 |
| D | < 0.70 |

---

## 🏆 Reward System

Rewards are computed per step based on the task type and tool outcome.

### Easy — `weather_selection`

| Condition | Reward |
|-----------|--------|
| Tool error or corrupted data | −2.0 |
| Temperature in range (20–30°C) | +3.0 |
| Temperature out of range | −1.0 |
| Step cost (every action) | −0.5 |

### Medium — `flight_selection`

| Condition | Reward |
|-----------|--------|
| Tool error | −2.0 |
| `search_flights`: cheapest flight ≤ ₹5,000 | +3.0 |
| `search_flights`: cheapest flight > ₹5,000 | −2.0 |
| `get_weather`: temperature in range | +2.0 |
| `get_weather`: temperature out of range | −1.0 |
| Step cost (every action) | −0.5 |

### Hard — `full_trip_planning`

| Condition | Reward |
|-----------|--------|
| Tool error | −2.0 |
| `search_flights`: cheapest flight ≤ ₹5,000 | +2.0 |
| `search_flights`: cheapest flight > ₹5,000 | −2.0 |
| `get_weather`: temperature in range | +2.0 |
| `get_weather`: temperature out of range | −1.0 |
| `book_ticket`: status = `booked` | +4.0 |
| `book_ticket`: not confirmed (pending/error) | −2.0 |
| Step cost (every action) | −0.5 |

Normalised score = `min(total_reward / 10.0, 1.0)`

---

## 💻 Usage Examples

### Python — Complete Episode

```python
import requests

BASE_URL = "http://localhost:7860"

# 1. Start a hard episode
state = requests.post(f"{BASE_URL}/reset", json={"task_id": "hard"}).json()
print("Goal:", state["goal"])

# 2. Check weather in candidate cities
for city in ["Delhi", "Mumbai", "Bangalore"]:
    result = requests.post(f"{BASE_URL}/step", json={
        "tool_name": "get_weather",
        "parameters": {"city": city}
    }).json()
    print(f"{city}: {result['state']['last_tool_output']}, reward={result['reward']}")

# 3. Search cheapest flight to a comfortable city
result = requests.post(f"{BASE_URL}/step", json={
    "tool_name": "search_flights",
    "parameters": {"source": "Pune", "destination": "Mumbai"}
}).json()
print("Flights:", result["state"]["last_tool_output"])

# 4. Book the cheapest flight
result = requests.post(f"{BASE_URL}/step", json={
    "tool_name": "book_ticket",
    "parameters": {"flight_number": "AI404"}
}).json()
print("Booking:", result["state"]["last_tool_output"])
print("Done:", result["done"], "| Total reward:", result["state"]["total_reward"])

# 5. Check grading
grades = requests.get(f"{BASE_URL}/grader").json()
print("Grade:", grades["results"])
```

### Python — Run Baseline

```python
import requests

result = requests.get("http://localhost:7860/baseline").json()
for task, scores in result.items():
    pct = scores["normalized_score"] * 100
    print(f"{task:8s} → reward: {scores['final_reward']:6.2f}  score: {pct:.1f}%  steps: {scores['steps']}")
```

---

## 📁 Project Structure

```
openenv-agent-lab/
├── app.py              # Flask server — REST API routes and web dashboard
├── env.py              # ToolOrchestrationEnv — core OpenEnv environment
├── tools.py            # Tool implementations (weather, flights, booking)
├── tasks.py            # Task definitions (easy, medium, hard)
├── baseline.py         # Rule-based baseline agent
├── grader.py           # Episode scoring and grade assignment
├── reward.py           # Reward utility functions
├── chaos_engine.py     # Configurable API failure injection
├── weather_data.json   # Static weather data for 9 cities
├── flights_data.json   # Static flight routes and prices
├── openenv.yaml        # OpenEnv-compatible environment specification
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker image for HuggingFace / cloud deployment
└── README.md           # This file
```

---

## ⚙️ Configuration

### Environment Variables

```bash
PORT=7860           # Server port (default: 7860)
DEBUG=False         # Flask debug mode (default: False)
PYTHONUNBUFFERED=1  # Unbuffered stdout (set automatically in Dockerfile)
```

### Chaos Engine

Edit `chaos_engine.py` to adjust failure rates:

```python
ChaosEngine(
    failure_types   = ['timeout', 'wrong_data', 'partial_success', 'normal_execution'],
    failure_weights = [0.1,        0.1,          0.1,               0.7]
)
```

Set `failure_weights = [0, 0, 0, 1]` for deterministic testing with no failures.

### OpenEnv Spec

`openenv.yaml` documents the observation space, action space, and reward range for each task. It follows the OpenEnv standard and can be consumed by compatible training frameworks.

---

## 🚀 Deployment

### HuggingFace Spaces

The `Dockerfile` is pre-configured for HuggingFace Spaces. Simply upload all files to a Docker Space — no further configuration required. The app starts on port 7860 as expected by the platform.

### Docker (local or cloud)

```bash
# Build
docker build -t openenv-lab .

# Run locally
docker run -p 7860:7860 openenv-lab

# Run with custom port
docker run -p 8080:7860 -e PORT=7860 openenv-lab
```

### Gunicorn (production)

```bash
gunicorn --bind 0.0.0.0:7860 --workers 1 --timeout 30 app:app
```

> Use `--workers 1` — the environment holds in-process state so multiple workers would not share episode state correctly.

---

## 🧪 Testing

### Quick smoke test

```python
from app import app

client = app.test_client()

# Reset
r = client.post('/reset', json={'task_id': 'easy'})
assert r.get_json()['success']

# Step
r = client.post('/step', json={'tool_name': 'get_weather', 'parameters': {'city': 'Mumbai'}})
assert r.get_json()['success']

# Baseline
r = client.get('/baseline')
data = r.get_json()
assert 'easy' in data and 'medium' in data and 'hard' in data

print("All smoke tests passed ✅")
```

### Step-before-reset guard

```python
# Must return 400 with a helpful message
r = client.post('/step', json={'tool_name': 'get_weather', 'parameters': {'city': 'Mumbai'}})
assert r.status_code == 400
assert 'reset' in r.get_json()['error'].lower()
```

---

## 🐛 Troubleshooting

**Port already in use**
```bash
PORT=8080 python app.py
# or
lsof -ti:7860 | xargs kill -9
```

**Module not found**
```bash
pip install -r requirements.txt
```

**Docker build fails**
```bash
docker system prune -a
docker build --no-cache -t openenv-lab .
```

**Episode stuck / unexpected done**
Always call `/reset` before calling `/step`. If `/step` returns `done: true` immediately, it means the episode was not started — call `/reset` first.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **OpenEnv** — Standard environment specification
- **HuggingFace** — Hosting infrastructure
- **Flask** — Web framework
- **Python Community** — Open source ecosystem

---

<div align="center">

[⭐ Star on GitHub](https://github.com/GitROG09/tool-orchestration-env) • [🚀 Deploy on HuggingFace Spaces](https://huggingface.co/spaces)

</div>
