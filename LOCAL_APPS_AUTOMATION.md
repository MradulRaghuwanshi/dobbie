Local apps automation
=====================

This tool helps the assistant open locally installed applications from a natural-language command.

Files added:
- `assistant_orchestrator.py` — CLI that accepts a phrase like "Open calculator", extracts the app name
  (optionally using OpenAI if `OPENAI_API_KEY` is set), searches common installation paths, and opens the app.

Usage
-----
Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run examples:

```powershell
python assistant_orchestrator.py "Open notepad"
python assistant_orchestrator.py "Launch Chrome"
```

To enable better intent extraction using an LLM, set your `OPENAI_API_KEY` environment variable:

```powershell
$env:OPENAI_API_KEY = "sk-..."
python assistant_orchestrator.py "Open calculator"
```

Notes
-----
- The script includes a rule-based fallback if `OPENAI_API_KEY` is not provided.
- The search is Windows-focused and performs shallow scans of common install locations. It may not find every app.
- For more robust discovery, you can extend `find_executable_by_name` to parse Start Menu shortcuts or read registry entries.
