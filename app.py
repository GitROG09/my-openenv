import os
from flask import Flask, jsonify, request, render_template_string

from env import ToolOrchestrationEnv
from baseline import BaselineAgent


app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


env = ToolOrchestrationEnv()
baseline_agent = BaselineAgent()


# =========================
# DASHBOARD UI
# =========================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>

<title>OpenEnv Agent Decision Lab</title>

<style>

*, *::before, *::after { box-sizing: border-box; }

body {
  font-family: 'Segoe UI', sans-serif;
  margin: 0;
  background: linear-gradient(135deg, #4c6ef5, #7950f2);
  color: white;
  min-height: 100vh;
}

.container {
  max-width: 1100px;
  margin: auto;
  padding: 30px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}
.header h1 { margin-bottom: 6px; }
.header p  { margin: 0; opacity: 0.85; }

.card {
  background: white;
  color: black;
  padding: 25px;
  margin-bottom: 20px;
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}

.step-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
}

button {
  background: #4c6ef5;
  border: none;
  color: white;
  padding: 11px 22px;
  border-radius: 8px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s;
}
button:hover  { background: #364fc7; }
button:active { background: #2c41a8; }
button:disabled {
  background: #adb5bd;
  cursor: not-allowed;
}

select, input[type=text] {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ced4da;
  font-size: 14px;
  margin-right: 8px;
  outline: none;
  transition: border-color 0.15s;
}
select:focus, input[type=text]:focus {
  border-color: #4c6ef5;
}

.goal-box {
  background: #f1f3f5;
  padding: 15px;
  border-radius: 10px;
  font-size: 13px;
  margin-top: 14px;
  white-space: pre-wrap;
  font-family: monospace;
  min-height: 48px;
  color: #333;
}

.timeline {
  background: #1a1a2e;
  color: #00ff9c;
  padding: 15px;
  border-radius: 10px;
  font-family: monospace;
  font-size: 13px;
  max-height: 320px;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.5;
}

.reward-row {
  display: flex;
  gap: 30px;
  flex-wrap: wrap;
  align-items: center;
}
.reward-block { text-align: center; }
.reward-label { font-size: 12px; color: #868e96; margin-bottom: 4px; }
.reward-value { font-size: 26px; font-weight: 700; color: #2f9e44; }
.reward-value.negative { color: #e03131; }

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  margin-left: 10px;
  vertical-align: middle;
}
.badge-idle    { background: #e9ecef; color: #495057; }
.badge-running { background: #d3f9d8; color: #2b8a3e; }
.badge-done    { background: #ffe3e3; color: #c92a2a; }

.input-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.hint {
  font-size: 12px;
  color: #868e96;
  margin-top: 8px;
}

.steps-bar-wrap  { margin-top: 14px; }
.steps-bar-label { font-size: 12px; color: #868e96; margin-bottom: 5px; }
.steps-bar-bg    { background: #e9ecef; border-radius: 6px; height: 10px; overflow: hidden; }
.steps-bar-fill  {
  background: #4c6ef5;
  height: 100%;
  width: 0%;
  border-radius: 6px;
  transition: width 0.3s;
}

</style>
</head>

<body>
<div class="container">

  <div class="header">
    <h1>🚀 OpenEnv Agent Decision Lab</h1>
    <p>Observe how an agent explores environment states and optimises actions</p>
  </div>

  <!-- CARD 1 -->
  <div class="card">
    <div class="step-title">
      1️⃣ Select Mission
      <span id="episodeBadge" class="badge badge-idle">Not started</span>
    </div>
    <div class="input-row">
      <select id="taskSelect">
        <option value="easy">🌤️ Weather Optimisation Mission</option>
        <option value="medium">✈️ Flight Selection Mission</option>
        <option value="hard">🗺️ Full Trip Planning Mission</option>
      </select>
      <button onclick="resetEnv()">▶ Start Episode</button>
    </div>
    <div id="goalBox" class="goal-box">Mission goal will appear here after you click Start Episode...</div>
  </div>

  <!-- CARD 2 -->
  <div class="card">
    <div class="step-title">2️⃣ Execute Action</div>
    <div class="input-row">
      <select id="toolSelect" onchange="updatePlaceholder()">
        <option value="get_weather">🌡️ Check Weather</option>
        <option value="search_flights">🔍 Search Flights</option>
        <option value="book_ticket">🎫 Book Ticket</option>
      </select>
      <input id="paramsInput" type="text" placeholder="Mumbai" style="width:200px">
      <button id="executeBtn" onclick="executeStep()">⚡ Execute Action</button>
    </div>
    <div id="inputHint" class="hint">Enter a city name, e.g. <strong>Mumbai</strong></div>
    <div class="steps-bar-wrap">
      <div class="steps-bar-label" id="stepsLabel">Steps: 0 / 0 used</div>
      <div class="steps-bar-bg">
        <div class="steps-bar-fill" id="stepsBar"></div>
      </div>
    </div>
  </div>

  <!-- CARD 3 -->
  <div class="card">
    <div class="step-title">3️⃣ Agent Timeline</div>
    <div id="timelineOutput" class="timeline">No actions yet. Start an episode first.</div>
  </div>

  <!-- CARD 4 -->
  <div class="card">
    <div class="step-title">4️⃣ Episode Reward</div>
    <div class="reward-row">
      <div class="reward-block">
        <div class="reward-label">Step Reward</div>
        <div class="reward-value" id="stepReward">—</div>
      </div>
      <div class="reward-block">
        <div class="reward-label">Total Reward</div>
        <div class="reward-value" id="totalReward">0.00</div>
      </div>
      <div class="reward-block">
        <div class="reward-label">Normalised Score</div>
        <div class="reward-value" id="normScore">0.00</div>
      </div>
    </div>
  </div>

  <!-- CARD 5 -->
  <div class="card">
    <div class="step-title">5️⃣ Baseline Agent Evaluation</div>
    <button onclick="runBaseline()" id="baselineBtn">🤖 Run Baseline Solver</button>
    <div id="baselineOutput" class="timeline" style="margin-top:14px">Baseline not executed yet...</div>
  </div>

</div>

<script>

// ── client state ──
let episodeStarted = false;
let episodeDone    = false;
let maxSteps       = 0;
let stepCount      = 0;

// ── run on page load so placeholder is immediately correct ──
updatePlaceholder();

function updatePlaceholder() {
  const tool  = document.getElementById('toolSelect').value;
  const input = document.getElementById('paramsInput');
  const hint  = document.getElementById('inputHint');

  if (tool === 'get_weather') {
    input.placeholder = 'Mumbai';
    hint.innerHTML    = 'Enter a city name, e.g. <strong>Mumbai</strong> or <strong>Delhi</strong>';
  } else if (tool === 'search_flights') {
    input.placeholder = 'Pune, Delhi';
    hint.innerHTML    = 'Enter <strong>Source, Destination</strong> separated by a comma — e.g. <strong>Pune, Delhi</strong>';
  } else {
    input.placeholder = 'AI101';
    hint.innerHTML    = 'Enter a flight number, e.g. <strong>AI101</strong> or <strong>SG202</strong>';
  }
}

function setBadge(status) {
  const b = document.getElementById('episodeBadge');
  b.className = 'badge';
  if (status === 'running') {
    b.classList.add('badge-running');
    b.textContent = '✅ Running';
  } else if (status === 'done') {
    b.classList.add('badge-done');
    b.textContent = '🏁 Done';
  } else {
    b.classList.add('badge-idle');
    b.textContent = 'Not started';
  }
}

function setRewardEl(id, value) {
  const el = document.getElementById(id);
  if (value === '—') { el.textContent = '—'; el.classList.remove('negative'); return; }
  el.textContent = typeof value === 'number' ? value.toFixed(2) : value;
  el.classList.toggle('negative', typeof value === 'number' && value < 0);
}

function updateStepsBar(used, total) {
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  document.getElementById('stepsBar').style.width  = pct + '%';
  document.getElementById('stepsLabel').textContent = 'Steps used: ' + used + ' / ' + total;
}

function appendTimeline(text) {
  const box = document.getElementById('timelineOutput');
  box.textContent += text + '\\n';
  box.scrollTop = box.scrollHeight;
}

// ── START EPISODE ──
async function resetEnv() {
  const task = document.getElementById('taskSelect').value;

  try {
    const res  = await fetch('/reset', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ task_id: task })
    });
    const data = await res.json();

    if (!data.success) { alert('Reset failed: ' + data.error); return; }

    episodeStarted = true;
    episodeDone    = false;
    maxSteps       = data.remaining_steps;
    stepCount      = 0;

    document.getElementById('goalBox').textContent       = JSON.stringify(data.goal, null, 2);
    document.getElementById('timelineOutput').textContent = '▶ Episode started — execute actions below.\\n';
    document.getElementById('executeBtn').disabled       = false;
    document.getElementById('executeBtn').textContent    = '⚡ Execute Action';

    setBadge('running');
    updateStepsBar(0, maxSteps);
    setRewardEl('stepReward',  '—');
    setRewardEl('totalReward', 0);
    setRewardEl('normScore',   0);

  } catch (err) {
    alert('Network error: ' + err.message);
  }
}

// ── EXECUTE ACTION ──
async function executeStep() {

  if (!episodeStarted) {
    alert('Please click "▶ Start Episode" first before executing actions.');
    return;
  }
  if (episodeDone) {
    alert('Episode is finished. Click "▶ Start Episode" to begin a new one.');
    return;
  }

  const tool = document.getElementById('toolSelect').value;
  const raw  = document.getElementById('paramsInput').value.trim();

  if (!raw) {
    alert('Please type a value in the input field first.\\n' +
          document.getElementById('inputHint').innerText);
    return;
  }

  let params = {};

  if (tool === 'get_weather') {
    params = { city: raw };

  } else if (tool === 'search_flights') {
    const parts = raw.split(',');
    if (parts.length !== 2 || !parts[0].trim() || !parts[1].trim()) {
      alert('For Search Flights please enter Source and Destination separated by a comma.\\nExample: Pune, Delhi');
      return;
    }
    params = { source: parts[0].trim(), destination: parts[1].trim() };

  } else {
    params = { flight_number: raw };
  }

  const btn = document.getElementById('executeBtn');
  btn.disabled    = true;
  btn.textContent = '⏳ Running...';

  try {
    const res  = await fetch('/step', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ tool_name: tool, parameters: params })
    });
    const data = await res.json();

    if (!data.success) {
      appendTimeline('❌ Server error: ' + data.error);
      return;
    }

    const state = data.state;
    const last  = state.history[state.history.length - 1];
    stepCount   = state.step;

    const outputStr = JSON.stringify(last.output, null, 2)
      .split('\\n').map(l => '    ' + l).join('\\n');

    const sign = data.reward >= 0 ? '+' : '';
    appendTimeline(
      '── Step ' + state.step + ' ──────────────────────────\\n' +
      '  Tool      : ' + last.tool + '\\n' +
      '  Parameters: ' + JSON.stringify(last.parameters) + '\\n' +
      '  Output    :\\n' + outputStr + '\\n' +
      '  Reward    : ' + sign + data.reward.toFixed(2) +
        '   |   Total: ' + state.total_reward.toFixed(2)
    );

    updateStepsBar(stepCount, maxSteps);
    setRewardEl('stepReward',  data.reward);
    setRewardEl('totalReward', state.total_reward);
    setRewardEl('normScore',   state.normalized_score);

    if (data.done) {
      episodeDone     = true;
      btn.disabled    = true;
      btn.textContent = '⚡ Execute Action';
      setBadge('done');
      appendTimeline(
        '\\n🏁 Episode complete!  Final reward: ' + state.total_reward.toFixed(2) +
        '  |  Score: ' + (state.normalized_score * 100).toFixed(1) + '%' +
        '\\nClick "▶ Start Episode" to run a new episode.'
      );
    }

  } catch (err) {
    appendTimeline('❌ Network error: ' + err.message);
  } finally {
    if (!episodeDone) {
      btn.disabled    = false;
      btn.textContent = '⚡ Execute Action';
    }
  }
}

// ── BASELINE ──
async function runBaseline() {
  const btn = document.getElementById('baselineBtn');
  btn.disabled    = true;
  btn.textContent = '⏳ Running all tasks...';

  const out = document.getElementById('baselineOutput');
  out.textContent = 'Running baseline agent on easy, medium, and hard tasks...\\n';

  try {
    const res  = await fetch('/baseline');
    const data = await res.json();

    if (data.error) { out.textContent = '❌ Error: ' + data.error; return; }

    let display = '';
    for (const [, result] of Object.entries(data)) {
      const grade = result.normalized_score >= 0.8 ? '🟢' :
                    result.normalized_score >= 0.5 ? '🟡' : '🔴';
      display +=
        grade + ' Task: ' + result.task.toUpperCase() + '\\n' +
        '   Steps used   : ' + result.steps + '\\n' +
        '   Final reward : ' + result.final_reward.toFixed(2) + '\\n' +
        '   Score        : ' + (result.normalized_score * 100).toFixed(1) + '%\\n\\n';
    }
    out.textContent = display;

  } catch (err) {
    out.textContent = '❌ Network error: ' + err.message;
  } finally {
    btn.disabled    = false;
    btn.textContent = '🤖 Run Baseline Solver';
  }
}

</script>
</body>
</html>
"""


# =========================
# ROUTES
# =========================

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/reset', methods=['POST'])
def reset():
    try:
        data    = request.json or {}
        task_id = data.get('task_id', 'easy')
        state   = env.reset(task_id)
        return jsonify({'success': True, **state})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/step', methods=['POST'])
def step():
    try:
        data       = request.json or {}
        tool_name  = data.get('tool_name')
        parameters = data.get('parameters', {})

        # Guard: must call /reset before /step
        if env.current_task is None:
            return jsonify({
                'success': False,
                'error':   'No episode started. Call /reset first.'
            }), 400

        state, reward, done, info = env.step(tool_name, parameters)
        return jsonify({'success': True, 'state': state, 'reward': reward, 'done': done})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/baseline', methods=['GET'])
def run_baseline():
    try:
        results = baseline_agent.solve()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/grader', methods=['GET'])
def get_grader():
    try:
        return jsonify({'success': True, 'results': env.get_grading_results()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =========================
# SERVER START
# =========================

if __name__ == '__main__':
    port  = int(os.environ.get('PORT', 7860))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
