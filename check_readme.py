"""Check the repository README against the repository it describes.

Two failures this catches, both of which happened: a Layout block that names
a file nobody wrote, and prose that reintroduces a term the glossary banned
-- the README is read by more people than the paper is.
"""
import io
import os
import re
import sys

os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")

# The same file has two names: REPO_README.md in the working tree, where it
# is one of several READMEs, and README.md in the assembled repository,
# where it is the one a reader sees.  Checking only the first name made this
# script exit 1 on the copy it exists to check.
name = next((f for f in ("README.md", "REPO_README.md") if os.path.exists(f)),
            None)
if name is None:
    print("  no README.md or REPO_README.md here")
    sys.exit(1)
s = io.open(name, encoding="utf-8").read()
print(f"  {name}: {len(s.splitlines())} lines")

blk = s.split("## Layout")[1].split("```")[1]
base, missing, named = None, [], 0
for line in blk.splitlines():
    m = re.match(r"^([A-Za-z0-9_-]+)/$", line.strip())
    if m:
        base = m.group(1)
        continue
    m = re.match(r"^\s{2}([A-Za-z0-9_.-]+\.(?:py|sh|tex|txt|md|json))", line)
    if m and base:
        named += 1
        p = os.path.join(base, m.group(1))
        if not os.path.exists(p):
            missing.append(p)
print(f"  {named} files named in Layout; missing: "
      + (", ".join(missing) if missing else "none"))

bad_hits = []
for rule in io.open("paper/glossary.txt", encoding="utf-8"):
    if rule.startswith("#") or "|" not in rule:
        continue
    pref, rest = rule.split("|", 1)
    for bad in rest.split("#")[0].split(","):
        bad = bad.strip()
        if bad and re.search(r"\b" + re.escape(bad) + r"\b", s, re.I):
            bad_hits.append((bad, pref.split(",")[0].strip()))
for bad, pref in bad_hits:
    print(f"  GLOSSARY: '{bad}' appears; this project says '{pref}'")
if not bad_hits:
    print("  glossary: clean")

# numbers that must agree with the measurements
import json
d = json.load(open("order-intervention/forward_backward_sigma.json"))["corpora"]
for k, v in (("Fable5", 0.0552), ("GPT54", 0.0753), ("GPT56", 0.1088),
             ("Gemini31", 0.0161), ("Opus46", 0.0574)):
    got = d[k]["median_all"]
    ok = abs(got - v) < 5e-5 and f"{v:+.4f}" in s
    print(f"  {k:<10} README {v:+.4f}  measured {got:+.4f}  "
          + ("ok" if ok else "MISMATCH"))
sys.exit(1 if missing or bad_hits else 0)
