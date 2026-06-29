#!/usr/bin/env python3
"""Validate canonical Agent Skills + the no-dead-link invariant. Stdlib only."""
import re, sys, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ("knowledge/", ".dev/", "CLAUDE.md", "GEMINI.md", "GPT.md")
errors = []

def err(where, msg): errors.append(f"{where}: {msg}")

def check_skill(skill_md: Path):
    rel = skill_md.relative_to(ROOT)
    src = skill_md.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", src, re.S)
    if not m:
        err(rel, "missing YAML frontmatter"); return
    fm = m.group(1)
    if len(fm) > 1024: err(rel, f"frontmatter {len(fm)} chars > 1024")
    fields = {}
    for line in fm.splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1); fields[k.strip()] = v.strip()
    extra = set(fields) - {"name", "description"}
    if extra: err(rel, f"non-canonical frontmatter keys: {sorted(extra)}")
    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9-]+", name): err(rel, f"bad name: {name!r}")
    if name != skill_md.parent.name: err(rel, f"name {name!r} != dir {skill_md.parent.name!r}")
    desc = fields.get("description", "")
    if not desc.startswith("Use when"): err(rel, "description must start with 'Use when'")
    for link in re.findall(r"\]\((reference/[^)]+)\)", src):
        if not (skill_md.parent / link).exists(): err(rel, f"dead reference link: {link}")

def check_dead_links():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout
    tracked = [ROOT / p for p in out.split() if p.endswith((".md", ".json"))]
    for f in tracked:
        if not f.exists() or f.name == "validate_skills.py": continue
        text = f.read_text()
        for tok in PRIVATE:
            for ln in text.splitlines():
                if tok in ln and not ln.lstrip().startswith(("#", "//", ">")):
                    err(f.relative_to(ROOT), f"references private path {tok!r}: {ln.strip()[:80]}")

for skill in sorted((ROOT / "skills").glob("*/SKILL.md")):
    check_skill(skill)
check_dead_links()

if errors:
    print("FAIL"); [print(" -", e) for e in errors]; sys.exit(1)
print("OK — all skills + docs valid"); sys.exit(0)
