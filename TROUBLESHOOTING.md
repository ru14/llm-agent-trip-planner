# Troubleshooting – AgentsVille AI Trip Planner

---

## Common Errors

### "API key not found" / `AuthenticationError`

**Symptom:** `openai.AuthenticationError: No API key provided.`

**Fix:**
```bash
export OPENAI_API_KEY="sk-..."
```
Or set it directly in the notebook setup cell:
```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."
```

---

### "Rate limit exceeded" / `RateLimitError`

**Symptom:** `openai.RateLimitError: You exceeded your current quota.`

**Fix:**
- Add `time.sleep(10)` between test scenarios.
- Upgrade to a paid OpenAI tier.
- Switch `MAIN_MODEL` to `"gpt-4o-mini"` to reduce token consumption.

---

### "Invalid JSON response" / `json.JSONDecodeError`

**Symptom:** Agent fails to parse LLM output as JSON.

**Fix:**
- Ensure `openai` package is version 1.0.0 or higher: `pip install --upgrade openai`.
- Both agents use `response_format={"type": "json_object"}` which requires
  the gpt-4o / gpt-4o-mini model family. Non-JSON models will fail.

---

### "Model not available" / `NotFoundError`

**Symptom:** `openai.NotFoundError: The model 'gpt-4o' does not exist.`

**Fix:**
- Check your account has access to gpt-4o at https://platform.openai.com.
- Alternatively, change `MAIN_MODEL = "gpt-3.5-turbo"` (lower quality).

---

### Plan exceeds budget after revision

**Symptom:** `_check_budget_accuracy` keeps failing.

**Fix:**
- Increase `budget` in `VacationInfo`.
- Alternatively, increase `max_iterations` (default: 10) in the
  `ItineraryRevisionAgent` constructor.
- Check that activities added by the agent are genuinely in the catalog
  (no hallucinated activities).

---

### `ValidationError` from Pydantic

**Symptom:** `pydantic_core.ValidationError: X validation errors for TravelPlan`

**Fix:**
- The LLM returned a JSON structure that doesn't match the Pydantic model.
- Re-run the cell; gpt-4o occasionally drifts on complex schemas.
- If it persists, update the system prompt to reinforce the exact field names.

---

## FAQs

**Q: Can I use a different city?**
A: The activity catalog and weather simulation are hard-coded to "AgentsVille".
To use a real city, replace `ACTIVITIES_CATALOG` and `get_weather_forecast()`
with real API calls.

**Q: How do I save multiple itineraries?**
A: Each run writes to `outputs/itinerary_agentsville_<date>.json`. Run the
notebook multiple times with different `VacationInfo` objects.

**Q: The ReAct agent takes too long. How do I speed it up?**
A: Set `MAIN_MODEL = "gpt-4o-mini"` and `EVAL_MODEL = "gpt-4o-mini"` in the
setup cell. This roughly halves latency and reduces cost by ~10×.

**Q: Can I add more activities to the catalog?**
A: Yes – see the "Adding a New Activity" section in `DOCUMENTATION.md`.
