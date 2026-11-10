#!/usr/bin/env python3
"""screen-focus.py: where a screen recording changes, as candidate zoom boxes for the `screen` beat (format 43).

The fallback when no cursor data exists (macOS screen recordings keep none; Tella's get_mouse_events is the real
source when you record there). It never invents a cursor or a click: it only reports the region of the screen
that changed (typing, a menu opening, a result streaming in), in SOURCE pixels, padded to a 16:9 box you can
paste into "moves" as {"at": t, "focus": [x, y, w, h]}. You still pick which ones matter: zoom on the thing you
name, one or two per 30 s.

Usage: python3 screen-focus.py --video screen.mp4 [--out focus.json] [--fps 2] [--min-gap 2.0] [--threshold 18]
Prints one line per stretch of change: start, end, box, how much changed.
"""
import argparse, json, subprocess, sys

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--out", default="")
ap.add_argument("--fps", type=float, default=2.0)
ap.add_argument("--width", type=int, default=240, help="analysis width in px (the box is scaled back to source px)")
ap.add_argument("--threshold", type=int, default=18, help="grey-level change that counts as a changed pixel (0-255)")
ap.add_argument("--min-area", type=float, default=0.002, help="smallest changed fraction of the frame that counts")
ap.add_argument("--min-gap", type=float, default=2.0, help="seconds of stillness that end a stretch")
a = ap.parse_args()

probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                   "-of", "json", a.video], capture_output=True, text=True).stdout)
W0, H0 = probe["streams"][0]["width"], probe["streams"][0]["height"]
W = a.width; H = max(2, round(H0 * W / W0 / 2) * 2); k = W0 / float(W)
p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.video, "-vf", "fps=%s,scale=%d:%d,format=gray" % (a.fps, W, H),
                      "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
prev, samples, i = None, [], 0
while True:
    buf = p.stdout.read(W * H)
    if len(buf) < W * H:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W).astype(np.int16)
    if prev is not None:
        m = np.abs(f - prev) > a.threshold
        frac = m.mean()
        if frac >= a.min_area:
            ys, xs = np.nonzero(m)
            x0, x1 = np.percentile(xs, [2, 98]); y0, y1 = np.percentile(ys, [2, 98])   # ignore stray pixels
            samples.append((i / a.fps, frac, x0, y0, x1 + 1, y1 + 1))
    prev = f; i += 1

stretches = []
for s in samples:
    if stretches and s[0] - stretches[-1]["end"] <= a.min_gap:
        st = stretches[-1]
        st["end"] = s[0]; st["x0"] = min(st["x0"], s[2]); st["y0"] = min(st["y0"], s[3])
        st["x1"] = max(st["x1"], s[4]); st["y1"] = max(st["y1"], s[5]); st["sum"] += s[1]; st["n"] += 1
    else:
        stretches.append({"start": s[0], "end": s[0], "x0": s[2], "y0": s[3], "x1": s[4], "y1": s[5], "sum": s[1], "n": 1})

out = []
for st in stretches:
    x0, y0, x1, y1 = st["x0"] * k, st["y0"] * k, st["x1"] * k, st["y1"] * k
    w, h = x1 - x0, y1 - y0
    pad = 0.12
    w, h = w * (1 + 2 * pad), h * (1 + 2 * pad)
    if w / h < 16 / 9.0:          # pad to 16:9 so the zoom fills the frame
        w = h * 16 / 9.0
    else:
        h = w * 9 / 16.0
    w, h = min(w, W0), min(h, H0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bx = max(0, min(W0 - w, cx - w / 2)); by = max(0, min(H0 - h, cy - h / 2))
    full = bool(w >= 0.92 * W0)          # the whole screen changed (a page load, a scroll): no zoom target
    rec = {"start": round(st["start"] - 1 / a.fps, 2), "end": round(st["end"], 2), "focus": [round(bx), round(by), round(w), round(h)],
           "zoom": round(min(2.0, W0 / w, H0 / h), 2), "changed": round(st["sum"] / st["n"], 4), "whole_screen": full}
    out.append(rec)
    print("%6.2f-%6.2f  %s  zoom %.2f  changed %.1f%%%s" % (rec["start"], rec["end"], rec["focus"], rec["zoom"], 100 * rec["changed"],
                                                        "  (whole screen: show it, do not zoom)" if full else ""))
if a.out:
    json.dump({"video": a.video, "size": [W0, H0], "stretches": out}, open(a.out, "w"), indent=1)
print("%d stretches of change in %s (%dx%d)" % (len(out), a.video, W0, H0), file=sys.stderr)
