#!/usr/bin/env python3
"""Strike tasks in ROADMAP.md when PR body contains 'closes TASK:XYZ' tags."""
import os
import re
import sys
from pathlib import Path

TAGS = [t.strip() for t in os.getenv("COMPLETED_TAGS", "").split(",") if t.strip()]
ROADMAP = Path("ROADMAP.md")

if not TAGS or not ROADMAP.exists():
    sys.exit(0)

pattern = re.compile(r"^- \[ \] <!--TASK:(?P<tag>[A-Z]+)-->")

lines = ROADMAP.read_text().splitlines()
new_lines = []
for line in lines:
    m = pattern.match(line)
    if m and m.group("tag") in TAGS:
        line = line.replace("- [ ]", "- [x]", 1)
        # ajoute le ~~ barré si pas déjà présent
        if "~~" not in line:
            parts = line.split("-->", 1)
            line = f"{parts[0]}-->{'~~' + parts[1].strip() + '~~'}"
    new_lines.append(line)

ROADMAP.write_text("\n".join(new_lines))
