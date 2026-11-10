# Sounds

No audio files ship with this skill. Pixabay's licence lets you use its sounds in your videos, but not share the files
as they are, so you download your own copies (free, no attribution needed) and the skill uses them from there.
This file lists every sound the skill uses, what to search for on Pixabay to find something similar, and when the
skill plays it.

## Where the files go

Inside your project folder (the one you opened in Claude Code):

```
videos/_shared/sfx/     sound effects
videos/_shared/music/   the music bed
```

Add each file with the skill's script so it gets trimmed, levelled and recorded with its licence. Use the **name** and
**category** from the tables, because the skill looks sounds up by name:

```bash
python3 .claude/skills/youtube-edit/scripts/sfx.py add ~/Downloads/<file>.mp3 --name click --category ui \
  --source "Pixabay: <page url>" --license pixabay
```

Or just tell Claude: "Add this Pixabay sound to my library as `click`" and drop the file in.

Shortcut: the free HyperFrames media-use library already includes many of these (typing, key-press, click, click-soft,
pop, ping, notification, chime, sparkle, error, whooshes, riser, impacts). After installing HyperFrames, run
`python3 .claude/skills/youtube-edit/scripts/sfx.py library` to see them and `sfx.py stage <name>` to add them.

Pixabay sound effects: https://pixabay.com/sound-effects/ · Pixabay music: https://pixabay.com/music/

## The rule behind every sound

Silence is the default. A sound plays only when something on screen would really make that noise: a cursor clicks, a
keyboard types, a logo pops in. One or two sounds in a hook is plenty. Never a whoosh on text.

## Core sounds (the skill places these on its own)

| Name | Category | Search Pixabay for | When the skill uses it | Volume |
|---|---|---|---|---|
| `typing` | `typing` | "keyboard typing short" | real typing on screen (a prompt window, a search box), for exactly the typing time | 0.22 |
| `key-press` | `typing` | "single key press" | one key: a shortcut, pressing Enter to send | low |
| `click` | `ui` | "mouse click" | every visible cursor click | 0.28 |
| `click-soft` | `ui` | "soft UI click" or "tap" | a light UI tap: a toggle, a menu item | low |
| `pop` | `pop` | "pop" or "bubble pop short" | a tool logo appearing on screen (logo card, logo swap) | 0.34 |
| `cash` | `money` | "cash register" or "ka-ching" | a money number landing, kept to a whisper | 0.07 |
| `chime` | `accent` | "success chime" | a success that is shown, like a stamp or a check landing | low |
| `chime-short` | `accent` | the same chime, cut to about 1.5 s | the same, when the full chime is too long | low |
| `ping` | `notification` | "phone notification ping" | a phone or app notification that is literally on screen | to taste |
| `notification` | `notification` | "notification sound" | a notification banner on screen | to taste |

## Music

| Name | Category | Search Pixabay Music for | When the skill uses it |
|---|---|---|---|
| `lofi-bed` (in `music/`) | `music` | "lofi background", calm, about 3 min, no vocals | the bed under the talking body of the video, ducked 16 to 19 dB under your voice by `scripts/mix.py`, starting where its beat comes in |

Pixabay music can still get a Content ID claim from its artist on YouTube. If that happens, dispute it with the
Pixabay licence page: https://pixabay.com/service/license-summary/

## Extra sounds (only proposed, never placed on their own)

The skill keeps these in the library but only suggests them at the storyboard check, with the moment it wants them.
You decide.

| Name | Category | Search Pixabay for | When the skill suggests it |
|---|---|---|---|
| `sparkle` | `accent` | "magic sparkle" | an AI result appearing on screen |
| `error` | `accent` | "error sound" or "wrong answer" | a visible error state or a wrong answer |
| `riser` | `riser` | "riser" or "tension build" (about 8 s) | the build into a reveal, ending on the reveal frame |
| `impact-bass-1` | `impact` | "bass impact" or "boom" | a big number or reveal that earns weight (rare) |
| `impact-bass-2` | `impact` | "bass impact long tail" | the same, with a longer tail |
| `whoosh-short` | `whoosh` | "whoosh short" | a full-frame scene sweeping in or out, at most once a minute |
| `whoosh` | `whoosh` | "whoosh" | a large object flying through the frame |
| `whoosh-cinematic` | `whoosh` | "cinematic whoosh" | a chapter-sized transition in a trailer-style hook |

## Optional: Sonniss and Epidemic Sound

The skill can also use effects and ambient "mood beds" from the free Sonniss GDC bundle (sonniss.com). Mark any sound
you only want now and then as on request in the manifest, and the skill uses it only when you ask for it by name. Sonniss files can't be shared either;
download the bundle yourself and add picks with `--license sonniss-gdc`.

If you have Epidemic Sound, connect it in Claude and the skill can search and download from it (`--license epidemic`).
