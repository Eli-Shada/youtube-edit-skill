"""formats/proven.py: the ten formats moved out of a real video's build. They build, and their guards hold."""
import os, unittest
from .helpers import run, scratch, write, read

MATTE = {"src": "broll/m.webm", "start": 20.0}
BEATS = [
    {"type": "scorecard", "id": "sc", "title": "Which one?", "title_em": [1],
     "cols": [{"logos": ["img/a.svg"], "name": "A"}, {"name": "B"}, {"name": "C", "wordmark": "+ X"}],
     "rows": [{"label": "Cuts", "cells": ["no", "yes", "yes"], "at": 1.0}, {"label": "Cost", "cells": [["gold", "$9"], ["txt", "Some"], ["good", "$0"]], "at": 1.5}],
     "focus": [[1, 2.0]], "winner": {"col": 2, "at": 3.0}, "in": 0.5, "out": 4.0, "anchor": "-"},
    {"type": "receipt", "id": "rc", "rows": [{"label": "Pro", "value": "$20", "at": 4.6}], "total": {"value": "$20", "unit": "/mo", "at": 5.4},
     "in": 4.2, "out": 6.0, "anchor": "-"},
    {"type": "panels", "id": "pn", "panels": [{"name": "One", "at": 6.4}, {"name": "Two", "at": 6.8}], "pick": {"index": 2, "at": 7.5, "stamp": "My pick"},
     "in": 6.2, "out": 9.0, "anchor": "-"},
    {"type": "pagetour", "id": "pt", "src": "img/p.png", "size": [1920, 1400], "domain": "example.com", "start": [0, 0, 1920, 1060],
     "cams": [[10.0, [600, 600, 640, 356]]], "marks": [{"at": 10.5, "rect": [700, 700, 100, 30]}, {"at": 11.0, "rect": [650, 650, 300, 90], "kind": "box"}],
     "in": 9.2, "out": 12.0, "anchor": "-"},
    {"type": "sidelist", "id": "sl", "head": "2 THINGS", "items": [["First", 12.6, "-"], ["Second", 13.0, "-"]], "focus": {"index": 1, "at": 13.6},
     "in": 12.2, "out": 14.6, "anchor": "-"},
    {"type": "goodbad", "id": "gb", "good": [["Long", 15.2, "-"]], "bad": [["Short", 15.8, "-"]], "in": 14.8, "out": 16.8, "anchor": "-"},
    {"type": "subs", "id": "sb", "words": [["hello", 17.2], ["there", 17.5]], "in": 17.0, "out": 18.4},
    {"type": "bignum", "id": "bn", "value": 2000, "prefix": "$", "count_at": 20.2, "crack_at": 22.0, "matte": MATTE, "in": 20.0, "out": 24.0, "anchor": "-"},
    {"type": "behind", "id": "bh", "lines": [[["$100", 25.0, "gold"]]], "kicker": "MAX", "kick_at": 24.8, "matte": dict(MATTE, start=24.5),
     "in": 24.5, "out": 27.0, "anchor": "-"},
]


def board(*beats, **kw):
    d = {"id": "t", "duration": 30.0, "beats": list(beats)}
    d.update(kw)
    return d


class ProvenFormats(unittest.TestCase):
    def build(self, spec, files=()):
        d = scratch(self)
        for rel, text in files:
            write(os.path.join(d, rel), text)
        sp = write(os.path.join(d, "storyboard.json"), spec)
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        page = read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""
        return r, page, d

    def test_all_build(self):
        r, page, _ = self.build(board(*BEATS))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for needle in ('id="sc-ring2"', 'id="sc-stamp"', 'id="rc-tot"', 'id="pn-stamp"', 'id="pt-m1" style', 'class="wp-box"',
                       'id="sl-n1"', 'id="gb-Gh"', 'id="sb-l0"', 'class="bn-half l"', 'id="bn-matte"', 'id="bh-matte"', ".ct-ring {"):
            self.assertIn(needle, page)
        self.assertIn('data-at="1.000" data-anchor="Cuts"', page)          # a scorecard row is anchored to its label by default
        self.assertIn("WARN bn: broll/m.webm is not in public/", r.stdout)   # a missing matte is named

    def test_scorecard_guards(self):
        bad = dict(BEATS[0], rows=[{"label": "X", "cells": ["yes"], "at": 1.0}])
        r, _, _ = self.build(board(bad))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("has 1 cells for 3 columns", r.stdout + r.stderr)
        r, _, _ = self.build(board(dict(BEATS[0], cols=BEATS[0]["cols"][:1])))
        self.assertNotEqual(r.returncode, 0)

    def test_matte_is_required_and_camera_warns(self):
        nomatte = dict(BEATS[7]); nomatte.pop("matte")
        r, _, _ = self.build(board(nomatte))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("needs a subject matte", r.stdout + r.stderr)
        r, _, _ = self.build(board(BEATS[7], camera=[["punch", 21.0, 1.18]]))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("keep the camera at 1.0", r.stdout)

    def test_subs_from_transcript(self):
        tr = '[{"text": "one", "start": 1.0, "end": 1.2}, {"text": "two", "start": 1.4, "end": 1.6}, {"text": "late", "start": 9.0, "end": 9.3}]'
        r, page, _ = self.build(board({"type": "subs", "id": "sb", "auto": True, "in": 0.5, "out": 3.0}), files=[("transcript.json", tr)])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(">one<", page); self.assertIn(">two<", page); self.assertNotIn(">late<", page)

    def test_fileread_checks_the_mark_text(self):
        d = scratch(self)
        f = write(os.path.join(d, "notes.md"), "# Title\n\nThe **first** rule.\nSecond line with `code`.\n")
        good = {"type": "fileread", "id": "fr", "file": f, "ranges": [[1, 4]], "marks": [{"at": 2.0, "line": 3, "text": "**first** rule"}], "in": 0.5, "out": 4.0}
        r, page, _ = self.build(board(good))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('<span class="sk-m" data-layout-allow-occlusion><b data-layout-allow-occlusion>first</b> rule<i></i></span>', page)
        r, _, _ = self.build(board(dict(good, marks=[{"at": 2.0, "line": 3, "text": "not there"}])))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not contain", r.stdout + r.stderr)


class LucideIcons(unittest.TestCase):
    def test_lucide_name_works_anywhere_an_icon_does(self):
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 5.0, "beats": [
            {"type": "pills", "id": "pl", "layout": "row", "in": 0.3, "out": 4.0, "anchor": "-",
             "items": [{"text": "Bot", "at": 0.5, "icon": "bot"}, {"text": "House", "at": 0.8, "icon": "robot"}]}]})
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stderr)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertIn('<g transform="scale(2.6667)"><path class="ic" style="stroke-width:1.7" d="M12 8V4H8"', page)   # Lucide bot, on the house grid
        self.assertIn('<path class="ic" d="M16 22h32v26H16z', page)                                       # the house robot is unchanged

    def test_unknown_icon_points_to_the_search(self):
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 5.0, "beats": [
            {"type": "pills", "id": "pl", "in": 0.3, "out": 4.0, "anchor": "-", "items": [{"text": "X", "at": 0.5, "icon": "no-such-icon-xyz"}]}]})
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("icon-search.py", r.stdout + r.stderr)

    def test_search_ranks_by_meaning(self):
        r = run("icon-search.py", "robot", "--limit", "3")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.splitlines()[0].startswith("robot"), r.stdout)   # the house icon first
        self.assertIn("bot", r.stdout)


class Signature(unittest.TestCase):
    def build(self, *beats):
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 20.0, "beats": list(beats)})
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        return r, (read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else "")

    def test_timeline_and_prompt_build(self):
        r, page = self.build(
            {"type": "timeline", "id": "rl", "title": "Releases", "events": [{"date": "A", "title": "One", "at": 1.0}, {"date": "B", "title": "Two", "at": 2.5}],
             "now": {"at": 4.0}, "in": 0.5, "out": 6.0, "anchor": "-"},
            {"type": "promptresult", "id": "pr", "prompt": 'a "quoted" prompt', "type_at": 7.0, "type_end": 8.0, "result": {"lines": ["one", "two"], "at": 9.5},
             "in": 6.5, "out": 12.0, "anchor": "-"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('data-at="2.500" data-anchor="Two"', page)
        self.assertIn("x: -520, duration: 0.9", page)                 # the camera travels one gap to the second release
        self.assertNotIn("{ className", page)                        # no GSAP class toggles (not seek-safe)
        self.assertIn('data-full="a &quot;quoted&quot; prompt"', page)
        self.assertIn("full.slice(0, Math.floor(o.n))", page)        # typing from one proxy

    def test_guards(self):
        r, _ = self.build({"type": "timeline", "id": "rl", "events": [{"title": "One", "at": 1.0}], "in": 0.5, "out": 3.0})
        self.assertNotEqual(r.returncode, 0); self.assertIn("2 to 8 events", r.stdout + r.stderr)
        r, _ = self.build({"type": "promptresult", "id": "pr", "prompt": "x", "result": {"lines": []}, "in": 0.5, "out": 3.0})
        self.assertNotEqual(r.returncode, 0); self.assertIn("real output image", r.stdout + r.stderr)


class Overlays(unittest.TestCase):
    def test_all_build(self):
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), {"id": "t", "duration": 14.0, "beats": [
            {"type": "grain", "id": "gr", "in": 0.0, "out": 3.0},
            {"type": "lightleak", "id": "lk", "in": 0.2, "out": 3.0},
            {"type": "captionbg", "id": "cb", "in": 3.2, "out": 6.0},
            {"type": "lowerthird", "id": "lt", "name": "A Name", "role": "Role", "in": 6.2, "out": 9.0, "anchor": "-"},
            {"type": "outline", "id": "ol", "rect": [100, 100, 300, 200], "label": "this", "at": 9.6, "in": 9.4, "out": 12.0, "anchor": "-"}]})
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        page = read(os.path.join(d, "public", "index.html"))
        self.assertTrue(os.path.exists(os.path.join(d, "public", "img", "grain-256.png")))
        self.assertIn('style="z-index:40;left:0;top:0;', page)                   # grain above every card
        self.assertIn("card-host clip ov-under", page)                           # the caption gradient sits under the line
        self.assertIn("backgroundColor: 'rgba(255,255,255,0.18)'", page)         # lower third glass tinted, never faded through opacity
        self.assertIn('id="ol-r"', page); self.assertIn('id="ol-l"', page)
