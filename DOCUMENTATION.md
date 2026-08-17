# AgentsVille AI Trip Planner – Technical Documentation

---

## 1. Architecture Overview

### System Components

```
project_lib.py
├── Pydantic Models
│   ├── VacationInfo      – traveller preferences and constraints
│   ├── Activity          – single activity (name, cost, description)
│   ├── DayPlan           – one day's activities and cost
│   └── TravelPlan        – complete itinerary (destination, days, total_cost)
│
├── Simulated Data
│   ├── ACTIVITIES_CATALOG  – 18 activities across 7 categories
│   └── get_weather_forecast / get_available_activities
│
├── Evaluation System (run_evals)
│   ├── _check_budget_accuracy        (rule-based)
│   ├── _check_city_date_correctness  (rule-based)
│   ├── _check_minimum_activities     (rule-based)
│   ├── _check_activity_availability  (rule-based)
│   └── _check_weather_compatibility  (LLM-based, gpt-4o-mini)
│
├── Tool Functions (for OpenAI function-calling)
│   ├── calculator_tool_fn
│   ├── get_activities_by_date_tool_fn
│   └── TOOLS_SCHEMA (4 schemas: calculator, activities, run_evals, final_answer)
│
├── Agents
│   ├── ItineraryAgent          – initial plan generation
│   └── ItineraryRevisionAgent  – ReAct revision loop
│
└── Display Helpers
    ├── generate_trip_summary
    ├── print_itinerary
    └── print_eval_results
```

### Data Flow

```
VacationInfo
     │
     ├──► get_weather_forecast()     ──► weather_data: Dict[date, condition]
     │
     └──► get_available_activities() ──► available_activities: Dict[date, [Activity]]
                │
                └──► ItineraryAgent.generate()
                          │
                          └──► TravelPlan (initial)
                                    │
                                    └──► run_evals()
                                              │
                                    ┌─────────┴──────────┐
                                    │                    │
                               all pass              any fail
                                    │                    │
                             generate_trip         ItineraryRevisionAgent.revise()
                                 summary()                    │
                                    │                final validated TravelPlan
                             print_itinerary()
```

---

## 2. Detailed Component Guides

### 2.1 VacationInfo Model

```python
class VacationInfo(BaseModel):
    destination: str          # City/region name; used in city_date_correctness check
    start_date:  str          # "YYYY-MM-DD"; inclusive
    end_date:    str          # "YYYY-MM-DD"; inclusive
    interests:   List[str]    # e.g. ["food", "outdoor"] – guides LLM activity selection
    budget:      float        # Total USD budget; enforced by budget_accuracy check
    constraints: List[str]    # Optional – e.g. ["vegetarian", "accessibility"]
```

**Field notes:**
- `interests` directly influences which activities the ItineraryAgent selects.
  Use catalog categories (`culture`, `food`, `outdoor`, `sports`,
  `entertainment`, `sightseeing`, `wellness`) for best results.
- `constraints` are passed as context to the LLM but are **not** enforced by
  the rule-based checks. For hard constraints, extend the evaluation system.

### 2.2 Activity and DayPlan Models

```python
class Activity(BaseModel):
    name:        str    # Must match ACTIVITIES_CATALOG name exactly
    cost:        float  # Must match catalog cost exactly
    description: str    # Free-text; typically copied from catalog

class DayPlan(BaseModel):
    date:           str            # "YYYY-MM-DD"
    activities:     List[Activity]
    day_total_cost: float          # Must equal sum(a.cost for a in activities)
```

### 2.3 Activity Catalog Structure

Each entry in `ACTIVITIES_CATALOG` has five fields:

| Field | Type | Values |
|---|---|---|
| `name` | str | Unique display name |
| `cost` | float | USD price |
| `description` | str | Short description |
| `weather_requirement` | str | `"any"`, `"sunny"`, `"sunny_or_partly_cloudy"` |
| `category` | str | `culture`, `food`, `outdoor`, `sports`, `entertainment`, `sightseeing`, `wellness` |

**Weather compatibility matrix:**

| Weather | `"any"` | `"sunny_or_partly_cloudy"` | `"sunny"` |
|---|---|---|---|
| sunny | ✅ | ✅ | ✅ |
| partly_cloudy | ✅ | ✅ | ❌ |
| cloudy | ✅ | ❌ | ❌ |
| rainy | ✅ | ❌ | ❌ |
| stormy | ✅ | ❌ | ❌ |

### 2.4 Weather Simulation Logic

```python
# Deterministic formula – reproducible for a given start_date
idx = (current.day * 3 + current.month * 7) % len(weather_pool)
```

`weather_pool = ["sunny", "partly_cloudy", "sunny", "sunny",
                 "partly_cloudy", "cloudy", "rainy", "stormy"]`

This ensures consistent weather across runs (no random seed needed).

---

## 3. Prompt Engineering Notes

### 3.1 ItineraryAgent System Prompt

**Design goals:**
- Clear role statement: "expert travel planner for AgentsVille"
- Explicit task decomposition: interests → weather → budget → variety
- Hard constraints for JSON schema compliance
- Emphasis on cost arithmetic accuracy (a common LLM failure mode)

**Key design choices:**
- Telling the LLM "the Available Activities list is already filtered" prevents
  it from second-guessing weather compatibility.
- Demanding exact names/costs from the catalog prevents hallucination of
  non-existent activities.

**Example of a good output:** 3-day plan, 2-3 activities/day, costs sum
correctly, varied categories, all within budget.

**Example of a bad output:** Activities not in catalog, day_total_cost doesn't
sum activities, over-budget plan. The evaluation + revision system catches these.

### 3.2 Revision Agent System Prompt

**Design goals:**
- Explicit ReAct framing: THOUGHT → ACTION → OBSERVATION
- Full list of available tools with descriptions
- Hard rules for arithmetic correctness
- Condition for submitting: "ONLY when all checks pass"

**Tuning guidelines:**
- If the agent loops without converging, check whether the budget is too low
  for the number of days (add a pre-flight budget validation).
- If the agent submits before all checks pass, tighten the system prompt to
  emphasise "verify with run_evals_tool before calling final_answer_tool".

---

## 4. ReAct Loop Deep Dive

### State Machine

```
    ┌──────────┐
    │  START   │  initial plan + eval results
    └────┬─────┘
         │
         ▼
    ┌──────────────────────────────────────────────┐
    │  THINK: analyse failing checks                │
    │  → identify root cause (weather / budget /    │
    │    arithmetic / missing dates)                │
    └────────────┬─────────────────────────────────┘
                 │
        ┌────────▼─────────┐
        │ tool_choice=auto  │  LLM selects a tool
        └────────┬──────────┘
                 │
     ┌───────────┼──────────────────────────┐
     │           │           │              │
     ▼           ▼           ▼              ▼
calculator  get_activities run_evals   final_answer
  _tool      _by_date_tool   _tool        _tool
     │           │           │              │
     └───────────┴─────┬─────┘              │ done=True
                       │                    └──► END
                  OBSERVE result
                       │
                  next iteration ──► THINK again
```

### Tool Execution Flow

1. `calculator_tool` – pure Python sum, no LLM call
2. `get_activities_by_date_tool` – filters `ACTIVITIES_CATALOG` against
   `weather_data` for the requested date
3. `run_evals_tool` – validates a candidate plan; returns full eval dict
4. `final_answer_tool` – validates the plan with Pydantic and stores it as the
   result; sets `done=True` to exit the loop

### Error Handling

- Pydantic `ValidationError` from `TravelPlan.model_validate()` → returns
  `{"error": str(exc), "all_passed": False}` so the agent can retry.
- Unknown tool name → returns `{"error": "Unknown tool: <name>"}`.
- Max iterations reached → loop exits and returns the last `current_plan`.

---

## 5. Evaluation System Details

### Check 1 – budget_accuracy (rule-based)

1. Recalculate `day_total_cost` for every day from `sum(a.cost for a in day.activities)`.
2. Fail if any day's stored cost differs by more than `$0.01`.
3. Recalculate `total_cost` from `sum(day.day_total_cost for day in plan.days)`.
4. Fail if stored total differs by more than `$0.01`.
5. Fail if `total_cost > vacation_info.budget`.

**Edge cases:** Floating-point accumulation errors are handled by the `$0.01`
tolerance. The revision agent uses `calculator_tool` to avoid these errors.

### Check 2 – city_date_correctness (rule-based)

1. Case-insensitive comparison of `plan.destination` vs `vacation_info.destination`.
2. Build expected date set from `start_date` to `end_date` (inclusive).
3. Compare with `{day.date for day in plan.days}` – report missing/extra dates.

### Check 3 – minimum_activities (rule-based)

- Default threshold: `min_per_day=2`.
- Fails if any day has fewer than 2 activities.

### Check 4 – activity_availability (rule-based)

- For each day, look up available activity names (from `available_activities`).
- Case-insensitive name matching.
- Catches both "wrong weather" and "hallucinated activity" failures.

### Check 5 – weather_compatibility (LLM-based)

Uses `gpt-4o-mini` in JSON mode with a detailed prompt describing the weather
compatibility rules for each weather condition. Returns
`{"compatible": bool, "issues": [...]}`.

**Why LLM-based?** This check acts as a second opinion to catch subtle
mismatches that the rule-based availability check might miss (e.g., an activity
marked "any" weather that is logically incompatible with a stormy day).

**Limitation:** Non-deterministic – rare false positives possible. The
availability check (rule-based) is the primary gate for weather compliance.

### How Checks Work Together

Checks 1-4 are fast and deterministic; they run first. Check 5 (LLM) runs
after and provides a semantic safety net. All five must pass for
`all_passed=True`.

---

## 6. API Reference

### `VacationInfo`
Pydantic model. All fields required except `constraints` (default `[]`).

### `TravelPlan`
Pydantic model. Field `summary` is optional (set by `generate_trip_summary`).

### `get_weather_forecast(vacation_info) -> Dict[str, str]`
Returns `{date_str: weather_condition}` for all trip dates.

### `get_available_activities(vacation_info, weather_data) -> Dict[str, List[Dict]]`
Returns `{date_str: [activity_dict]}` filtered by that day's weather.

### `run_evals(plan, vacation_info, weather_data, available_activities, client, model) -> Dict`
Returns `{check_name: {"passed": bool, "message": str}, "all_passed": bool}`.

### `ItineraryAgent(client, model="gpt-4o")`
- `.generate(vacation_info, weather_data, available_activities) -> TravelPlan`

### `ItineraryRevisionAgent(client, model="gpt-4o")`
- `.revise(plan, vacation_info, weather_data, available_activities, eval_model) -> TravelPlan`
- `.reasoning_log` – list of `{type, ...}` dicts recorded during revision

### `generate_trip_summary(plan, vacation_info, client, model) -> str`
Returns a 2-3 sentence narrative summary.

### `print_itinerary(plan) -> None`
Pretty-prints the plan to stdout.

### `print_eval_results(eval_results) -> None`
Pretty-prints evaluation results to stdout.
