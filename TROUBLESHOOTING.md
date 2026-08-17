# Troubleshooting Guide

---

## Authentication and API Errors

### `openai.AuthenticationError: Incorrect API key provided`

**Cause:** The `OPENAI_API_KEY` environment variable is not set or is invalid.

**Fix:**
```bash
export OPENAI_API_KEY="sk-..."   # macOS / Linux
set OPENAI_API_KEY=sk-...        # Windows cmd
```

Verify it is set:
```bash
echo $OPENAI_API_KEY             # macOS / Linux
echo %OPENAI_API_KEY%            # Windows cmd
```

---

### `openai.RateLimitError`

**Cause:** API quota exceeded (rate limit or billing limit).

**Fix:**
- Wait a few seconds and retry.
- Check your usage at https://platform.openai.com/usage.
- Upgrade your OpenAI plan if needed.
- Switch `MAIN_MODEL` to `gpt-4o-mini` to reduce cost.

---

### `openai.APIConnectionError`

**Cause:** No internet connection or OpenAI API is down.

**Fix:**
- Check your internet connection.
- Visit https://status.openai.com for service status.

---

## Notebook and Kernel Issues

### Kernel dies when running the notebook

**Cause:** Out of memory (rare), or environment misconfiguration.

**Fix:**
1. Restart the kernel (`Kernel → Restart`).
2. Ensure the correct virtual environment is selected.
3. Reduce trip duration (fewer days = fewer API calls).

---

### `ModuleNotFoundError: No module named 'project_lib'`

**Cause:** The notebook is not running from the project root directory.

**Fix:**
- Launch Jupyter from the project root: `jupyter notebook`
- Or add the project root to `sys.path` at the top of the notebook:
  ```python
  import sys
  sys.path.insert(0, "/path/to/llm-agent-trip-planner")
  ```

---

## Evaluation Failures

### Budget accuracy check fails repeatedly

**Cause:** LLM arithmetic errors in `day_total_cost` or `total_cost`.

**Fix:** The revision agent uses `calculator_tool` to fix these automatically.
If it loops without converging, increase `max_iterations`:
```python
revision_agent.max_iterations = 15
```

---

### Activity availability check fails

**Cause:** The LLM used an activity name that doesn't exactly match the catalog,
or scheduled an outdoor activity on a rainy day.

**Fix:** The revision agent uses `get_activities_by_date_tool` to find
replacements. Check `revision_agent.reasoning_log` to see the agent's reasoning.

---

### Weather compatibility check fails despite correct activities

**Cause:** The LLM-based weather check can occasionally disagree with the
rule-based availability check. This is a known limitation of LLM evaluation.

**Fix:** If the rule-based `activity_availability` check passes, the plan is
technically valid. You can investigate by checking the weather compatibility
check message in `eval_results["weather_compatibility"]["message"]`.

---

## Data and Validation Issues

### `pydantic.ValidationError`

**Cause:** The LLM returned malformed JSON or a JSON object that doesn't match
the `TravelPlan` schema.

**Fix:**
- Re-run the cell (LLM responses are non-deterministic).
- Use `gpt-4o` instead of `gpt-4o-mini` for the main model.
- Check the raw response: `response.choices[0].message.content`.

---

### Plan has wrong destination

**Cause:** LLM did not use the exact destination string.

**Fix:** The `city_date_correctness` check catches this and the revision agent
fixes it. If it persists, ensure `vacation_info.destination = "AgentsVille"`.

---

## Performance Issues

### Revision loop takes many iterations

**Cause:** Complex plan with multiple issues, or budget too tight.

**Fix:**
- Increase `budget` relative to number of days.
- Check `revision_agent.reasoning_log` for the root cause.
- Use `gpt-4o` for the revision agent for better reasoning.

---

### API calls are slow

**Cause:** Network latency or OpenAI server load.

**Fix:**
- Use `gpt-4o-mini` for both main and eval models during development.
- Check OpenAI status at https://status.openai.com.

---

## Getting Help

1. Check this guide first.
2. Review the [DOCUMENTATION.md](DOCUMENTATION.md) for technical details.
3. Open an issue on the GitHub repository.
