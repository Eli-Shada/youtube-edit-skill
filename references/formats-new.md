# New formats (43-61): full specs

The composer builds every one of these from `storyboard.json` through the plugin hook (`formats/*.py`). Each
section below is that module's own docstring, so it stays in step with the code. SKILL.md has the one-line row and
when to pick it; read the spec here before writing the beat.

## formats/screen.py (screen)

```
screen (format 43) and the tutorial layout (format 23): a REAL screen recording or screenshot, framed on the brand
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
```

## formats/proven.py (bignum, behind, sidelist, goodbad, subs, panels, pagetour, fileread, receipt, scorecard)

```
Formats proven on a real delivery, moved out of that video's own build scripts so every
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
```

## formats/signature.py (timeline, promptresult)

```
Signature formats for an AI-tools channel (with 50 scorecard in proven.py). Use one or two per video, varied.

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
```

## formats/lottie.py (lottie)

```
54 lottie: a Lottie animation (After Effects export, a licensed LottieFiles file, or one made here) played frame by
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
```

## formats/overlays.py (grain, lightleak, captionbg, lowerthird, outline)

```
Overlays: quiet finishing layers, each for a reason. None of them is a look to leave on by default.

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
```

Regenerate: `cd .claude/skills/youtube-edit && python3 references/build-formats-md.py`
