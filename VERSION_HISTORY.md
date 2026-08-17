# Version History – AgentsVille AI Trip Planner

---

## v1.0.0 – Current Release

**Date:** 2026-08-17

### Features

- `VacationInfo` Pydantic model capturing destination, dates, interests, budget
- Deterministic weather forecast simulation (5 weather conditions)
- 18-activity catalog with weather-requirement filtering
- `ItineraryAgent` – generates initial `TravelPlan` using gpt-4o with JSON mode
- 5-check evaluation system (4 rule-based + 1 LLM-based)
- `ItineraryRevisionAgent` – ReAct loop with 4 tools and max-iteration safeguard
- `generate_trip_summary` – narrative summary via gpt-4o
- `print_itinerary` / `print_eval_results` – display helpers
- `project_starter.ipynb` – 8-step walkthrough notebook
- `test_scenarios.ipynb` – 6 automated test scenarios

### Known Limitations

- Weather and activity data are simulated (no real API integration).
- City is fixed to "AgentsVille"; extending to real cities requires API changes.
- `ItineraryRevisionAgent` may occasionally exceed `max_iterations` on very
  tight budgets with adverse weather.

### Future Improvements

- Real weather API integration (e.g. OpenWeatherMap).
- Real activity/booking API integration.
- Support for multiple cities.
- Streaming output for real-time reasoning display.
- Web UI (Streamlit or Gradio).
