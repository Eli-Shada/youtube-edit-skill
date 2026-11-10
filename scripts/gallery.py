#!/usr/bin/env python3
"""gallery.py: one snapshot of every format that has been used anywhere in the project, on one page, so you can point
at a look ("use the staircase one", "the scorecard again").

Scans every videos/**/storyboard.json, takes the first beat of each type (a real use beats a test), snapshots it from
that project's composed public/ (skipped when it is not composed), and writes videos/_gallery/FORMATS.html with the
number, name and "use for" from SKILL.md's format table. Formats with no sample yet are listed at the end.
Rerun after every delivery: new formats appear on their own.

Usage: python3 gallery.py [--out videos/_gallery] [--refresh]   (--refresh re-snapshots images that already exist)
"""
import argparse, glob, html, json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SKILL = os.path.join(HERE, "..", "SKILL.md")
ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(ROOT, "videos", "_gallery"))
ap.add_argument("--refresh", action="store_true")
a = ap.parse_args()
os.makedirs(os.path.join(a.out, "img"), exist_ok=True)

# the format table: | # | Format | Use for | Composer type |
table = {}
for line in open(SKILL).read().splitlines():
    m = re.match(r"\|\s*([\w*.-]+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|", line)
    if not m or m.group(1) in ("#", "---"):
        continue
    types = re.findall(r"`([a-z0-9]+)`", m.group(4))
    for ty in types or ["(hand-built) " + m.group(2).strip()]:
        table.setdefault(ty, (m.group(1).strip(), m.group(2).strip().strip("*"), m.group(3).strip()))

# first use of each type: real videos first, tests last
boards = sorted(glob.glob(os.path.join(ROOT, "videos", "**", "storyboard.json"), recursive=True),
                key=lambda p: ("/_tests/" in p, "/_gallery/" in p, p))
first = {}
for sb in boards:
    try:
        S = json.load(open(sb))
    except ValueError:
        continue
    pub = os.path.join(os.path.dirname(sb), "public")
    if not os.path.exists(os.path.join(pub, "index.html")):
        continue
    for b in S.get("beats", []):
        ty = b.get("type")
        if ty and ty not in first:
            t0, t1 = float(b["in"]), float(b["out"])
            at = min(t1 - 0.3, t0 + max(0.9, (t1 - t0) * 0.6))          # most of the scene has arrived by 60%
            first[ty] = (pub, round(at, 2), os.path.relpath(sb, ROOT))

by_pub = {}
for ty, (pub, at, src) in first.items():
    if a.refresh or not os.path.exists(os.path.join(a.out, "img", ty + ".jpg")):
        by_pub.setdefault(pub, []).append((ty, at))
for pub, items in by_pub.items():
    tmp = os.path.join(a.out, ".snap")
    shutil.rmtree(tmp, ignore_errors=True)
    times = sorted(set(at for _, at in items))
    r = subprocess.run(["npx", "hyperframes", "snapshot", pub, "--at", ",".join("%g" % t for t in times), "--no-end", "-o", tmp],
                       capture_output=True, text=True, cwd=ROOT)
    for ty, at in items:
        hit = [f for f in glob.glob(os.path.join(tmp, "*.png")) if re.search(r"-at-%ss\.png$" % re.escape("%g" % at), f)]
        if hit:
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", hit[0], "-vf", "scale=640:-2", "-q:v", "4", os.path.join(a.out, "img", ty + ".jpg")])
        else:
            print("no snapshot for %s (%s)" % (ty, (r.stderr or r.stdout).strip().splitlines()[-1:] or "?"))
    shutil.rmtree(tmp, ignore_errors=True)

def num_key(ty):
    n = table.get(ty, ("999",))[0]
    m = re.match(r"(\d+)", n)
    return (int(m.group(1)) if m else 999, n, ty)

tiles = []
for ty in sorted(first, key=num_key):
    n, name, use = table.get(ty, ("", ty, ""))
    img = "img/%s.jpg" % ty
    if not os.path.exists(os.path.join(a.out, img)):
        continue
    tiles.append('<figure><img src="%s" alt="" loading="lazy"><figcaption><b>%s %s</b> <code>%s</code><br>%s<br><small>from %s</small></figcaption></figure>'
                 % (img, html.escape(n), html.escape(name), ty, html.escape(use), html.escape(first[ty][2])))
missing = sorted((t for t in table if t not in first and not t.startswith("(hand-built)")), key=num_key)
hand = sorted(t[13:] for t in table if t.startswith("(hand-built)"))
page = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Format gallery</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>:root{--bg:#0b0d12;--fg:#e8ebf0;--mut:#9aa3b2;--acc:#4FC3FF}body{margin:0;padding:24px 16px;background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,system-ui,sans-serif}
h1{font-size:24px;margin:0 0 4px}p{color:var(--mut);margin:0 0 20px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}
figure{margin:0;background:#141821;border-radius:12px;overflow:hidden}img{width:100%%;display:block;aspect-ratio:16/9;object-fit:cover}
figcaption{padding:10px 12px 12px}code{color:var(--acc)}small{color:var(--mut)}ul{color:var(--mut);columns:2}</style></head><body>
<h1>Format gallery</h1><p>Every format used so far, from its first use. Say the number or the name to ask for it. Built by scripts/gallery.py.</p>
<div class="g">%s</div><h2>No sample yet</h2><ul>%s</ul><h2>Hand-built (no composer type)</h2><ul>%s</ul></body></html>""" % (
    "\n".join(tiles), "".join("<li>%s %s <code>%s</code></li>" % (html.escape(table[t][0]), html.escape(table[t][1]), t) for t in missing),
    "".join("<li>%s</li>" % html.escape(h) for h in hand))
open(os.path.join(a.out, "FORMATS.html"), "w").write(page)
print("%d formats with a sample, %d without -> %s" % (len(tiles), len(missing), os.path.join(a.out, "FORMATS.html")))
