# 🌍 AgentsVille AI Trip Planner

An AI-powered travel planning system that generates and iteratively refines
day-by-day vacation itineraries using large language models, structured
evaluation, and a ReAct (Reason + Act) revision loop.

The system takes a traveler's preferences, fetches simulated weather and
activity data for AgentsVille, produces an initial itinerary, then automatically
revises it until five independent checks all pass – including budget accuracy,
date coverage, activity availability, and weather compatibility.

---

## Quick Start

### Installation

```bash
git clone https://github.com/ru14/llm-agent-trip-planner.git
cd llm-agent-trip-planner
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### API Key

```bash
export OPENAI_API_KEY="sk-..."
```

### Basic Usage

```python
from openai import OpenAI
from project_lib import (
    VacationInfo, get_weather_forecast, get_available_activities,
    run_evals, ItineraryAgent, ItineraryRevisionAgent, print_itinerary,
)

client = OpenAI()

vacation_info = VacationInfo(
    destination="AgentsVille",
    start_date="2026-06-10",
    end_date="2026-06-12",
    interests=["culture", "food"],
    budget=250.0,
)

weather_data         = get_weather_forecast(vacation_info)
available_activities = get_available_activities(vacation_info, weather_data)

initial_plan = ItineraryAgent(client=client).generate(
    vacation_info=vacation_info,
    weather_data=weather_data,
    available_activities=available_activities,
)

revision_agent = ItineraryRevisionAgent(client=client)
final_plan = revision_agent.revise(
    plan=initial_plan,
    vacation_info=vacation_info,
    weather_data=weather_data,
    available_activities=available_activities,
)

print_itinerary(final_plan)
```

**Expected output:**

```
📅  2026-06-10  |  weather: sunny
   • City Museum Tour        $30.00
   • Local Food Tour         $45.00
   Day total: $75.00
...
💰  Total: $220.00  (budget: $250.00)
✅  All 5 evaluation checks passed
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        project_starter.ipynb                     │
│  Steps 1-8: orchestration, display, save                         │
└────────────────────┬─────────────────────────────────────────────┘
                     │ imports
                     ▼
┌──────────────────────────────────────────────────────────────────┐
│                         project_lib.py                           │
│                                                                  │
│  ┌─────────────┐   ┌──────────────────┐   ┌──────────────────┐  │
│  │ Pydantic    │   │  Simulated APIs  │   │  Evaluation      │  │
│  │ Models      │   │                  │   │  System          │  │
│  │ VacationInfo│   │ get_weather_     │   │  5 checks        │  │
│  │ Activity    │   │ forecast()       │   │  (4 rule-based   │  │
│  │ DayPlan     │   │                  │   │   + 1 LLM)       │  │
│  │ TravelPlan  │   │ get_available_   │   │  run_evals()     │  │
│  └─────────────┘   │ activities()     │   └──────────────────┘  │
│                    └──────────────────┘                          │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │  Agents                                                  │    │
│  │  ItineraryAgent ──────────────► LLM (gpt-4o)            │    │
│  │  ItineraryRevisionAgent ──────► LLM + ReAct tools        │    │
│  │    • calculator_tool_fn                                  │    │
│  │    • get_activities_by_date_tool_fn                      │    │
│  │    • run_evals (via tool wrapper)                        │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

**Data flow:**

```
VacationInfo → weather forecast → available activities
    → ItineraryAgent → initial TravelPlan
        → run_evals (5 checks)
            → ItineraryRevisionAgent (ReAct loop)
                → final TravelPlan (all checks pass)
                    → generate_trip_summary → save JSON
```

---

## How It Works

| Step | Description |
|------|-------------|
| 1 | Define `VacationInfo` (destination, dates, interests, budget) |
| 2 | Simulate weather forecast and available activities per day |
| 3 | `ItineraryAgent` generates an initial JSON-structured plan |
| 4 | `run_evals` runs 5 automated checks on the initial plan |
| 5 | `ItineraryRevisionAgent` enters the ReAct loop |
| 6 | Agent cycles through THOUGHT → ACTION → OBSERVATION until all checks pass |
| 7 | `generate_trip_summary` writes a narrative overview |
| 8 | Final plan saved to `outputs/` as JSON |

### ReAct Loop

```
┌─────────────────────────────────────────────────┐
│                  ReAct Agent                    │
│                                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ THOUGHT │→ │ ACTION  │→ │  OBSERVATION    │ │
│  │ (LLM    │  │ (tool   │  │  (tool result   │ │
│  │  reason)│  │  call)  │  │   injected)     │ │
│  └─────────┘  └─────────┘  └────────┬────────┘ │
│       ▲                             │           │
│       └─────────────────────────────┘           │
│                                                 │
│  Exit: final_answer_tool called                 │
│        OR max iterations reached                │
└─────────────────────────────────────────────────┘
```

Available tools: `calculator_tool_fn`, `get_activities_by_date_tool_fn`,
`run_evals` (wrapper), `final_answer_tool`.

---

## System Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.8 or higher |
| OpenAI API key | Required – [get one here](https://platform.openai.com/api-keys) |
| RAM | 512 MB minimum |
| Disk | < 50 MB (excluding outputs) |
| Estimated API cost | ~$0.05–$0.15 per full run (gpt-4o + gpt-4o-mini) |

---

## Installation & Setup

### Virtual Environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### API Key Configuration

**Option A – Shell export (recommended):**
```bash
export OPENAI_API_KEY="sk-..."
```

**Option B – Inline in notebook (not for shared environments):**
```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."
```

### Vocareum Setup

1. Open a terminal in the Vocareum workspace.
2. Run `pip install -r requirements.txt`.
3. Set `OPENAI_API_KEY` in the environment variables panel.
4. Open `project_starter.ipynb` and run all cells.

---

## Usage Examples

### Culture Lover (3 days, $250)

```python
vacation_info = VacationInfo(
    destination="AgentsVille",
    start_date="2026-06-10",
    end_date="2026-06-12",
    interests=["art", "museums", "culture"],
    budget=250.0,
)
```

### Complex Constraints (outdoor focus, tight budget)

```python
vacation_info = VacationInfo(
    destination="AgentsVille",
    start_date="2026-06-13",
    end_date="2026-06-15",
    interests=["hiking", "sports", "outdoor activities"],
    budget=150.0,
    constraints=["avoid expensive activities"],
)
```

### Modifying Preferences

Change the `interests` list and `budget` in the `VacationInfo` object.
Any strings are accepted; the LLM maps them to the activity catalog.

### Running Test Scenarios

```bash
jupyter notebook test_scenarios.ipynb
```

Run all cells to execute 6 pre-built scenarios covering budget constraints,
outdoor adventures, cultural trips, food tours, extended stays, and weather
challenges.

---

## API Reference

See [`DOCUMENTATION.md`](DOCUMENTATION.md) for the full technical reference.

### Key Classes

| Class | Purpose |
|-------|---------|
| `VacationInfo` | Traveler preferences and constraints |
| `Activity` | Single activity with cost and description |
| `DayPlan` | One day's activities and subtotal |
| `TravelPlan` | Complete itinerary |
| `ItineraryAgent` | Generates the initial plan |
| `ItineraryRevisionAgent` | Refines the plan via ReAct |

### Key Functions

| Function | Purpose |
|----------|---------|
| `get_weather_forecast(vi)` | Returns `{date: condition}` mapping |
| `get_available_activities(vi, weather)` | Returns activities filtered by weather |
| `run_evals(plan, vi, weather, activities, client)` | Runs all 5 checks |
| `generate_trip_summary(plan, vi, client)` | Writes a narrative summary |
| `print_itinerary(plan)` | Pretty-prints the plan |
| `print_eval_results(results)` | Pretty-prints evaluation results |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `AuthenticationError` | Set `OPENAI_API_KEY` correctly |
| `RateLimitError` | Add `time.sleep(10)` between scenarios or use a paid tier |
| `ValidationError` from Pydantic | Check JSON schema matches `TravelPlan` fields |
| Plan exceeds budget | The ReAct agent will retry; increase `max_iterations` if needed |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| LLM returns non-JSON | Update the `openai` package to the latest version |

---

## Contributing

1. Fork the repository and create a feature branch.
2. Follow [PEP 8](https://peps.python.org/pep-0008/) and add type hints.
3. Add docstrings to all new public functions.
4. Add a test scenario in `test_scenarios.ipynb` for any new feature.
5. Run the full test notebook before submitting a pull request.

**Adding a new activity:**

```python
# In project_lib.py, append to ACTIVITIES_CATALOG:
{
    "name": "My New Activity",
    "cost": 40.0,
    "description": "Short description of the activity",
    "weather_requirement": "any",   # "any" | "sunny" | "sunny_or_partly_cloudy"
    "category": "culture",
}
```

**Adding a new evaluation check:**

1. Write `_check_my_rule(plan, vacation_info) -> tuple[bool, str]`.
2. Call it inside `run_evals()` and add the result to `results`.

---

## License & Attribution

This project was developed as part of an AI/LLM course assignment.

**Dependencies:**
- [OpenAI Python SDK](https://github.com/openai/openai-python) – MIT License
- [Pydantic](https://docs.pydantic.dev/) – MIT License
- [Jupyter](https://jupyter.org/) – BSD License
