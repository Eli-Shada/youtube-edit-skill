#!/usr/bin/env python3
"""mix.py: lay a music bed under a finished master, ducked under the voice (the tested settings), and
deliver at -14 LUFS with the true peak under -1 dBTP. The no-music master is never touched (keep it as the twin).

  1. voice: measured; raised or lowered to -14 LUFS when it is off by more than 0.5 LU (assemble.py usually did it)
  2. bed: starts where its beat comes in (found from the music's own level, or --music-start), loops if the film is
     longer, -12 dB, 0.12 s fade in, faded out over the last 1.3 s
  3. duck: sidechaincompress threshold 0.06, ratio 2.5, attack 30 ms, release 600 ms (approved: the bed sits about
     16 dB under the voice and comes forward a little in pauses)
  4. limiter with headroom (-1.5 dBFS), AAC 256k; then the file is measured: if the true peak still exceeds -1.0 dBTP
     after the encode, it is limited again lower by the overshoot (one master measured -0.8 dBTP)
  5. report: integrated loudness, true peak, how far the ducked bed sits under the voice; then verify-render --master

Usage: python3 mix.py --master master-nomusic.mp4 --music videos/_shared/music/lofi-bed.mp3 --out master.mp4
       [--music-start 4.9] [--bed-db -12] [--duck hook|body|off] [--target -14] [--no-verify]
--duck hook ducks harder (about 16 dB under), body is the approved default (about 16-19 dB), off lays the bed flat.
"""
import argparse, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--master", required=True)
ap.add_argument("--music", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--music-start", type=float)
ap.add_argument("--bed-db", type=float, default=-12.0)
ap.add_argument("--duck", choices=["hook", "body", "off"], default="body")
ap.add_argument("--target", type=float, default=-14.0)
ap.add_argument("--fade-out", type=float, default=1.3)
ap.add_argument("--no-verify", action="store_true")
a = ap.parse_args()


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


def loud(p, extra=None):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p] + (extra or []) + ["-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    s = r[r.rfind("Summary:"):]
    I = float(re.search(r"I:\s*(-?[\d.]+)", s).group(1)); TP = float(re.search(r"Peak:\s*(-?[\d.]+|-inf)", s).group(1).replace("-inf", "-99"))
    return I, TP


def beat_onset(p):
    """Where the music's beat comes in: the first 0.5 s window reaching 70% of the typical level of its first minute."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-t", "60", "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True)
    import array
    x = array.array("h", r.stdout)
    hop = 160      # 20 ms
    rms = [(sum(v * v for v in x[i:i + hop]) / hop) ** 0.5 for i in range(0, len(x) - hop, hop)]
    if len(rms) < 100:
        return 0.0
    win = [sum(rms[i:i + 25]) / 25 for i in range(len(rms) - 25)]
    typical = sorted(win[len(win) // 6:])[len(win[len(win) // 6:]) // 2]
    for i, v in enumerate(win):
        if v >= 0.7 * typical:
            return round(i * 0.02, 2)
    return 0.0


D = dur(a.master)
I0, TP0 = loud(a.master)
gain = a.target - I0 if abs(a.target - I0) > 0.5 else 0.0
def approved_start(music):
    """A start you approved for this track, kept in the sound manifest ("start": seconds), wins over detection."""
    man = os.path.join(HERE, "..", "..", "..", "..", "videos", "_shared", "sfx", "manifest.json")
    try:
        for e in json.load(open(man))["sounds"].values():
            if e.get("file") and os.path.samefile(os.path.join(HERE, "..", "..", "..", "..", e["file"]), music) and e.get("start") is not None:
                return float(e["start"])
    except (OSError, ValueError, KeyError):
        pass
    return None


start = a.music_start if a.music_start is not None else approved_start(a.music)
start = start if start is not None else beat_onset(a.music)
duck = {"hook": "threshold=0.04:ratio=3:attack=30:release=500", "body": "threshold=0.06:ratio=2.5:attack=30:release=600"}.get(a.duck)
print("voice %.1f LUFS -> %+.1f dB; bed from %.2f s at %+.1f dB; duck %s" % (I0, gain, start, a.bed_db, a.duck))


def run(limit_db):
    fo = max(0.0, D - a.fade_out)
    bed = "[1:a]aresample=48000,atrim=0:%.3f,volume=%.1fdB,afade=t=in:d=0.12,afade=t=out:st=%.3f:d=%.2f[bed]" % (D, a.bed_db, fo, a.fade_out)
    if duck:
        g = "[0:a]volume=%.2fdB,asplit=3[voice][sc][vm];%s;[bed][sc]sidechaincompress=%s,asplit=2[duck][bm];" % (gain, bed, duck)
    else:
        g = "[0:a]volume=%.2fdB,asplit=2[voice][vm];%s;[bed]asplit=2[duck][bm];" % (gain, bed)
    g += "[voice][duck]amix=inputs=2:duration=first:normalize=0,alimiter=limit=%.4f:level=false[a];[vm]anullsink;[bm]anullsink" % (10 ** (limit_db / 20.0))
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.master, "-stream_loop", "-1", "-ss", "%.3f" % start, "-i", a.music, "-filter_complex", g,
           "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-movflags", "+write_colr+faststart", a.out]
    subprocess.run(cmd, check=True)
    return loud(a.out)


limit = -1.5
I1, TP1 = run(limit)
if TP1 > -1.0:
    limit -= (TP1 + 1.0) + 0.3
    print("true peak %.2f dBTP after the encode: limiting again at %.1f dBFS" % (TP1, limit))
    I1, TP1 = run(limit)

# how far under the voice the ducked bed sits: the bed alone through the same chain, measured against the voice
bed_cmd = ["ffmpeg", "-y", "-v", "error", "-i", a.master, "-stream_loop", "-1", "-ss", "%.3f" % start, "-i", a.music, "-filter_complex",
           ("[0:a]volume=%.2fdB[sc];[1:a]aresample=48000,atrim=0:%.3f,volume=%.1fdB[bed];" % (gain, D, a.bed_db)) +
           ("[bed][sc]sidechaincompress=%s[b]" % duck if duck else "[bed][sc]amix=inputs=2:weights=1 0:duration=first[b]"),
           "-map", "[b]", "-t", "%.3f" % D, "-f", "wav", "-"]
r = subprocess.run(bed_cmd, capture_output=True)
under = None
if r.returncode == 0 and r.stdout:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "wav", "-i", "-", "-af", "ebur128", "-f", "null", "-"], input=r.stdout, capture_output=True).stderr
    m = re.findall(r"I:\s*(-?[\d.]+)\s*LUFS", p.decode("utf-8", "replace"))
    if m:
        under = (I0 + gain) - float(m[-1])
print("out: %.1f LUFS, true peak %.1f dBTP%s -> %s" % (I1, TP1, ", bed %.1f dB under the voice" % under if under is not None else "", a.out))
if under is not None and not 12 <= under <= 22:
    print("WARN the bed sits %.1f dB under the voice (approved: about 16 hook / 16-19 body): adjust --bed-db" % under)
if not a.no_verify:
    vr = subprocess.run([sys.executable, os.path.join(HERE, "verify-render.py"), "--render", a.out, "--index", "/nonexistent",
                         "--res", "%sx%s" % tuple(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                                                                  "-of", "csv=p=0", a.out], capture_output=True, text=True).stdout.strip().split(",")[:2]),
                         "--master", "--min-mbps", "0", "--out", os.path.splitext(a.out)[0] + "-VERIFY.md"], capture_output=True, text=True)
    print("\n".join(l for l in vr.stdout.splitlines() if re.search(r"Audio|Loud|True|Clip|Digital|PASS ->|FAIL ->", l)))
    sys.exit(vr.returncode)
