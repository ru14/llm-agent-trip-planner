# Deployment Guide

This guide explains how to set up and run the AgentsVille AI Trip Planner in
different environments.

---

## Local Development

### Prerequisites

- Python 3.9 or later
- pip 21+
- An OpenAI API key

### Setup

```bash
# Clone the repository
git clone https://github.com/ru14/llm-agent-trip-planner.git
cd llm-agent-trip-planner

# Create a virtual environment (strongly recommended)
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."   # macOS / Linux
# set OPENAI_API_KEY=sk-...      # Windows cmd
# $Env:OPENAI_API_KEY="sk-..."   # Windows PowerShell

# Launch Jupyter
jupyter notebook
```

Then open `project_starter.ipynb` in the browser.

---

## Classroom / Shared Environment

1. Distribute the repository (zip or git clone).
2. Students create their own virtual environment and install dependencies.
3. Each student sets their own `OPENAI_API_KEY`.
4. Open `project_starter.ipynb` and run cells top-to-bottom.

### Using `.env` files (optional)

```bash
pip install python-dotenv
```

Create `.env` in the project root:
```
OPENAI_API_KEY=sk-...
```

Add to the top of the first notebook cell:
```python
from dotenv import load_dotenv
load_dotenv()
```

> **Security:** Never commit `.env` files to git. The `.gitignore` already
> excludes `.env` patterns.

---

## Running with VS Code

1. Open the project folder in VS Code.
2. Install the **Jupyter** extension.
3. Select your virtual environment as the Python interpreter
   (`Ctrl+Shift+P` → "Python: Select Interpreter").
4. Open `project_starter.ipynb` and click **Run All**.

---

## Running the Test Suite

```bash
# With Jupyter from the command line
jupyter nbconvert --to notebook --execute test_scenarios.ipynb \
    --output test_scenarios_output.ipynb

# Or open in Jupyter and run all cells manually
jupyter notebook test_scenarios.ipynb
```

---

## Model Configuration

Edit the model constants at the top of each notebook:

```python
MAIN_MODEL = "gpt-4o"        # higher quality, higher cost
EVAL_MODEL = "gpt-4o-mini"   # faster and cheaper for evaluations
```

**Recommended models:**

| Use case | Model | Notes |
|---|---|---|
| Production / best quality | `gpt-4o` | Higher cost |
| Development / testing | `gpt-4o-mini` | Faster, cheaper |
| Budget-sensitive | `gpt-4o-mini` for both | May need more revision iterations |

---

## Cost Estimates

| Model | Typical cost per scenario | Notes |
|---|---|---|
| `gpt-4o` (main) + `gpt-4o-mini` (eval) | ~$0.05–$0.20 | Depends on trip length |
| `gpt-4o-mini` for both | ~$0.01–$0.05 | May require more revisions |

*Prices are approximate and subject to OpenAI pricing changes.*

---

## Troubleshooting Installation

| Problem | Solution |
|---|---|
| `pip: command not found` | Use `pip3` or `python -m pip` |
| `jupyter: command not found` | Activate the virtual environment first |
| `ModuleNotFoundError: No module named 'openai'` | Run `pip install -r requirements.txt` |
| Jupyter opens but kernel dies | Ensure the virtual environment's kernel is selected |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues.
