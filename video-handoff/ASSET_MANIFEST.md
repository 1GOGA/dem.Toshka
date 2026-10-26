# Asset Manifest: CS2 Highlights Studio Video Handoff

> **Creation Date:** 2026-10-23  
> **Project Root Directory:** `c:\Users\pyPypy\Documents\MySCOPE\demToshka`  
> **Base Asset Directory:** `c:\Users\pyPypy\Documents\MySCOPE\demToshka\video-handoff\assets`  
> **Total Curated Screenshots:** 7 essential files (All 1920×1080 Full HD, PNG)  
> **Total Video Footage:** 3 files (1080p 120fps/60fps, MP4 / H.264 + AAC)

---

## 1. Verified High-Resolution Screenshots (1920×1080)

All screenshots are stored in `video-handoff/assets/screenshots/` and captured directly from the live unmodified web application running against the active SQLite match database (`demtoshka.db`).

| File Name | Resolution | Format | Size | Description & UI Focus |
| :--- | :---: | :---: | :---: | :--- |
| **`01_showcase_hero.png`** | 1920×1080 | PNG | 473 KB | **Landing Showcase:** Headline *"Будущее нарезки хайлайтов начинается с ИИ"*, CTA buttons (*"В студию хайлайтов"*, *"Открыть демо-библиотеку"*), pipeline cards, and stats. |
| **`02_studio_step2_players.png`** | 1920×1080 | PNG | 243 KB | **Studio Step 2 (Player Selection):** Selected player card with Terrorist Phoenix avatar, frag count (23 frags), team side indicators (T / CT), and full match player roster. |
| **`03_studio_step3_radar.png`** | 1920×1080 | PNG | 287 KB | **Studio Step 3 (Moments & 2D Radar):** Dual layout featuring detected highlight cards (2K, 3K, ACE tags) on the left and interactive 2D Mirage radar on the right. |
| **`04_studio_step4_export.png`** | 1920×1080 | PNG | 155 KB | **Studio Step 4 (Video & Export Settings):** POV Director (Hero vs Killcam PRO), 4:3 stretched mode toggle, progressive FPS selector (30, 60, 120 FPS), and resolution. |
| **`05_match_scoreboard.png`** | 1920×1080 | PNG | 252 KB | **Match Analytics & Scoreboard:** Team score overview, round-by-round event timeline with bomb plant/defuse icons, player K/D, ADR, and HS%. |
| **`06_tactical_replay_2d.png`** | 1920×1080 | PNG | 241 KB | **Tactical 2D Replay View:** Full radar with player motion trails, dynamic nickname zoom scaling, smoke/fire countdown timer pills, and playback scrubber. |
| **`07_clips_gallery.png`** | 1920×1080 | PNG | 174 KB | **Clips & Montage Gallery:** Grid of completed MP4 video files, clip durations, resolutions, batch selection tools, and *"Создать хайлайт-монтаж"* button. |

---

## 2. Real Video Footage Clips (1080p Gameplay & Montage)

All video clips are stored in `video-handoff/assets/footage/` and produced directly by the project's FFmpeg and HLAE rendering engine from real parsed CS2 demos:

| File Name | Resolution | Frame Rate | Duration | Size | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`01_highlight_mirage_frag.mp4`** | 1920×1080 | 120 FPS | 5.0 sec | 13.1 MB | **Ultra-Smooth 120 FPS Mirage Frag:** POV rifle elimination with crystal-clear CS2 hit registration, weapon audio, and kill banner. Ideal for high-speed slow-motion showcases. |
| **`02_highlight_nuke_kill.mp4`** | 1920×1080 | 60 FPS | 2.1 sec | 3.4 MB | **Nuke Fast-Action Elimination:** POV frag on de_nuke showing crisp camera direction and synchronized sound effects. |
| **`03_montage_reel_preview.mp4`** | 1920×1080 | 120 FPS | 6.0 sec | 18.8 MB | **Compiled Multi-Frag Montage:** Stitched multi-kill sequence created by the in-app FFmpeg montage compiler demonstrating seamless cut-to-cut compilation. |

---

## 3. Directory Structure Overview

```text
video-handoff/
├── PROJECT_FACTS.md        # Comprehensive technical facts, stack, and active database statistics
├── FEATURE_MATRIX.md       # Verified status matrix of all 14 product capabilities
├── RUN_LOCAL.md            # Exact step-by-step local launch instructions, ports, and URLs
├── SHOT_LIST.md            # 12-scene filming blueprint with exact in-app timestamps and camera focal points
├── STORYBOARD_DRAFT.md     # 4-act narrative storyboard
├── ASSET_MANIFEST.md       # This file
└── assets/
    ├── screenshots/        # 7 essential Full HD UI screenshots
    └── footage/            # 3 real rendered CS2 1080p video clips
```
