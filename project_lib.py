"""
project_lib.py

Helper functions, Pydantic models, agents, and tools for the AgentsVille AI Trip Planner.
"""

import json
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================
# Pydantic Models
# ============================================================


class VacationInfo(BaseModel):
    """Captures all traveler preferences and constraints."""

    destination: str
    start_date: date
    end_date: date
    interests: List[str]
    budget: float
    constraints: List[str] = Field(default_factory=list)


class Activity(BaseModel):
    """Represents a single activity in the itinerary."""

    name: str
    cost: float
    description: str


class DayPlan(BaseModel):
    """Represents activities planned for a single day."""

    date: str
    activities: List[Activity]


class TravelPlan(BaseModel):
    """Complete travel itinerary with per-day plans and total cost."""

    days: List[DayPlan]
    total_cost: float


# ============================================================
# Simulated Data (replaces real API calls)
# ============================================================

WEATHER_DATA: Dict[str, Dict[str, Any]] = {
    "2026-06-10": {
        "condition": "Sunny",
        "temperature": 75,
        "recommendation": "Great for outdoor activities",
    },
    "2026-06-11": {
        "condition": "Partly Cloudy",
        "temperature": 70,
        "recommendation": "Good for most activities",
    },
    "2026-06-12": {
        "condition": "Rainy",
        "temperature": 65,
        "recommendation": "Best for indoor activities",
    },
    "2026-06-13": {
        "condition": "Sunny",
        "temperature": 78,
        "recommendation": "Perfect for outdoor activities",
    },
    "2026-06-14": {
        "condition": "Sunny",
        "temperature": 80,
        "recommendation": "Excellent beach weather",
    },
}

ACTIVITIES_DATA: Dict[str, List[Dict[str, Any]]] = {
    "2026-06-10": [
        {
            "name": "City Museum Tour",
            "cost": 30,
            "description": "Explore the history of AgentsVille",
        },
        {
            "name": "Harbor Boat Tour",
            "cost": 45,
            "description": "Scenic boat tour of the harbor",
        },
        {
            "name": "Central Park Picnic",
            "cost": 15,
            "description": "Relaxing picnic in the main park",
        },
        {
            "name": "Art Gallery Visit",
            "cost": 20,
            "description": "Browse local and international art",
        },
    ],
    "2026-06-11": [
        {
            "name": "Cooking Class",
            "cost": 60,
            "description": "Learn to cook local cuisine",
        },
        {
            "name": "Historic District Walk",
            "cost": 0,
            "description": "Self-guided walking tour of historic landmarks",
        },
        {
            "name": "Local Market Tour",
            "cost": 25,
            "description": "Visit the famous AgentsVille market",
        },
        {
            "name": "Wine Tasting",
            "cost": 40,
            "description": "Sample local wines at a vineyard",
        },
    ],
    "2026-06-12": [
        {
            "name": "Science Museum",
            "cost": 25,
            "description": "Interactive science exhibits",
        },
        {
            "name": "Indoor Rock Climbing",
            "cost": 35,
            "description": "Beginner-friendly climbing gym",
        },
        {
            "name": "Escape Room Adventure",
            "cost": 30,
            "description": "Solve puzzles in a themed room",
        },
        {
            "name": "Spa Day",
            "cost": 80,
            "description": "Relaxing spa treatments and wellness",
        },
    ],
    "2026-06-13": [
        {
            "name": "Hiking Trail",
            "cost": 10,
            "description": "Scenic mountain trail with great views",
        },
        {
            "name": "Bike Tour",
            "cost": 35,
            "description": "Guided bike tour of the city",
        },
        {
            "name": "Beach Day",
            "cost": 20,
            "description": "Relax at the local beach",
        },
        {
            "name": "Sunset Cruise",
            "cost": 55,
            "description": "Evening cruise to watch the sunset",
        },
    ],
    "2026-06-14": [
        {
            "name": "Farmers Market",
            "cost": 15,
            "description": "Fresh local produce and artisan goods",
        },
        {
            "name": "Kayaking",
            "cost": 40,
            "description": "Sea kayaking adventure",
        },
        {
            "name": "Food Tour",
            "cost": 50,
            "description": "Guided tour of local restaurants and street food",
        },
        {
            "name": "Photography Tour",
            "cost": 30,
            "description": "Capture the best spots in the city",
        },
    ],
}


def get_weather_forecast(destination: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """Simulate an API call to retrieve weather forecasts for a date range.

    Args:
        destination: The travel destination name.
        start_date: Inclusive start date in YYYY-MM-DD format.
        end_date: Inclusive end date in YYYY-MM-DD format.

    Returns:
        A dict mapping date strings to weather information dicts.
    """
    forecast: Dict[str, Any] = {}
    for date_str, weather in WEATHER_DATA.items():
        if start_date <= date_str <= end_date:
            forecast[date_str] = weather
    return forecast


def get_available_activities(destination: str, date_str: str) -> List[Dict[str, Any]]:
    """Simulate an API call to retrieve available activities for a given date.

    Args:
        destination: The travel destination name.
        date_str: The date in YYYY-MM-DD format.

    Returns:
        A list of activity dicts available on that date.
    """
    return ACTIVITIES_DATA.get(date_str, [])


# ============================================================
# Evaluation Functions
# ============================================================


def evaluate_weather_compatibility(
    travel_plan: TravelPlan, weather_forecast: Dict[str, Any]
) -> Dict[str, Any]:
    """Check that activities are appropriate for the forecasted weather.

    Outdoor keywords trigger a failure when the weather is rainy.
    """
    outdoor_keywords = [
        "beach",
        "hike",
        "hiking",
        "bike",
        "outdoor",
        "picnic",
        "boat",
        "cruise",
        "kayak",
    ]
    issues: List[str] = []
    for day in travel_plan.days:
        weather = weather_forecast.get(day.date, {})
        if weather.get("condition") == "Rainy":
            for activity in day.activities:
                text = f"{activity.name} {activity.description}".lower()
                if any(kw in text for kw in outdoor_keywords):
                    issues.append(
                        f"On {day.date}, '{activity.name}' may be affected by rainy weather."
                    )
    return {
        "check": "weather_compatibility",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def evaluate_activity_availability(travel_plan: TravelPlan) -> Dict[str, Any]:
    """Check that every scheduled activity is available on its date."""
    issues: List[str] = []
    for day in travel_plan.days:
        available_names = [a["name"] for a in ACTIVITIES_DATA.get(day.date, [])]
        if available_names:
            for activity in day.activities:
                if activity.name not in available_names:
                    issues.append(
                        f"'{activity.name}' is not available on {day.date}. "
                        f"Available: {available_names}"
                    )
    return {
        "check": "activity_availability",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def evaluate_budget(travel_plan: TravelPlan, budget: float) -> Dict[str, Any]:
    """Check that total_cost is accurately calculated and within budget."""
    calculated_total = sum(
        activity.cost for day in travel_plan.days for activity in day.activities
    )
    issues: List[str] = []
    if abs(calculated_total - travel_plan.total_cost) > 0.01:
        issues.append(
            f"Total cost mismatch: plan reports {travel_plan.total_cost} "
            f"but calculated {calculated_total}."
        )
    if calculated_total > budget:
        issues.append(
            f"Total cost (${calculated_total}) exceeds the budget (${budget})."
        )
    return {
        "check": "budget",
        "passed": len(issues) == 0,
        "issues": issues,
        "calculated_total": calculated_total,
    }


def evaluate_minimum_activities(
    travel_plan: TravelPlan, min_activities: int = 2
) -> Dict[str, Any]:
    """Check that each day has at least *min_activities* activities."""
    issues: List[str] = []
    for day in travel_plan.days:
        if len(day.activities) < min_activities:
            issues.append(
                f"Day {day.date} has only {len(day.activities)} "
                f"activit{'y' if len(day.activities) == 1 else 'ies'} "
                f"(minimum is {min_activities})."
            )
    return {
        "check": "minimum_activities",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def evaluate_city_date_correctness(
    travel_plan: TravelPlan, vacation_info: VacationInfo
) -> Dict[str, Any]:
    """Check that every day in the plan falls within the vacation date range."""
    start = str(vacation_info.start_date)
    end = str(vacation_info.end_date)
    issues: List[str] = []
    for day in travel_plan.days:
        if not (start <= day.date <= end):
            issues.append(
                f"Date {day.date} is outside the travel window ({start} – {end})."
            )
    return {
        "check": "city_date_correctness",
        "passed": len(issues) == 0,
        "issues": issues,
    }


def run_all_evaluations(
    travel_plan: TravelPlan,
    vacation_info: VacationInfo,
    weather_forecast: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Run all evaluation checks and return a list of result dicts."""
    return [
        evaluate_weather_compatibility(travel_plan, weather_forecast),
        evaluate_activity_availability(travel_plan),
        evaluate_budget(travel_plan, vacation_info.budget),
        evaluate_minimum_activities(travel_plan),
        evaluate_city_date_correctness(travel_plan, vacation_info),
    ]


def print_eval_results(eval_results: List[Dict[str, Any]]) -> None:
    """Pretty-print evaluation results to stdout."""
    all_passed = all(r["passed"] for r in eval_results)
    print(f"\n{'='*50}")
    print(f"Evaluation Results  ({'✓ ALL PASSED' if all_passed else '✗ ISSUES FOUND'})")
    print("=" * 50)
    for result in eval_results:
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"  [{status}] {result['check']}")
        for issue in result.get("issues", []):
            print(f"           ↳ {issue}")
    print()


# ============================================================
# ItineraryAgent — generates the initial travel plan
# ============================================================


class ItineraryAgent:
    """Generates an initial travel itinerary using a structured LLM call."""

    SYSTEM_PROMPT = (
        "You are an expert travel planner. Your task is to create a detailed "
        "day-by-day travel itinerary based on the traveler's preferences, "
        "weather conditions, and available activities.\n\n"
        "Rules:\n"
        "- Only use activities from the provided available activities list for each date.\n"
        "- Calculate total_cost as the exact sum of all activity costs.\n"
        "- Choose weather-appropriate activities (avoid outdoor activities on rainy days).\n"
        "- Stay within the traveler's budget.\n"
        "- Include at least 2 activities per day.\n"
        "- Match traveler interests when possible."
    )

    def __init__(self, client: Any, model: str = "gpt-4o") -> None:
        self.client = client
        self.model = model

    def generate(
        self,
        vacation_info: VacationInfo,
        weather_forecast: Dict[str, Any],
        activities_by_date: Dict[str, Any],
    ) -> TravelPlan:
        """Call the LLM to produce a structured TravelPlan."""
        user_message = (
            "Please create a travel itinerary for the following traveler.\n\n"
            f"Traveler Information:\n{vacation_info.model_dump_json(indent=2)}\n\n"
            f"Weather Forecast:\n{json.dumps(weather_forecast, indent=2)}\n\n"
            f"Available Activities by Date:\n{json.dumps(activities_by_date, indent=2)}\n\n"
            "Requirements:\n"
            "1. Respect weather conditions — avoid outdoor activities on rainy days.\n"
            f"2. Stay within the budget of ${vacation_info.budget}.\n"
            f"3. Match interests: {', '.join(vacation_info.interests)}.\n"
            f"4. Respect constraints: "
            f"{', '.join(vacation_info.constraints) if vacation_info.constraints else 'None'}.\n"
            "5. Include at least 2 activities per day.\n"
            "6. Only use activities from the available list for each date."
        )

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=TravelPlan,
        )
        return response.choices[0].message.parsed


# ============================================================
# Tool Definitions for the ReAct Agent
# ============================================================


def calculator_tool(activities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate the total cost of a list of activity dicts.

    Args:
        activities: List of dicts with at least a ``cost`` field.

    Returns:
        Dict with ``total_cost`` and the original ``breakdown`` list.
    """
    total = sum(float(a.get("cost", 0)) for a in activities)
    return {"total_cost": total, "breakdown": activities}


def get_activities_by_date_tool(date_str: str) -> List[Dict[str, Any]]:
    """Return available activities for a given date string (YYYY-MM-DD)."""
    return ACTIVITIES_DATA.get(date_str, [])


def run_evals_tool(
    plan_dict: Dict[str, Any],
    vacation_dict: Dict[str, Any],
    weather_dict: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Parse dicts into models and run all evaluations.

    Args:
        plan_dict: Dict matching the TravelPlan schema.
        vacation_dict: Dict matching the VacationInfo schema.
        weather_dict: Weather forecast dict keyed by date string.

    Returns:
        List of evaluation result dicts.
    """
    travel_plan = TravelPlan(**plan_dict)
    vacation_info = VacationInfo(**vacation_dict)
    return run_all_evaluations(travel_plan, vacation_info, weather_dict)


def final_answer_tool(plan_dict: Dict[str, Any]) -> TravelPlan:
    """Validate and return the final TravelPlan.

    Args:
        plan_dict: Dict matching the TravelPlan schema.

    Returns:
        A validated TravelPlan instance.
    """
    return TravelPlan(**plan_dict)


def execute_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """Dispatch a tool call by name.

    Args:
        tool_name: One of the registered tool names.
        tool_args: Keyword arguments for the tool function.

    Returns:
        The tool's return value.
    """
    tools = {
        "calculator_tool": calculator_tool,
        "get_activities_by_date_tool": get_activities_by_date_tool,
        "run_evals_tool": run_evals_tool,
        "final_answer_tool": final_answer_tool,
    }
    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}
    return tools[tool_name](**tool_args)


# OpenAI function-calling schema for the ReAct agent
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator_tool",
            "description": (
                "Accurately calculate the total cost of a list of activities. "
                "Use this to verify budget accuracy."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "activities": {
                        "type": "array",
                        "description": "List of activity objects with name, cost, and description.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "cost": {"type": "number"},
                                "description": {"type": "string"},
                            },
                        },
                    }
                },
                "required": ["activities"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_activities_by_date_tool",
            "description": "Retrieve the list of available activities for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_str": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    }
                },
                "required": ["date_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_evals_tool",
            "description": "Evaluate the current travel plan by running all quality checks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_dict": {
                        "type": "object",
                        "description": "Travel plan dict with 'days' and 'total_cost'.",
                    },
                    "vacation_dict": {
                        "type": "object",
                        "description": "Vacation info dict.",
                    },
                    "weather_dict": {
                        "type": "object",
                        "description": "Weather forecast dict keyed by date string.",
                    },
                },
                "required": ["plan_dict", "vacation_dict", "weather_dict"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "final_answer_tool",
            "description": (
                "Submit the final validated travel plan. "
                "Only call this when all evaluations pass."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_dict": {
                        "type": "object",
                        "description": "Final travel plan dict with 'days' and 'total_cost'.",
                    }
                },
                "required": ["plan_dict"],
            },
        },
    },
]


# ============================================================
# ItineraryRevisionAgent — ReAct loop to fix failing evals
# ============================================================


class ItineraryRevisionAgent:
    """Revises a travel itinerary using the ReAct (Reasoning + Acting) framework.

    The agent iterates through a THOUGHT → ACTION → OBSERVATION loop until
    all evaluation checks pass, then calls ``final_answer_tool`` to submit
    the validated plan.
    """

    SYSTEM_PROMPT = (
        "You are an expert travel planner that revises itineraries using a "
        "ReAct (Reasoning + Acting) approach.\n\n"
        "Follow this loop:\n"
        "  THOUGHT  — Analyse what needs to be fixed.\n"
        "  ACTION   — Call the appropriate tool.\n"
        "  OBSERVATION — Review the tool's output and decide next step.\n\n"
        "Available tools:\n"
        "  • calculator_tool          — Verify cost calculations.\n"
        "  • get_activities_by_date_tool — Look up valid activities for a date.\n"
        "  • run_evals_tool           — Run all quality checks on the current plan.\n"
        "  • final_answer_tool        — Submit the final plan (only when all checks pass).\n\n"
        "Always run evaluations after making changes. "
        "Call final_answer_tool only when every check returns passed=true."
    )

    def __init__(
        self, client: Any, model: str = "gpt-4o", max_iterations: int = 10
    ) -> None:
        self.client = client
        self.model = model
        self.max_iterations = max_iterations

    def revise(
        self,
        travel_plan: TravelPlan,
        vacation_info: VacationInfo,
        weather_forecast: Dict[str, Any],
        eval_results: List[Dict[str, Any]],
    ) -> TravelPlan:
        """Run the ReAct loop to produce an itinerary that passes all checks.

        Args:
            travel_plan: The current (potentially flawed) travel plan.
            vacation_info: The traveler's preferences and constraints.
            weather_forecast: Weather data keyed by date string.
            eval_results: Results from the initial evaluation run.

        Returns:
            A revised TravelPlan that passes all evaluations.
        """
        failed_count = sum(1 for r in eval_results if not r["passed"])
        initial_message = (
            "Please revise the travel plan based on the evaluation results below.\n\n"
            f"Current Travel Plan:\n{travel_plan.model_dump_json(indent=2)}\n\n"
            f"Vacation Information:\n{vacation_info.model_dump_json(indent=2)}\n\n"
            f"Weather Forecast:\n{json.dumps(weather_forecast, indent=2)}\n\n"
            f"Evaluation Results:\n{json.dumps(eval_results, indent=2)}\n\n"
            f"Failed checks: {failed_count} / {len(eval_results)}\n\n"
            "Fix all issues and submit the corrected plan using final_answer_tool."
        )

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": initial_message},
        ]

        final_plan = travel_plan
        print("\n=== Starting ReAct Revision Loop ===")

        for iteration in range(1, self.max_iterations + 1):
            print(f"\n--- Iteration {iteration} ---")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )

            message = response.choices[0].message
            messages.append(message)

            if not message.tool_calls:
                print("Agent stopped without calling any tool.")
                break

            done = False
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                print(f"  THOUGHT : deciding to call '{tool_name}'")
                print(f"  ACTION  : {tool_name}({json.dumps(tool_args)[:120]}...)")

                result = execute_tool(tool_name, tool_args)

                # Serialise the result for the message history
                if isinstance(result, TravelPlan):
                    result_payload = result.model_dump()
                else:
                    result_payload = result

                print(f"  OBSERVATION : {json.dumps(result_payload)[:200]}...")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result_payload),
                    }
                )

                if tool_name == "final_answer_tool":
                    final_plan = result  # TravelPlan instance
                    print("\n✓ Final answer submitted.")
                    done = True

            if done:
                break
        else:
            print(f"\nReached maximum iterations ({self.max_iterations}).")

        return final_plan


# ============================================================
# Trip Summary & Persistence
# ============================================================


def generate_trip_summary(
    client: Any,
    travel_plan: TravelPlan,
    vacation_info: VacationInfo,
    model: str = "gpt-4o",
) -> str:
    """Generate a short narrative summary of the completed itinerary.

    Args:
        client: An OpenAI client instance.
        travel_plan: The final validated travel plan.
        vacation_info: The traveler's preferences.
        model: The LLM model to use.

    Returns:
        A 3-4 sentence narrative summary string.
    """
    prompt = (
        f"Write a short, engaging narrative summary (3–4 sentences) of this travel itinerary "
        f"for a trip to {vacation_info.destination}.\n\n"
        f"Travel Plan:\n{travel_plan.model_dump_json(indent=2)}\n\n"
        "Highlight the trip's key experiences, total cost, and what makes the itinerary special."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def save_itinerary(
    travel_plan: TravelPlan,
    vacation_info: VacationInfo,
    summary: str,
    filename: Optional[str] = None,
) -> str:
    """Persist the final itinerary to the ``outputs/`` directory.

    Args:
        travel_plan: The validated travel plan.
        vacation_info: The traveler's preferences.
        summary: The narrative trip summary.
        filename: Optional override for the output path.

    Returns:
        The path of the saved file.
    """
    os.makedirs("outputs", exist_ok=True)
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_dest = vacation_info.destination.replace(" ", "_")
        filename = f"outputs/itinerary_{safe_dest}_{timestamp}.json"

    output = {
        "vacation_info": json.loads(vacation_info.model_dump_json()),
        "travel_plan": json.loads(travel_plan.model_dump_json()),
        "summary": summary,
    }
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2)

    print(f"Itinerary saved to {filename}")
    return filename
