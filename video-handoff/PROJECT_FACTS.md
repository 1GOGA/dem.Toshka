# Project Facts: CS2 Highlights Studio (dem.Toshka | pytoshka)

> **Document Version:** 1.0.0  
> **Last Verified:** 2026-10-23  
> **Target Audience:** Next AI Agent / Video Editor / Technical Reviewer

---

## 1. Project Identification & Location
- **Product Name:** CS2 Highlights Studio (`dem.Toshka | pytoshka`)
- **Repository Root (Absolute Path):** `c:\Users\pyPypy\Documents\MySCOPE\demToshka`
- **Application Category:** Desktop Local-first CS2 Match Analytics & Cinematic Highlight Video Studio
- **Target Audience:** Content creators, CS2 esports players, fragmovie editors, and match analysts.
- **Operating Model:** Standalone Single-user Desktop MVP with zero external cloud dependencies. Ingests local `.dem` files, parses protobuf telemetry, visualizes 2D radar replays, and controls external rendering pipelines.

---

## 2. Technology Stack & Runtime Architecture

### Frontend
- **Framework:** React 19.2.8 with TypeScript 6.0.2
- **Build Tool:** Vite 8.3.4 (Dev server configured with `/api` reverse proxy to backend)
- **Styling & UI:** Custom responsive dark glassmorphic design system (`Plus Jakarta Sans`, `Space Grotesk`, `JetBrains Mono`), zero bloated component libraries.
- **Key Modules:**
  - `CinematicShowcaseView.tsx` — Landing/Hero screen with direct access to studio and library.
  - `HighlightsStudioView.tsx` — Flagship 4-step wizard workspace (Match ➔ Player ➔ Moments & 2D Radar ➔ Export & Settings).
  - `Round2DReplayView.tsx` & `TacticalReplayRadar.tsx` — Interactive SVG/Canvas 2D map with dynamic nickname scaling (`1 / zoom^1.35`), smoke/fire duration pills, bomb site plant timers, and freeze-time auto-skipping.
  - `MatchOverviewView.tsx` — Deep match analytics, round breakdown timeline, player K/D, ADR, HS%.
  - `ClipsMontageView.tsx` — In-app MP4 clips gallery with video player, multi-clip selection, and FFmpeg concatenation.
  - `LibraryView.tsx` — Ingested demo archive with map previews, date/tickrate info, and drag-and-drop upload.
  - `SettingsView.tsx` — CS2 Config Shield (autoexec protection), storage paths, and HLAE configuration.
  - `RenderQueueModal.tsx` & `ClipSettingsModal.tsx` — Queue management, progressive FPS selector, esports 4:3 stretched mode, crosshair simulator.

### Backend
- **Runtime:** Python 3.12 (Virtual Environment located at `.venv`)
- **API Framework:** FastAPI 0.142.2 running under Uvicorn 0.54.0
- **Database:** SQLite 3 with WAL mode enabled (`demtoshka.db`). Schema version 1.
- **CS2 Demo Parsing:**
  - `awpy 2.0.2` & `demoparser2 0.42.0` for parsing CS2 protobuf event streams.
  - Extracts kills, damages, utility throws, round freeze time, bomb plants/defuses, player positions (X/Y/Z, eye angles, view angles).
- **Video Capture & Montage Engine:**
  - HLAE 2.164.2 (`AfxHookSource2`) integrated via `tools/hlae/HLAE.exe`.
  - CS2 engine automation scripts (`mirv_cmd`, spectator POV targeting, exec cfg generation).
  - Bundled FFmpeg 9.0.2 full build (`tools/hlae/ffmpeg/bin/ffmpeg.exe`) for lossless video muxing, NVENC/libx264 encoding, and montage compilation.

---

## 3. Verified State & Dataset In SQLite (`demtoshka.db`)

The active SQLite database contains comprehensive, verified real-world CS2 competitive match telemetry:
- **Total Parsed Demos:** 6 complete CS2 matches.
  - Maps: `de_mirage`, `de_nuke`, `de_anubis`
  - Tickrates: 64 tick and 128 tick
- **Total Rounds Parsed:** 118 rounds.
- **Total Players Tracked:** 60 unique player profiles (SteamIDs, nicknames, teams).
- **Total Kill Events:** 886 detailed frags (weapons, hitgroups, blind status, wallbangs, coordinates).
- **Detected Highlights:** 730 automatically classified moments:
  - Multi-kills: 2K, 3K, 4K, ACE (5K)
  - Clutch situations: 1v1, 1v2, 1v3, 1v4
  - Weapon specialties: AWP flicks, Deagle one-taps, knife kills, smoke defuses.
- **Render History:** 35 render jobs recorded in database, 14 finalized MP4 video files stored in `renders/` (~1.2 GB total).

---

## 4. Distinctive Product Features

1. **Intelligent Highlight Detection:**
   - Detects frag clusters with precise tick intervals, multi-kill pacing, weapon context, and clutch survivor status without relying on external APIs.
2. **2D Tactical Radar Replay:**
   - Accurate map coordinate translation for official CS2 maps.
   - Dynamic nickname zoom scaling keeps text legible at all zoom levels without covering teammate icons.
   - Live smoke and incendiary grenade timer rings (counting down active seconds).
   - Freeze-time auto-skipping eliminates dead 10-15s spawn wait.
3. **Esports POV & Aspect Ratio Engine:**
   - Native 4:3 Stretched mode (models appear 33% wider, the esports standard).
   - Progressive FPS control: 30 FPS (quick draft), 60 FPS (standard), 120 FPS (smooth slow-motion).
   - POV Director with 2 modes: "Главный Герой" (100% fragger POV) and "Килл-кам PRO" (victim death ➔ rewind ➔ killer POV).
   - Live interactive crosshair simulator (size, gap, thickness, color, dot).
4. **CS2 Config Shield:**
   - Automatic backup and restore of player's `cs2_video.txt` and `autoexec.cfg` prior to HLAE demo recording, ensuring user settings and keybindings are never corrupted.
5. **In-App Media Player & Multi-Clip Montage:**
   - Scrubbable video player with 4:3 stretched toggle and speed control.
   - Batch selection of clips with one-click FFmpeg stitcher producing cohesive highlight reels.

