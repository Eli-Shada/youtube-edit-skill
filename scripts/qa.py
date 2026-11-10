#!/usr/bin/env python3
"""qa.py: every quality gate for one video folder, in order, with one summary (QA.md). Exit 1 when a gate fails.

Before the render (W/public/index.html):
  check        npx hyperframes check: lint, runtime (JS errors, missing media, missing 3D assets), layout (off-screen,
               overlap, occluded or cropped text), contrast, motion, audio wiring
  beats        beat-check.py: every anchored element on its word (needs W/transcript.json)
  gaps         gap-scan.py: no long stretch without an overlay or a camera move (long form, over 90 s)
After the render (--render FILE):
  render       verify-render.py: resolution, BT.709 tags, bitrate, duration, A/V, black frames, audio present,
               loudness, true peak, clipping, loud moments, digital silence (--master: the delivered file, strict)

Then the part no script can do: QA.md ends with the creative review (read the frames, judge pacing, readability,
consistency, and whether each effect serves what you say). A clean QA is not proof the edit is good.

Usage: python3 qa.py videos/<p> [--render videos/<p>/output-4k.mp4] [--res 4k|1080p] [--master] [--skip check,beats,gaps]
"""
import argparse, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("project")
ap.add_argument("--render")
ap.add_argument("--res", default="4k")
ap.add_argument("--master", action="store_true")
ap.add_argument("--skip", default="")
a = ap.parse_args()
W = a.project.rstrip("/")
PUB = os.path.join(W, "public")
INDEX = os.path.join(PUB, "index.html")
skip = set(x for x in a.skip.split(",") if x)
rows, notes = [], []


def gate(name, ok, detail):
    rows.append((name, ok, detail))
    print("%-8s %-5s %s" % (name, {True: "PASS", False: "FAIL", None: "skip"}[ok], detail), flush=True)


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


if not os.path.exists(INDEX):
    sys.exit("no %s: compose first" % INDEX)
html = open(INDEX).read()
m = re.search(r'data-composition-id="[^"]+"[^>]*data-duration="([\d.]+)"', html)
D = float(m.group(1)) if m else 0.0

# ---- check -------------------------------------------------------------------------------------------------------
if "check" in skip:
    gate("check", None, "skipped")
else:
    r = sh(["npx", "hyperframes", "check", PUB, "--json"])
    t = r.stdout
    try:
        rep, _ = json.JSONDecoder().raw_decode(t[t.find("{"):])
    except ValueError:
        rep = None
    if rep is None:
        gate("check", False, "no report (%s)" % (r.stderr.strip().splitlines() or ["?"])[-1][:120])
    else:
        errs, warns = [], 0
        def walk(o):
            global warns
            if isinstance(o, dict):
                if "code" in o and o.get("severity") in ("error", "warning"):
                    if o["severity"] == "error":
                        errs.append("%s %s%s" % (o["code"], o.get("selector", ""), " t=%.2f" % o["time"] if isinstance(o.get("time"), (int, float)) else ""))
                    else:
                        warns += 1
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(rep)
        gate("check", bool(rep.get("ok")) and not errs, "%d error(s), %d warning(s)" % (len(errs), warns))
        if errs:
            notes.append(["## check errors", ""] + ["- " + e for e in errs[:40]])

# ---- beats -------------------------------------------------------------------------------------------------------
tr = os.path.join(W, "transcript.json")
if "beats" in skip:
    gate("beats", None, "skipped")
elif not os.path.exists(tr):
    gate("beats", None, "no transcript.json")
else:
    r = sh([sys.executable, os.path.join(HERE, "beat-check.py"), "--index", INDEX, "--transcript", tr])
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    gate("beats", r.returncode == 0, tail[:140])
    if r.returncode:
        notes.append(["## beat-check", "", "```", r.stdout.strip()[-3000:], "```"])

# ---- gaps --------------------------------------------------------------------------------------------------------
if "gaps" in skip or D <= 90:
    gate("gaps", None, "skipped" if "gaps" in skip else "short film (%.0f s): the long-form gap rules do not apply" % D)
else:
    r = sh([sys.executable, os.path.join(HERE, "gap-scan.py"), "--index", INDEX])
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    gate("gaps", r.returncode == 0, tail[:140])
    if r.returncode:
        notes.append(["## gap-scan", "", "```", r.stdout.strip()[-3000:], "```"])

# ---- render ------------------------------------------------------------------------------------------------------
if a.render:
    out = os.path.join(os.path.dirname(os.path.abspath(a.render)), "VERIFY.md")
    cmd = [sys.executable, os.path.join(HERE, "verify-render.py"), "--render", a.render, "--index", INDEX, "--res", a.res, "--out", out]
    if a.master:
        cmd.append("--master")
    r = sh(cmd)
    fails = [ln.split()[0] + (" " + ln.split()[1] if ln.split()[1] not in ("PASS", "FAIL", "WARN", "skip") else "")
             for ln in r.stdout.splitlines() if re.search(r"\s(FAIL)\s", ln)]
    warns = [ln.split("  ")[0].strip() for ln in r.stdout.splitlines() if re.search(r"\sWARN\s", ln)]
    gate("render", r.returncode == 0, "see %s%s%s" % (os.path.relpath(out), "; FAIL: " + ", ".join(fails) if fails else "",
                                                       "; WARN: " + ", ".join(warns) if warns else ""))
else:
    gate("render", None, "pass --render FILE after rendering")

# ---- report ------------------------------------------------------------------------------------------------------
bad = [r for r in rows if r[1] is False]
snaps = sorted(set(round(float(x) + 0.9, 2) for x in re.findall(r'class="card-host clip[^"]*"[^>]*data-start="([\d.]+)"', html)))
lines = ["# QA: %s" % os.path.basename(W), "", "**%s**  (%s)" % ("PASS" if not bad else "FAIL: " + ", ".join(r[0] for r in bad), time.strftime("%Y-%m-%d %H:%M")), "",
         "| Gate | Result | Detail |", "|---|---|---|"]
lines += ["| %s | %s | %s |" % (n, {True: "PASS", False: "FAIL", None: "skip"}[ok], d) for n, ok, d in rows]
for n in notes:
    lines += [""] + n
lines += ["", "## Creative review (by eye, every delivery)", "",
          "Read the snapshot sheet (`snap-beats.py`) and the render sheet, plus contiguous-frame strips across every transition.",
          "Moments to read: " + (" ".join("%.2f" % t for t in snaps) if snaps else "(no cards)"), "",
          "- [ ] Every effect explains, demonstrates or emphasises something said; nothing is there because it could be.",
          "- [ ] Pacing follows the narration (denser on a list or a reveal, calm on a story); no effect on a fixed interval.",
          "- [ ] Every word on screen reads in under 2 s at phone size; captions and cards clear of the face and the edges.",
          "- [ ] One design language: Manrope, the three accents, light glass, the same easing; 3D and icons match it.",
          "- [ ] Demos are the real product (real recordings, real pages); 3D and generated shots never pose as proof.",
          "- [ ] Sounds only where something on screen makes them; the voice is always clear over music and effects.",
          "- [ ] The hook gate (SKILL.md): a meaningful first frame, works muted, the promise has its payoff."]
qa = os.path.join(W, "QA.md")
open(qa, "w").write("\n".join(lines) + "\n")
print("%s -> %s" % ("PASS" if not bad else "FAIL", qa))
sys.exit(1 if bad else 0)
