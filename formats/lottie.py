"""54 lottie: a Lottie animation (After Effects export, a licensed LottieFiles file, or one made here) played frame by
frame from the timeline, so it seeks like every other format.

{"type": "lottie", "id": "ok", "src": "lottie/done.json"            a file in public/ (or in your --shared lottie/ folder)
   | "make": {"kind": "check|cross|arrow|ring|dots|pulse", ...},     an original made here, in the house colours
 "at": t (default in), "speed": 1.0, "segment": [f0, f1] (frames of the file), "pos": "tl|tr|bl|br|center" | [x, y] (the
 centre, frame px), "size": 220, "plate": true (a light glass plate behind it), "label": "..", "in": t, "out": t, "anchor": ".."}

make kinds (all on a 200 x 200 canvas, 30 fps): check (a sky blue disc pops, a dark check draws: "it worked", done
items), cross (a rose ring, an X draws: the wrong answer), arrow (a line draws to a head: "this leads to"), ring (a
progress ring fills to "value" %, with "color"), dots (three dots pulse "loops" times: thinking, loading), pulse (rings
spread from a dot "loops" times: live, recording). Options: "color": "cyan|amber|magenta|white", "loops": 3,
"value": 72, "dir": "right|down|left|up".

Licences: a LottieFiles animation keeps its own licence (most free ones use the Lottie Simple License: free for
commercial use, no attribution, no reselling the files); record each one in videos/_shared/lottie/LICENSES.md. The made
ones are original to this skill. lottie-web (the player) is MIT.
"""
import json, math, os

TYPES = ["lottie"]

CSS = """
  /* 54. lottie */
  .lt-box { position:absolute; }
  .lt-box .lt-anim { position:absolute; inset:0; }
  .lt-plate { position:absolute; border-radius:36px; background:rgba(255,255,255,.18); border:3px solid rgba(255,255,255,.58);
    box-shadow:0 24px 80px rgba(0,0,0,.38); backdrop-filter:blur(30px) saturate(1.25); -webkit-backdrop-filter:blur(30px) saturate(1.25); opacity:0; }
"""

COL = {"cyan": [0.31, 0.765, 1.0, 1], "amber": [1.0, 0.788, 0.239, 1], "magenta": [1.0, 0.31, 0.482, 1],
       "white": [1, 1, 1, 1], "ink": [0.024, 0.075, 0.11, 1]}
EASE_OUT = {"o": {"x": [0.215], "y": [0.61]}, "i": {"x": [0.355], "y": [1]}}      # easeOutCubic (power2.out)
EASE_IO = {"o": {"x": [0.645], "y": [0.045]}, "i": {"x": [0.355], "y": [1]}}      # easeInOutCubic


def _st(v):
    return {"a": 0, "k": v}


def _anim(keys, ease=EASE_OUT):
    """keys: [(frame, value or [values])]; every key but the last carries the ease out of it."""
    out = []
    for i, (t, v) in enumerate(keys):
        k = {"t": t, "s": v if isinstance(v, list) else [v]}
        if i < len(keys) - 1:
            k.update(json.loads(json.dumps(ease)))
            if isinstance(v, list) and len(v) > 1:
                k["o"] = {"x": ease["o"]["x"] * len(v), "y": ease["o"]["y"] * len(v)}
                k["i"] = {"x": ease["i"]["x"] * len(v), "y": ease["i"]["y"] * len(v)}
        out.append(k)
    return {"a": 1, "k": out}


def _tr(p=(0, 0), s=None, o=None):
    return {"ty": "tr", "p": _st(list(p)), "a": _st([0, 0]), "s": s or _st([100, 100]), "r": _st(0), "o": o or _st(100), "sk": _st(0), "sa": _st(0)}


def _path(pts, closed=False):
    z = [[0, 0] for _ in pts]
    return {"ty": "sh", "ks": _st({"i": z, "o": z, "v": [list(p) for p in pts], "c": closed})}


def _layer(ind, name, shapes, op, s=None, p=(100, 100)):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": name, "sr": 1, "ao": 0, "ip": 0, "op": op, "st": 0, "bm": 0,
            "ks": {"o": _st(100), "r": _st(0), "p": _st([p[0], p[1], 0]), "a": _st([0, 0, 0]), "s": s or _st([100, 100, 100])},
            "shapes": shapes}


def _stroke(col, w):
    return {"ty": "st", "c": _st(col), "o": _st(100), "w": _st(w), "lc": 2, "lj": 2}


def _fill(col):
    return {"ty": "fl", "c": _st(col), "o": _st(100), "r": 1}


def _trim(f0, f1):
    return {"ty": "tm", "s": _st(0), "e": _anim([(f0, 0), (f1, 100)]), "o": _st(0), "m": 1}


def make(spec):
    """An original Lottie (bodymovin 5.7 JSON) for the common UI moments, in the house palette."""
    kind = spec.get("kind", "check")
    col = COL.get(spec.get("color", {"cross": "magenta"}.get(kind, "cyan")), COL["cyan"])
    loops = int(spec.get("loops", 3))
    layers, op = [], 45
    if kind in ("check", "cross"):
        pop = _anim([(0, [0, 0, 100]), (12, [100, 100, 100])])
        if kind == "check":
            disc = [{"ty": "gr", "nm": "disc", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([160, 160])}, _fill(col), _tr()]}]
            mark = [{"ty": "gr", "nm": "check", "it": [_path([(-36, 2), (-11, 27), (38, -24)]), _trim(10, 26), _stroke(COL["ink"], 17), _tr()]}]
        else:
            disc = [{"ty": "gr", "nm": "ring", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([150, 150])}, _stroke(col, 12),
                                                     {"ty": "fl", "c": _st([col[0], col[1], col[2], 1]), "o": _st(18), "r": 1}, _tr()]}]
            mark = [{"ty": "gr", "nm": "x1", "it": [_path([(-28, -28), (28, 28)]), _trim(10, 20), _stroke(col, 15), _tr()]},
                    {"ty": "gr", "nm": "x2", "it": [_path([(28, -28), (-28, 28)]), _trim(16, 26), _stroke(col, 15), _tr()]}]
        layers = [_layer(1, "mark", mark, op), _layer(2, "disc", disc, op, s=pop)]
    elif kind == "arrow":
        d = spec.get("dir", "right")
        rot = {"right": 0, "down": 90, "left": 180, "up": 270}[d]
        a = math.radians(rot)
        R = lambda x, y: (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
        shaft = {"ty": "gr", "nm": "shaft", "it": [_path([R(-70, 0), R(62, 0)]), _trim(0, 16), _stroke(col, 14), _tr()]}
        head = {"ty": "gr", "nm": "head", "it": [_path([R(30, -32), R(64, 0), R(30, 32)]), _trim(14, 24), _stroke(col, 14), _tr()]}
        layers = [_layer(1, "arrow", [head, shaft], op)]
    elif kind == "ring":
        v = max(0.0, min(100.0, float(spec.get("value", 75))))
        track = {"ty": "gr", "nm": "track", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([150, 150])}, _stroke([1, 1, 1, 1], 14),
                                                  {"ty": "tr", "p": _st([0, 0]), "a": _st([0, 0]), "s": _st([100, 100]), "r": _st(0), "o": _st(22), "sk": _st(0), "sa": _st(0)}]}
        arc = {"ty": "gr", "nm": "arc", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([150, 150])},
                                              {"ty": "tm", "s": _st(0), "e": _anim([(0, 0), (36, v)], EASE_IO), "o": _st(0), "m": 1},
                                              _stroke(col, 14), _tr()]}
        layers = [_layer(1, "ring", [arc, track], op, s=_st([100, 100, 100]))]
        layers[0]["ks"]["r"] = _st(-90)
        op = 45
    elif kind == "dots":
        per = 24; op = per * loops
        for i in range(3):
            keys = []
            for L in range(loops):
                b = L * per + i * 4
                keys += [(b, [70, 70, 100]), (b + 6, [118, 118, 100]), (b + 12, [70, 70, 100])]
            keys.append((op, [70, 70, 100]))
            layers.append(_layer(i + 1, "dot%d" % i, [{"ty": "gr", "nm": "d", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([34, 34])}, _fill(col), _tr()]}],
                                 op, s=_anim(keys, EASE_IO), p=(56 + 44 * i, 100)))
    elif kind == "pulse":
        per = 36; op = per * loops
        for r in range(2):
            keys_s, keys_o = [], []
            for L in range(loops):
                b = L * per + r * 12
                keys_s += [(b, [20, 20, 100]), (b + 30, [100, 100, 100])]
                keys_o += [(b, 90), (b + 30, 0)]
            ring = {"ty": "gr", "nm": "ring", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([180, 180])}, _stroke(col, 6),
                                                    _tr(o=_anim(keys_o))]}
            layers.append(_layer(r + 2, "ring%d" % r, [ring], op, s=_anim(keys_s)))
        layers.insert(0, _layer(1, "dot", [{"ty": "gr", "nm": "d", "it": [{"ty": "el", "p": _st([0, 0]), "s": _st([46, 46])}, _fill(col), _tr()]}], op))
    else:
        raise SystemExit("lottie make: kind is check, cross, arrow, ring, dots or pulse (got %r)" % kind)
    for L in layers:
        L["op"] = op
    return {"v": "5.7.4", "fr": 30, "ip": 0, "op": op, "w": 200, "h": 200, "nm": "yt-%s" % kind, "ddd": 0, "assets": [], "layers": layers}


POS = {"tl": (300, 290), "tr": (1620, 290), "bl": (300, 790), "br": (1620, 790), "center": (960, 500)}


def build(b, ctx):
    bid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    src_lib = os.path.join(ctx.SKILL, "assets", "vendor", "lottie", "lottie_light.min.js")
    ctx.stage_file(src_lib, "vendor/lottie_light.min.js")
    ctx.script('    <script src="vendor/lottie_light.min.js"></script>\n')
    if b.get("make"):
        data = make(b["make"])
    else:
        p = os.path.join(ctx.OUT, b["src"])
        if not os.path.exists(p) and ctx.shared and os.path.exists(os.path.join(ctx.shared, b["src"])):
            ctx.stage_file(os.path.join(ctx.shared, b["src"]), b["src"])
        if not os.path.exists(p):
            raise SystemExit("%s: no Lottie file at %s" % (bid, p))
        data = json.load(open(p))
        if '"x":"' in json.dumps(data) or '"x": "' in json.dumps(data):
            print("WARN %s: this Lottie uses expressions, which the light player skips: check its snapshot" % bid)
    fr = float(data.get("fr", 30)); ip, op = float(data.get("ip", 0)), float(data.get("op", 60))
    f0, f1 = (float(x) for x in b.get("segment", [ip, op - 1]))
    speed = float(b.get("speed", 1.0))
    at = float(b.get("at", t_in))
    dur = (f1 - f0) / fr / speed
    if at + dur > t_out + 1e-3:
        print("note %s: the animation runs %.2f s past the beat's out: it is cut at %.2f" % (bid, at + dur - t_out, t_out))
    size = float(b.get("size", 220))
    pos = b.get("pos", "center")
    cx, cy = POS[pos] if isinstance(pos, str) else pos
    plate = ""
    if b.get("plate"):
        pad = size * 0.16
        plate = '<div class="lt-plate" id="%s-plate" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx"></div>' % (bid, cx - size / 2 - pad, cy - size / 2 - pad, size + 2 * pad, size + 2 * pad)
    inner = '%s<div class="lt-box" style="left:%.0fpx;top:%.0fpx;width:%.0fpx;height:%.0fpx"><div class="lt-anim" id="%s-lt"></div></div>%s' % (
        plate, cx - size / 2, cy - size / 2, size, size, bid, ctx.scene_label(bid, b, t_out))
    ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, b.get("anchor", "")))
    ctx.js("window.__hf = window.__hf || {}; window.__hf.buildReady = window.__hf.buildReady || {};")
    # The HyperFrames runtime finds every animation in window.lottie's registry and seeks it to ROOT time, which would
    # override this beat's start, speed and segment. The player is taken off the global once, so the one paused GSAP
    # timeline is its only driver (seek-safe).
    ctx.js("window.__ytLottie = window.__ytLottie || window.lottie; try { delete window.lottie; } catch (e) { window.lottie = undefined; }")
    ctx.js("(function(){ var anim = window.__ytLottie.loadAnimation({ container: document.getElementById('%s-lt'), renderer: 'svg', loop: false, autoplay: false,"
           " rendererSettings: { preserveAspectRatio: 'xMidYMid meet', progressiveLoad: false }, animationData: %s });"
           " window.__hf.buildReady['lottie-%s'] = new Promise(function (res) { if (anim.isLoaded) res(); else anim.addEventListener('DOMLoaded', res); });"
           " var o = { f: %.3f }; var put = function () { anim.goToAndStop(o.f - %.3f, true); };"
           " anim.addEventListener('DOMLoaded', put); put();"
           " tl.fromTo(o, { f: %.3f }, { f: %.3f, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: put }, %.3f); })();"
           % (bid, json.dumps(data, separators=(",", ":")), bid, f0, ip, f0, f1, dur, at))
    if b.get("plate"):
        ctx.js("tl.fromTo('#%s-plate', { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, at - 0.15))
        ctx.js("tl.to('#%s-plate', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
    ctx.js("tl.to('#%s-lt', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.32))
    ctx.transition(b, t_in, t_out)


if __name__ == "__main__":      # write an original Lottie file: python3 formats/lottie.py check out.json [color=amber loops=2 value=60 dir=down]
    import sys
    spec = {"kind": sys.argv[1]}
    for kv in sys.argv[3:]:
        k, v = kv.split("=", 1)
        spec[k] = v if k in ("color", "dir") else float(v)
    json.dump(make(spec), open(sys.argv[2], "w"))
    print("wrote", sys.argv[2])
