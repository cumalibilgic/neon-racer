# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Neon Racer: a synthwave three-lane racing game in Python + pygame-ce. Game logic and rendering live in `main.py`. Platform-specific code is isolated in `audio.py` (pygame.mixer) and `storage.py` (save data) so it can be swapped out later, e.g. for a Unity port. It runs on the desktop and in the browser (built with pygbag, published to GitHub Pages at https://cumalibilgic.github.io/neon-racer/). README, commit messages and UI text are in Turkish.

Geliştirme planı için [ROADMAP.md](ROADMAP.md)'ye bak.

## Commands

```
pip install pygame-ce
python main.py                      # run on desktop
pip install pygbag
python -m pygbag --build .          # web build -> build/web (gitignored)
python -m pygbag .                  # local web server for testing the browser build
pip install numpy soundfile
python tools/make_sounds.py         # regenerate assets/*.ogg (music + sound effects)
```

On Windows, run pygbag with `PYTHONUTF8=1`, otherwise it fails to read the Turkish characters in `main.py` (cp1254 decode error).

There are no tests, linter config or dependency files. Every push to `main` triggers `.github/workflows/deploy.yml`, which builds with pygbag (Python 3.12) and deploys to GitHub Pages, so pushing to `main` publishes the game.

## Web compatibility constraints (pygbag)

- The entry point must stay `main.py` with an `async def main()` loop that calls `await asyncio.sleep(0)` every frame; pygbag requires this to yield to the browser.
- `WEB = sys.platform == "emscripten"` detects the browser. Web performance is the main constraint: on web the supersample factor `SS` is 1 (desktop uses 2).
- Use only pygame-ce features that work under emscripten. Graphics are generated in code (no image files); fonts use `pygame.font.Font(None, ...)`.
- Sounds are `.ogg` files in `assets/`, synthesized offline by `tools/make_sounds.py`. Don't hand-edit them and don't import numpy in the game itself. On Windows, libsndfile crashes when writing large Vorbis blocks, so the script writes in chunks.
- Browsers block audio until the first user input, so `Game.handle_event` calls `audio.start_music()` on the first key or click (on desktop the music starts immediately). Music plays as a looping `Sound` on reserved channel 0.
- `storage.py` uses `platform.window.localStorage` on web and `save.json` (gitignored) next to the code on desktop. All persistent data lives in the `Game.data` dict and is written by `Game.save()`.
- Touch input arrives as mouse events. Press, motion and release are tracked in `handle_event`: a horizontal drag past `SWIPE_DIST` changes lane immediately, and a release without a swipe calls `tap()` (left/right half of the screen, the mute button, or start).

## Architecture

- **Fake-3D projection**: world objects have a lane x (`LANES`, in world units) and a depth `z` (0..`Z_FAR`). `Game.project(xw, z)` converts these to screen x/y/scale using `CAM`, `HORIZON` and `BASE_Y`, and adds road curvature through `self.curve`. Everything drawn on the road (road segments, cars, pads, lamps, particles spawned at the player) goes through `project`. The returned coordinates are already multiplied by `SS`.
- **Supersampled render pipeline** (`Game.draw`): the world is drawn to `self.canvas` (size `WIDTH*SS × HEIGHT*SS`), downscaled to the screen, then a cheap bloom pass (downscale, square via `BLEND_MULT`, additive blit), vignette, crash flash, and finally the HUD/menus drawn directly at screen resolution. When drawing to the canvas, multiply pixel sizes by `SS`. When drawing to the screen (HUD), do not.
- **Prebuilt surfaces**: sky, sun, skylines, haze, vignette and glow sprites are built once by the `make_*` / `glow_sprite` helpers (glow sprites are cached). Avoid allocating surfaces every frame.
- **Game state**: `Game.state` is `"menu"`, `"play"` or `"over"`. `update()` runs every frame in all states (the road keeps scrolling in the menu and slows down after a crash). `reset()` reinitializes the per-run state, and `high_score` persists across runs.
- **Timing is frame-based**: speeds, timers (`BOOST_TIME`, `spawn_timer`, `over_timer`) and easing are per-frame at `FPS = 60`, not delta-time.
- **Fairness**: `spawn()` refuses to spawn a car if it would block all lanes near the far end (`busy` lanes). Keep this invariant when changing traffic generation.
- Depth fog (`fog_amount`, `mix`) tints distant objects toward `FOG`. Colors are module-level constants at the top of the file.
