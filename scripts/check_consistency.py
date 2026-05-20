#!/usr/bin/env python3
"""Consistency checker for WB-Bot — runs as CI gate in automerge.yml."""

import sys
from pathlib import Path

errors = []


def fail(msg):
    errors.append(msg)


claude_md = Path("CLAUDE.md").read_text()
automerge = Path(".github/workflows/automerge.yml").read_text()

# 1. CLAUDE.md: no Flask mention (stack is FastAPI)
if "Flask" in claude_md:
    fail("CLAUDE.md: mentions 'Flask' — stack is FastAPI (web/app.py), update the reference")

# 2. CLAUDE.md: no dev branch or promote.yml references
if "→ dev" in claude_md or "promote.yml" in claude_md:
    fail("CLAUDE.md: references '→ dev' or 'promote.yml' — workflow is claude/... → main directly")

# 3. automerge.yml: uses explicit branches allowlist, not branches-ignore
if "branches-ignore" in automerge:
    fail("automerge.yml: uses 'branches-ignore' — should use explicit branches: [claude/**, cursor/**]")
if "claude/**" not in automerge:
    fail("automerge.yml: missing 'claude/**' in branches filter")
if "cursor/**" not in automerge:
    fail("automerge.yml: missing 'cursor/**' in branches filter")

# 4. CLAUDE.md: all 4 AI providers listed (SSOT = web/app.py:api_generate())
for provider in ["openai", "anthropic", "gemini", "deepseek"]:
    if provider not in claude_md.lower():
        fail(f"CLAUDE.md: missing provider '{provider}' — must match web/app.py:api_generate()")

if errors:
    print("CONSISTENCY ERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("Consistency check passed.")
