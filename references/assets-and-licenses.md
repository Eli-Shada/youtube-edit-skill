# Assets, libraries and licences

Where everything lives, what it may be used for, and how to add more without breaking the licence trail.
Third-party media stays in `videos/_shared/` (never in the skill, never committed to git, never redistributed as a pack).

## Libraries the skill ships (code, in `assets/vendor/`)

| Library | Version | Licence | Used by | Update |
|---|---|---|---|---|
| GSAP | 3.14.2 | GreenSock standard no-charge licence | every format | `curl` the CDN build into `assets/vendor/gsap.min.js` |
| lottie-web light player | 5.13.0 | MIT (`vendor/lottie/LICENSE.md`) | lottie | `npm install -D lottie-web@<v>`, copy `build/player/lottie_light.min.js` |
| Lucide icon data | 1.70.0 | ISC (`vendor/lucide/LICENSE`) | every `"icon"` key | `npm install -D lucide-static@<v>`, copy `icon-nodes.json`, `tags.json`, `LICENSE` |
| Manrope | - | SIL OFL (`assets/fonts/Manrope-OFL.txt`) | all type | - |

The project's `package.json` pins the HyperFrames CLI (0.9.22) and holds these packages for updates.

## Media in `videos/_shared/`

| Folder | What | Licence trail |
|---|---|---|
| `sfx/` + `music/` | sounds and beds | `sfx/manifest.json` (scripts/sfx.py): source, licence, licence URL, attribution, use, never |
| `lottie/` | Lottie files | `lottie/LICENSES.md`: one row per file (the `yt-*.json` ones are original to this skill) |
| `img/` | logos, page captures, stills | logos from the brands' press kits or sites; captures are your own screenshots of public pages |

## Licences in short

- **Pixabay Content License** (most of the current sounds, the lo-fi bed): free for commercial use, no attribution.
  Music can still draw a Content ID claim from its artist; dispute it with the licence page.
- **Sonniss GDC bundles**: free, commercial use, no attribution; **no AI or machine-learning training** with the files,
  no redistribution of the files as sound effects. The download server refuses scripted downloads: download a part in
  your browser, then `sfx.py add` each sound you keep (with `--license sonniss-gdc` and the bundle year in `--source`).
- **LottieFiles free animations**: usually the Lottie Simple License (commercial use, no attribution, no reselling the
  files); check each file's page. Premium files are not used.
- **Mixkit**: the free licence only, never the Restricted one. **Pexels** stock video: free, no credit (Stock B-roll route).
- **Epidemic Sound**: covered while the subscription is active; record the track in the manifest with `--license epidemic`.
- **Unknown source**: `"license": "unconfirmed"`. The editor never picks it; the composer refuses it in `"sounds"`.

## Adding things safely

```bash
python3 "$SK/scripts/sfx.py" add ~/Downloads/soft-tap.wav --name tap-soft --category ui \
  --source "Pixabay: https://pixabay.com/sound-effects/<page>" --license pixabay --use "a soft UI tap" --never "copy"
python3 "$SK/formats/lottie.py" ring videos/_shared/lottie/yt-ring-90.json value=90 color=amber
```

Then add the Lottie or image row to its `LICENSES.md` by hand. Never use these files to train a model, and never send
them to a service that trains on uploads.
