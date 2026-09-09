# AgentsVille Trip Planner - Technical Documentation

## Project overview

This project implements an LLM-driven itinerary planner for a fictional destination ("AgentsVille").  
The core logic lives in `project_lib.py`, while `project_starter.ipynb` provides the guided notebook workflow.

## Repository structure

- `project_starter.ipynb`: main assignment notebook
- `test_scenarios.ipynb`: interactive scenario runs
- `project_lib.py`: models, simulated data APIs, evaluation checks, and agents
- `tests/test_project_lib.py`: automated unit tests for deterministic core logic
- `outputs/`: generated itinerary JSON files

## Core components

### Data models

- `VacationInfo`: destination, date range, interests, budget, constraints
- `Activity`: itinerary item with name, cost, and description
- `DayPlan`: one day of activities and subtotal
- `TravelPlan`: destination-level itinerary, days, total cost, optional summary

### Simulation helpers

- `get_weather_forecast(vacation_info)`: deterministic weather by trip date
- `get_available_activities(vacation_info, weather_data)`: filters activity catalog by weather compatibility

### Evaluation pipeline

`run_evals(...)` executes five checks:

1. budget accuracy
2. city/date correctness
3. minimum activities/day
4. activity availability by date
5. weather compatibility

The returned object includes per-check pass/fail messages and an `all_passed` summary.

## Running the project

```bash
pip install -r requirements.txt
jupyter notebook project_starter.ipynb
```

## Running tests

```bash
python -m unittest discover -s tests -p "test_*.py"
```
