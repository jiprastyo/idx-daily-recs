#!/bin/bash
# Local one-shot run (macOS/Linux). Windows: run `python pipeline.py` in the repo dir.
set -e
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python pipeline.py "$@"
echo "Preview: open http://localhost:8000  (run: .venv/bin/python -m http.server 8000 -d site)"
