"""Overlays: quiet finishing layers, each for a reason. None of them is a look to leave on by default.

  57 grain       fine film grain over a stretch (a cinematic hook, a dark B-roll run), opacity 0.05-0.10. Deterministic:
                 a seeded noise tile shifted a step every frame from the timeline.
     {"type": "grain", "id": "gr", "amount": 0.07, "in": t, "out": t}
  58 lightleak   a soft warm light drifting across the frame once: a hook open, a chapter turn. Never under copy.
     {"type": "lightleak", "id": "lk", "color": "warm|cyan", "strength": 0.35, "from": "left|right", "in": t, "out": t}
  59 captionbg   a bottom gradient so a lower line reads over bright footage (a window, a white wall).
     {"type": "captionbg", "id": "cb", "height": 360, "strength": 0.55, "in": t, "out": t}
  60 lowerthird  name and role for a guest or a person on screen, light glass, on its name.
     {"type": "lowerthird", "id": "lt", "name": "Ada Lovelace", "role": "Founder, Example AI", "pos": "bl|br", "in": t, "out": t, "anchor": "Ada"}
  61 outline     a sky blue rounded box drawing itself round something in the footage (a product held up, a detail),
                 optional short label. In frame px.
     {"type": "outline", "id": "ol", "rect": [x, y, w, h], "label": "the mic", "label_side": "top|bottom", "at": t, "in": t, "out": t}

HyperFrames registry equivalents (grain-overlay, light-leak, lt-* lower thirds) exist; these are the house-styled,
seek-safe versions the composer can place. Particles are not here on purpose (SKILL.md "Rejected").
"""
import os, random, struct, zlib

TYPES = ["grain", "lightleak", "captionbg", "lowerthird", "outline"]

CSS = """
  /* 57-61. overlays */
  .ov-grain { position:absolute; left:-256px; top:-256px; width:2432px; height:1592px; background-repeat:repeat; mix-blend-mode:overlay; pointer-events:none; }
  .ov-leak { position:absolute; left:-30%; top:-20%; width:90%; height:140%; border-radius:50%; mix-blend-mode:screen; opacity:0; pointer-events:none; }
  .ov-under { z-index:9 !important; }      /* under the lower line it is there for */
  .ov-cbg { position:absolute; left:0; right:0; bottom:0; pointer-events:none; opacity:0; }
  .ov-lt { position:absolute; bottom:96px; padding:22px 40px 24px 30px; border-radius:24px; display:flex; align-items:center; gap:22px;
    background:rgba(255,255,255,0); border:3px solid rgba(255,255,255,0); backdrop-filter:blur(30px) saturate(1.25); -webkit-backdrop-filter:blur(30px) saturate(1.25); }
  .ov-lt .bar { width:8px; align-self:stretch; border-radius:4px; background:var(--cyan); }
  .ov-lt .tx { opacity:0; }
  .ov-lt .nm { font-weight:700; font-size:52px; line-height:1.05; letter-spacing:-.012em; color:#fff; text-shadow:0 2px 8px rgba(0,0,0,.6); white-space:nowrap; }
  .ov-lt .rl { margin-top:8px; font-weight:500; font-size:32px; color:rgba(255,255,255,.9); text-shadow:0 2px 8px rgba(0,0,0,.6); white-space:nowrap; }
  .ov-ol { position:absolute; overflow:visible; pointer-events:none; }
  .ov-ol rect { fill:none; stroke:var(--cyan); stroke-width:6; filter:drop-shadow(0 0 10px rgba(79,195,255,.7)); }
  .ov-oll { position:absolute; padding:10px 22px; border-radius:999px; background:var(--cyan); color:#06131c; font-weight:700; font-size:34px; white-space:nowrap; opacity:0; }
"""


def _noise_png(path, size=256, seed=7):
    """A grey noise tile (seeded, so every build is identical), written as a PNG with zlib only."""
    rnd = random.Random(seed)
    rows = b"".join(b"\x00" + bytes(rnd.randrange(60, 196) for _ in range(size)) for _ in range(size))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, "wb").write(png)


def build(b, ctx):
    bid, t, t_in, t_out = b["id"], b["type"], float(b["in"]), float(b["out"])
    J = ctx.js
    if t == "grain":
        _noise_png(os.path.join(ctx.OUT, "img", "grain-256.png"))
        amt = max(0.0, min(0.2, float(b.get("amount", 0.07))))
        inner = '<div class="ov-grain" id="%s-g" style="background-image:url(img/grain-256.png);opacity:%.3f"></div>' % (bid, amt)
        h = ctx.host(bid, t_in, t_out, ctx.track, inner, "-")
        ctx.html(h.replace('style="left:0;top:0;', 'style="z-index:40;left:0;top:0;', 1))     # above every card
        # a new grain position every frame: a stepped proxy, so any frame lands on the same offset
        J("(function(){ var g = document.getElementById('%s-g'), o = { f: 0 }; var put = function(){ var k = Math.floor(o.f);"
          " g.style.transform = 'translate(' + (((k * 97) %% 256) - 128) + 'px,' + (((k * 61) %% 256) - 128) + 'px)'; }; put();"
          " tl.fromTo(o, { f: 0 }, { f: %d, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: put }, %.3f); })();" % (bid, int((t_out - t_in) * 30), t_out - t_in, t_in))
    elif t == "lightleak":
        col = {"warm": "rgba(255,170,90,.9)", "cyan": "rgba(79,195,255,.85)"}.get(b.get("color", "warm"), "rgba(255,170,90,.9)")
        inner = '<div class="ov-leak" id="%s-k" style="background:radial-gradient(closest-side, %s, rgba(255,120,60,.25) 55%%, transparent)"></div>' % (bid, col)
        ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, "-"))
        x0, x1 = (-300, 1500) if b.get("from", "left") == "left" else (1500, -300)
        s = float(b.get("strength", 0.35)); d = t_out - t_in
        J("tl.fromTo('#%s-k', { x: %d, opacity: 0 }, { x: %d, duration: %.3f, ease: 'power1.inOut', immediateRender: false }, %.3f);" % (bid, x0, x1, d, t_in))
        J("tl.to('#%s-k', { opacity: %.2f, duration: %.3f, ease: 'power1.out' }, %.3f);" % (bid, s, d * 0.35, t_in))
        J("tl.to('#%s-k', { opacity: 0, duration: %.3f, ease: 'power1.in' }, %.3f);" % (bid, d * 0.4, t_out - d * 0.4))
    elif t == "captionbg":
        hgt, s = int(b.get("height", 360)), float(b.get("strength", 0.55))
        inner = '<div class="ov-cbg" id="%s-c" style="height:%dpx;background:linear-gradient(0deg, rgba(0,0,0,%.2f) 0%%, rgba(0,0,0,%.2f) 45%%, transparent 100%%)"></div>' % (bid, hgt, s, s * 0.55)
        h = ctx.host(bid, t_in, t_out, ctx.track, inner, "-")
        ctx.html(h.replace('class="card-host clip"', 'class="card-host clip ov-under"', 1))
        J("tl.fromTo('#%s-c', { opacity: 0 }, { opacity: 1, duration: 0.35, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in))
        J("tl.to('#%s-c', { opacity: 0, duration: 0.35, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.35))
    elif t == "lowerthird":
        side = "left:70px" if b.get("pos", "bl") == "bl" else "right:70px"
        inner = ('<div class="ov-lt" id="%s-lt" style="%s"><div class="bar"></div><div class="tx" id="%s-tx"><div class="nm">%s</div>%s</div></div>'
                 % (bid, side, bid, ctx.hesc(b["name"]), '<div class="rl">%s</div>' % ctx.hesc(b["role"]) if b.get("role") else ""))
        ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, b.get("anchor", b["name"])))
        # glass is never faded through an ancestor's opacity (SKILL.md "Animating glass"): tint, border and copy instead
        J("tl.fromTo('#%s-lt', { backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', x: -40 }, { backgroundColor: 'rgba(255,255,255,0.18)', borderColor: 'rgba(255,255,255,0.58)', x: 0, duration: 0.42, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, t_in))
        J("tl.fromTo('#%s-tx', { opacity: 0 }, { opacity: 1, duration: 0.36, immediateRender: false }, %.3f);" % (bid, t_in + 0.06))
        J("tl.to('#%s-tx', { opacity: 0, duration: 0.28, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.4))
        J("tl.to('#%s-lt', { backgroundColor: 'rgba(255,255,255,0)', borderColor: 'rgba(255,255,255,0)', duration: 0.33, ease: 'power2.in' }, %.3f);" % (bid, t_out - 0.35))
    else:   # outline
        x, y, w, h = b["rect"]; at = float(b.get("at", t_in + 0.1)); pad = 10
        per = 2 * (w + h)
        inner = ('<svg class="ov-ol" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx" viewBox="0 0 %d %d"><rect id="%s-r" x="3" y="3" width="%d" height="%d" rx="22"'
                 ' style="stroke-dasharray:%d;stroke-dashoffset:%d"/></svg>' % (x - pad, y - pad, w + 2 * pad, h + 2 * pad, w + 2 * pad, h + 2 * pad, bid, w + 2 * pad - 6, h + 2 * pad - 6, per + 80, per + 80))
        if b.get("label"):
            top = y - pad - 74 if b.get("label_side", "top") == "top" else y + h + pad + 18
            inner += '<div class="ov-oll" id="%s-l" style="left:%dpx;top:%dpx">%s</div>' % (bid, x - pad, top, ctx.hesc(b["label"]))
        ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, b.get("anchor", "")))
        J("tl.fromTo('#%s-r', { strokeDashoffset: %d }, { strokeDashoffset: 0, duration: 0.6, ease: 'power2.inOut', immediateRender: false }, %.3f);" % (bid, per + 80, at))
        if b.get("label"):
            J("tl.fromTo('#%s-l', { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, at + 0.45))
        J("tl.to('#%s .ov-ol, #%s-l', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % ("host-" + bid, bid, t_out - 0.32))
