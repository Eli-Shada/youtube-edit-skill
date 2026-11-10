"""Formats proven on a real delivery, moved out of that video's own build scripts so every
video can use them. The motion is kept exactly as approved there; only the inputs became storyboard keys.

  1   bignum    the big number behind the head (counts up in full digits; optional crack and fall)
  44  behind    big words behind the head, each popping on its word (needs a subject matte)
  45  sidelist  "4 DOWNSIDES": a numbered list sliding in from the left over a darkened edge; one item can take focus
  46  goodbad   "Good for / Bad for": two columns of glass items, green left, red right
  47  subs      word-by-word subtitles (each word lands sky blue and settles white); built from transcript.json
  48  panels    two to four tall panels (number, logos, a still, a name) landing on their beats; one is picked, the rest
                slide off and it grows to the centre, with an optional "My pick" stamp
  18c pagetour  a real page screenshot in a browser window: the camera frames one rect after another, with gold marks or boxes
  18d fileread  a long text file (a SKILL.md, a config) starts zoomed out so it reads as long, then the camera lands on
                each marked line and underlines it
  49  receipt   "What I pay": rows of cost landing on their words, a rule, then the total
  50  scorecard tools side by side: rows of checks, crosses and short values, the column you talk about ringed, and a
                winner that lights with a stamp (the comparison signature)

A subject matte (bignum, behind): "matte": {"src": "subject-matte.webm", "start": t, "media_start": 0} plays over the text
for the beat; keep the camera at 1.0 for that window (a root-level matte does not ride the camera).
"""
import html as _h, json, os, re

TYPES = ["bignum", "behind", "sidelist", "goodbad", "subs", "panels", "pagetour", "fileread", "receipt", "scorecard"]

FONT = '"Manrope", ui-sans-serif, system-ui, sans-serif'
SYS = '-apple-system, "SF Pro Text", "Helvetica Neue", Arial, sans-serif'
MONO = 'ui-monospace, "SF Mono", Menlo, monospace'
GREEN, RED = "#3DDC84", "#FF5468"
CHECK = '<svg width="40" height="40" viewBox="0 0 44 44"><path d="M11 23 L19 31 L33 14" fill="none" stroke="#06131c" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = '<svg width="32" height="32" viewBox="0 0 32 32"><path d="M7 7 L25 25 M25 7 L7 25" stroke="#FF4F7B" stroke-width="5" stroke-linecap="round"/></svg>'

CSS = """
  /* ---- proven formats (formats/proven.py) ---- */
  .pv-host { position:absolute; left:0; top:0; width:1920px; height:1080px; overflow:hidden; pointer-events:none; }
  .pv-matte { position:absolute; left:0; top:0; width:1920px; height:1080px; object-fit:cover; z-index:4; }
  /* 1. big number behind the head */
  .bn-layer { position:absolute; left:0; top:0; width:1920px; height:1080px; z-index:2; pointer-events:none; overflow:hidden; }
  .bn-half { position:absolute; left:0; top:36px; padding:60px 0 90px; width:1920px; text-align:center; white-space:nowrap; font:700 250px/1 FONT; letter-spacing:-.02em;
    color:#fff; -webkit-text-stroke:5px #fff; text-shadow:0 18px 60px rgba(0,0,0,.42); font-variant-numeric:tabular-nums; }
  .bn-half.l { clip-path:polygon(0 0, 50.4% 0, 49.3% 22%, 51.1% 41%, 48.8% 60%, 50.9% 79%, 49.6% 100%, 0 100%); transform-origin:30% 100%; }
  .bn-half.r { clip-path:polygon(50.4% 0, 100% 0, 100% 100%, 49.6% 100%, 50.9% 79%, 48.8% 60%, 51.1% 41%, 49.3% 22%); transform-origin:70% 100%; }
  .bn-whole { position:absolute; left:0; top:36px; padding:60px 0 90px; width:1920px; text-align:center; white-space:nowrap; font:700 250px/1 FONT; letter-spacing:-.02em;
    color:#fff; -webkit-text-stroke:5px #fff; text-shadow:0 18px 60px rgba(0,0,0,.42); font-variant-numeric:tabular-nums; }
  .bn-crack { position:absolute; left:0; top:96px; width:1920px; height:250px; z-index:3; overflow:visible; }
  /* 44. words behind the head */
  .bh-layer { position:absolute; left:0; top:0; width:1920px; height:1080px; z-index:2; pointer-events:none; overflow:hidden; }
  .bh-line { position:absolute; left:0; width:1920px; text-align:center; white-space:nowrap; font:700 230px/1 FONT; letter-spacing:-.02em; color:#fff;
    text-shadow:0 18px 60px rgba(0,0,0,.42); }
  .bh-line .w { display:inline-block; opacity:0; } .bh-line .gold { color:var(--amber); } .bh-line .cyan { color:var(--cyan); }
  .bh-kick { position:absolute; left:0; width:1920px; text-align:center; font:700 44px/1 FONT; letter-spacing:.18em; color:#fff; opacity:0;
    text-shadow:0 2px 4px rgba(0,0,0,.9), 0 3px 18px rgba(0,0,0,.75); }
  /* 45. side list */
  .sl-shade { position:absolute; left:0; top:0; width:1100px; height:1080px; opacity:0;
    background:linear-gradient(90deg, rgba(5,6,12,.86) 0%, rgba(5,6,12,.72) 45%, rgba(5,6,12,0) 100%); }
  .sl-col { position:absolute; left:90px; top:230px; width:640px; }
  .sl-head { font:700 34px/1 FONT; letter-spacing:.18em; color:rgba(255,255,255,.78); opacity:0; }
  .sl-row { margin-top:34px; display:flex; align-items:center; gap:28px; opacity:0; }
  .sl-n { flex:none; width:78px; height:78px; border-radius:20px; display:flex; align-items:center; justify-content:center; font:700 42px/1 FONT; color:#fff;
    border:3px solid rgba(255,255,255,.5); box-sizing:border-box; }
  .sl-t { font:700 58px/1.05 FONT; color:#fff; letter-spacing:-.015em; white-space:nowrap; }
  /* 46. good for / bad for */
  .gb-col { position:absolute; top:150px; width:560px; }
  .gb-head { display:inline-flex; align-items:center; gap:16px; height:80px; padding:0 34px 0 22px; border-radius:40px; font:700 44px/1 FONT; color:#06130b; opacity:0; }
  .gb-head .ic { width:48px; height:48px; border-radius:24px; background:rgba(0,0,0,.18); display:flex; align-items:center; justify-content:center; }
  .gb-item { margin-top:22px; padding:22px 30px; border-radius:24px; font:700 40px/1.18 FONT; color:#fff; opacity:0; box-sizing:border-box;
    background:rgba(17,17,17,.58); border:3px solid rgba(255,255,255,.4); backdrop-filter:blur(30px); -webkit-backdrop-filter:blur(30px); }
  /* 47. word-by-word subtitles */
  .sb-line { position:absolute; left:0; right:0; top:880px; text-align:center; white-space:nowrap; }
  .sb-line .w { display:inline-block; margin:0 10px; font:700 66px/1.1 FONT; color:#fff; opacity:0; letter-spacing:-.01em;
    text-shadow:0 4px 14px rgba(0,0,0,.85), 0 0 2px rgba(0,0,0,.9); }
  /* 48. panels */
  .pn-title { position:absolute; left:0; right:0; top:70px; text-align:center; font:700 66px/1 FONT; letter-spacing:-.015em; color:#fff;
    text-shadow:0 3px 10px rgba(0,0,0,.6); opacity:0; }
  .pn-title .em { color:var(--cyan); }
  .pn-panel { position:absolute; top:196px; height:800px; border-radius:30px; background:rgba(14,16,24,.78); opacity:0;
    border:3px solid rgba(255,255,255,.3); box-shadow:0 30px 90px rgba(0,0,0,.55); transform-origin:50% 50%; }
  .pn-head { position:absolute; left:34px; right:34px; top:30px; height:80px; display:flex; align-items:center; justify-content:space-between; }
  .pn-no { font:700 66px/1 FONT; color:rgba(255,255,255,.55); letter-spacing:.02em; }
  .pn-logos { display:flex; align-items:center; gap:12px; } .pn-logos img { height:58px; width:auto; max-width:120px; }
  .pn-logos .plus { font:700 36px/1 FONT; color:rgba(255,255,255,.7); } .pn-logos .wm { font:700 30px/1 FONT; color:#fff; letter-spacing:-.02em; }
  .pn-scr { position:absolute; left:24px; right:24px; top:128px; height:520px; border-radius:20px; overflow:hidden; background:#0a0c12;
    box-shadow:inset 0 0 0 2px rgba(255,255,255,.08); }
  .pn-img { position:absolute; inset:0; background-size:cover; background-position:center; transform-origin:50% 40%; }
  .pn-name { position:absolute; left:10px; right:10px; top:676px; text-align:center; font:700 50px/1.06 FONT; letter-spacing:-.015em; color:#fff; }
  .pn-stamp { position:absolute; top:-36px; right:-34px; height:80px; padding:0 32px 0 16px; border-radius:40px; display:flex; align-items:center; gap:14px;
    background:rgba(17,17,17,.75); border:3px solid var(--cyan); opacity:0; font:700 38px/1 FONT; color:#fff; z-index:3; white-space:nowrap; }
  .pn-stamp .ok { width:50px; height:50px; border-radius:25px; background:var(--cyan); display:flex; align-items:center; justify-content:center; }
  /* 18c. page tour */
  .wp-win { position:absolute; left:150px; top:60px; width:1620px; height:960px; border-radius:18px; overflow:hidden; background:#fff; opacity:0;
    box-shadow:0 40px 120px rgba(0,0,0,.6); }
  .wp-chrome { position:absolute; left:0; right:0; top:0; height:62px; background:#1d1d1f; display:flex; align-items:center; gap:10px; padding:0 22px; z-index:3; }
  .wp-chrome .dt { width:15px; height:15px; border-radius:50%; } .wp-chrome .r { background:#FF5F57; } .wp-chrome .y { background:#FEBC2E; } .wp-chrome .g { background:#28C840; }
  .wp-url { margin-left:24px; height:38px; padding:0 22px; border-radius:19px; background:#2c2c2e; color:#d1d1d6; font:500 21px/38px SYS; }
  .wp-page { position:absolute; left:0; right:0; top:62px; bottom:0; overflow:hidden; }
  .wp-in { position:absolute; left:0; top:0; transform-origin:0 0; background-repeat:no-repeat; background-size:100% 100%; }
  .wp-mk { position:absolute; border-radius:6px; background:rgba(255,201,61,.6); mix-blend-mode:multiply; transform:scaleX(0); transform-origin:0 50%; }
  .wp-box { position:absolute; border-radius:12px; border:5px solid #FFC93D; background:rgba(255,201,61,.14); box-shadow:0 0 28px rgba(255,201,61,.7); opacity:0; }
  /* 18d. file read */
  .sk-win { position:absolute; left:110px; top:50px; width:1700px; height:980px; border-radius:18px; overflow:hidden; background:#16181d; opacity:0;
    box-shadow:0 40px 120px rgba(0,0,0,.65), 0 0 0 1px rgba(255,255,255,.08); }
  .sk-chrome { position:absolute; left:0; right:0; top:0; height:58px; background:#1d1f25; display:flex; align-items:center; gap:10px; padding:0 22px; z-index:3; border-bottom:1px solid #2a2d35; }
  .sk-chrome .dt { width:14px; height:14px; border-radius:50%; } .sk-chrome .r { background:#FF5F57; } .sk-chrome .y { background:#FEBC2E; } .sk-chrome .g { background:#28C840; }
  .sk-tab { margin-left:22px; font:600 20px/1 MONO; color:#d6d6d6; }
  .sk-page { position:absolute; left:0; right:0; top:58px; bottom:0; overflow:hidden; }
  .sk-in { position:absolute; left:0; top:0; width:1700px; transform-origin:0 0; padding:40px 70px 80px; box-sizing:border-box; }
  .sk-ln { font:400 26px/40px SYS; color:#b9bec8; white-space:pre; overflow:hidden; height:40px; }
  .sk-ln.h1 { font:700 44px/64px SYS; color:#fff; height:64px; } .sk-ln.h2 { padding-top:26px; font:700 34px/52px SYS; color:#fff; height:78px; box-sizing:border-box; }
  .sk-ln b { color:#e8ebf0; } .sk-ln code { font:500 23px/1 MONO; color:#FFC93D; }
  .sk-m { position:relative; color:#fff; }
  .sk-m i { position:absolute; left:0; right:0; bottom:-4px; height:5px; border-radius:3px; background:var(--amber); transform:scaleX(0); transform-origin:0 50%; }
  /* 49. receipt */
  .rc-card { position:absolute; left:410px; top:150px; width:1100px; border-radius:34px; padding:64px 80px 70px;
    background:rgba(255,255,255,.13); border:3px solid rgba(255,255,255,.55); box-shadow:0 30px 100px rgba(0,0,0,.5); opacity:0; }
  .rc-title { font:700 40px/1 FONT; letter-spacing:.16em; color:rgba(255,255,255,.75); }
  .rc-row { margin-top:52px; display:flex; justify-content:space-between; align-items:center; opacity:0; }
  .rc-row .k { display:flex; align-items:center; gap:24px; font:700 60px/1 FONT; color:#fff; letter-spacing:-.012em; }
  .rc-row .k img { height:56px; width:56px; object-fit:contain; }
  .rc-row .v { font:700 60px/1 FONT; color:var(--cyan); }
  .rc-row .v.gold { color:var(--amber); }
  .rc-rule { margin-top:46px; height:3px; background:rgba(255,255,255,.35); transform:scaleX(0); transform-origin:0 50%; }
  .rc-tot { margin-top:40px; display:flex; justify-content:space-between; align-items:baseline; opacity:0; }
  .rc-tot .k { font:700 60px/1 FONT; color:#fff; }
  .rc-tot .v { font:700 110px/1 FONT; color:var(--amber); letter-spacing:-.02em; }
  .rc-tot .v small { font-size:46px; color:rgba(255,255,255,.8); margin-left:8px; }
  /* 50. scorecard */
  .ct-wrap { position:absolute; left:110px; width:1700px; }
  .ct-title { position:absolute; left:0; right:0; top:46px; text-align:center; font:700 60px/1 FONT; letter-spacing:-.015em; color:#fff; opacity:0; }
  .ct-title .em { color:var(--cyan); }
  .ct-head, .ct-row { display:flex; align-items:center; }
  .ct-head { height:170px; }
  .ct-row { height:142px; border-top:2px solid rgba(255,255,255,.12); opacity:0; }
  .ct-lab { width:560px; flex:none; padding-left:20px; font:700 46px/1.1 FONT; color:#fff; letter-spacing:-.012em; }
  .ct-col { flex:none; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
  .ct-head .ct-col img { height:70px; width:auto; max-width:150px; }
  .ct-head .ct-col .pair { display:flex; align-items:center; gap:14px; height:76px; }
  .ct-head .ct-col .pair .wm { font:700 34px/1 FONT; color:#fff; letter-spacing:-.02em; }
  .ct-head .ct-col .nm { margin-top:16px; font:700 32px/1 FONT; color:rgba(255,255,255,.88); }
  .ct-head .ct-col { opacity:0; }
  .ct-yes, .ct-no { width:72px; height:72px; border-radius:36px; display:flex; align-items:center; justify-content:center; }
  .ct-yes { background:var(--cyan); box-shadow:0 0 26px rgba(79,195,255,.5); }
  .ct-no { background:rgba(255,79,123,.18); border:3px solid var(--magenta); }
  .ct-txt { font:700 38px/1.1 FONT; color:rgba(255,255,255,.92); }
  .ct-txt.gold { color:var(--amber); } .ct-txt.good { color:var(--cyan); }
  .ct-ring { position:absolute; top:-12px; border-radius:30px; border:5px solid var(--cyan); opacity:0;
    box-shadow:0 0 36px rgba(79,195,255,.55), inset 0 0 30px rgba(79,195,255,.18); }
  .ct-dim { position:absolute; top:-12px; background:rgba(5,6,12,.62); opacity:0; border-radius:24px; }
  .ct-stamp { position:absolute; top:-48px; height:72px; padding:0 28px 0 14px; border-radius:36px; display:flex; align-items:center; gap:12px;
    background:rgba(17,17,17,.8); border:3px solid var(--cyan); opacity:0; font:700 34px/1 FONT; color:#fff; white-space:nowrap; z-index:3; }
  .ct-stamp .ok { width:46px; height:46px; border-radius:23px; background:var(--cyan); display:flex; align-items:center; justify-content:center; }
""".replace("MONO", MONO).replace("SYS", SYS).replace("FONT", FONT)


def _hostdiv(ctx, pid, t_in, t_out, inner, z=20, anchor="-"):
    a = ctx.attr_anchor(anchor or "-")
    return ('    <div class="pv-host clip" id="%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s style="z-index:%d">%s</div>\n'
            % (pid, t_in, t_out - t_in, ctx.track, a, z, inner))


def _matte(ctx, b, t_in, t_out):
    m = b.get("matte")
    if not m:
        raise SystemExit("%s: %s needs a subject matte: \"matte\": {\"src\": \"subject-matte.webm\", \"start\": t, \"media_start\": 0}" % (b["id"], b["type"]))
    if isinstance(m, str):
        m = {"src": m}
    for op in ctx.S.get("camera", []):
        ts = [float(op[1])] + ([float(op[2])] if op[0] == "creep" else [])
        if any(t_in - 0.01 < t < t_out + 0.01 for t in ts) and not (op[0] == "set" and float(op[2]) == 1.0):
            print("WARN %s: camera op %s at %.2f inside the matte window: keep the camera at 1.0 there (the matte does not ride it)" % (b["id"], op[0], ts[0]))
    if not os.path.exists(os.path.join(ctx.OUT, m["src"])):
        print("WARN %s: %s is not in public/ yet (npx hyperframes remove-background ... --quality best)" % (b["id"], m["src"]))
    return ('    <video class="clip pv-matte" id="%s-matte" src="%s" muted playsinline data-start="%.3f" data-duration="%.3f" data-media-start="%.3f" data-track-index="%d" data-unanchored="1" data-layout-allow-occlusion></video>\n'
            % (b["id"], m["src"], float(m.get("start", t_in)), t_out - float(m.get("start", t_in)), float(m.get("media_start", 0)), ctx.next_track()))


def _esc(s):
    return _h.escape(str(s), quote=False)


# ---------------------------------------------------------------------------------------------------------------
def bignum(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    prefix, suffix = b.get("prefix", ""), b.get("suffix", "")
    value = b["value"]; t_count = float(b.get("count_at", t_in + 0.1)); dur = float(b.get("count_dur", 1.4))
    crack = b.get("crack_at")
    num = _esc(prefix) + "0" + _esc(suffix)
    if crack is not None:
        inner = ('<div class="bn-half l" id="%s-l" data-layout-allow-occlusion>%s</div><div class="bn-half r" id="%s-r" data-layout-allow-occlusion>%s</div>'
                 '<svg class="bn-crack" viewBox="0 0 1920 250"><polyline id="%s-ck" points="967,0 946,55 981,102 937,150 977,198 952,250" fill="none" stroke="#fff" stroke-width="7" stroke-linejoin="bevel"'
                 ' style="filter:drop-shadow(0 0 10px rgba(255,255,255,.9))"/></svg>') % (pid, num, pid, num, pid)
        sel = "#%s-l, #%s-r" % (pid, pid)
    else:
        inner = '<div class="bn-whole" id="%s-l" data-layout-allow-occlusion>%s</div>' % (pid, num)
        sel = "#%s-l" % pid
    pl = b.get("place")
    if pl:
        inner = ('<div style="position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:960px 96px;'
                 'transform:translate(%dpx,%dpx) scale(%.3f)">%s</div>' % (pl[0], pl[1], pl[2], inner))
    ctx.html('    <div class="bn-layer clip" id="%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s>%s</div>\n'
             % (pid, t_in, t_out - t_in, ctx.track, ctx.attr_anchor(b.get("anchor", "-")), inner))
    ctx.html(_matte(ctx, b, t_in, t_out))
    ids = "[%s]" % ", ".join("document.getElementById('%s')" % s.strip()[1:] for s in sel.split(","))
    ctx.js("(function(){ var els = %s; var o = { v: 0 };"
           " var put = function(){ var s = %s + Math.round(o.v).toLocaleString('en-US') + %s; els.forEach(function(e){ e.textContent = s; }); }; put();"
           " tl.fromTo(o, { v: 0 }, { v: %s, duration: %.3f, ease: 'power2.out', immediateRender: false, onUpdate: put }, %.3f); })();"
           % (ids, json.dumps(prefix), json.dumps(suffix), value, dur, t_count))
    ctx.js("tl.fromTo('%s', { opacity:0, y:30 }, { opacity:1, y:0, duration:.35, ease:'power2.out' }, %.3f);" % (sel, t_count - 0.05))
    if crack is not None:
        tc = float(crack)
        ctx.js("(function(){ var p = document.getElementById('%s-ck'); var L = p.getTotalLength(); p.style.strokeDasharray = L; p.style.strokeDashoffset = L; p.style.opacity = 0;"
               " tl.set(p, { opacity: 1 }, %.3f); tl.to(p, { strokeDashoffset: 0, duration: .22, ease: 'power2.in' }, %.3f);"
               " tl.to(p, { opacity: 0, duration: .2 }, %.3f); })();" % (pid, tc, tc, tc + 0.45))
        ctx.js("tl.to('%s', { color:'#FF3B4A', webkitTextStrokeColor:'#FF3B4A', duration:.3, ease:'power1.out' }, %.3f);" % (sel, tc + 0.18))
        ctx.js("tl.to('#%s-l', { x:-60, rotation:-5, duration:.25, ease:'power2.out' }, %.3f);" % (pid, tc + 0.22))
        ctx.js("tl.to('#%s-r', { x:60, rotation:5, duration:.25, ease:'power2.out' }, %.3f);" % (pid, tc + 0.22))
        ctx.js("tl.to('#%s-l', { y:1100, x:-180, rotation:-24, duration:.85, ease:'power2.in' }, %.3f);" % (pid, tc + 0.38))
        ctx.js("tl.to('#%s-r', { y:1100, x:180, rotation:22, duration:.85, ease:'power2.in' }, %.3f);" % (pid, tc + 0.44))
    else:
        ctx.js("tl.to('%s', { opacity:0, y:-30, duration:.3, ease:'power2.in' }, %.3f);" % (sel, t_out - 0.32))


def behind(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    top, size = int(b.get("top", 70)), int(b.get("size", 230)); styles = b.get("styles")
    body = ""
    for li, words in enumerate(b["lines"]):
        ws = "".join('<span class="w %s" id="%s-w%d-%d">%s</span> ' % (w[2] if len(w) > 2 else "", pid, li, k, _esc(w[0])) for k, w in enumerate(words))
        st = styles[li] if styles else "top:%dpx;font-size:%dpx" % (top + li * int(size * 0.98), size)
        body += '<div class="bh-line" style="%s" data-layout-allow-occlusion>%s</div>' % (st, ws)
    if b.get("kicker"):
        body += '<div class="bh-kick" id="%s-k" style="%s">%s</div>' % (pid, b.get("kick_style") or "top:%dpx" % (top - 56), _esc(b["kicker"]))
    ctx.html('    <div class="bh-layer clip" id="%s" data-start="%.3f" data-duration="%.3f" data-track-index="%d"%s>%s</div>\n'
             % (pid, t_in, t_out - t_in, ctx.track, ctx.attr_anchor(b.get("anchor", "-")), body))
    ctx.html(_matte(ctx, b, t_in, t_out))
    if b.get("kicker"):
        ctx.js("tl.fromTo('#%s-k', { opacity:0, y:12 }, { opacity:1, y:0, duration:.3 }, %.3f);" % (pid, float(b.get("kick_at", t_in))))
    for li, words in enumerate(b["lines"]):
        for k, w in enumerate(words):
            ctx.js("tl.fromTo('#%s-w%d-%d', { opacity:0, y:60, scale:.85 }, { opacity:1, y:0, scale:1, duration:.35, ease:'back.out(1.8)' }, %.3f);" % (pid, li, k, float(w[1])))
    ctx.js("tl.to('#%s .w, #%s .bh-kick', { opacity:0, y:-30, duration:.3, ease:'power2.in' }, %.3f);" % (pid, pid, t_out - 0.32))


def sidelist(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    items = b["items"]
    rows = "".join('<div class="sl-row" id="%s-r%d"%s><div class="sl-n" id="%s-n%d">%d</div><div class="sl-t">%s</div></div>'
                   % (pid, k, ' data-at="%.3f"%s' % (float(it[1]), ctx.attr_anchor(it[2] if len(it) > 2 else it[0])), pid, k, k + 1, _esc(it[0]))
                   for k, it in enumerate(items))
    inner = '<div class="sl-shade" id="%s-sh"></div><div class="sl-col"><div class="sl-head" id="%s-h">%s</div>%s</div>' % (pid, pid, _esc(b.get("head", "")), rows)
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, inner, 15, b.get("anchor", "-")))
    J = ctx.js
    J("tl.fromTo('#%s-sh', { opacity:0, x:-260 }, { opacity:1, x:0, duration:.45, ease:'power3.out' }, %.3f);" % (pid, t_in))
    J("tl.fromTo('#%s-h', { opacity:0, x:-60 }, { opacity:1, x:0, duration:.35, ease:'power3.out' }, %.3f);" % (pid, t_in + 0.1))
    for k, it in enumerate(items):
        J("tl.fromTo('#%s-r%d', { opacity:0, x:-90 }, { opacity:1, x:0, duration:.4, ease:'power3.out' }, %.3f);" % (pid, k, float(it[1])))
    f = b.get("focus")
    if f:
        fi, tf = int(f["index"]), float(f["at"])
        others = ", ".join("#%s-r%d" % (pid, k) for k in range(len(items)) if k != fi)
        if others:
            J("tl.to('%s', { opacity:.35, duration:.35 }, %.3f);" % (others, tf))
        J("tl.to('#%s-n%d', { backgroundColor:'#4FC3FF', borderColor:'#4FC3FF', color:'#06131c', duration:.3 }, %.3f);" % (pid, fi, tf))
        J("tl.fromTo('#%s-r%d', { x:0 }, { x:18, duration:.3, ease:'power2.out', immediateRender:false }, %.3f);" % (pid, fi, tf))
    J("tl.to('#%s .sl-row, #%s-h', { opacity:0, x:-60, duration:.3, ease:'power2.in', stagger:.03 }, %.3f);" % (pid, pid, t_out - 0.4))
    J("tl.to('#%s-sh', { opacity:0, duration:.3 }, %.3f);" % (pid, t_out - 0.3))


def goodbad(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    good, bad = b.get("good", []), b.get("bad", [])
    labels = b.get("labels", ["Good for", "Bad for"])

    def col(x, key, head, color, items, ic):
        its = "".join('<div class="gb-item" id="%s-%s%d" style="border-color:%s" data-at="%.3f"%s>%s</div>'
                      % (pid, key, k, color, float(it[1]), ctx.attr_anchor(it[2] if len(it) > 2 else it[0]), _esc(it[0])) for k, it in enumerate(items))
        return ('<div class="gb-col" style="left:%dpx"><div class="gb-head" id="%s-%sh" style="background:%s"><span class="ic">%s</span>%s</div>%s</div>'
                % (x, pid, key, color, ic, _esc(head), its))
    ok = CHECK.replace('stroke="#06131c"', 'stroke="#06130b"')
    no = CROSS.replace("#FF4F7B", "#2a0509")
    inner = col(70, "G", labels[0], GREEN, good, ok) + col(1290, "B", labels[1], RED, bad, no)
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, inner, 15, b.get("anchor", "-")))
    tg = float(b.get("good_at", good[0][1] - 0.3 if good else t_in)); tb = float(b.get("bad_at", bad[0][1] - 0.3 if bad else t_in))
    ctx.js("tl.fromTo('#%s-Gh', { opacity:0, x:-30 }, { opacity:1, x:0, duration:.35, ease:'power2.out' }, %.3f);" % (pid, tg))
    ctx.js("tl.fromTo('#%s-Bh', { opacity:0, x:30 }, { opacity:1, x:0, duration:.35, ease:'power2.out' }, %.3f);" % (pid, tb))
    for k, it in enumerate(good):
        ctx.js("tl.fromTo('#%s-G%d', { opacity:0, x:-30 }, { opacity:1, x:0, duration:.35, ease:'power2.out' }, %.3f);" % (pid, k, float(it[1])))
    for k, it in enumerate(bad):
        ctx.js("tl.fromTo('#%s-B%d', { opacity:0, x:30 }, { opacity:1, x:0, duration:.35, ease:'power2.out' }, %.3f);" % (pid, k, float(it[1])))
    ctx.js("tl.to('#%s .gb-head, #%s .gb-item', { opacity:0, duration:.3 }, %.3f);" % (pid, pid, t_out - 0.32))


def subs(b, ctx):
    """words: [[text, t], ...], or "auto": true to take every word of transcript.json (next to the storyboard) in [in, out]."""
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    words = b.get("words")
    if not words and b.get("auto"):
        tp = b.get("transcript") or os.path.join(os.path.dirname(os.path.abspath(ctx.OUT)), "transcript.json")
        tr = json.load(open(tp))
        tr = tr["words"] if isinstance(tr, dict) else tr
        words = [[w["text"], float(w["start"])] for w in tr if t_in <= float(w["start"]) < t_out - 0.1]
    if not words:
        raise SystemExit("%s: subs needs \"words\" or \"auto\": true with a transcript.json" % pid)
    per = int(b.get("per_line", 6))
    lines = [words[i:i + per] for i in range(0, len(words), per)]
    body = ""
    for li, ln in enumerate(lines):
        body += '<div class="sb-line" id="%s-l%d" style="visibility:hidden">%s</div>' % (pid, li, "".join(
            '<span class="w" id="%s-w%d-%d">%s</span>' % (pid, li, k, _esc(w[0])) for k, w in enumerate(ln)))
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, body, 16, "-"))
    for li, ln in enumerate(lines):
        a = float(ln[0][1]) - 0.02
        bb = float(lines[li + 1][0][1]) - 0.04 if li + 1 < len(lines) else t_out - 0.05
        ctx.js("tl.set('#%s-l%d', { visibility:'inherit' }, %.3f); tl.set('#%s-l%d', { visibility:'hidden' }, %.3f);" % (pid, li, a, pid, li, bb))
        for k, w in enumerate(ln):
            t = float(w[1])
            ctx.js("tl.fromTo('#%s-w%d-%d', { opacity:0, y:-40, color:'#4FC3FF' }, { opacity:1, y:0, duration:.22, ease:'back.out(2)' }, %.3f);" % (pid, li, k, t - 0.02))
            ctx.js("tl.to('#%s-w%d-%d', { color:'#ffffff', duration:.25 }, %.3f);" % (pid, li, k, t + 0.3))


def panels(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    P = b["panels"]; n = len(P)
    if not 2 <= n <= 4:
        raise SystemExit("%s: panels takes two to four panels" % pid)
    W = min(600, int((1848 - 24 * (n - 1)) / n)); x0 = int((1920 - (W * n + 24 * (n - 1))) / 2)
    xs = [x0 + i * (W + 24) for i in range(n)]
    pick = b.get("pick")
    html = ""
    for i, p in enumerate(P):
        logos = "".join('<img src="%s">' % l if not l.startswith("+") else '<span class="plus">+</span>' for l in p.get("logos", []))
        if p.get("wordmark"):
            logos += '<span class="wm">%s</span>' % _esc(p["wordmark"])
        st = ""
        if pick and int(pick["index"]) - 1 == i and pick.get("stamp"):
            st = '<div class="pn-stamp" id="%s-stamp"><div class="ok">%s</div>%s</div>' % (pid, CHECK, _esc(pick["stamp"]))
        media = '<div class="pn-img" id="%s-im%d" style="background-image:url(%s)"></div>' % (pid, i, p["media"]) if p.get("media") else ""
        html += ('<div class="pn-panel" id="%s-p%d" style="left:%dpx;width:%dpx" data-at="%.3f"%s><div class="pn-head"><div class="pn-no" id="%s-no%d">%s</div><div class="pn-logos">%s</div></div>'
                 '<div class="pn-scr">%s</div><div class="pn-name">%s</div>%s</div>'
                 % (pid, i, xs[i], W, float(p["at"]), ctx.attr_anchor(p.get("anchor", "-")), pid, i, _esc(p.get("no", "%02d" % (i + 1))), logos, media, _esc(p.get("name", "")), st))
    ttl = ""
    if b.get("title"):
        ttl = '<div class="pn-title" id="%s-title">%s</div>' % (pid, ctx.em_spans(_esc(b["title"]), b.get("title_em")))
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, '<div class="cut"><div class="gridbg"></div></div>%s%s' % (ttl, html), 20, b.get("anchor", "-")))
    J = ctx.js
    if b.get("title"):
        J("tl.fromTo('#%s-title', { opacity:0, y:20 }, { opacity:1, y:0, duration:.4, ease:'power2.out' }, %.3f);" % (pid, t_in + 0.03))
    for i, p in enumerate(P):
        ta = float(p["at"])
        J("tl.fromTo('#%s-p%d', { opacity:0, y:110, scale:.86 }, { opacity:1, y:0, scale:1, duration:.5, ease:'back.out(1.5)' }, %.3f);" % (pid, i, ta))
        if p.get("media"):      # a slow push keeps a still alive while it is on screen
            J("tl.fromTo('#%s-im%d', { scale:1.0 }, { scale:1.08, duration:%.3f, ease:'none' }, %.3f);" % (pid, i, max(0.5, t_out - ta), ta))
    if pick:
        k = int(pick["index"]) - 1; tp = float(pick["at"]); grow = float(b.get("grow", 1.3)); gy = int(b.get("gy", -56))
        if b.get("dim", True):
            others = ", ".join("#%s-p%d" % (pid, i) for i in range(n) if i != k)
            J("tl.to('%s', { opacity:.4, duration:.3 }, %.3f);" % (others, tp - 0.05))
        for i in range(n):
            if i != k:
                J("tl.to('#%s-p%d', { x:%d, opacity:0, duration:.55, ease:'power3.in' }, %.3f);" % (pid, i, -1300 if i < k else 1300, tp + 0.15))
        J("tl.to('#%s-p%d', { borderColor:'rgba(79,195,255,1)', boxShadow:'0 0 80px rgba(79,195,255,.5), 0 30px 90px rgba(0,0,0,.55)', duration:.35 }, %.3f);" % (pid, k, tp))
        J("tl.to('#%s-no%d', { color:'#4FC3FF', duration:.35 }, %.3f);" % (pid, k, tp))
        J("tl.to('#%s-p%d', { x:%d, y:%d, scale:%.3f, duration:.75, ease:'power3.inOut' }, %.3f);" % (pid, k, 960 - (xs[k] + W / 2), gy, grow, tp + 0.3))
        if b.get("title"):
            J("tl.to('#%s-title', { opacity:0, y:-20, duration:.35 }, %.3f);" % (pid, tp + 0.2))
        if pick.get("stamp"):
            J("tl.fromTo('#%s-stamp', { opacity:0, scale:.7 }, { opacity:1, scale:1, duration:.45, ease:'back.out(2)' }, %.3f);" % (pid, tp + 0.95))
    ctx.transition(b, t_in, t_out)


def pagetour(b, ctx):
    """src: a page screenshot (page px); start / cams: page rects [x, y, w, h] the camera frames; marks: gold strokes or boxes."""
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    pw, ph = b.get("size") or ctx.media_size(b["src"])
    VW, VH = 1620, 898

    def cam(r):
        x, y, w, h = r; s = min(VW / float(w), VH / float(h))
        return (-(x + w / 2.0) * s + VW / 2.0, -(y + h / 2.0) * s + VH / 2.0, s)
    mk = ""
    for k, m in enumerate(b.get("marks", [])):
        x, y, w, h = m["rect"]
        mk += '<div class="wp-%s" id="%s-m%d" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"></div>' % ("mk" if m.get("kind", "mark") == "mark" else "box", pid, k, x, y, w, h)
    inner = ('<div class="cut"><div class="gridbg"></div></div><div class="wp-win" id="%s-win" style="background:%s"><div class="wp-chrome" data-layout-ignore data-layout-allow-occlusion><span class="dt r"></span><span class="dt y"></span>'
             '<span class="dt g"></span><div class="wp-url">%s</div></div><div class="wp-page"><div class="wp-in" id="%s-in" data-layout-allow-overflow data-layout-allow-occlusion style="width:%dpx;height:%dpx;background-image:url(%s)">%s</div></div></div>%s'
             % (pid, "#0b0b0d" if b.get("dark") else "#fff", _esc(b.get("domain", "")), pid, pw, ph, b["src"], mk, ctx.scene_label(pid, b, t_out)))
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, inner, 20, b.get("anchor", "-")))
    x0, y0, s0 = cam(b.get("start", [0, 0, pw, min(ph, pw * VH / VW)]))
    ctx.js("tl.fromTo('#%s-win', { opacity:0, y:40, scale:.97 }, { opacity:1, y:0, scale:1, duration:.4, ease:'power2.out' }, %.3f);" % (pid, t_in))
    ctx.js("tl.set('#%s-in', { x:%.1f, y:%.1f, scale:%.4f }, %.3f);" % (pid, x0, y0, s0, t_in))
    for t, r in b.get("cams", []):
        x, y, s = cam(r)
        ctx.js("tl.to('#%s-in', { x:%.1f, y:%.1f, scale:%.4f, duration:.8, ease:'power2.inOut' }, %.3f);" % (pid, x, y, s, float(t)))
    for k, m in enumerate(b.get("marks", [])):
        if m.get("kind", "mark") == "mark":
            ctx.js("tl.to('#%s-m%d', { scaleX:1, duration:.35, ease:'power1.out' }, %.3f);" % (pid, k, float(m["at"])))
        else:
            ctx.js("tl.fromTo('#%s-m%d', { opacity:0, scale:1.12 }, { opacity:1, scale:1, duration:.35, ease:'back.out(2)' }, %.3f);" % (pid, k, float(m["at"])))
    ctx.transition(b, t_in, t_out)


def _file_lines(path, ranges, marks):
    src = open(path).read().split("\n")
    out, idx = [], {}
    for a, z in ranges:
        for n in range(int(a), int(z) + 1):
            if n > len(src):
                break
            raw = src[n - 1]
            cls = "h1" if raw.startswith("# ") else ("h2" if raw.startswith("## ") or raw.startswith("### ") else "")
            t = _h.escape(re.sub(r"^#+\s*", "", raw))
            t = re.sub(r"\*\*(.+?)\*\*", r"<b data-layout-allow-occlusion>\1</b>", t)
            t = re.sub(r"`([^`]+)`", r"<code data-layout-allow-occlusion>\1</code>", t)
            if n in marks:
                m = re.sub(r"\*\*(.+?)\*\*", r"<b data-layout-allow-occlusion>\1</b>", _h.escape(marks[n]))
                if m not in t:
                    raise SystemExit("fileread: line %d of %s does not contain %r" % (n, path, marks[n]))
                t = t.replace(m, '<span class="sk-m" data-layout-allow-occlusion>%s<i></i></span>' % m, 1)
                idx[n] = len(out)
            out.append((cls, t if t.strip() else "&nbsp;"))
        out.append(("", "&nbsp;"))
    return out, idx


def fileread(b, ctx):
    """file + ranges [[first, last], ...] (1-based file lines, markdown lightly rendered); marks: [{"at", "line", "text"}]
    (the line number in the file, the words to underline). zoom_out_at pulls back out to the whole page."""
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    path = b["file"] if os.path.isabs(b["file"]) else os.path.join(ctx.ROOT, b["file"])
    marks = sorted(b.get("marks", []), key=lambda m: float(m["at"]))
    lines, idx = _file_lines(path, b.get("ranges", [[1, 40]]), {int(m["line"]): m["text"] for m in marks})
    LH = {"h1": 64, "h2": 78, "": 40}
    ys, y = [], 40
    for cls, _ in lines:
        ys.append(y); y += LH.get(cls, 40)
    H = y + 80
    body = "".join('<div class="sk-ln %s" id="%s-ln%d" data-layout-allow-occlusion>%s</div>' % (cls, pid, i, txt) for i, (cls, txt) in enumerate(lines))
    tab = b.get("tab", os.path.relpath(path, ctx.ROOT) if path.startswith(ctx.ROOT) else os.path.basename(path))
    inner = ('<div class="cut"><div class="gridbg"></div></div><div class="sk-win" id="%s-win"><div class="sk-chrome" data-layout-ignore data-layout-allow-occlusion><span class="dt r"></span><span class="dt y"></span><span class="dt g"></span>'
             '<div class="sk-tab">%s</div></div><div class="sk-page"><div class="sk-in" id="%s-in" data-layout-allow-overflow data-layout-allow-occlusion>%s</div></div></div>%s'
             % (pid, _esc(tab), pid, body, ctx.scene_label(pid, b, t_out)))
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, inner, 20, b.get("anchor", "-")))
    VW, VH = 1700, 922
    s_out = max(VH / float(H), 0.42)
    J = ctx.js
    J("tl.fromTo('#%s-win', { opacity:0, y:40, scale:.97 }, { opacity:1, y:0, scale:1, duration:.4, ease:'power2.out' }, %.3f);" % (pid, t_in))
    J("tl.set('#%s-in', { x:%.1f, y:0, scale:%.4f }, %.3f);" % (pid, (VW - 1700 * s_out) / 2, s_out, t_in))
    if marks:
        drift = float(marks[0]["at"]) - 0.75 - (t_in + 0.4)        # ends exactly where the first move starts (one owner of y)
        if drift > 0.2:
            J("tl.to('#%s-in', { y:-6, duration:%.3f, ease:'none' }, %.3f);" % (pid, drift, t_in + 0.4))
    for k, m in enumerate(marks):
        li = idx[int(m["line"])]; t = float(m["at"]); s = float(b.get("zoom", 1.35)); yc = ys[li] + 20
        J("tl.to('#%s-in', { x:%.1f, y:%.1f, scale:%.3f, duration:%.2f, ease:'power3.inOut' }, %.3f);" % (pid, -40 * s + 60, -yc * s + VH * 0.45, s, 0.9 if k == 0 else 0.6, t - (0.75 if k == 0 else 0.45)))
        J("tl.to('#%s-ln%d .sk-m i', { scaleX:1, duration:.45, ease:'power1.out' }, %.3f);" % (pid, li, t + 0.05))
    if b.get("zoom_out_at"):
        J("tl.to('#%s-in', { x:%.1f, y:0, scale:%.4f, duration:.9, ease:'power3.inOut' }, %.3f);" % (pid, (VW - 1700 * s_out) / 2, s_out, float(b["zoom_out_at"])))
    ctx.transition(b, t_in, t_out)


def receipt(b, ctx):
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    body = '<div class="rc-title">%s</div>' % _esc(b.get("title", "WHAT I PAY"))
    for i, r in enumerate(b["rows"]):
        gold = r.get("gold", "$" in str(r["value"]))
        body += '<div class="rc-row" id="%s-r%d" data-at="%.3f"%s><div class="k">%s%s</div><div class="v%s">%s</div></div>' % (
            pid, i, float(r["at"]), ctx.attr_anchor(r.get("anchor", r["label"])), '<img src="%s">' % r["icon"] if r.get("icon") else "",
            _esc(r["label"]), " gold" if gold else "", _esc(r["value"]))
    tot = b.get("total")
    if tot:
        body += ('<div class="rc-rule" id="%s-rule"></div><div class="rc-tot" id="%s-tot"><div class="k">%s</div><div class="v">%s<small>%s</small></div></div>'
                 % (pid, pid, _esc(tot.get("label", "Total")), _esc(tot["value"]), _esc(tot.get("unit", ""))))
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, '<div class="cut"><div class="gridbg"></div></div><div class="rc-card" id="%s-card">%s</div>' % (pid, body), 20, b.get("anchor", "-")))
    ctx.js("tl.fromTo('#%s-card', { opacity:0, y:40 }, { opacity:1, y:0, duration:.45, ease:'power2.out' }, %.3f);" % (pid, t_in))
    for i, r in enumerate(b["rows"]):
        ctx.js("tl.fromTo('#%s-r%d', { opacity:0, y:22 }, { opacity:1, y:0, duration:.4, ease:'power2.out' }, %.3f);" % (pid, i, float(r["at"])))
    if tot:
        ta = float(tot["at"])
        ctx.js("tl.to('#%s-rule', { scaleX:1, duration:.5, ease:'power2.inOut' }, %.3f);" % (pid, float(tot.get("rule_at", ta - 0.5))))
        ctx.js("tl.fromTo('#%s-tot', { opacity:0, y:22 }, { opacity:1, y:0, duration:.45, ease:'power2.out' }, %.3f);" % (pid, ta))
    ctx.transition(b, t_in, t_out)


def scorecard(b, ctx):
    """cols: [{"logos": [...], "wordmark": "..", "name": "..", "at": t}] (2-4); rows: [{"label": "..", "cells": [..], "at": t}]
    (up to 6) where a cell is "yes", "no", or [kind, text] with kind txt | gold | good; focus: [[col, t], ...] rings the
    column you talk about and dims the rest; winner: {"col": i, "at": t, "stamp": "Winner"}. Columns count from 0."""
    pid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    cols, rows = b["cols"], b["rows"]
    n, R = len(cols), len(rows)
    if not 2 <= n <= 4 or not 1 <= R <= 6:
        raise SystemExit("%s: scorecard takes 2-4 columns and 1-6 rows" % pid)
    CW = int((1700 - 560) / n)
    top = 150 if b.get("title") else 80
    if b.get("title") and R > 5:
        top = 120
    head = '<div class="ct-head"><div class="ct-lab"></div>%s</div>' % "".join(
        '<div class="ct-col" id="%s-h%d" style="width:%dpx"><div class="pair">%s%s</div><div class="nm">%s</div></div>'
        % (pid, i, CW, "".join('<img src="%s">' % l for l in c.get("logos", [])), '<span class="wm">%s</span>' % _esc(c["wordmark"]) if c.get("wordmark") else "",
           _esc(c.get("name", ""))) for i, c in enumerate(cols))
    body = ""
    for r, row in enumerate(rows):
        if len(row["cells"]) != n:
            raise SystemExit("%s: row %r has %d cells for %d columns" % (pid, row["label"], len(row["cells"]), n))
        cs = ""
        for cell in row["cells"]:
            if cell == "yes":
                c = '<div class="ct-yes">%s</div>' % CHECK
            elif cell == "no":
                c = '<div class="ct-no">%s</div>' % CROSS
            else:
                kind, txt = cell
                c = '<div class="ct-txt %s">%s</div>' % ({"gold": "gold", "good": "good"}.get(kind, ""), _esc(txt))
            cs += '<div class="ct-col" style="width:%dpx">%s</div>' % (CW, c)
        body += '<div class="ct-row" id="%s-r%d" data-at="%.3f"%s><div class="ct-lab">%s</div>%s</div>' % (
            pid, r, float(row["at"]), ctx.attr_anchor(row.get("anchor", row["label"])), _esc(row["label"]), cs)
    RH = 170 + 142 * R + 26
    xs = [560 + CW * i for i in range(n)]
    over = "".join('<div class="ct-ring" id="%s-ring%d" style="left:%dpx;width:%dpx;height:%dpx"></div><div class="ct-dim" id="%s-dim%d" data-layout-allow-occlusion style="left:%dpx;width:%dpx;height:%dpx"></div>'
                   % (pid, i, x + 4, CW - 8, RH, pid, i, x, CW, RH) for i, x in enumerate(xs))
    w = b.get("winner")
    if w:
        wi = int(w["col"])
        over += '<div class="ct-stamp" id="%s-stamp" style="left:%dpx"><div class="ok">%s</div>%s</div>' % (pid, xs[wi] + CW // 2 - 110, CHECK.replace('width="40" height="40"', 'width="32" height="32"'), _esc(w.get("stamp", "Winner")))
    ttl = '<div class="ct-title" id="%s-title">%s</div>' % (pid, ctx.em_spans(_esc(b["title"]), b.get("title_em"))) if b.get("title") else ""
    inner = '<div class="cut"><div class="gridbg"></div></div>%s<div class="ct-wrap" style="top:%dpx">%s%s%s</div>' % (ttl, top, head, body, over)
    ctx.html(_hostdiv(ctx, pid, t_in, t_out, inner, 20, b.get("anchor", "-")))
    J = ctx.js
    if b.get("title"):
        J("tl.fromTo('#%s-title', { opacity:0, y:20 }, { opacity:1, y:0, duration:.4, ease:'power2.out' }, %.3f);" % (pid, t_in + 0.03))
    for i, c in enumerate(cols):
        J("tl.fromTo('#%s-h%d', { opacity:0, y:-20 }, { opacity:1, y:0, duration:.4, ease:'power2.out' }, %.3f);" % (pid, i, float(c.get("at", t_in + 0.2 + 0.12 * i))))
    for r, row in enumerate(rows):
        J("tl.fromTo('#%s-r%d', { opacity:0, x:-30 }, { opacity:1, x:0, duration:.4, ease:'power2.out' }, %.3f);" % (pid, r, float(row["at"])))
    prev = None
    focus = [[int(f[0]), float(f[1])] for f in b.get("focus", [])]
    if w:
        focus.append([wi, float(w["at"])])
    for ci, tc in sorted(focus, key=lambda f: f[1]):
        if prev is not None and prev != ci:
            J("tl.to('#%s-ring%d', { opacity:0, duration:.3 }, %.3f);" % (pid, prev, tc))
        J("tl.to('#%s-ring%d', { opacity:1, duration:.4, ease:'power2.out' }, %.3f);" % (pid, ci, tc))
        for j in range(n):
            J("tl.to('#%s-dim%d', { opacity:%s, duration:.4 }, %.3f);" % (pid, j, "0" if j == ci else "1", tc))
        prev = ci
    if w:
        J("tl.fromTo('#%s-stamp', { opacity:0, scale:.7 }, { opacity:1, scale:1, duration:.45, ease:'back.out(2)' }, %.3f);" % (pid, float(w["at"]) + 0.35))
    ctx.transition(b, t_in, t_out)


BUILDERS = {"bignum": bignum, "behind": behind, "sidelist": sidelist, "goodbad": goodbad, "subs": subs, "panels": panels,
            "pagetour": pagetour, "fileread": fileread, "receipt": receipt, "scorecard": scorecard}


def build(b, ctx):
    BUILDERS[b["type"]](b, ctx)
