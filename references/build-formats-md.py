#!/usr/bin/env python3
"""Rebuild references/formats-new.md from the format modules' docstrings (run from the skill folder)."""
import importlib.util, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
out = ["# New formats (43-61): full specs", "", "The composer builds every one of these from `storyboard.json` through the plugin hook (`formats/*.py`). Each",
       "section below is that module's own docstring, so it stays in step with the code. SKILL.md has the one-line row and",
       "when to pick it; read the spec here before writing the beat.", ""]
for f in ["screen", "proven", "signature", "lottie", "overlays"]:
    spec = importlib.util.spec_from_file_location(f, "formats/%s.py" % f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    out += ["## formats/%s.py (%s)" % (f, ", ".join(m.TYPES)), "", "```", m.__doc__.strip(), "```", ""]
out += ["Regenerate: `cd .claude/skills/youtube-edit && python3 references/build-formats-md.py`"]
open("references/formats-new.md", "w").write("\n".join(out) + "\n")
print("wrote references/formats-new.md")
