#!/usr/bin/env python3
"""icon-search.py: find a line icon by meaning, for any beat that takes "icon" (pills, pipeline, world, deck, ...).

Searches the house set (compose.py ICONS) and every Lucide icon (assets/vendor/lucide, ISC licence) by name and by
Lucide's own tags, best match first. Any name it prints works as "icon": "<name>" in a storyboard.

Usage: python3 icon-search.py ai agent          (words are OR-ed; a name match beats a tag match)
       python3 icon-search.py --svg brain        (also print the inline SVG the composer will draw)
"""
import argparse, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LUC = os.path.join(HERE, "..", "assets", "vendor", "lucide")
ap = argparse.ArgumentParser()
ap.add_argument("words", nargs="+")
ap.add_argument("--limit", type=int, default=15)
ap.add_argument("--svg", action="store_true")
a = ap.parse_args()

src = open(os.path.join(HERE, "compose.py")).read()
block = src[src.index("ICONS = {"):src.index("}", src.index("ICONS = {"))]
house = re.findall(r'"([a-z]+)":', block)
nodes = json.load(open(os.path.join(LUC, "icon-nodes.json")))
tags = json.load(open(os.path.join(LUC, "tags.json")))

words = [w.lower() for w in a.words]
scored = []
for name in set(house) | set(nodes):
    parts = name.split("-"); tg = [t.lower() for t in tags.get(name, [])]
    s = 0
    for w in words:
        if w == name: s += 12
        elif w in parts: s += 8
        elif len(w) >= 4 and w in name: s += 4
        if w in tg: s += 5
        elif len(w) >= 4 and any(w in t for t in tg): s += 2
    if s:
        if name in house: s += 3          # the house set first when it fits
        s -= len(parts) * 0.1             # shorter names first
        scored.append((s, name))
scored.sort(key=lambda x: (-x[0], x[1]))
if not scored:
    sys.exit("no icon matches %s" % " ".join(a.words))
for s, name in scored[:a.limit]:
    print("%-28s %s" % (name, "house" if name in house else "lucide: " + ", ".join(tags.get(name, [])[:6])))
if a.svg:
    name = scored[0][1]
    if name in house:
        print('\n<svg class="icn" viewBox="0 0 64 64"><path class="ic" d="..."/></svg>   (house icon %s)' % name)
    else:
        els = "".join('<%s class="ic" style="stroke-width:1.7" %s/>' % (t, " ".join('%s="%s"' % kv for kv in at.items() if kv[0] != "key")) for t, at in nodes[name])
        print('\n<svg class="icn" viewBox="0 0 64 64"><g transform="scale(2.6667)">%s</g></svg>' % els)
