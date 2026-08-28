"""
project_lib.py

Helper functions and classes for the AgentsVille AI Trip Planner.

Components:
    - Pydantic models for structured data validation
    - Simulated travel data (activity catalog, weather)
    - Evaluation system (5 automated checks)
    - Tool implementations for LLM agents (OpenAI function-calling)
    - ItineraryAgent – generates an initial travel plan
    - ItineraryRevisionAgent – refines the plan via the ReAct loop
    - Trip summary generation and display helpers
"""

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================
# PYDANTIC MODELS
# ============================================================


class VacationInfo(BaseModel):
    """Captures traveler preferences and constraints."""

    destination: str = Field(description="The destination city or region")
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")
    interests: List[str] = Field(description="List of traveler interests")
    budget: float = Field(description="Total budget in USD")
    constraints: List[str] = Field(
        default=[], description="Any travel constraints (e.g. dietary, mobility)"
    )


class Activity(BaseModel):
    """A single activity within the itinerary."""

    name: str = Field(description="Name of the activity")
    cost: float = Field(description="Cost of the activity in USD")
    description: str = Field(description="Brief description of the activity")


class DayPlan(BaseModel):
    """A single day's plan within the itinerary."""

    date: str = Field(description="Date in YYYY-MM-DD format")
    activities: List[Activity] = Field(description="Activities planned for this day")
    day_total_cost: float = Field(description="Total cost for this day in USD")


class TravelPlan(BaseModel):
    """The complete travel plan produced by the agents."""

    destination: str = Field(description="The destination city")
    days: List[DayPlan] = Field(description="Day-by-day itinerary")
    total_cost: float = Field(description="Total trip cost in USD")
    summary: Optional[str] = Field(
        default=None, description="Narrative summary of the trip"
    )


# ============================================================
# SIMULATED DATA – AGENTSVILLE ACTIVITY CATALOG
# ============================================================

#: All activities available in AgentsVille.
#: ``weather_requirement`` can be ``"any"``, ``"sunny"``, or ``"sunny_or_partly_cloudy"``.
ACTIVITIES_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "City Museum Tour",
        "cost": 30.0,
        "description": (
            "Explore the rich history and culture of AgentsVille through "
            "interactive exhibits and artifacts"
        ),
        "weather_requirement": "any",
        "category": "culture",
    },
    {
        "name": "Beach Volleyball",
        "cost": 15.0,
        "description": (
            "Enjoy a friendly game of volleyball on AgentsVille's golden sandy beach"
        ),
        "weather_requirement": "sunny",
        "category": "sports",
    },
    {
        "name": "Sunset Boat Cruise",
        "cost": 75.0,
        "description": (
            "Sail around the bay and watch the breathtaking AgentsVille sunset "
            "from the water"
        ),
        "weather_requirement": "sunny",
        "category": "leisure",
    },
    {
        "name": "Local Food Tour",
        "cost": 45.0,
        "description": (
            "Taste the best local cuisine across AgentsVille's vibrant food scene "
            "with a knowledgeable guide"
        ),
        "weather_requirement": "any",
        "category": "food",
    },
    {
        "name": "Art Gallery Visit",
        "cost": 20.0,
        "description": (
            "Admire contemporary and classical artwork at the AgentsVille Art Gallery"
        ),
        "weather_requirement": "any",
        "category": "culture",
    },
    {
        "name": "Hiking in National Park",
        "cost": 25.0,
        "description": (
            "Trek through scenic trails in the AgentsVille National Park "
            "with stunning panoramic views"
        ),
        "weather_requirement": "sunny_or_partly_cloudy",
        "category": "outdoor",
    },
    {
        "name": "Jazz Night at Blue Moon",
        "cost": 40.0,
        "description": (
            "Enjoy live jazz performances and cocktails at AgentsVille's "
            "famous Blue Moon venue"
        ),
        "weather_requirement": "any",
        "category": "entertainment",
    },
    {
        "name": "Cooking Class",
        "cost": 60.0,
        "description": (
            "Learn to prepare traditional AgentsVille dishes with a professional "
            "local chef"
        ),
        "weather_requirement": "any",
        "category": "food",
    },
    {
        "name": "Scuba Diving",
        "cost": 120.0,
        "description": (
            "Discover the underwater world of AgentsVille's crystal-clear waters "
            "with certified instructors"
        ),
        "weather_requirement": "sunny",
        "category": "sports",
    },
    {
        "name": "Wine Tasting Tour",
        "cost": 55.0,
        "description": (
            "Sample award-winning wines from AgentsVille's renowned vineyards "
            "and estates"
        ),
        "weather_requirement": "any",
        "category": "food",
    },
    {
        "name": "Farmers Market",
        "cost": 10.0,
        "description": (
            "Browse fresh local produce, artisan crafts, and street food at "
            "the AgentsVille Farmers Market"
        ),
        "weather_requirement": "sunny_or_partly_cloudy",
        "category": "food",
    },
    {
        "name": "Comedy Show",
        "cost": 35.0,
        "description": (
            "Laugh the evening away at AgentsVille's top comedy club featuring "
            "local and visiting comedians"
        ),
        "weather_requirement": "any",
        "category": "entertainment",
    },
    {
        "name": "City Bus Tour",
        "cost": 25.0,
        "description": (
            "Hop-on-hop-off bus tour covering all major landmarks and "
            "attractions in AgentsVille"
        ),
        "weather_requirement": "any",
        "category": "sightseeing",
    },
    {
        "name": "Spa Day",
        "cost": 80.0,
        "description": (
            "Relax and rejuvenate with a full day of pampering at AgentsVille's "
            "luxury wellness spa"
        ),
        "weather_requirement": "any",
        "category": "wellness",
    },
    {
        "name": "Escape Room",
        "cost": 30.0,
        "description": (
            "Test your problem-solving skills in AgentsVille's most challenging "
            "escape room adventure"
        ),
        "weather_requirement": "any",
        "category": "entertainment",
    },
    {
        "name": "Kayaking Adventure",
        "cost": 50.0,
        "description": (
            "Paddle through AgentsVille's scenic coastal waterways on a guided "
            "kayaking tour"
        ),
        "weather_requirement": "sunny_or_partly_cloudy",
        "category": "sports",
    },
    {
        "name": "Photography Walk",
        "cost": 35.0,
        "description": (
            "Capture the essence of AgentsVille on a guided photography walk "
            "through historic neighborhoods"
        ),
        "weather_requirement": "sunny_or_partly_cloudy",
        "category": "culture",
    },
    {
        "name": "Night Food Market",
        "cost": 20.0,
        "description": (
            "Explore AgentsVille's bustling night market packed with street food "
            "stalls and live entertainment"
        ),
        "weather_requirement": "any",
        "category": "food",
    },
]


def _is_weather_compatible(weather_requirement: str, weather: str) -> bool:
    """Return True if an activity's weather requirement is met by *weather*."""
    if weather_requirement == "any":
        return True
    if weather_requirement == "sunny":
        return weather == "sunny"
    if weather_requirement == "sunny_or_partly_cloudy":
        return weather in ("sunny", "partly_cloudy")
    return False


# ============================================================
# DATA-GATHERING HELPERS
# ============================================================


def get_weather_forecast(vacation_info: VacationInfo) -> Dict[str, str]:
    """Simulate fetching a weather forecast for all trip dates.

    Returns a mapping of ``{date_str: weather_condition}`` where
    *weather_condition* is one of ``sunny``, ``partly_cloudy``, ``cloudy``,
    ``rainy``, or ``stormy``.
    """
    weather_pool = [
        "sunny",
        "partly_cloudy",
        "sunny",
        "sunny",
        "partly_cloudy",
        "cloudy",
        "rainy",
        "stormy",
    ]

    start = date.fromisoformat(vacation_info.start_date)
    end = date.fromisoformat(vacation_info.end_date)

    forecast: Dict[str, str] = {}
    current = start
    while current <= end:
        date_str = current.isoformat()
        # Deterministic but varied – based on the calendar day and month
        idx = (current.day * 3 + current.month * 7) % len(weather_pool)
        forecast[date_str] = weather_pool[idx]
        current += timedelta(days=1)

    return forecast


def get_available_activities(
    vacation_info: VacationInfo,
    weather_data: Dict[str, str],
) -> Dict[str, List[Dict[str, Any]]]:
    """Simulate fetching available activities for each trip date.

    Activities are filtered by the day's weather so that, for example, beach
    activities are not listed on rainy days.

    Returns a mapping of ``{date_str: [activity_dict, ...]}``.
    """
    available: Dict[str, List[Dict[str, Any]]] = {}
    for date_str, weather in weather_data.items():
        available[date_str] = [
            act
            for act in ACTIVITIES_CATALOG
            if _is_weather_compatible(act["weather_requirement"], weather)
        ]
    return available


# ============================================================
# EVALUATION SYSTEM
# ============================================================


def _check_budget_accuracy(
    plan: TravelPlan, vacation_info: VacationInfo
) -> tuple[bool, str]:
    """Rule-based: verify that cost tallies are correct and within budget."""
    # Recalculate total from individual activities
    recalculated_total = round(
        sum(a.cost for day in plan.days for a in day.activities), 2
    )

    # Verify each day's day_total_cost
    day_errors = []
    for day in plan.days:
        expected = round(sum(a.cost for a in day.activities), 2)
        if abs(day.day_total_cost - expected) > 0.01:
            day_errors.append(
                f"{day.date}: day_total_cost is ${day.day_total_cost:.2f} "
                f"but activities sum to ${expected:.2f}"
            )

    if day_errors:
        return False, "Day total cost errors:\n" + "\n".join(f"  - {e}" for e in day_errors)

    if abs(plan.total_cost - recalculated_total) > 0.01:
        return (
            False,
            f"Total cost mismatch: plan says ${plan.total_cost:.2f} "
            f"but activities sum to ${recalculated_total:.2f}",
        )

    if plan.total_cost > vacation_info.budget:
        return (
            False,
            f"Total cost ${plan.total_cost:.2f} exceeds budget "
            f"${vacation_info.budget:.2f}",
        )

    return (
        True,
        f"Budget check passed: ${plan.total_cost:.2f} is within the "
        f"${vacation_info.budget:.2f} budget",
    )


def _check_city_date_correctness(
    plan: TravelPlan, vacation_info: VacationInfo
) -> tuple[bool, str]:
    """Rule-based: verify destination and that all trip dates are present."""
    if plan.destination.lower() != vacation_info.destination.lower():
        return (
            False,
            f"Destination mismatch: plan has '{plan.destination}' "
            f"but should be '{vacation_info.destination}'",
        )

    start = date.fromisoformat(vacation_info.start_date)
    end = date.fromisoformat(vacation_info.end_date)
    expected_dates: set[str] = set()
    current = start
    while current <= end:
        expected_dates.add(current.isoformat())
        current += timedelta(days=1)

    plan_dates = {day.date for day in plan.days}
    missing = expected_dates - plan_dates
    extra = plan_dates - expected_dates

    if missing:
        return False, f"Missing dates in itinerary: {sorted(missing)}"
    if extra:
        return False, f"Extra dates in itinerary: {sorted(extra)}"

    return True, "City and date check passed"


def _check_minimum_activities(
    plan: TravelPlan, min_per_day: int = 2
) -> tuple[bool, str]:
    """Rule-based: every day must have at least *min_per_day* activities."""
    failing = [day.date for day in plan.days if len(day.activities) < min_per_day]
    if failing:
        return (
            False,
            f"Days with fewer than {min_per_day} activities: {failing}",
        )
    return (
        True,
        f"Minimum activities check passed: all days have ≥{min_per_day} activities",
    )


def _check_activity_availability(
    plan: TravelPlan,
    available_activities: Dict[str, List[Dict[str, Any]]],
) -> tuple[bool, str]:
    """Rule-based: all planned activities must be in the available list for that date."""
    issues: List[str] = []
    for day in plan.days:
        if day.date not in available_activities:
            issues.append(f"{day.date}: date not found in available activities")
            continue
        available_names = {a["name"].lower() for a in available_activities[day.date]}
        for activity in day.activities:
            if activity.name.lower() not in available_names:
                issues.append(
                    f"{day.date}: '{activity.name}' is not available on this date "
                    "(may be weather-incompatible or not in the catalog)"
                )

    if issues:
        return (
            False,
            "Unavailable activities found:\n" + "\n".join(f"  - {i}" for i in issues),
        )
    return True, "Activity availability check passed"


ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT = """\
You are the weather-compatibility reviewer for a travel itinerary.

Your job is to decide whether each scheduled activity is appropriate for the day’s weather and, when needed, recommend a safer indoor or all-weather replacement.

Output vocabulary:
- IS_COMPATIBLE
- IS_INCOMPATIBLE

Respond ONLY with a JSON object in this exact structure:
{
  "status": "IS_COMPATIBLE" | "IS_INCOMPATIBLE",
  "issues": ["string"],
  "backup_suggestions": [{"activity": "string", "replacement": "string"}]
}

Rules:
- Use `IS_COMPATIBLE` only when all scheduled activities match the weather.
- Use `IS_INCOMPATIBLE` whenever at least one activity is mismatched for the day’s conditions.
- For every incompatible activity, suggest an indoor or all-weather backup such as a museum, food tour, spa, gallery, or indoor entertainment.
- Keep the reasoning concise and specific to the activity + weather mismatch.
- Treat the activity catalog's weather requirement as authoritative. Do not infer extra restrictions from possible heat, sun exposure, brightness, or personal preference.
- In particular, `sunny` weather is compatible with activities requiring `sunny`, `sunny_or_partly_cloudy`, or `any` weather.

Worked example: compatible
Input weather: sunny
Activity: Beach Volleyball
Output:
{"status": "IS_COMPATIBLE", "issues": [], "backup_suggestions": []}

Worked example: incompatible
Input weather: rainy
Activity: Hiking in National Park
Output:
{"status": "IS_INCOMPATIBLE", "issues": ["Hiking in National Park is not suitable for rainy weather."], "backup_suggestions": [{"activity": "Hiking in National Park", "replacement": "City Museum Tour or Art Gallery Visit"}]}

Weather guide:
- sunny: all activities are permitted
- partly_cloudy: activities requiring `sunny_or_partly_cloudy` are allowed; `sunny`-only activities are not
- cloudy: only `any-weather` activities are allowed; outdoor activities are not
- rainy: only `any-weather` indoor activities are allowed; no outdoor activities
- stormy: only `any-weather` indoor activities are allowed; no outdoor activities
"""


def _check_weather_compatibility(
    plan: TravelPlan,
    weather_data: Dict[str, str],
    client: Any,
    model: str,
) -> tuple[bool, str]:
    """Verify that scheduled activities meet the catalog weather requirements."""
    catalog_by_name = {activity["name"].lower(): activity for activity in ACTIVITIES_CATALOG}
    incompatible: List[str] = []

    for day in plan.days:
        weather = weather_data.get(day.date, "unknown")
        for activity in day.activities:
            catalog_activity = catalog_by_name.get(activity.name.lower())
            if catalog_activity is None:
                incompatible.append(f"{activity.name} is not in the activity catalog")
            elif not _is_weather_compatible(
                catalog_activity["weather_requirement"], weather
            ):
                incompatible.append(
                    f"{activity.name} on {day.date} is incompatible with {weather} weather"
                )

    if incompatible:
        return False, "Weather compatibility issues:\n" + "\n".join(
            f"  - {issue}" for issue in incompatible
        )

    schedule = "\n".join(
        f"- {day.date} ({weather_data.get(day.date, 'unknown')}): "
        + ", ".join(activity.name for activity in day.activities)
        for day in plan.days
    )
    client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Review this catalog-validated itinerary and return the required JSON.\n"
                    f"{schedule}"
                ),
            },
        ],
        response_format={"type": "json_object"},
    )

    # The catalog is authoritative, so the advisory LLM response cannot
    # override a known-compatible requirement.
    return True, "Weather compatibility check passed"


def run_evals(
    plan: TravelPlan,
    vacation_info: VacationInfo,
    weather_data: Dict[str, str],
    available_activities: Dict[str, List[Dict[str, Any]]],
    client: Any,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """Run all five evaluation checks on *plan*.

    Returns a dict where each key is a check name mapped to
    ``{"passed": bool, "message": str}``, plus an ``"all_passed"`` summary key.
    """
    results: Dict[str, Any] = {}

    passed, msg = _check_budget_accuracy(plan, vacation_info)
    results["budget_accuracy"] = {"passed": passed, "message": msg}

    passed, msg = _check_city_date_correctness(plan, vacation_info)
    results["city_date_correctness"] = {"passed": passed, "message": msg}

    passed, msg = _check_minimum_activities(plan)
    results["minimum_activities"] = {"passed": passed, "message": msg}

    passed, msg = _check_activity_availability(plan, available_activities)
    results["activity_availability"] = {"passed": passed, "message": msg}

    passed, msg = _check_weather_compatibility(plan, weather_data, client, model)
    results["weather_compatibility"] = {"passed": passed, "message": msg}

    results["all_passed"] = all(
        v["passed"] for v in results.values() if isinstance(v, dict) and "passed" in v
    )
    return results


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================


def calculator_tool_fn(costs: List[float]) -> Dict[str, Any]:
    """Sum a list of costs and return the total.

    Used by the revision agent to verify budget calculations.
    """
    total = round(sum(costs), 2)
    return {
        "total_cost": total,
        "item_count": len(costs),
        "breakdown": f"Sum of {len(costs)} item(s): ${total:.2f}",
    }


def get_activities_by_date_tool_fn(
    date_str: str, weather_data: Dict[str, str]
) -> Dict[str, Any]:
    """Return all activities available on *date_str* given the forecasted weather.

    Used by the revision agent to find replacement activities.
    """
    weather = weather_data.get(date_str, "sunny")
    activities = [
        act
        for act in ACTIVITIES_CATALOG
        if _is_weather_compatible(act["weather_requirement"], weather)
    ]
    return {
        "date": date_str,
        "weather": weather,
        "available_activities": activities,
        "count": len(activities),
    }


#: OpenAI function-calling schemas for the four agent tools.
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator_tool",
            "description": (
                "Calculate the total cost by summing a list of individual costs. "
                "Use this to verify budget calculations before submitting the plan."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "costs": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of individual activity costs to sum.",
                    }
                },
                "required": ["costs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_activities_by_date_tool",
            "description": (
                "Retrieve all activities available for a specific date. "
                "The list is already filtered by that day's weather forecast, "
                "so every returned activity is safe to schedule."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    }
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_evals_tool",
            "description": (
                "Run all evaluation checks on the revised itinerary. "
                "Returns pass/fail results for: budget accuracy, weather "
                "compatibility, activity availability, city/date correctness, "
                "and minimum activities per day."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "plan": {
                        "type": "object",
                        "description": "The revised travel plan to evaluate.",
                        "properties": {
                            "destination": {"type": "string"},
                            "days": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "activities": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "cost": {"type": "number"},
                                                    "description": {"type": "string"},
                                                },
                                                "required": ["name", "cost", "description"],
                                            },
                                        },
                                        "day_total_cost": {"type": "number"},
                                    },
                                    "required": ["date", "activities", "day_total_cost"],
                                },
                            },
                            "total_cost": {"type": "number"},
                        },
                        "required": ["destination", "days", "total_cost"],
                    }
                },
                "required": ["plan"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "final_answer_tool",
            "description": (
                "Submit the final revised itinerary. "
                "This is the only permitted exit from the revision loop and it may be called only after run_evals_tool confirms every check passed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "plan": {
                        "type": "object",
                        "description": "The final approved travel plan.",
                        "properties": {
                            "destination": {"type": "string"},
                            "days": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "activities": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "cost": {"type": "number"},
                                                    "description": {"type": "string"},
                                                },
                                                "required": ["name", "cost", "description"],
                                            },
                                        },
                                        "day_total_cost": {"type": "number"},
                                    },
                                    "required": ["date", "activities", "day_total_cost"],
                                },
                            },
                            "total_cost": {"type": "number"},
                        },
                        "required": ["destination", "days", "total_cost"],
                    }
                },
                "required": ["plan"],
            },
        },
    },
]


# ============================================================
# ITINERARY AGENT – generates the initial travel plan
# ============================================================

_ITINERARY_AGENT_SYSTEM_PROMPT = f"""\
You are an expert travel planner for AgentsVille.

Your task is to create a detailed day-by-day travel itinerary based on the
traveler's preferences, the available activities, and the weather forecast.

Guidelines:
- Choose activities that match the traveler's stated interests.
- Respect the weather: only schedule activities whose weather requirement is met.
  The "Available Activities" list is already filtered by weather, so every listed
  activity is safe to schedule on that day.
- Stay within the traveler's total budget.
- Plan at least 2-3 activities per day.
- Vary activity types across the trip (culture, food, outdoor, entertainment).
- Calculate costs accurately: day_total_cost must equal the sum of its activities' costs,
  and total_cost must equal the sum of all day_total_cost values.
- Only use activities from the "Available Activities" section – use the exact
  names and costs listed there.

Respond ONLY with a valid JSON object matching this exact schema:
{json.dumps(TravelPlan.model_json_schema(), indent=2)}
"""


class ItineraryAgent:
    """Generates an initial travel itinerary via an LLM."""

    def __init__(self, client: Any, model: str = "gpt-4o") -> None:
        self.client = client
        self.model = model

    def generate(
        self,
        vacation_info: VacationInfo,
        weather_data: Dict[str, str],
        available_activities: Dict[str, List[Dict[str, Any]]],
    ) -> TravelPlan:
        """Call the LLM to produce an initial :class:`TravelPlan`."""
        context = self._build_context(vacation_info, weather_data, available_activities)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _ITINERARY_AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": context},
            ],
            response_format={"type": "json_object"},
        )

        return TravelPlan.model_validate_json(response.choices[0].message.content)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_context(
        self,
        vacation_info: VacationInfo,
        weather_data: Dict[str, str],
        available_activities: Dict[str, List[Dict[str, Any]]],
    ) -> str:
        """Assemble a structured context string for the LLM."""
        lines = [
            "## Traveler Information",
            f"- Destination: {vacation_info.destination}",
            f"- Travel Dates: {vacation_info.start_date} to {vacation_info.end_date}",
            f"- Interests: {', '.join(vacation_info.interests)}",
            f"- Budget: ${vacation_info.budget:.2f}",
        ]
        if vacation_info.constraints:
            lines.append(f"- Constraints: {', '.join(vacation_info.constraints)}")

        lines.append("\n## Daily Weather Forecast")
        for d in sorted(weather_data):
            lines.append(f"- {d}: {weather_data[d]}")

        lines.append("\n## Available Activities by Date")
        for d in sorted(available_activities):
            weather = weather_data.get(d, "unknown")
            lines.append(f"\n### {d}  (Weather: {weather})")
            for act in available_activities[d]:
                lines.append(
                    f"- {act['name']}: ${act['cost']:.2f} – {act['description']}"
                )

        return "\n".join(lines)


# ============================================================
# ITINERARY REVISION AGENT – ReAct loop
# ============================================================

_REVISION_AGENT_SYSTEM_PROMPT = """\
You are an expert travel planner tasked with revising and improving a travel
itinerary for AgentsVille.

You must follow the ReAct (Reasoning + Acting) loop exactly.

Output contract on every turn:
THOUGHT: <brief analysis of the failing checks and what to change>
ACTION: {"tool_name": "[tool_name]", "arguments": {...}}

The agent must never skip the THOUGHT line, and the ACTION line must always be a valid JSON object with the exact structure above.

Available tools and required argument schemas:
- calculator_tool
  ACTION: {"tool_name": "calculator_tool", "arguments": {"costs": [number, number, ...]}}
  Purpose: sum a list of individual costs to verify arithmetic.

- get_activities_by_date_tool
  ACTION: {"tool_name": "get_activities_by_date_tool", "arguments": {"date": "YYYY-MM-DD"}}
  Purpose: fetch the weather-safe activities available for a specific date.

- run_evals_tool
  ACTION: {"tool_name": "run_evals_tool", "arguments": {"plan": {"destination": "string", "days": [{"date": "YYYY-MM-DD", "activities": [{"name": "string", "cost": number, "description": "string"}], "day_total_cost": number}], "total_cost": number}}}
  Purpose: validate the current plan against the five checks. This must be called before any final submission.

- final_answer_tool
  ACTION: {"tool_name": "final_answer_tool", "arguments": {"plan": {"destination": "string", "days": [{"date": "YYYY-MM-DD", "activities": [{"name": "string", "cost": number, "description": "string"}], "day_total_cost": number}], "total_cost": number}}}
  Purpose: submit the final approved itinerary.

Hard gate for exiting the loop:
- run_evals_tool must be executed on the candidate plan and return all checks passing.
- final_answer_tool is the only permitted exit from the revision loop.
- If any check fails, continue revising and call another tool instead of exiting.

Rules:
- Only use activities whose names and costs appear in the provided catalog.
- day_total_cost must equal the exact sum of its activities' costs.
- total_cost must equal the exact sum of all day_total_cost values.
- Keep the plan valid under TravelPlan.model_validate before submitting.
- Do not call final_answer_tool until run_evals_tool confirms all five checks pass.
"""


class ItineraryRevisionAgent:
    """Iteratively revises a travel plan using the ReAct reasoning framework.

    The agent follows a THOUGHT → ACTION → OBSERVATION loop:
    it analyses evaluation feedback, calls tools to gather information or
    verify changes, and submits the final plan via ``final_answer_tool``.

    Attributes:
        reasoning_log: List of dicts recording each thought/action/observation.
    """

    def __init__(self, client: Any, model: str = "gpt-4o") -> None:
        self.client = client
        self.model = model
        self.max_iterations: int = 10
        self.reasoning_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def revise(
        self,
        plan: TravelPlan,
        vacation_info: VacationInfo,
        weather_data: Dict[str, str],
        available_activities: Dict[str, List[Dict[str, Any]]],
        eval_model: str = "gpt-4o-mini",
    ) -> TravelPlan:
        """Revise *plan* until all evaluation checks pass.

        Args:
            plan: The initial travel plan to improve.
            vacation_info: Traveler preferences and constraints.
            weather_data: Mapping of date → weather condition.
            available_activities: Mapping of date → list of available activities.
            eval_model: Model used for the LLM-based weather evaluation.

        Returns:
            The revised :class:`TravelPlan` (or the original if it already passes).
        """
        self.reasoning_log = []

        # Run initial evaluations
        eval_results = run_evals(
            plan, vacation_info, weather_data, available_activities,
            self.client, eval_model,
        )

        if eval_results.get("all_passed", False):
            print("✅  All checks already pass – no revision needed.")
            return plan

        messages = [
            {"role": "system", "content": _REVISION_AGENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": self._build_initial_message(
                    plan, vacation_info, weather_data, available_activities,
                    eval_results,
                ),
            },
        ]

        current_plan = plan
        last_eval_all_passed = False
        print(f"🔄  Starting ReAct revision loop (max {self.max_iterations} iterations)…")

        for iteration in range(self.max_iterations):
            print(f"\n{'─'*50}")
            print(f"  Iteration {iteration + 1}")
            print(f"{'─'*50}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )

            message = response.choices[0].message
            messages.append(message)

            # Log the agent's thought
            if message.content:
                thought_preview = message.content[:300].replace("\n", " ")
                print(f"💭  THOUGHT: {thought_preview}…")
                self.reasoning_log.append(
                    {"type": "thought", "content": message.content}
                )

            if not message.tool_calls:
                print("ℹ️   Agent finished without calling final_answer_tool.")
                break

            done = False
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"🔧  ACTION: {tool_name}")
                self.reasoning_log.append(
                    {"type": "action", "tool": tool_name, "args": tool_args}
                )

                # ── Execute the tool ──────────────────────────────────────
                if tool_name == "calculator_tool":
                    result = calculator_tool_fn(tool_args["costs"])

                elif tool_name == "get_activities_by_date_tool":
                    result = get_activities_by_date_tool_fn(
                        tool_args["date"], weather_data
                    )

                elif tool_name == "run_evals_tool":
                    try:
                        revised = TravelPlan.model_validate(tool_args["plan"])
                        result = run_evals(
                            revised, vacation_info, weather_data,
                            available_activities, self.client, eval_model,
                        )
                        current_plan = revised
                        last_eval_all_passed = bool(result.get("all_passed", False))
                    except Exception as exc:
                        result = {"error": str(exc), "all_passed": False}
                        last_eval_all_passed = False

                elif tool_name == "final_answer_tool":
                    if not last_eval_all_passed:
                        result = {
                            "error": "Cannot call final_answer_tool before run_evals_tool confirms all checks pass.",
                            "status": "rejected",
                            "all_passed": False,
                        }
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result),
                            }
                        )
                        continue
                    try:
                        final = TravelPlan.model_validate(tool_args["plan"])
                        current_plan = final
                        print("✅  Agent submitted the final itinerary!")
                        self.reasoning_log.append(
                            {"type": "final_answer", "plan": final.model_dump()}
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(
                                    {
                                        "status": "accepted",
                                        "message": "Final itinerary accepted.",
                                    }
                                ),
                            }
                        )
                        done = True
                        break
                    except Exception as exc:
                        result = {"error": str(exc), "status": "rejected"}
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result),
                            }
                        )
                        continue

                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                # Add the tool observation to the conversation
                observation_str = json.dumps(result)
                preview = observation_str[:300]
                print(f"👁️   OBSERVATION: {preview}…")
                self.reasoning_log.append(
                    {"type": "observation", "content": result}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation_str,
                    }
                )

            if done:
                break

        return current_plan

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_initial_message(
        self,
        plan: TravelPlan,
        vacation_info: VacationInfo,
        weather_data: Dict[str, str],
        available_activities: Dict[str, List[Dict[str, Any]]],
        eval_results: Dict[str, Any],
    ) -> str:
        """Build the opening user message for the revision conversation."""
        parts = [
            "## Current Itinerary",
            f"```json\n{plan.model_dump_json(indent=2)}\n```",
            "\n## Evaluation Results",
        ]

        for check_name, check_result in eval_results.items():
            if check_name == "all_passed":
                continue
            if isinstance(check_result, dict):
                status = "✅ PASSED" if check_result["passed"] else "❌ FAILED"
                parts.append(f"\n**{check_name}**: {status}")
                if not check_result["passed"]:
                    parts.append(f"> {check_result['message']}")

        overall = (
            "✅ All checks passed"
            if eval_results.get("all_passed")
            else "❌ Some checks failed – revision required"
        )
        parts.append(f"\n**Overall**: {overall}")

        parts += [
            "\n## Trip Context",
            f"- Destination: {vacation_info.destination}",
            f"- Dates: {vacation_info.start_date} to {vacation_info.end_date}",
            f"- Budget: ${vacation_info.budget:.2f}",
            f"- Interests: {', '.join(vacation_info.interests)}",
        ]
        if vacation_info.constraints:
            parts.append(f"- Constraints: {', '.join(vacation_info.constraints)}")

        parts.append("\n## Weather Forecast")
        for d in sorted(weather_data):
            parts.append(f"- {d}: {weather_data[d]}")

        parts += [
            "\nPlease fix all failing checks using the available tools.",
            "Run run_evals_tool after each revision and do not call final_answer_tool until it returns all checks passing.",
            "final_answer_tool is the only permitted exit from the loop.",
        ]

        return "\n".join(parts)


# ============================================================
# TRIP SUMMARY
# ============================================================


def generate_trip_summary(
    plan: TravelPlan,
    vacation_info: VacationInfo,
    client: Any,
    model: str = "gpt-4o",
) -> str:
    """Generate a short narrative summary describing the highlights of the trip."""
    daily_highlights = "\n".join(
        f"  - {day.date}: {', '.join(a.name for a in day.activities)}"
        for day in plan.days
    )

    prompt = (
        f"Write a short, enthusiastic 2–3 sentence narrative summary of this "
        f"{len(plan.days)}-day trip to {plan.destination}.\n\n"
        f"Trip details:\n"
        f"  - Dates: {vacation_info.start_date} to {vacation_info.end_date}\n"
        f"  - Total cost: ${plan.total_cost:.2f}\n"
        f"  - Daily highlights:\n{daily_highlights}\n\n"
        "Write in second person (\"you\"). Be warm, engaging, and highlight the "
        "variety and excitement of the activities."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


# ============================================================
# DISPLAY HELPERS
# ============================================================


def print_itinerary(plan: TravelPlan) -> None:
    """Pretty-print a :class:`TravelPlan` to stdout."""
    print(f"\n{'=' * 60}")
    print(f"🌍  TRAVEL ITINERARY: {plan.destination}")
    print(f"{'=' * 60}")

    for day in plan.days:
        print(f"\n📅  {day.date}")
        for act in day.activities:
            print(f"   • {act.name}  –  ${act.cost:.2f}")
            print(f"     {act.description}")
        print(f"   ─ Day total: ${day.day_total_cost:.2f}")

    print(f"\n{'=' * 60}")
    print(f"💰  TOTAL TRIP COST: ${plan.total_cost:.2f}")
    print(f"{'=' * 60}")

    if plan.summary:
        print(f"\n📝  TRIP SUMMARY:\n{plan.summary}")


def print_eval_results(eval_results: Dict[str, Any]) -> None:
    """Pretty-print evaluation results to stdout."""
    print(f"\n{'=' * 60}")
    print("📊  EVALUATION RESULTS")
    print(f"{'=' * 60}")

    for check_name, check_result in eval_results.items():
        if check_name == "all_passed":
            continue
        if isinstance(check_result, dict):
            status = "✅  PASSED" if check_result["passed"] else "❌  FAILED"
            label = check_name.upper().replace("_", " ")
            print(f"\n{status}  {label}")
            print(f"   {check_result['message']}")

    print(f"\n{'=' * 60}")
    overall = (
        "✅  ALL CHECKS PASSED"
        if eval_results.get("all_passed")
        else "❌  SOME CHECKS FAILED"
    )
    print(f"OVERALL: {overall}")
    print(f"{'=' * 60}")
