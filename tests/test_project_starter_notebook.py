import json
from pathlib import Path
import unittest


class ProjectStarterNotebookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        notebook_path = (
            Path(__file__).resolve().parents[1] / "project_starter.ipynb"
        )
        with notebook_path.open("r", encoding="utf-8") as f:
            notebook = json.load(f)
        cls.notebook_source = "\n".join(
            "".join(cell.get("source", [])) for cell in notebook.get("cells", [])
        )

    def test_vacation_info_model_is_defined_in_notebook(self):
        self.assertIn("class VacationInfo(BaseModel)", self.notebook_source)
        self.assertIn("destination: str", self.notebook_source)
        self.assertIn("start_date: str", self.notebook_source)
        self.assertIn("end_date: str", self.notebook_source)
        self.assertIn("interests: List[str]", self.notebook_source)
        self.assertIn("budget: float", self.notebook_source)

    def test_weather_and_activity_date_range_setup_is_present(self):
        self.assertIn("start_date = date.fromisoformat(vacation_info.start_date)", self.notebook_source)
        self.assertIn("end_date = date.fromisoformat(vacation_info.end_date)", self.notebook_source)
        self.assertIn("weather_data_by_dates", self.notebook_source)
        self.assertIn("activities_by_dates", self.notebook_source)

    def test_itinerary_prompt_contains_role_reasoning_schema_and_context(self):
        self.assertIn("ITINERARY_AGENT_SYSTEM_PROMPT", self.notebook_source)
        self.assertIn("expert travel planner", self.notebook_source)
        self.assertIn("Reasoning guidance", self.notebook_source)
        self.assertIn("TravelPlan.model_json_schema()", self.notebook_source)
        self.assertIn("VacationInfo", self.notebook_source)
        self.assertIn("weather forecast by date", self.notebook_source)
        self.assertIn("weather-compatible activities by date", self.notebook_source)

    def test_weather_compatibility_prompt_contains_output_format_and_examples(self):
        self.assertIn("ACTIVITY_AND_WEATHER_ARE_COMPATIBLE_SYSTEM_PROMPT", self.notebook_source)
        self.assertIn('"status": "IS_COMPATIBLE" | "IS_INCOMPATIBLE"', self.notebook_source)
        self.assertIn("Compatible example", self.notebook_source)
        self.assertIn("Incompatible example", self.notebook_source)

    def test_tool_docstring_and_revision_react_prompt_are_present(self):
        self.assertIn("def get_activities_by_date_tool(date: str) -> dict:", self.notebook_source)
        self.assertIn("Calendar date in YYYY-MM-DD format", self.notebook_source)
        self.assertIn("ITINERARY_REVISION_AGENT_SYSTEM_PROMPT", self.notebook_source)
        self.assertIn("THOUGHT -> ACTION -> OBSERVATION", self.notebook_source)
        self.assertIn('{"tool_name": "[tool_name]", "arguments": {"arg1": "value1", ...}}', self.notebook_source)
        self.assertIn("You MUST run run_evals_tool before final_answer_tool", self.notebook_source)


if __name__ == "__main__":
    unittest.main()
