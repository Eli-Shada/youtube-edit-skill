"""Signature formats for an AI-tools channel (with 50 scorecard in proven.py). Use one or two per video, varied.

  55 timeline       new releases on a dated line: the camera travels to each release as you name it, the current one
                    bright, the past ones dimmed, an optional "now" marker pulsing at the end.
     {"type": "timeline", "id": "tl1", "title": "Six weeks of releases", "title_em": [3],
      "events": [{"date": "Sep 30", "title": "Sora 2", "sub": "video + sound", "logo": "img/openai.svg", "at": t}, ...] (2-8),
      "now": {"label": "Today", "at": t}, "in": t, "out": t}
  56 promptresult   a prompt types in a dark bar (one proxy, seek-safe), sends, a short shimmer, then the REAL result
                    appears in a window: your output image or screenshot ("src"), or two to five lines of text.
     {"type": "promptresult", "id": "pr", "app": "Midjourney", "logo": "img/mj.svg", "prompt": "..",
      "type_at": t, "type_end": t, "send_at": t, "result": {"src": "img/out.png", "at": t} | {"lines": [".."], "at": t},
      "caption": "..", "in": t, "out": t}
     The result is always real output you made; never an invented result (SKILL.md: proof is your real screen).
"""
import json

TYPES = ["timeline", "promptresult"]

CSS = """
  /* 55. release timeline */
  .rl-title { position:absolute; left:0; right:0; top:78px; text-align:center; font-weight:700; font-size:66px; letter-spacing:-.015em; color:#fff; opacity:0; }
  .rl-title .em { color:var(--cyan); }
  .rl-track { position:absolute; left:0; top:0; height:1080px; will-change:transform; }
  .rl-line { position:absolute; top:560px; height:4px; border-radius:2px; background:rgba(255,255,255,.22); }
  .rl-lit { position:absolute; top:560px; height:4px; border-radius:2px; background:var(--cyan); box-shadow:0 0 18px rgba(79,195,255,.6); transform-origin:0 50%; transform:scaleX(0); }
  .rl-ev { position:absolute; top:0; width:440px; margin-left:-220px; height:1080px; opacity:0; }
  .rl-dot { position:absolute; left:50%; top:562px; width:34px; height:34px; margin:-17px 0 0 -17px; border-radius:50%; background:#0b1120;
    border:5px solid rgba(255,255,255,.6); }
  .rl-date { position:absolute; left:0; right:0; top:440px; text-align:center; font-weight:700; font-size:40px; letter-spacing:.06em; color:rgba(255,255,255,.75); }
  .rl-card { position:absolute; left:20px; right:20px; top:622px; padding:28px 26px 30px; border-radius:26px; text-align:center;
    background:rgba(255,255,255,.12); border:3px solid rgba(255,255,255,.4); box-shadow:0 24px 80px rgba(0,0,0,.38); }
  .rl-logo { height:64px; width:auto; max-width:200px; display:block; margin:0 auto 18px; }
  .rl-name { font-weight:700; font-size:54px; line-height:1.05; letter-spacing:-.015em; color:#fff; }
  .rl-sub { margin-top:10px; font-weight:500; font-size:32px; color:rgba(255,255,255,.8); }
  .rl-now { position:absolute; top:562px; width:0; height:0; opacity:0; }
  .rl-now i { position:absolute; left:-30px; top:-30px; width:60px; height:60px; border-radius:50%; border:4px solid var(--amber); }
  .rl-now b { position:absolute; left:-12px; top:-12px; width:24px; height:24px; border-radius:50%; background:var(--amber); }
  .rl-now span { position:absolute; left:-100px; width:200px; top:-118px; text-align:center; font-weight:700; font-size:40px; color:var(--amber); letter-spacing:.06em; }
  /* 56. prompt -> result */
  .pr-app { position:absolute; left:0; right:0; top:84px; display:flex; justify-content:center; align-items:center; gap:18px; font-weight:700; font-size:44px; color:#fff; opacity:0; }
  .pr-app img { height:56px; width:auto; }
  .pr-bar { position:absolute; left:260px; right:260px; top:200px; min-height:120px; padding:30px 150px 30px 44px; border-radius:30px; background:rgba(16,18,26,.92);
    border:3px solid rgba(255,255,255,.22); box-shadow:0 30px 90px rgba(0,0,0,.5); font-weight:500; font-size:42px; line-height:1.3; color:#fff; opacity:0; }
  .pr-bar .caret { display:inline-block; width:4px; height:46px; margin-left:4px; vertical-align:-8px; background:var(--cyan); }
  .pr-send { position:absolute; right:30px; bottom:26px; width:72px; height:72px; border-radius:50%; background:var(--cyan); display:flex; align-items:center; justify-content:center; }
  .pr-win { position:absolute; left:360px; right:360px; top:390px; bottom:90px; border-radius:26px; overflow:hidden; background:#0b0d13;
    border:3px solid rgba(255,255,255,.22); box-shadow:0 40px 120px rgba(0,0,0,.6); opacity:0; }
  .pr-shim { position:absolute; inset:0; background:linear-gradient(100deg, rgba(255,255,255,0) 30%, rgba(255,255,255,.14) 50%, rgba(255,255,255,0) 70%);
    background-size:200% 100%; opacity:0; }
  .pr-img { position:absolute; inset:0; background-size:contain; background-repeat:no-repeat; background-position:center; clip-path:inset(100% 0 0 0); }
  .pr-lines { position:absolute; left:56px; right:56px; top:50px; }
  .pr-line { margin-bottom:26px; font-weight:500; font-size:40px; line-height:1.3; color:#e9edf3; opacity:0; }
  .pr-cap { position:absolute; left:0; right:0; bottom:22px; text-align:center; font-weight:700; font-size:40px; color:#fff; opacity:0; text-shadow:0 3px 12px rgba(0,0,0,.7); }
"""

SEND = '<svg width="34" height="34" viewBox="0 0 24 24"><path d="M12 19V5 M5 12l7-7 7 7" fill="none" stroke="#06131c" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def timeline(b, ctx):
    bid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    ev = b["events"]
    if not 2 <= len(ev) <= 8:
        raise SystemExit("%s: timeline takes 2 to 8 events" % bid)
    GAP = 520; x0 = 960
    xs = [x0 + i * GAP for i in range(len(ev))]
    end = xs[-1] + (GAP if b.get("now") else 0)
    html = '<div class="rl-line" style="left:%dpx;width:%dpx"></div><div class="rl-lit" id="%s-lit" style="left:%dpx;width:%dpx"></div>' % (x0 - 400, end - x0 + 800, bid, x0, end - x0)
    for i, e in enumerate(ev):
        logo = '<img class="rl-logo" src="%s">' % e["logo"] if e.get("logo") else ""
        sub = '<div class="rl-sub">%s</div>' % ctx.hesc(e["sub"]) if e.get("sub") else ""
        html += ('<div class="rl-ev" id="%s-e%d" style="left:%dpx" data-at="%.3f"%s><div class="rl-date">%s</div><div class="rl-dot"></div>'
                 '<div class="rl-card">%s<div class="rl-name">%s</div>%s</div></div>'
                 % (bid, i, xs[i], float(e["at"]), ctx.attr_anchor(e.get("anchor", e["title"])), ctx.hesc(e.get("date", "")), logo, ctx.hesc(e["title"]), sub))
    if b.get("now"):
        html += '<div class="rl-now" id="%s-now" style="left:%dpx"><i id="%s-nowr"></i><b></b><span>%s</span></div>' % (bid, end, bid, ctx.hesc(b["now"].get("label", "Today")))
    ttl = '<div class="rl-title" id="%s-title">%s</div>' % (bid, ctx.em_spans(ctx.hesc(b["title"]), b.get("title_em"))) if b.get("title") else ""
    inner = '<div class="cut"><div class="gridbg"></div></div>%s<div class="rl-track" id="%s-tr" style="width:%dpx" data-layout-allow-overflow>%s</div>%s' % (
        ttl, bid, end + 1400, html, ctx.scene_label(bid, b, t_out))
    ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, b.get("anchor", "")))
    J = ctx.js
    if b.get("title"):
        J("tl.fromTo('#%s-title', { opacity:0, y:20 }, { opacity:1, y:0, duration:.4, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, t_in + 0.05))
    J("tl.set('#%s-tr', { x: 0 }, %.3f);" % (bid, t_in))
    span = float(end - x0) or 1.0
    prev = None
    for i, e in enumerate(ev):
        t = float(e["at"])
        if i > 0:      # the camera travels to the release you name: one gesture, landing as its card arrives
            J("tl.to('#%s-tr', { x: %d, duration: 0.9, ease: 'power2.inOut' }, %.3f);" % (bid, -(xs[i] - x0), t - 0.55))
            J("tl.to('#%s-lit', { scaleX: %.4f, duration: 0.9, ease: 'power2.inOut' }, %.3f);" % (bid, (xs[i] - x0) / span, t - 0.55))
        J("tl.fromTo('#%s-e%d', { opacity:0, y:30 }, { opacity:1, y:0, duration:.45, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, i, t - 0.1))
        # the current release lights (explicit tweens, never a class toggle: seek-safe)
        J("tl.to('#%s-e%d .rl-dot', { borderColor: '#4FC3FF', backgroundColor: '#4FC3FF', boxShadow: '0 0 26px rgba(79,195,255,.7)', duration: .3 }, %.3f);" % (bid, i, t))
        J("tl.to('#%s-e%d .rl-card', { borderColor: 'rgba(79,195,255,1)', duration: .3 }, %.3f);" % (bid, i, t))
        if prev is not None:
            J("tl.to('#%s-e%d .rl-dot', { borderColor: 'rgba(255,255,255,0.6)', backgroundColor: '#0b1120', boxShadow: '0 0 0px rgba(79,195,255,0)', duration: .3 }, %.3f);" % (bid, prev, t))
            J("tl.to('#%s-e%d .rl-card', { borderColor: 'rgba(255,255,255,0.4)', duration: .3 }, %.3f);" % (bid, prev, t))
            J("tl.to('#%s-e%d', { opacity: .56, duration: .4 }, %.3f);" % (bid, prev, t))
        prev = i
    if b.get("now"):
        tn = float(b["now"]["at"])
        J("tl.to('#%s-tr', { x: %d, duration: 0.9, ease: 'power2.inOut' }, %.3f);" % (bid, -(end - x0) + 260, tn - 0.55))
        J("tl.to('#%s-lit', { scaleX: 1, duration: 0.9, ease: 'power2.inOut' }, %.3f);" % (bid, tn - 0.55))
        J("tl.fromTo('#%s-now', { opacity:0 }, { opacity:1, duration:.3, immediateRender:false }, %.3f);" % (bid, tn))
        J("tl.fromTo('#%s-nowr', { scale:.6, opacity:1 }, { scale:1.6, opacity:0, duration:1.2, ease:'power1.out', repeat:%d, immediateRender:false }, %.3f);"
          % (bid, max(0, int((t_out - tn - 1.2) / 1.2)), tn))
    ctx.transition(b, t_in, t_out)


def promptresult(b, ctx):
    bid, t_in, t_out = b["id"], float(b["in"]), float(b["out"])
    prompt = b["prompt"]; t0 = float(b.get("type_at", t_in + 0.5)); t1 = float(b.get("type_end", t0 + max(1.2, len(prompt) / 18.0)))
    ts = float(b.get("send_at", t1 + 0.3)); res = b["result"]; tr = float(res.get("at", ts + 1.2))
    app = ""
    if b.get("app") or b.get("logo"):
        app = '<div class="pr-app" id="%s-app">%s%s</div>' % (bid, '<img src="%s">' % b["logo"] if b.get("logo") else "", ctx.hesc(b.get("app", "")))
    if res.get("src"):
        body = '<div class="pr-img" id="%s-img" style="background-image:url(%s)"></div>' % (bid, res["src"])
    else:
        lines = res.get("lines") or []
        if not 1 <= len(lines) <= 5:
            raise SystemExit("%s: a text result takes 1 to 5 lines (or give the real output image as result.src)" % bid)
        body = '<div class="pr-lines">%s</div>' % "".join('<div class="pr-line" id="%s-l%d">%s</div>' % (bid, i, ctx.hesc(l)) for i, l in enumerate(lines))
    cap = '<div class="pr-cap" id="%s-cap">%s</div>' % (bid, ctx.hesc(b["caption"])) if b.get("caption") else ""
    inner = ('<div class="cut"><div class="gridbg"></div></div>%s<div class="pr-bar" id="%s-bar"><span id="%s-tx" data-full="%s"></span><span class="caret" id="%s-caret"></span>'
             '<div class="pr-send" id="%s-send">%s</div></div><div class="pr-win" id="%s-win"><div class="pr-shim" id="%s-shim"></div>%s</div>%s'
             % (app, bid, bid, ctx.hesc(prompt).replace('"', "&quot;"), bid, bid, SEND, bid, bid, body, cap))
    ctx.html(ctx.host(bid, t_in, t_out, ctx.track, inner, b.get("anchor", "")))
    J = ctx.js
    if app:
        J("tl.fromTo('#%s-app', { opacity:0, y:16 }, { opacity:1, y:0, duration:.4, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, t_in + 0.05))
    J("tl.fromTo('#%s-bar', { opacity:0, y:30 }, { opacity:1, y:0, duration:.45, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, t_in + 0.1))
    # typing: ONE proxy tween writes the visible slice (a tl.set per letter leaves letters behind on a backward seek)
    J("(function(){ var el = document.getElementById('%s-tx'), full = el.getAttribute('data-full'), o = { n: 0 };"
      " var put = function(){ el.textContent = full.slice(0, Math.floor(o.n)); }; put();"
      " tl.fromTo(o, { n: 0 }, { n: full.length, duration: %.3f, ease: 'none', immediateRender: false, onUpdate: put }, %.3f); })();" % (bid, t1 - t0, t0))
    J("tl.fromTo('#%s-send', { scale:1 }, { scale:.86, duration:.08, ease:'power2.in', yoyo:true, repeat:1, immediateRender:false }, %.3f);" % (bid, ts))
    J("tl.to('#%s-caret', { opacity:0, duration:.1 }, %.3f);" % (bid, ts))
    J("tl.fromTo('#%s-win', { opacity:0, y:40 }, { opacity:1, y:0, duration:.5, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, ts + 0.15))
    J("tl.fromTo('#%s-shim', { opacity:1, backgroundPosition:'100%% 0' }, { backgroundPosition:'-100%% 0', duration:%.3f, ease:'none', immediateRender:false }, %.3f);" % (bid, max(0.4, tr - ts - 0.2), ts + 0.2))
    J("tl.to('#%s-shim', { opacity:0, duration:.25 }, %.3f);" % (bid, tr))
    if res.get("src"):
        J("tl.fromTo('#%s-img', { clipPath:'inset(100%% 0%% 0%% 0%%)' }, { clipPath:'inset(0%% 0%% 0%% 0%%)', duration:.9, ease:'power3.inOut', immediateRender:false }, %.3f);" % (bid, tr))
        J("tl.fromTo('#%s-img', { scale:1.0 }, { scale:1.04, duration:%.3f, ease:'none', immediateRender:false }, %.3f);" % (bid, max(0.5, t_out - tr), tr))
    else:
        for i in range(len(res["lines"])):
            J("tl.fromTo('#%s-l%d', { opacity:0, y:14 }, { opacity:1, y:0, duration:.35, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, i, tr + 0.28 * i))
    if b.get("caption"):
        J("tl.fromTo('#%s-cap', { opacity:0, y:16 }, { opacity:1, y:0, duration:.4, ease:'power2.out', immediateRender:false }, %.3f);" % (bid, float(b.get("caption_at", tr + 0.9))))
    ctx.transition(b, t_in, t_out)


def build(b, ctx):
    {"timeline": timeline, "promptresult": promptresult}[b["type"]](b, ctx)
