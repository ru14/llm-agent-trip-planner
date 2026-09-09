import unittest

from project_lib import (
    DayPlan,
    TravelPlan,
    VacationInfo,
    calculator_tool_fn,
    get_available_activities,
    run_evals,
)


class _DummyCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return {"ok": True}


class _DummyClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": _DummyCompletions()})()


class ProjectLibTests(unittest.TestCase):
    def test_get_available_activities_filters_by_weather(self):
        vacation_info = VacationInfo(
            destination="AgentsVille",
            start_date="2026-06-10",
            end_date="2026-06-10",
            interests=["culture"],
            budget=200.0,
        )
        available = get_available_activities(
            vacation_info, {"2026-06-10": "rainy"}
        )["2026-06-10"]

        self.assertGreater(len(available), 0)
        self.assertTrue(all(a["weather_requirement"] == "any" for a in available))

    def test_calculator_tool_fn_returns_expected_total(self):
        result = calculator_tool_fn([30.0, 45.0, 20.0])
        self.assertEqual(result["total_cost"], 95.0)
        self.assertEqual(result["item_count"], 3)

    def test_run_evals_all_passed_for_valid_single_day_plan(self):
        client = _DummyClient()
        vacation_info = VacationInfo(
            destination="AgentsVille",
            start_date="2026-06-10",
            end_date="2026-06-10",
            interests=["culture", "food"],
            budget=100.0,
        )
        plan = TravelPlan(
            destination="AgentsVille",
            days=[
                DayPlan(
                    date="2026-06-10",
                    activities=[
                        {
                            "name": "City Museum Tour",
                            "cost": 30.0,
                            "description": "Museum visit",
                        },
                        {
                            "name": "Local Food Tour",
                            "cost": 45.0,
                            "description": "Food walk",
                        },
                    ],
                    day_total_cost=75.0,
                )
            ],
            total_cost=75.0,
        )
        available_activities = {
            "2026-06-10": [
                {
                    "name": "City Museum Tour",
                    "cost": 30.0,
                    "description": "Museum visit",
                    "weather_requirement": "any",
                },
                {
                    "name": "Local Food Tour",
                    "cost": 45.0,
                    "description": "Food walk",
                    "weather_requirement": "any",
                },
            ]
        }
        results = run_evals(
            plan=plan,
            vacation_info=vacation_info,
            weather_data={"2026-06-10": "sunny"},
            available_activities=available_activities,
            client=client,
        )

        self.assertTrue(results["all_passed"])
        self.assertEqual(len(client.chat.completions.calls), 1)


if __name__ == "__main__":
    unittest.main()
