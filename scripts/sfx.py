#!/usr/bin/env python3
"""sfx.py: the sound library (videos/_shared/sfx and music) as a searchable manifest with licences.

Every sound has: name, file, category, duration, intensity (soft / medium / strong, from its level), mood, source,
licence, licence URL, attribution, recommended use, never on, peak, onset (silence before the transient). The manifest
is videos/_shared/sfx/manifest.json: the measured fields are refreshed by `index`, the written ones are kept.

  sfx.py index                      measure every file, keep the written fields, list what lacks a licence
  sfx.py find click                 search name, category, mood, use (OR of words); --cat ui --max-dur 0.5
  sfx.py add FILE --name n --category ui --source "Pixabay: <page url>" --license pixabay [--mood ..] [--use ..] [--never ..]
                                    trims the silence before the hit, peak-normalises to -3 dBFS, copies, records it
                                    (--category ambient: a mood bed: stereo, at most 2 min from --start, faded ends, -24 LUFS)
  sfx.py library                    the HyperFrames media-use sounds (Pixabay Content License) not staged yet
  sfx.py stage whoosh-short [...]   copy library sounds in the same way (licence filled in)

A sound with "license": "unconfirmed" is listed but never picked by the editor until you confirm its source.
A sound with "on_request": true (for example effects you tried and did not like) is hidden
from `find` (use --all) and refused by the composer unless the storyboard sound says "requested": true.
Sound rules live in SKILL.md "Sound": a sound needs a cause on screen; never a whoosh on copy.
Do not use these files to train AI models or hand them to training services (Sonniss and other licences forbid it).
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SHARED = os.path.join(ROOT, "videos", "_shared")
MAN = os.path.join(SHARED, "sfx", "manifest.json")
LIB = os.path.expanduser("~/.claude/skills/media-use/audio/assets/sfx")
LICENSES = {
    "pixabay": ("Pixabay Content License", "https://pixabay.com/service/license-summary/", "none required"),
    "sonniss-gdc": ("Sonniss GDC Game Audio Bundle licence", "https://sonniss.com/gdc-bundle-license/", "none required; no AI training; no redistribution of the files"),
    "mixkit": ("Mixkit Free License (sound effects)", "https://mixkit.co/license/#sfxFree", "none required; not the Restricted licence"),
    "epidemic": ("Epidemic Sound subscription", "https://www.epidemicsound.com/license-terms/", "covered while the subscription is active (channel whitelisted)"),
    "cc0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", "none required"),
    "own": ("your own recording", "", "none"),
    "unconfirmed": ("unconfirmed: do not use until the source is known", "", "unknown"),
}
CATS = ["ui", "typing", "pop", "notification", "money", "whoosh", "impact", "riser", "glitch", "accent", "ambient", "music"]


def load():
    if os.path.exists(MAN):
        return json.load(open(MAN))
    return {"about": "videos/_shared sound library; written fields kept, measured fields refreshed by sfx.py index", "sounds": {}}


def save(m):
    os.makedirs(os.path.dirname(MAN), exist_ok=True)
    json.dump(m, open(MAN, "w"), indent=1, sort_keys=True)


def measure(path):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip() or 0)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "volumedetect,ebur128=framelog=info", "-f", "null", "-"], capture_output=True, text=True).stderr
    peak = float((re.search(r"max_volume:\s*(-?[\d.]+)", r) or [0, 0])[1])
    M = [float(x) for x in re.findall(r"M:\s*(-?[\d.]+)", r)]
    mmax = max(M) if M else -70.0
    r2 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "silencedetect=noise=-40dB:d=0.01", "-f", "null", "-"], capture_output=True, text=True).stderr
    m0 = re.search(r"silence_start:\s*(-?[\d.]+)", r2); m1 = re.search(r"silence_end:\s*([\d.]+)", r2)
    onset = float(m1.group(1)) if (m0 and float(m0.group(1)) <= 0.001 and m1) else 0.0
    inten = "strong" if mmax > -12 else ("medium" if mmax > -22 else "soft")
    return {"duration": round(dur, 3), "peak_db": peak, "loudest_momentary_lufs": round(mmax, 1), "onset": round(onset, 3), "intensity": inten}


def index(_a=None):
    m = load(); S = m["sounds"]
    files = sorted(glob.glob(os.path.join(SHARED, "sfx", "*.mp3")) + glob.glob(os.path.join(SHARED, "sfx", "*.wav")) +
                   glob.glob(os.path.join(SHARED, "music", "*.mp3")) + glob.glob(os.path.join(SHARED, "music", "*.wav")))
    seen = set()
    for f in files:
        name = os.path.splitext(os.path.basename(f))[0]
        if name.endswith("-src"):
            continue        # untouched originals kept next to the trimmed file
        seen.add(name)
        e = S.setdefault(name, {"license": "unconfirmed", "category": "music" if "/music/" in f else "", "source": "", "mood": "", "use": "", "never": ""})
        e["file"] = os.path.relpath(f, ROOT)
        e.update(measure(f))
        lic = LICENSES.get(e.get("license", "unconfirmed"), LICENSES["unconfirmed"])
        e["license_name"], e["license_url"], e["attribution"] = lic
    for gone in [k for k in S if k not in seen]:
        del S[gone]
    save(m)
    for k, e in sorted(S.items()):
        print("%-18s %-12s %5.2fs %-7s %-12s %s" % (k, e.get("category", ""), e["duration"], e["intensity"], e.get("license", ""), e.get("use", "")[:60]))
    bad = [k for k, e in S.items() if e.get("license") == "unconfirmed"]
    if bad:
        print("\nno confirmed licence (never picked until confirmed): %s" % ", ".join(sorted(bad)))


def find(a):
    S = load()["sounds"]; words = [w.lower() for w in a.words]; rows = []
    for k, e in S.items():
        if (e.get("license") == "unconfirmed" or e.get("on_request")) and not a.all:
            continue
        if a.cat and e.get("category") != a.cat:
            continue
        if a.max_dur and e["duration"] > a.max_dur:
            continue
        hay = " ".join(str(e.get(f, "")) for f in ("category", "mood", "use", "source")) + " " + k
        score = sum(3 if w in k else (1 if w in hay.lower() else 0) for w in words) if words else 1
        if score:
            rows.append((-score, k, e))
    for _, k, e in sorted(rows):
        print("%-18s %-11s %5.2fs %-7s vol %-4s %s | never: %s" % (k, e.get("category"), e["duration"], e["intensity"], e.get("volume", ""), e.get("use", ""), e.get("never", "")))
    if not rows:
        print("no match; `sfx.py library` lists more, `sfx.py add` brings in your own")


def normalise(src, dst):
    """Trim the silence before the hit (so data-start is the transient) and peak-normalise to -3 dBFS."""
    tmp = tempfile.mktemp(suffix=".wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", "silenceremove=start_periods=1:start_threshold=-40dB", "-ar", "48000", tmp], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", tmp, "-af", "volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    peak = float((re.search(r"max_volume:\s*(-?[\d.]+)", r) or [0, 0])[1])
    args = ["-c:a", "libmp3lame", "-b:a", "192k"] if dst.endswith(".mp3") else []
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "volume=%.2fdB" % (-3.0 - peak)] + args + [dst], check=True)
    os.remove(tmp)


def normalise_bed(src, dst, max_len=120.0, start=0.0):
    """A mood bed or ambience: stereo, at most max_len seconds (from start), 1 s fades so a loop never clicks, matched
    to -24 LUFS integrated (peak capped at -1 dBFS) so beds can be swapped without a level jump. No silence trim."""
    tmp = tempfile.mktemp(suffix=".wav")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip())
    L = min(max_len, dur - start)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % start, "-t", "%.3f" % L, "-i", src, "-ac", "2", "-ar", "48000",
                    "-af", "afade=t=in:d=1,afade=t=out:st=%.3f:d=1" % (L - 1), tmp], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128=peak=true,volumedetect", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", r)[-1]); peak = float(re.search(r"max_volume:\s*(-?[\d.]+)", r).group(1))
    g = min(-24.0 - I, -1.0 - peak)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", "volume=%.2fdB" % g, "-c:a", "libmp3lame", "-b:a", "192k", dst], check=True)
    os.remove(tmp)


def add(a):
    if a.license not in LICENSES or a.license == "unconfirmed":
        sys.exit("give --license (%s): a sound without a known licence does not enter the library" % ", ".join(k for k in LICENSES if k != "unconfirmed"))
    if a.category not in CATS:
        sys.exit("--category is one of %s" % ", ".join(CATS))
    sub = "music" if a.category == "music" else "sfx"
    dst = os.path.join(SHARED, sub, a.name + ".mp3")
    if os.path.exists(dst) and not a.force:
        sys.exit("%s exists (--force to replace)" % os.path.relpath(dst, ROOT))
    if a.category == "music":
        shutil.copy(a.file, dst)
    elif a.category == "ambient":
        normalise_bed(a.file, dst, start=a.start or 0.0)
    else:
        normalise(a.file, dst)
    m = load()
    m["sounds"][a.name] = {"license": a.license, "category": a.category, "source": a.source, "mood": a.mood or "", "use": a.use or "",
                           "never": a.never or "", "volume": a.volume or ""}
    save(m)
    index()


def library(_a):
    have = set(load()["sounds"])
    man = json.load(open(os.path.join(LIB, "manifest.json")))
    for k, v in sorted(man.items()):
        if k not in have:
            print("%-18s %5.2fs  %s" % (k, v.get("duration", 0), v.get("description", "")[:100]))


CURATED = {   # the HyperFrames library sounds worth having, with the house rules attached
    "click-soft": ("ui", "quiet", "a light UI tap: a toggle, a menu item, a hover click", "anything without a cursor", "0.22"),
    "key-press": ("typing", "quiet", "one key: a shortcut, Enter to send", "copy appearing", "0.25"),
    "typing": ("typing", "busy", "real typing for exactly the typing time (prompt window, search)", "anything that is not a keyboard", "0.22"),
    "ping": ("notification", "bright", "a phone or app notification, literally", "a number landing, a reveal, an accent", "0.30"),
    "notification": ("notification", "bright", "a notification banner that is on screen", "a reveal, an accent", "0.30"),
    "whoosh-short": ("whoosh", "fast", "a full-frame scene sweeping in or out (camera or panel motion), at most once a minute", "copy of any kind", "0.18"),
    "whoosh": ("whoosh", "airy", "a large object flying through frame", "copy of any kind", "0.18"),
    "whoosh-cinematic": ("whoosh", "big", "a chapter-scale transition in a trailer-style hook", "copy; body sections", "0.15"),
    "impact-bass-1": ("impact", "heavy", "a hard stop: a big number landing, a reveal that earns weight (rare)", "every reveal; under speech", "0.22"),
    "impact-bass-2": ("impact", "heavy", "the same, longer tail", "under speech", "0.22"),
    "riser": ("riser", "tension", "the build into a reveal you name, ending on the reveal frame", "anything without a payoff", "0.16"),
    "sparkle": ("accent", "light", "a magic or AI moment shown on screen (a result appearing)", "copy, numbers", "0.18"),
    "error": ("accent", "negative", "a visible error state or a wrong answer", "jokes", "0.22"),
}


def stage(a):
    man = json.load(open(os.path.join(LIB, "manifest.json")))
    m = load()
    for name in a.names:
        if name not in man:
            sys.exit("%s is not in the library (sfx.py library)" % name)
        dst = os.path.join(SHARED, "sfx", name + ".mp3")
        normalise(os.path.join(LIB, man[name]["file"]), dst)
        cat, mood, use, never, vol = CURATED.get(name, ("accent", "", man[name].get("description", ""), "", ""))
        m["sounds"][name] = {"license": "pixabay", "category": cat, "mood": mood, "use": use, "never": never, "volume": vol,
                             "source": "HyperFrames media-use library (Pixabay), %s" % man[name]["file"]}
        save(m)
        print("staged", os.path.relpath(dst, ROOT))
    index()


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index")
    s = sub.add_parser("find"); s.add_argument("words", nargs="*"); s.add_argument("--cat"); s.add_argument("--max-dur", type=float); s.add_argument("--all", action="store_true")
    s = sub.add_parser("add"); s.add_argument("file"); s.add_argument("--name", required=True); s.add_argument("--category", required=True)
    s.add_argument("--source", required=True); s.add_argument("--license", required=True); s.add_argument("--mood"); s.add_argument("--use"); s.add_argument("--never")
    s.add_argument("--volume"); s.add_argument("--force", action="store_true")
    s.add_argument("--start", type=float, help="ambient: where the kept 2 minutes begin in the source")
    sub.add_parser("library")
    s = sub.add_parser("stage"); s.add_argument("names", nargs="+")
    a = ap.parse_args()
    {"index": index, "find": find, "add": add, "library": library, "stage": stage}[a.cmd](a)


if __name__ == "__main__":
    main()
