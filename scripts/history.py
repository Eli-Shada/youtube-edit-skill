#!/usr/bin/env python3
"""history.py: which formats each delivered video used, so the next one mixes it up.

The tie-break rule in SKILL.md ("two formats compete: the one used least in this video, then the one used least in
your last video") reads this file: videos/_shared/format-history.json.

  history.py record videos/<p> [--title "..."]   after a delivery: counts every storyboard under the folder
  history.py show                                 every recorded video, newest first
  history.py fresh [--last 2]                     signature and occasional formats NOT used in the last N videos
"""
import argparse, glob, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
HIST = os.path.join(ROOT, "videos", "_shared", "format-history.json")
# the formats meant for once or twice a video: the ones worth rotating between videos
ROTATE = ["scorecard", "timeline", "promptresult", "panels", "world", "deck", "flow", "pipeline", "hub",
          "layers", "dashzoom", "lens", "growth", "bars", "stats", "equation", "fan3d", "browser3d", "masktitle", "receipt", "goodbad",
          "sidelist", "bignum", "behind", "pagetour", "fileread", "lottie", "screen", "search", "dock", "chat", "doc"]


def load():
    return json.load(open(HIST)) if os.path.exists(HIST) else {"videos": []}


def counts(folder):
    c = {}
    for sb in glob.glob(os.path.join(folder, "**", "storyboard.json"), recursive=True):
        if "/_tests/" in sb:
            continue
        for b in json.load(open(sb)).get("beats", []):
            c[b["type"]] = c.get(b["type"], 0) + 1
    return c


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record"); r.add_argument("folder"); r.add_argument("--title", default="")
    sub.add_parser("show")
    f = sub.add_parser("fresh"); f.add_argument("--last", type=int, default=2)
    a = ap.parse_args()
    h = load()
    if a.cmd == "record":
        c = counts(a.folder)
        if not c:
            sys.exit("no storyboards under %s" % a.folder)
        name = os.path.relpath(os.path.abspath(a.folder), ROOT)
        h["videos"] = [v for v in h["videos"] if v["folder"] != name]
        h["videos"].append({"folder": name, "title": a.title, "recorded": time.strftime("%Y-%m-%d"), "formats": c})
        os.makedirs(os.path.dirname(HIST), exist_ok=True)
        json.dump(h, open(HIST, "w"), indent=1)
        print("recorded %s: %s" % (name, ", ".join("%s %d" % kv for kv in sorted(c.items(), key=lambda kv: -kv[1]))))
    elif a.cmd == "show":
        for v in reversed(h["videos"]):
            print("%s  %s %s\n   %s" % (v["recorded"], v["folder"], v.get("title", ""), ", ".join("%s %d" % kv for kv in sorted(v["formats"].items(), key=lambda kv: -kv[1]))))
    else:
        recent = set()
        for v in h["videos"][-a.last:]:
            recent |= set(v["formats"])
        ever = {}
        for v in h["videos"]:
            for k, n in v["formats"].items():
                ever[k] = ever.get(k, 0) + n
        fresh = [t for t in ROTATE if t not in recent]
        print("not used in the last %d video(s), least used overall first:" % a.last)
        print("  " + ", ".join(sorted(fresh, key=lambda t: (ever.get(t, 0), ROTATE.index(t)))))


if __name__ == "__main__":
    main()
