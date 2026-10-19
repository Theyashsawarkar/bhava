#!/usr/bin/env python3
"""Builds bhava/emoji.json from Unicode's emoji-test.txt (names, groups,
skin-tone variants) and wofi-emoji's keyword list (MIT, Zeioth/wofi-emoji).

  tools/build-data.py emoji-test.txt /usr/bin/wofi-emoji > bhava/emoji.json
"""
import json
import re
import sys

test, wofi = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
keywords = {}
if wofi:
    data = open(wofi, encoding="utf-8").read().split("### DATA ###", 1)[-1]
    for line in data.splitlines():
        if " " in line:
            e, rest = line.split(" ", 1)
            keywords[e.replace("️", "")] = rest

group = sub = ""
emoji, base_of = [], {}
TONES = ["light skin tone", "medium-light skin tone", "medium skin tone", "medium-dark skin tone", "dark skin tone"]
for line in open(test, encoding="utf-8"):
    if line.startswith("# group:"):
        group = line.split(":", 1)[1].strip()
        continue
    if line.startswith("# subgroup:"):
        sub = line.split(":", 1)[1].strip()
        continue
    m = re.match(r"^([0-9A-F ]+)\s*;\s*fully-qualified\s*#\s*(\S+)\s+E[\d.]+\s+(.+)$", line)
    if not m or group == "Component":
        continue
    e, name = m.group(2), m.group(3)
    tone = next((i for i, t in enumerate(TONES) if name.endswith(": " + t) or name.endswith(", " + t)), None)
    if tone is not None and ":" in name and "," not in name.split(":", 1)[1]:
        base = name.split(":")[0]
        if base in base_of:
            base_of[base].setdefault("t", [None] * 5)[tone] = e
        continue
    if ":" in name and "skin tone" in name:
        continue  # mixed tones (two people): kept out of the grid
    item = {"e": e, "n": name, "g": group, "s": sub}
    k = keywords.get(e.replace("️", ""))
    if k:
        # wofi-emoji repeats the name first; keep only the extra words
        extra = k[len(name):].strip() if k.lower().startswith(name.lower()) else k
        if extra:
            item["k"] = extra
    emoji.append(item)
    base_of[name] = item
json.dump(emoji, sys.stdout, ensure_ascii=False, separators=(",", ":"))
print(f"{len(emoji)} emoji, {sum(1 for i in emoji if 't' in i)} with skin tones", file=sys.stderr)
