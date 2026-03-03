#!/usr/bin/env python3
"""Validation gate for Phase 2 refactor. ALL checks must pass."""
import os, sys

SRC = os.path.join(os.path.dirname(__file__), "..", "src", "gamecompanion")

REQUIRED_MODULES = [
    "config.py", "db.py", "llm.py", "graph.py",
    "rag.py", "memory.py", "export.py", "routes.py"
]

MIN_LINES = {
    "config.py": 20, "db.py": 30, "llm.py": 50, "graph.py": 50,
    "rag.py": 30, "memory.py": 30, "export.py": 30, "routes.py": 80
}

MAX_MAIN_LINES = 200  # main.py should be slim after refactor

errors = []

# Check all required modules exist and have content
for mod in REQUIRED_MODULES:
    path = os.path.join(SRC, mod)
    if not os.path.exists(path):
        errors.append(f"MISSING: {mod} does not exist")
        continue
    lines = len(open(path).readlines())
    if lines < MIN_LINES.get(mod, 10):
        errors.append(f"TOO_SHORT: {mod} has {lines} lines (need >= {MIN_LINES[mod]})")
    print(f"  ✓ {mod}: {lines} lines")

# Check main.py is slim
main_path = os.path.join(SRC, "main.py")
if os.path.exists(main_path):
    main_lines = len(open(main_path).readlines())
    if main_lines > MAX_MAIN_LINES:
        errors.append(f"MAIN_TOO_BIG: main.py has {main_lines} lines (max {MAX_MAIN_LINES})")
    else:
        print(f"  ✓ main.py: {main_lines} lines (slim!)")
else:
    errors.append("MISSING: main.py gone entirely")

if errors:
    print("\n❌ VALIDATION FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\n✅ All structural checks passed!")
    sys.exit(0)
