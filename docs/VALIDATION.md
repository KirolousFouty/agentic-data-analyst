# Validation record

This repository was syntax-checked with:

```bash
python3 -m compileall -q backend agents database frontend evaluation tests
```

It completed successfully. On a Python 3.11 Docker container, the focused automated suite passed: **13 passed in 0.19s**. Ruff reported `All checks passed!`; mypy reported `Success: no issues found in 14 source files`.

The full Compose image build is dependency-heavy (it includes Streamlit, Plotly, LangGraph, and Ollama client dependencies) and should be run with `make up` in an interactive terminal. No evaluation results are claimed until `make seed` and `make eval` execute against the locally seeded PostgreSQL database and local Ollama model.

Run the following after starting Docker Desktop:

```bash
cp .env.example .env
make up
make seed
make test
make lint
make eval
```
