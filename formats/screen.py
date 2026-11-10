"""screen (format 43) and the tutorial layout (format 23): a REAL screen recording or screenshot, framed on the brand
wash and directed: zoom to a box, pan between boxes, an optional cursor that travels to each click, click ripples (each
with the light click sound), spotlight and highlight boxes, and an optional camera that follows the cursor. With
"face", your camera footage shrinks into a rounded card bottom-right while the screen plays left of it (format 23).

Everything is in SOURCE pixels of the recording (the numbers you read off a frame of it), so a box survives any
framing. Every move is one GSAP tween on the paused timeline: any frame renders the same, seeking back included.

{"type": "screen", "id": "sc1", "src": "broll/demo.mp4" | "img/ui.png", "size": [w, h] (read from the file when left out),
 "media_start": 0, "frame": "plate" | "full", "chrome": "browser" | "window" | "none", "domain": "claude.ai",
 "moves":     [{"at": t, "focus": [x, y, w, h], "dur": 0.9, "zoom": 2.0}, {"at": t, "focus": "all"}],
 "cursor":    [[t, x, y], ...],          real positions (Tella's get_mouse_events) or ones you give; never invented clicks
 "clicks":    [[t, x, y], ...],          ripple + click sound; the cursor (when shown) arrives there by t
 "spotlight": [{"rect": [x, y, w, h], "at": t, "out": t}],
 "highlight": [{"rect": [x, y, w, h], "at": t, "out": t}],
 "follow":    {"from": t, "to": t, "zoom": 1.8},   the camera keeps the cursor in its middle third (needs "cursor")
 "face":      {"at": t, "out": t, "x": 0.52},      format 23: the camera footage to the corner card and back
 "cursor_size": 64, "zoom_max": 2.0, "settle": true, "sound": true, "label": "..", "transition": "zoomthrough",
 "in": t, "out": t, "anchor": ".."}

Rules (SKILL.md, Tella route): no zoom when a page first appears, zoom on the thing you name (not on every click),
~1.33 to 2.0, one or two per 30 s; every on-screen click makes a light click (0.28); moves never overlap.
"""
import math

TYPES = ["screen"]

CSS = """
  /* 43 / 23. screen recordings: the wash + plate frame under the root-level video (z 20), the cursor/boxes over it */
  .sc-wash { z-index:19 !important; }
  .sc-wash.sc-face { z-index:10 !important; }
  .sc-over { z-index:21 !important; }
  .sc-rig { position:absolute; left:0; top:0; width:1920px; height:1080px; transform-origin:0 0; will-change:transform; }
  .sc-plate { position:absolute; border-radius:18px; background:#0b0d12; overflow:hidden;
    box-shadow:0 40px 120px rgba(0,0,0,.55), 0 10px 30px rgba(0,0,0,.35), 0 0 0 1px rgba(255,255,255,.10); }
  .sc-bar { position:absolute; left:0; right:0; top:0; height:52px; background:#16181f; display:flex; align-items:center; gap:10px; padding:0 20px; }
  .sc-bar .dot { width:13px; height:13px; border-radius:50%; } .sc-bar .r { background:#ff5f57; } .sc-bar .y { background:#febc2e; } .sc-bar .g { background:#28c840; }
  .sc-bar .url { margin-left:16px; padding:7px 20px; border-radius:999px; background:#262a33; color:#e5e5e7; font-size:20px; font-weight:500; line-height:1; }
  .sc-img { position:absolute; display:block; }
  .sc-spot { position:absolute; border-radius:16px; box-shadow:0 0 0 6000px rgba(5,6,12,.62); opacity:0; }
  .sc-hl { position:absolute; border-radius:14px; border:4px solid var(--cyan); box-shadow:0 0 26px rgba(79,195,255,.55), inset 0 0 14px rgba(79,195,255,.18); opacity:0; }
  .sc-rip { position:absolute; left:0; top:0; width:110px; height:110px; margin:-55px 0 0 -55px; border-radius:50%;
    border:5px solid var(--cyan); background:rgba(79,195,255,.18); opacity:0; }
  .sc-cur { position:absolute; left:0; top:0; width:0; height:0; opacity:0; will-change:transform; }
  .sc-curk { position:absolute; left:0; top:0; width:0; height:0; transform-origin:0 0; }
  .sc-curk svg { position:absolute; overflow:visible; transform-origin:21% 14%; filter:drop-shadow(0 3px 5px rgba(0,0,0,.4)); }
"""

BAR = 52


def _ease_inout(p):          # GSAP power2.inOut (cubic)
    return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2


def _ease_out(p):            # GSAP power2.out
    return 1 - (1 - p) ** 3


def build(b, ctx):
    bid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    src = b["src"]
    is_video = src.lower().endswith((".mp4", ".mov", ".webm", ".m4v"))
    sw, sh = b.get("size") or ctx.media_size(src)
    face = b.get("face")
    chrome = b.get("chrome", "browser" if b.get("domain") else "none")
    frame = "plate" if face else b.get("frame", "plate")
    bh = BAR if (chrome != "none" and frame == "plate") else 0

    # ---- layout: where the recording sits at camera 1.0 -------------------------------------------------
    if frame == "full":
        s0 = max(1920.0 / sw, 1080.0 / sh)
        dw, dh = sw * s0, sh * s0
        mx, my = 960 - dw / 2, 540 - dh / 2
        px, py = mx, my
    else:
        if face:   # format 23: the plate fills the area left of the 360x540 corner card (right/bottom 48)
            box_l, box_t, box_w, box_h = 48, 48, 1920 - 48 - 360 - 48 - 40, 1080 - 96
        else:
            box_l, box_t, box_w, box_h = 120, 90, 1680, 900
        s0 = min(box_w / float(sw), (box_h - bh) / float(sh))
        dw, dh = sw * s0, sh * s0
        px = box_l + (box_w - dw) / 2
        py = box_t + (box_h - dh - bh) / 2
        mx, my = px, py + bh

    def to_stage(x, y):
        return mx + x * s0, my + y * s0

    # ---- camera keyframes: (start, dur, ease, Z, TX, TY) ---------------------------------------------
    zmax = float(b.get("zoom_max", 2.0))

    def clamp_t(T, Z, m, d, full):
        a, c = -Z * m, full - Z * (m + d)
        lo, hi = min(a, c), max(a, c)
        return max(lo, min(hi, T))

    def cam_for(focus, zoom=None):
        if focus == "all" or focus is None:
            return 1.0, 0.0, 0.0
        x, y, w, h = focus
        rx, ry = to_stage(x, y)
        rw, rh = w * s0, h * s0
        Z = float(zoom) if zoom else min(1600.0 / rw, 860.0 / rh)
        Z = max(1.0, min(zmax, Z))
        TX = 960 - Z * (rx + rw / 2)
        TY = 540 - Z * (ry + rh / 2)
        return Z, clamp_t(TX, Z, mx if frame == "full" else px, dw, 1920), clamp_t(TY, Z, my if frame == "full" else py, dh + bh, 1080)

    keys = []          # each: [t0, dur, ease, Z, TX, TY]
    settle = b.get("settle", True)
    state = (1.0, 0.0, 0.0)
    moves = sorted(b.get("moves", []), key=lambda m: float(m["at"]))
    if settle and not (moves and float(moves[0]["at"]) < t_in + 0.8):
        z0 = 1.04
        keys.append([t_in, 0.8, "power2.out", 1.0, 0.0, 0.0, (z0, 960 * (1 - z0), 540 * (1 - z0))])

    # follow: the camera recentres on the cursor whenever it leaves the middle third (dead zone), one gesture at a time
    fol = b.get("follow")
    cur_path = sorted([[float(p[0]), float(p[1]), float(p[2])] for p in b.get("cursor", [])])
    clicks = sorted([[float(c[0]), float(c[1]), float(c[2])] for c in b.get("clicks", [])])
    if cur_path or (clicks and b.get("show_cursor", True) and b.get("cursor") is not None):
        merged = {round(p[0], 3): p for p in cur_path}
        for c in clicks:
            merged.setdefault(round(c[0], 3), c)
        cur_path = sorted(merged.values())

    def cursor_at(t):
        if not cur_path:
            return None
        if t <= cur_path[0][0]:
            return cur_path[0][1:]
        for a, c in zip(cur_path, cur_path[1:]):
            if a[0] <= t <= c[0]:
                travel = min(c[0] - a[0], _travel(a, c))
                t0 = c[0] - travel
                if t < t0:
                    return a[1:]
                p = _ease_inout((t - t0) / travel) if travel > 0 else 1
                return a[1] + (c[1] - a[1]) * p, a[2] + (c[2] - a[2]) * p
        return cur_path[-1][1:]

    def _travel(a, c):
        dist = math.hypot((c[1] - a[1]) * s0, (c[2] - a[2]) * s0)
        return max(0.35, min(0.8, dist / 1500.0))

    if fol:
        if not cur_path:
            raise SystemExit('%s: "follow" needs a "cursor" path (real recorded positions, or ones you give)' % bid)
        fz = float(fol.get("zoom", 1.8)); f0, f1 = float(fol["from"]), float(fol["to"])
        cx, cy = cursor_at(f0)
        sz = (1600.0 / fz / s0, 860.0 / fz / s0)
        moves.append({"at": f0, "focus": [cx - sz[0] / 2, cy - sz[1] / 2, sz[0], sz[1]], "zoom": fz, "dur": 0.8})
        t = f0 + 0.8
        cam = cam_for([cx - sz[0] / 2, cy - sz[1] / 2, sz[0], sz[1]], fz)
        while t < f1 - 0.9:
            px_, py_ = cursor_at(t)
            sx, sy = to_stage(px_, py_)
            X, Y = cam[1] + cam[0] * sx, cam[2] + cam[0] * sy
            if abs(X - 960) > 330 or abs(Y - 540) > 190:
                foc = [px_ - sz[0] / 2, py_ - sz[1] / 2, sz[0], sz[1]]
                moves.append({"at": t, "focus": foc, "zoom": fz, "dur": 0.8})
                cam = cam_for(foc, fz)
                t += 0.9
            else:
                t += 0.1
        moves.append({"at": f1 - 0.9, "focus": "all", "dur": 0.9})
        moves.sort(key=lambda m: float(m["at"]))

    for m in moves:
        Z, TX, TY = cam_for(m.get("focus"), m.get("zoom"))
        keys.append([float(m["at"]), float(m.get("dur", 0.9)), "power2.inOut", Z, TX, TY, None])
    keys.sort(key=lambda k: k[0])
    for a, c in zip(keys, keys[1:]):
        if c[0] < a[0] + a[1] - 1e-3:
            raise SystemExit("%s: camera move at %.2f starts before the one at %.2f ends (%.2f): one gesture at a time" % (bid, c[0], a[0], a[0] + a[1]))
    if keys and keys[-1][0] + keys[-1][1] > t_out + 1e-3:
        raise SystemExit("%s: the last camera move ends at %.2f, after the beat's out (%.2f)" % (bid, keys[-1][0] + keys[-1][1], t_out))

    def cam_at(t):
        z, x, y = 1.0, 0.0, 0.0
        if keys and keys[0][6] is not None and t >= keys[0][0]:
            z, x, y = keys[0][6]
        for k in keys:
            if t < k[0]:
                break
            start = k[6] if k[6] is not None else (z, x, y)
            p = min(1.0, (t - k[0]) / k[1]) if k[1] > 0 else 1.0
            e = _ease_out(p) if k[2] == "power2.out" else _ease_inout(p)
            z = start[0] + (k[3] - start[0]) * e
            x = start[1] + (k[4] - start[1]) * e
            y = start[2] + (k[5] - start[2]) * e
        return z, x, y

    # ---- markup -----------------------------------------------------------------------------------------
    bar = ""
    if bh:
        url = '<div class="url">%s</div>' % ctx.hesc(b["domain"]) if b.get("domain") and chrome == "browser" else ""
        bar = '<div class="sc-bar" data-layout-ignore><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>%s</div>' % url
    radius = "0 0 18px 18px" if bh else ("18px" if frame == "plate" else "0")
    plate = ""
    if frame == "plate":
        plate = '<div class="sc-plate" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx">%s</div>' % (px, py, dw, dh + bh, bar)
    img = ""
    if not is_video:
        img = '<img class="sc-img" src="%s" alt="" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:%s" />' % (src, mx, my, dw, dh, radius)
    wash = '<div class="cut"><div class="gridbg"></div><div class="sc-rig" id="%s-wrig" data-layout-allow-overflow>%s%s</div></div>' % (bid, plate, img)
    if face:
        wash = '<div class="cut"><div class="gridbg"></div></div><div class="sc-rig" id="%s-wrig" data-layout-allow-overflow>%s%s</div>' % (bid, plate, img)
    h = ctx.host(bid, t_in, t_out, ctx.track, wash, b.get("anchor", ""))
    ctx.html(h.replace('class="card-host clip"', 'class="card-host clip sc-wash%s"' % (" sc-face" if face else ""), 1))

    rigs = ["#%s-wrig" % bid, "#%s-orig" % bid]
    if is_video:
        vt = ctx.next_track()
        ctx.html('    <video class="cutaway-video clip" id="%s-vid" src="%s" muted playsinline data-start="%.3f" data-duration="%.3f" data-media-start="%.3f" data-track-index="%d"'
                 ' style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;object-fit:fill;border-radius:%s"></video>\n'
                 % (bid, src, t_in, t_out - t_in, float(b.get("media_start", 0)), vt, mx, my, dw, dh, radius))
        ctx.js("tl.set('#%s-vid', { transformOrigin: '%.1fpx %.1fpx' }, %.3f);" % (bid, -mx, -my, t_in))
        rigs.append("#%s-vid" % bid)

    over = []
    if b.get("spotlight"):   # the dim stays inside the recording (never over the face card or the wash)
        spots = []
        for i, sp in enumerate(b["spotlight"]):
            x, y = sp["rect"][0] * s0, sp["rect"][1] * s0; pad = 10
            spots.append('<div class="sc-spot" id="%s-sp%d" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx"></div>'
                         % (bid, i, x - pad, y - pad, sp["rect"][2] * s0 + 2 * pad, sp["rect"][3] * s0 + 2 * pad))
        over.append('<div class="sc-clip" style="position:absolute;overflow:hidden;left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:%s">%s</div>'
                    % (mx, my, dw, dh, radius, "".join(spots)))
    for i, hl in enumerate(b.get("highlight", [])):
        x, y = to_stage(hl["rect"][0], hl["rect"][1]); pad = 8
        z = cam_at(float(hl["at"]))[0]
        over.append('<div class="sc-hl" id="%s-hl%d" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-width:%.2fpx;border-radius:%.1fpx"></div>'
                    % (bid, i, x - pad, y - pad, hl["rect"][2] * s0 + 2 * pad, hl["rect"][3] * s0 + 2 * pad, 4.0 / z, 14.0 / z))
    for i, c in enumerate(clicks):
        over.append('<div class="sc-rip" id="%s-rp%d"></div>' % (bid, i))
    show_cursor = bool(cur_path)
    if show_cursor:
        size = float(b.get("cursor_size", 64))
        over.append('<div class="sc-cur" id="%s-cur"><div class="sc-curk" id="%s-curk">'
                    '<svg id="%s-cursvg" viewBox="0 0 24 24" style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx">'
                    '<path d="M5.2 2.6 L5.2 20.8 L9.9 16.6 L13 23 L16.3 21.4 L13.2 15.3 L19.4 15.3 Z" fill="#1c1c1c" stroke="#ffffff" stroke-width="1.4" stroke-linejoin="round"/></svg>'
                    '</div></div>' % (bid, bid, bid, -size * 5.2 / 24, -size * 2.6 / 24, size, size))
    label = ctx.scene_label(bid, b, t_out)
    oh = ctx.host(bid + "-over", t_in, t_out, ctx.next_track(), '<div class="sc-rig" id="%s-orig" data-layout-allow-overflow>%s</div>%s' % (bid, "".join(over), label), "-")
    ctx.html(oh.replace('class="card-host clip"', 'class="card-host clip sc-over"', 1))

    # ---- timeline -----------------------------------------------------------------------------------------
    R = ", ".join(rigs)
    ctx.js("tl.set('%s', { x: 0, y: 0, scale: 1 }, %.3f);" % (R, t_in))
    for k in keys:
        t0, dur, ease, Z, TX, TY, start = k
        if start is not None:
            ctx.js("tl.fromTo('%s', { x: %.1f, y: %.1f, scale: %.4f }, { x: %.1f, y: %.1f, scale: %.4f, duration: %.3f, ease: '%s', immediateRender: false }, %.3f);"
                   % (R, start[1], start[2], start[0], TX, TY, Z, dur, ease, t0))
        else:
            ctx.js("tl.to('%s', { x: %.1f, y: %.1f, scale: %.4f, duration: %.3f, ease: '%s' }, %.3f);" % (R, TX, TY, Z, dur, ease, t0))
        if show_cursor:     # the cursor and ripples keep their size on screen while the camera zooms
            zs = start[0] if start is not None else cam_at(t0 - 1e-3)[0]
            ctx.js("tl.fromTo('#%s-curk', { scale: %.4f }, { scale: %.4f, duration: %.3f, ease: '%s', immediateRender: false }, %.3f);" % (bid, 1 / zs, 1 / Z, dur, ease, t0))
    if show_cursor:
        ctx.js("tl.set('#%s-curk', { scale: %.4f }, %.3f);" % (bid, 1 / cam_at(t_in)[0], t_in))
        x0, y0 = to_stage(*cur_path[0][1:])
        ctx.js("tl.set('#%s-cur', { x: %.1f, y: %.1f }, %.3f);" % (bid, x0, y0, t_in))
        ctx.js("tl.to('#%s-cur', { opacity: 1, duration: 0.2 }, %.3f);" % (bid, max(t_in, cur_path[0][0] - 0.3)))
        for a, c in zip(cur_path, cur_path[1:]):
            travel = min(c[0] - a[0], _travel(a, c))
            if travel <= 0:
                continue
            x1, y1 = to_stage(c[1], c[2])
            ctx.js("tl.to('#%s-cur', { x: %.1f, y: %.1f, duration: %.3f, ease: 'power2.inOut' }, %.3f);" % (bid, x1, y1, travel, c[0] - travel))
        ctx.js("tl.to('#%s-cur', { opacity: 0, duration: 0.2 }, %.3f);" % (bid, t_out - 0.25))
    for i, c in enumerate(clicks):
        x, y = to_stage(c[1], c[2]); z = cam_at(c[0])[0]
        ctx.js("tl.set('#%s-rp%d', { x: %.1f, y: %.1f }, %.3f);" % (bid, i, x, y, t_in))
        ctx.js("tl.fromTo('#%s-rp%d', { scale: %.3f, opacity: 0.95 }, { scale: %.3f, opacity: 0, duration: 0.55, ease: 'power2.out', immediateRender: false }, %.3f);"
               % (bid, i, 0.25 / z, 1.2 / z, c[0]))
        if show_cursor:
            ctx.js("tl.to('#%s-cursvg', { scale: 0.82, duration: 0.07, ease: 'power2.in', yoyo: true, repeat: 1 }, %.3f);" % (bid, c[0] - 0.07))
        if b.get("sound", True):
            ctx.sfx(bid, "click.mp3", c[0] - 0.01, 0.35, 0.28)
    for i, sp in enumerate(b.get("spotlight", [])):
        ctx.js("tl.fromTo('#%s-sp%d', { opacity: 0 }, { opacity: 1, duration: 0.45, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, i, float(sp["at"])))
        ctx.js("tl.to('#%s-sp%d', { opacity: 0, duration: 0.35, ease: 'power2.in' }, %.3f);" % (bid, i, float(sp.get("out", t_out)) - 0.35))
    for i, hl in enumerate(b.get("highlight", [])):
        ctx.js("tl.fromTo('#%s-hl%d', { opacity: 0, scale: 1.05 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, i, float(hl["at"])))
        ctx.js("tl.to('#%s-hl%d', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, i, float(hl.get("out", t_out)) - 0.3))

    if face:   # format 23: the camera footage to a 360x540 card bottom-right and back (0.6 s power3.inOut, 0.3 s early)
        fx = float(face.get("x", float(str(ctx.origin).split("%")[0]) / 100.0))
        s = 0.5; card_l, card_t, card_w, card_h = 1920 - 48 - 360, 1080 - 48 - 540, 360, 540
        X = card_l + card_w / 2.0 - s * fx * 1920; Y = card_t
        L = (card_l - X) / s; Rr = 1920 - (card_l + card_w - X) / s
        L, Rr = max(0.0, L), max(0.0, Rr)
        ta, tb = float(face["at"]) - 0.3, float(face.get("out", t_out)) - 0.3
        ctx.js("tl.set('#video-wrap', { zIndex: 15, transformOrigin: '0px 0px', clipPath: 'inset(0px 0px 0px 0px round 0px)' }, %.3f);" % t_in)
        if is_video:   # the recording sits above the face: it fades in as the face leaves and out as the face returns
            ctx.js("tl.fromTo('#%s-vid', { opacity: 0 }, { opacity: 1, duration: 0.45, ease: 'power2.out', immediateRender: false }, %.3f);" % (bid, ta + 0.15))
            ctx.js("tl.to('#%s-vid', { opacity: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (bid, tb))
            ctx.js("tl.set('#%s-vid', { opacity: 0 }, %.3f);" % (bid, t_in))
        ctx.js("tl.to('#video-wrap', { x: %.1f, y: %.1f, scale: %.3f, clipPath: 'inset(0px %.1fpx 0px %.1fpx round 64px)', duration: 0.6, ease: 'power3.inOut' }, %.3f);" % (X, Y, s, Rr, L, ta))
        ctx.js("tl.to('#video-wrap', { x: 0, y: 0, scale: 1, clipPath: 'inset(0px 0px 0px 0px round 0px)', duration: 0.6, ease: 'power3.inOut' }, %.3f);" % tb)
        ctx.js("tl.set('#video-wrap', { zIndex: 'auto', transformOrigin: '50%% 0%%', clipPath: 'none' }, %.3f);" % t_out)
    ctx.transition(b, t_in, t_out)
