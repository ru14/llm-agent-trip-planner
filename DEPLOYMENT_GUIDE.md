# Deployment Guide – AgentsVille AI Trip Planner

Step-by-step instructions for running the system locally or on Vocareum.

---

## Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ru14/llm-agent-trip-planner.git
cd llm-agent-trip-planner
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs: `openai`, `pydantic`, `jupyter`, `notebook`, `ipykernel`.

### 4. Configure the OpenAI API Key

```bash
export OPENAI_API_KEY="sk-..."   # Linux / macOS
# set OPENAI_API_KEY=sk-...      # Windows cmd
# $env:OPENAI_API_KEY="sk-..."   # Windows PowerShell
```

### 5. Launch Jupyter

```bash
jupyter notebook
```

Open `project_starter.ipynb` in the browser and run all cells from top to bottom.

---

## Vocareum Setup

1. In the Vocareum workspace, open a terminal.
2. Run `pip install -r requirements.txt --quiet`.
3. In the Environment Variables panel, add `OPENAI_API_KEY` = your key.
4. Open `project_starter.ipynb`.
5. Select **Kernel → Restart & Run All**.

---

## Running the Test Suite

```bash
jupyter notebook test_scenarios.ipynb
```

Select **Kernel → Restart & Run All** and wait for all 6 scenarios to complete.
A summary table appears in the last cell showing pass/fail status for each scenario.

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MAIN_MODEL` | `"gpt-4o"` | Model for itinerary generation and revision |
| `EVAL_MODEL` | `"gpt-4o-mini"` | Model for weather compatibility evaluation |
| `max_iterations` | `10` | Maximum ReAct loop iterations per revision |

Change these in the notebook's setup cell or in the `ItineraryRevisionAgent`
constructor call.

---

## Interpreting Results

- **`print_itinerary(plan)`** – shows day-by-day activities and costs.
- **`print_eval_results(results)`** – shows ✅/❌ for each of the 5 checks.
- **`reasoning_log`** – inspect `revision_agent.reasoning_log` to see every
  THOUGHT, ACTION, and OBSERVATION in the ReAct loop.
- **`outputs/`** – the final plan JSON is saved here after Step 8.

---

## Common Configuration Issues

| Issue | Fix |
|-------|-----|
| Wrong Python version | Ensure Python 3.8+ with `python --version` |
| Jupyter not found | Run `pip install jupyter notebook` |
| Kernel dies during execution | Increase memory limit in Jupyter settings |
| Slow responses | Switch `MAIN_MODEL` to `"gpt-4o-mini"` for faster, cheaper runs |
