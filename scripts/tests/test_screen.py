"""formats/screen.py (43 screen + 23 tutorial layout) through compose.py's plugin hook, and screen-focus.py."""
import os, unittest
from .helpers import run, scratch, write, read, load, ffmpeg, needs_ffmpeg

SCREEN = {"type": "screen", "id": "sc", "src": "img/ui.png", "size": [1920, 1080], "chrome": "browser", "domain": "example.com",
          "moves": [{"at": 2.0, "focus": [1000, 200, 600, 340]}, {"at": 5.0, "focus": "all"}],
          "cursor": [[1.2, 900, 800], [3.5, 1300, 660]], "clicks": [[3.5, 1300, 660]],
          "highlight": [{"rect": [1050, 250, 490, 60], "at": 3.0, "out": 4.6}],
          "spotlight": [{"rect": [100, 100, 400, 300], "at": 4.0, "out": 4.8}],
          "in": 0.5, "out": 7.0, "anchor": "-"}


def board(*beats):
    return {"id": "t", "duration": 20.0, "beats": list(beats)}


class ScreenFormat(unittest.TestCase):
    def build(self, spec):
        d = scratch(self)
        sp = write(os.path.join(d, "storyboard.json"), spec)
        r = run("compose.py", "--spec", sp, "--out", os.path.join(d, "public"))
        page = read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""
        return r, page

    def test_builds_through_the_plugin_hook(self):
        r, page = self.build(board(SCREEN))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for needle in ('class="card-host clip sc-wash"', 'class="card-host clip sc-over"', 'id="sc-wrig"', 'id="sc-orig"',
                       'id="sc-cur"', 'id="sc-rp0"', 'id="sc-hl0"', 'id="sc-sp0"', 'class="sc-bar" data-layout-ignore',
                       'src="sfx/click.mp3"', ".sc-rig {"):
            self.assertIn(needle, page)
        self.assertIn('data-volume="0.28"', page)                       # every on-screen click: the light click
        self.assertIn("'#sc-wrig, #sc-orig'", page)                     # one tween moves both layers together
        self.assertIn("WARN sc: sfx/click.mp3", r.stdout)               # no --shared folder: the missing sound is named

    def test_zoom_is_capped_at_two(self):
        tiny = dict(SCREEN, moves=[{"at": 2.0, "focus": [1000, 600, 60, 30]}], cursor=[], clicks=[], highlight=[], spotlight=[])
        r, page = self.build(board(tiny))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("scale: 2.0000", page)
        self.assertNotIn("scale: 2.6", page)

    def test_css_only_when_used(self):
        r, page = self.build(board({"type": "chip", "id": "ch", "text": "hi", "in": 1.0, "out": 2.0, "anchor": "-"}))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn(".sc-rig", page)

    def test_moves_never_overlap(self):
        bad = dict(SCREEN, moves=[{"at": 2.0, "focus": [0, 0, 500, 300], "dur": 1.0}, {"at": 2.5, "focus": "all"}])
        r, _ = self.build(board(bad))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("one gesture at a time", r.stdout + r.stderr)

    def test_follow_needs_a_real_cursor_path(self):
        bad = dict(SCREEN, cursor=None, clicks=[], follow={"from": 1.0, "to": 6.0})
        bad.pop("cursor")
        r, _ = self.build(board(bad))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('"follow" needs a "cursor" path', r.stdout + r.stderr)

    def test_no_cursor_unless_given(self):
        nocur = dict(SCREEN); nocur.pop("cursor")
        r, page = self.build(board(nocur))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('id="sc-cur"', page)       # clicks alone draw ripples, never an invented cursor
        self.assertIn('id="sc-rp0"', page)

    def test_tutorial_layout_restores_the_footage(self):
        tut = dict(SCREEN, src="img/ui.png", face={"at": 1.0, "out": 6.5}); tut.pop("cursor"); tut["clicks"] = []
        r, page = self.build(board(tut))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('class="card-host clip sc-wash sc-face"', page)
        self.assertIn("zIndex: 15", page)
        self.assertIn("round 64px", page)                                # the 32 px card radius at scale 0.5
        self.assertIn("zIndex: 'auto', transformOrigin: '50% 0%', clipPath: 'none'", page)   # 3b bullets keep their origin

    def test_unknown_type_names_the_plugins(self):
        r, _ = self.build(board({"type": "nope", "id": "x", "in": 1.0, "out": 2.0}))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("screen", r.stdout + r.stderr)


@needs_ffmpeg
class ScreenFocus(unittest.TestCase):
    def test_finds_the_changed_region(self):
        d = scratch(self)
        v = os.path.join(d, "s.mp4")
        ffmpeg("-f", "lavfi", "-i", "color=c=0xf4f4f4:s=1920x1080:d=6:r=30", "-f", "lavfi", "-i", "color=c=0x1a73e8:s=300x40:d=6:r=30",
               "-filter_complex", "[0][1]overlay=x=1060:y=650:enable='between(t,2,3.5)'", "-t", "6", "-pix_fmt", "yuv420p", v)
        out = os.path.join(d, "focus.json")
        r = run("screen-focus.py", "--video", v, "--out", out)
        self.assertEqual(r.returncode, 0, r.stderr)
        st = load(out)["stretches"]
        self.assertEqual(len(st), 1)
        x, y, w, h = st[0]["focus"]
        self.assertTrue(x <= 1060 and y <= 650 and x + w >= 1360 and y + h >= 690, st[0])
        self.assertAlmostEqual(w / float(h), 16 / 9.0, places=1)
        self.assertLessEqual(st[0]["zoom"], 2.0)
        self.assertFalse(st[0]["whole_screen"])
