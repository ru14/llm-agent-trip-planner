# DOCUMENTATION – AgentsVille AI Trip Planner

Technical reference for `project_lib.py` and the surrounding system.

---

## Section 1 – Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────────┐
│  project_starter.ipynb   (user-facing orchestration)               │
│  test_scenarios.ipynb    (automated test suite)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          project_lib.py                             │
│                                                                     │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Pydantic Models     │  │  Simulated APIs                      │ │
│  │  ─────────────────── │  │  ──────────────────────────────────  │ │
│  │  VacationInfo        │  │  get_weather_forecast()              │ │
│  │  Activity            │  │  get_available_activities()          │ │
│  │  DayPlan             │  │  ACTIVITIES_CATALOG (18 entries)     │ │
│  │  TravelPlan          │  └──────────────────────────────────────┘ │
│  └──────────────────────┘                                           │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Evaluation System                                           │   │
│  │  ──────────────────────────────────────────────────────────  │   │
│  │  _check_budget_accuracy       (rule-based)                   │   │
│  │  _check_city_date_correctness (rule-based)                   │   │
│  │  _check_minimum_activities    (rule-based)                   │   │
│  │  _check_activity_availability (rule-based)                   │   │
│  │  _check_weather_compatibility (LLM-based)                    │   │
│  │  run_evals() ─── aggregates all 5                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Agents                                                      │   │
│  │  ItineraryAgent           ──► LLM structured output          │   │
│  │  ItineraryRevisionAgent   ──► ReAct loop + 4 tools           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Helpers                                                     │   │
│  │  generate_trip_summary()  print_itinerary()  print_eval_results() │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
[User] ──► VacationInfo ──► get_weather_forecast()
                        ──► get_available_activities()
                                      │
                                      ▼
                           ItineraryAgent.generate()
                                      │
                               initial TravelPlan
                                      │
                                      ▼
                              run_evals() ──► 5 check results
                                      │
                        ┌─── all_passed? ───┐
                        │ yes               │ no
                        │                  ▼
                        │    ItineraryRevisionAgent.revise()
                        │          (ReAct loop)
                        │                  │
                        └──────────────────┘
                                      │
                               final TravelPlan
                                      │
                            generate_trip_summary()
                                      │
                            save to outputs/*.json
```

---

## Section 2 – Pydantic Models Reference

### VacationInfo

```python
class VacationInfo(BaseModel):
    destination: str        # e.g. "AgentsVille"
    start_date:  str        # ISO format "YYYY-MM-DD"
    end_date:    str        # ISO format "YYYY-MM-DD"
    interests:   List[str]  # e.g. ["culture", "food", "outdoor activities"]
    budget:      float      # total USD budget
    constraints: List[str]  # optional, e.g. ["vegetarian", "low budget"]
```

**Validation rules:**
- All fields are required except `constraints` (defaults to `[]`).
- `start_date` and `end_date` must be parseable by `datetime.date.fromisoformat()`.
- `budget` must be a positive number.

### Activity

```python
class Activity(BaseModel):
    name:        str    # Display name
    cost:        float  # USD cost per person
    description: str    # Brief description
```

### DayPlan

```python
class DayPlan(BaseModel):
    date:           str            # "YYYY-MM-DD"
    activities:     List[Activity] # 2+ required to pass evaluations
    day_total_cost: float          # must equal sum of activity costs
```

### TravelPlan

```python
class TravelPlan(BaseModel):
    destination: str           # must match VacationInfo.destination
    days:        List[DayPlan] # one entry per trip day
    total_cost:  float         # must equal sum of day_total_cost
    summary:     Optional[str] # narrative added in Step 7
```

---

## Section 3 – Activity Catalog

18 activities are defined in `ACTIVITIES_CATALOG`. Each entry has:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Display name |
| `cost` | float | USD cost |
| `description` | str | Short description |
| `weather_requirement` | str | `"any"` \| `"sunny"` \| `"sunny_or_partly_cloudy"` |
| `category` | str | `culture` \| `food` \| `sports` \| `outdoor` \| `entertainment` \| `leisure` \| `sightseeing` \| `wellness` |

### Weather Requirements Explained

| Requirement | Allowed weather |
|-------------|----------------|
| `any` | All conditions (sunny, partly_cloudy, cloudy, rainy, stormy) |
| `sunny_or_partly_cloudy` | sunny, partly_cloudy only |
| `sunny` | sunny only |

### Activities by Category

| Category | Activities |
|----------|-----------|
| culture | City Museum Tour, Art Gallery Visit, Photography Walk |
| food | Local Food Tour, Cooking Class, Wine Tasting Tour, Farmers Market, Night Food Market |
| sports | Beach Volleyball, Scuba Diving, Kayaking Adventure |
| outdoor | Hiking in National Park |
| entertainment | Jazz Night at Blue Moon, Comedy Show, Escape Room |
| leisure | Sunset Boat Cruise |
| sightseeing | City Bus Tour |
| wellness | Spa Day |

### Cost Range

| Tier | Activities |
|------|-----------|
| Budget (≤ $20) | Beach Volleyball ($15), Farmers Market ($10), Art Gallery Visit ($20), Night Food Market ($20) |
| Mid-range ($21–$60) | City Museum Tour ($30), Hiking ($25), Jazz Night ($40), Cooking Class ($60), Wine Tasting ($55), Comedy Show ($35), City Bus Tour ($25), Escape Room ($30), Kayaking ($50), Photography Walk ($35), Local Food Tour ($45) |
| Premium (> $60) | Scuba Diving ($120), Spa Day ($80), Sunset Boat Cruise ($75) |

---

## Section 4 – Evaluation System Deep Dive

`run_evals()` runs five checks and returns:

```python
{
    "budget_accuracy":       {"passed": bool, "message": str},
    "city_date_correctness": {"passed": bool, "message": str},
    "minimum_activities":    {"passed": bool, "message": str},
    "activity_availability": {"passed": bool, "message": str},
    "weather_compatibility": {"passed": bool, "message": str},
    "all_passed":            bool,
}
```

### Check 1 – Budget Accuracy (rule-based)

Recalculates `total_cost` from individual activity costs and verifies:
1. Each `day.day_total_cost` matches the sum of its activities (tolerance: ±$0.01).
2. `plan.total_cost` matches the recalculated sum.
3. `plan.total_cost ≤ vacation_info.budget`.

### Check 2 – City/Date Correctness (rule-based)

1. `plan.destination` must equal `vacation_info.destination` (case-insensitive).
2. The set of `day.date` values must exactly equal the set of dates from
   `vacation_info.start_date` to `vacation_info.end_date` (inclusive).

### Check 3 – Minimum Activities (rule-based)

Every `DayPlan` must have `len(activities) >= 2`.

### Check 4 – Activity Availability (rule-based)

For every activity in every day, the activity name must appear in
`available_activities[day.date]` (case-insensitive). Activities that fail
the weather filter are not in the available list.

### Check 5 – Weather Compatibility (LLM-based)

The schedule is passed to `gpt-4o-mini` with a weather-compatibility guide.
The LLM returns `{"compatible": bool, "issues": [...]}`.

---

## Section 5 – Prompt Engineering

### ItineraryAgent System Prompt

Location: `ItineraryAgent._build_context()` (lines ~791–858 in `project_lib.py`).

**Structure:**
1. **Role** – "expert travel itinerary planner for AgentsVille"
2. **Task** – step-by-step instructions including budget constraints, weather
   awareness, and interest matching
3. **Output format** – JSON schema for `TravelPlan` embedded in the prompt
4. **Context** – actual `VacationInfo`, weather data, and available activities
   injected via f-string

**Design decisions:**
- JSON mode (`response_format={"type": "json_object"}`) enforces structured output.
- The full activity list is injected so the agent can only pick real activities.
- Explicit instruction: "Do not invent activities not in the provided list."

### Weather Compatibility System Prompt

Location: `_check_weather_compatibility()`.

**Structure:**
1. Role: weather reviewer
2. Weather guide mapping conditions to allowed activities
3. JSON output schema: `{"compatible": bool, "issues": [...]}`

**Design decisions:**
- Using `response_format={"type": "json_object"}` for reliable parsing.
- Weather rules are spelled out explicitly to reduce hallucination.

### ItineraryRevisionAgent System Prompt

Location: `ItineraryRevisionAgent._build_initial_message()` (lines ~1044–1102).

**Structure:**
1. **Role** – expert travel planner tasked with revising itineraries
2. **Tools** – four tools described with name, arguments, return type
3. **ReAct framework** – explicit THOUGHT/ACTION/OBSERVATION instructions
4. **Tool call format** – JSON `{"tool_name": "...", "arguments": {...}}`
5. **Exit condition** – call `final_answer_tool` when all evaluations pass

**Design decisions:**
- The agent is shown the full evaluation result on each loop so it knows
  exactly which checks failed.
- Max iterations prevent infinite loops.

---

## Section 6 – ReAct Loop State Machine

```
         ┌─────────────────────┐
         │     Initial State   │
         │  receive plan +     │
         │  eval failures      │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
    ┌──► │  THOUGHT            │
    │    │  LLM reasons about  │
    │    │  what to do next    │
    │    └──────────┬──────────┘
    │               │
    │               ▼
    │    ┌─────────────────────┐
    │    │  ACTION             │
    │    │  LLM emits JSON     │
    │    │  tool call          │
    │    └──────────┬──────────┘
    │               │
    │         ┌─────┴──────────────────────┐
    │         │ tool_name                  │
    │         ├──────────────┬─────────────┤
    │  calc   │ get_acts     │ run_evals   │ final_answer
    │  ──────►│ ────────────►│ ──────────►│ ──────────►
    │         └──────────────┴─────────────┘
    │               │                         │
    │    ┌──────────▼──────────┐    ┌─────────▼──────────┐
    └────┤  OBSERVATION        │    │  EXIT               │
         │  tool result        │    │  return final plan  │
         │  injected into      │    └────────────────────┘
         │  conversation       │
         └─────────────────────┘

  Also exits when max_iterations reached.
```

---

## Section 7 – Tool Reference

### `calculator_tool_fn(costs: List[float]) -> Dict[str, Any]`

Sums a list of floats. Used by the revision agent to verify cost totals.

**Returns:** `{"total": float, "breakdown": [float, ...]}`

### `get_activities_by_date_tool_fn(date: str, city: str) -> List[Dict]`

Returns all weather-compatible activities for a given date. The agent uses
this to discover valid replacement activities when a check fails.

**Args:**
- `date` – ISO format "YYYY-MM-DD" (must fall within trip dates)
- `city` – must be "AgentsVille"

**Returns:** List of activity dicts from `ACTIVITIES_CATALOG`.

### `run_evals` (tool wrapper)

Wraps `run_evals()` for use as a ReAct tool. The agent calls this to check
whether its revised plan passes all five checks.

**Returns:** `{"all_passed": bool, failures: [{"check": str, "message": str}]}`

### `final_answer_tool`

Signals that the agent has produced a satisfactory plan. The revision loop
exits and returns the plan.

**Args:** `final_output` – the `TravelPlan` JSON.

---

## Section 8 – Weather System

### Weather Conditions

| Condition | Description |
|-----------|-------------|
| `sunny` | Clear skies – all activities permitted |
| `partly_cloudy` | Mild cloud – outdoor activities (non-sun-only) permitted |
| `cloudy` | Full cloud – only `any`-weather activities |
| `rainy` | Rain – only `any`-weather (indoor) activities |
| `stormy` | Storm – only `any`-weather (indoor) activities |

### Forecast Generation

`get_weather_forecast()` uses a deterministic formula:

```python
idx = (current.day * 3 + current.month * 7) % len(weather_pool)
```

The `weather_pool` has 8 entries (biased towards sunny/partly_cloudy),
producing consistent, reproducible forecasts for the same dates.

### Activity Compatibility Mapping

`_is_weather_compatible(requirement, weather)` returns True when:

| requirement | allowed weather |
|-------------|----------------|
| `any` | all |
| `sunny_or_partly_cloudy` | sunny, partly_cloudy |
| `sunny` | sunny only |

---

## Section 9 – Performance & Optimization

### Token Usage (approximate per run)

| Step | Model | Tokens (in/out) |
|------|-------|----------------|
| ItineraryAgent.generate | gpt-4o | ~1 500 / ~500 |
| Each ReAct iteration | gpt-4o | ~2 000 / ~300 |
| Weather compat check | gpt-4o-mini | ~800 / ~100 |
| Trip summary | gpt-4o | ~500 / ~200 |

A typical 3-day run with 2–3 ReAct iterations uses ~8 000–12 000 tokens total.

### Cost Estimate

At July 2025 pricing:
- gpt-4o: $5/1M input, $15/1M output
- gpt-4o-mini: $0.15/1M input, $0.60/1M output

Typical run: **~$0.05–$0.15 USD**.

### Scalability

The number of ReAct iterations scales roughly with constraint complexity.
A 6-day trip with mixed weather requires 3–6 iterations on average.
The `max_iterations` safeguard (default: 10) prevents runaway loops.

---

## Section 10 – Extension Guide

### Adding a New Activity

1. Append to `ACTIVITIES_CATALOG` in `project_lib.py`:

```python
{
    "name": "New Activity Name",
    "cost": 35.0,
    "description": "What the activity involves",
    "weather_requirement": "any",   # or "sunny" or "sunny_or_partly_cloudy"
    "category": "entertainment",
}
```

2. No other changes are needed – the catalog is injected into agent prompts
   automatically.

### Adding a New Evaluation Check

1. Write a private function:

```python
def _check_my_rule(plan: TravelPlan, vacation_info: VacationInfo) -> tuple[bool, str]:
    if <condition fails>:
        return False, "Failure message"
    return True, "Pass message"
```

2. Call it in `run_evals()`:

```python
passed, msg = _check_my_rule(plan, vacation_info)
results["my_rule"] = {"passed": passed, "message": msg}
```

### Modifying the Revision Agent

- Change `max_iterations` in `ItineraryRevisionAgent.__init__()`.
- Add tools to `TOOLS_SCHEMA` and the tool dispatch dict in `revise()`.
- Update the system prompt to describe new tools.

### Custom Agent Strategies

Subclass `ItineraryRevisionAgent` and override `_build_initial_message()` to
inject custom instructions or few-shot examples.
