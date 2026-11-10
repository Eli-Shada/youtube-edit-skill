# YouTube Edit Skill for Claude Code

This skill turns Claude Code into a YouTube editor: it cuts your raw footage, adds animated text, cutaways, B-roll,
camera moves and sound, and renders a finished 4K MP4 on your own computer with HyperFrames. It learns your taste as you
go, so every note you give makes the next edit closer to how you want it.

Free to download and use. The brand colours (sky blue `#4FC3FF`, gold `#FFC93D`, rose `#FF4F7B`) and the Manrope font
are one creator's style, left in as working examples. **Replace them with your own**: see "Make it yours" below.

---

## Setup

1. **Download the Claude desktop app** and sign in with a **paid Claude plan** (Pro or Max). Claude Code needs one.
2. **Open Claude Code**: the **Code** tab in the desktop app.
3. **Set it to Local**, so Claude works on your own computer and your footage never leaves it.
4. **Pick a folder** for your videos (for example `Documents/YouTube`). This is your project folder.
5. **Turn permissions to auto**, so Claude can run the editing tools without asking you at every step.
6. Download this repo (green **Code** button, then **Download ZIP**), unzip it, and put the `youtube-edit-skill`
   folder inside your project folder.
7. Send this message:

   > Set up this video editing skill for me. Install HyperFrames, FFmpeg and Parakeet, and walk me through anything you can't do yourself.

Claude installs the skill into `.claude/skills/youtube-edit/` in your project folder, installs the tools, runs the
skill's tests and tells you if anything needs you (an admin password, for example).

---

## Build a free sound library from Pixabay

No audio comes with this skill: Pixabay's licence doesn't allow sharing its files as they are. You build the same
library yourself in about 20 minutes, for free.

1. Open [SOUNDS.md](SOUNDS.md). It lists every sound the skill uses, what to search for, and when the skill plays it.
2. For each row, search [Pixabay sound effects](https://pixabay.com/sound-effects/) (or
   [Pixabay music](https://pixabay.com/music/) for the music bed) with the suggested words, and download one you like.
3. Drop the files into the chat and say:

   > Add these Pixabay sounds to my library. Name them like SOUNDS.md says.

Claude trims the silence before each sound, levels it and records its licence. Start with the core sounds (typing,
click, pop, cash, chime); the rest are optional. Remember the rule the skill follows: a sound only plays when something
on screen would really make it.

---

## Test it on a hook

Start small, with the first 1 to 3 minutes of a video.

1. Put a raw clip in a folder called `raw` inside your project folder.
2. Send: "Use my editing skill to edit this hook: raw/<your file>."
3. Claude shows you the cut first, then a storyboard sheet of every animation, then renders it.
4. Watch it and give **timestamped notes**, one per line:

   > 0:04 the text is too small
   > 0:12 no sound on this part
   > 0:31 cut the second "so", it's a stutter
   > 0:45 hold the card a second longer

5. Claude fixes them and renders again. When you're happy, send:

   > Save what you learned to the skill

Claude writes your notes into the skill as plain rules, so the next video starts from your taste instead of the
example one. Do this for two or three hooks and the edits start to feel like yours.

### Make it yours

Tell Claude your colours and font, for example: "Change the house style to my colours #22C55E, #F97316 and #EAB308 and
my font Inter." It updates the skill's style paragraph, the colour tokens in `scripts/compose.py` and the fonts.
Add your own logos and images to `videos/_shared/img/`.

---

## The overnight run

Once the skill knows your style, put a full raw video in your `raw` folder before bed and send:

> Use my editing skill to edit the new video in my raw folder. Render the final file without stopping for my approval.

Leave the computer on and plugged in (Claude may offer to keep it awake). In the morning the finished 4K file is waiting
for you, with a storyboard of what it did, ready for your notes.

---

## What's inside

| Path | What it is |
|---|---|
| `SKILL.md` | The skill itself: every editing rule, route and format Claude follows |
| `SOUNDS.md` | The sound list for building your Pixabay library |
| `scripts/` | The cut, compose, mix, assemble and check tools (Python and Node) |
| `formats/` | The animation formats, one plugin file each |
| `references/` | Format specs and the licence notes for every library and asset |
| `assets/` | Fonts (Manrope, SIL Open Font License), GSAP, Lottie and Lucide icons |

Licences for the bundled libraries and models are in `references/assets-and-licenses.md` and next to each file.

---

## Links

- [Claude desktop app](https://claude.ai/download)
- [HyperFrames on GitHub](https://github.com/heygen-com/hyperframes)
- [FFmpeg](https://ffmpeg.org/download.html)
- [Pixabay music](https://pixabay.com/music/) and [Pixabay sound effects](https://pixabay.com/sound-effects/)
- [Higgsfield](https://higgsfield.ai) for AI B-roll
- [Implicator: what Claude Code can do inside DaVinci Resolve](https://www.implicator.ai/claude-code-davinci-resolve-five-editing-tasks/)
- [Overseer: how much YouTube video editing costs](https://www.overseeros.com/blog/youtube-video-editing-cost)
