#!/usr/bin/env python3
"""Consistency checker for WB-Bot — runs as CI gate in automerge.yml."""

import sys
from pathlib import Path

errors = []


def fail(msg):
    errors.append(msg)


# 1. CLAUDE.md: no 'Flask' (wrong stack — project uses FastAPI)
claude_md = Path("CLAUDE.md").read_text()
if "Flask" in claude_md:
    fail("CLAUDE.md: contains 'Flask' — project uses FastAPI")

# 2. CLAUDE.md: no 'dev' branch or 'promote.yml' references
if "promote.yml" in claude_md:
    fail("CLAUDE.md: references 'promote.yml' — it does not exist; flow is claude/** -> main via automerge.yml")
if any(pat in claude_md for pat in ["→ dev", "-> dev", "into dev", "targets dev", "→ `dev`"]):
    fail("CLAUDE.md: references 'dev' branch — git flow is claude/** -> main directly")

# 3. automerge.yml: uses explicit branches allowlist with both claude/** and cursor/**
automerge = Path(".github/workflows/automerge.yml").read_text()
if "branches-ignore" in automerge:
    fail("automerge.yml: uses 'branches-ignore' — should use explicit branches: [claude/**, cursor/**]")
if "claude/**" not in automerge:
    fail("automerge.yml: missing 'claude/**' in branches filter")
if "cursor/**" not in automerge:
    fail("automerge.yml: missing 'cursor/**' in branches filter")

# 4. CLAUDE.md: all four AI providers listed (must match web/app.py:api_generate())
for provider in ["openai", "anthropic", "gemini", "deepseek"]:
    if provider not in claude_md.lower():
        fail(f"CLAUDE.md: missing AI provider '{provider}' — must match web/app.py:api_generate()")

if errors:
    print("CONSISTENCY ERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("Consistency check passed.")
