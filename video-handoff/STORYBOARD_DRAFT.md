# Storyboard Draft: CS2 Highlights Studio Commercial

> **Format:** 30–45 second fast-paced promotional video  
> **Concept:** *"From Dem File to Cinematic Fragmovie in 30 Seconds"*  
> **Tone:** Professional, Esports-Grade, Sleek, Confident  
> **Target Audience:** CS2 content creators, competitive players, video editors

---

## Shot Accessibility Classification

To ensure complete honesty and zero production blockers, all planned shots are categorized into:
- 🟢 **ACCESSIBLE NOW**: 100% verified UI screens and real rendered CS2 gameplay footage assets ready in `video-handoff/assets/`.
- 🟡 **NEEDS LOCAL CS2/CAPTURE**: Requires active CS2 game client execution for live in-game recording (not needed for promo if using verified pre-rendered footage).
- 🔴 **EXCLUDED / DO NOT USE**: Non-functional elements, unverified third-party ratings, or hypothetical features.

---

## Narrative Arc & Scene Breakdown

### Act 1: The Problem & The Awakening (0:00 – 0:08)
- **Concept:** Every CS2 player knows the agony of typing console commands into `demoui`, finding round timestamps manually, and dealing with broken spectator cams.
- **Scene 1 (Hook):** 
  - *Visual:* Clean wide shot of `01_showcase_hero.png` with futuristic blue particle backdrop and title: *"Будущее нарезки хайлайтов начинается с ИИ. Меньше рутины в консоли."*
  - *Voiceover / Caption:* "Still clipping your CS2 frags with console commands and clunky spectator cams?"
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`01_showcase_hero.png`).
- **Scene 2 (One-Click Match Load):**
  - *Visual:* Cursor clicks into `09_demo_library.png`. Instant library cards for Mirage, Nuke, Anubis with 128 tickrate badges.
  - *Voiceover / Caption:* "Import any .dem match instantly. No manual tick math."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`09_demo_library.png`).

---

### Act 2: Intelligence & Tactical Clarity (0:08 – 0:20)
- **Concept:** Intelligent parsing reveals all frags, clutches, and tactical paths before opening the game.
- **Scene 3 (Roster & Moment Detection):**
  - *Visual:* Quick swipe into `02_studio_step2_players.png` highlighting player `pytoshka_` (Terrorist Phoenix avatar, 23 highlights), then transitioning to `03_studio_step3_radar.png` showing the 2D radar and auto-detected multi-kill badges (2K, 3K, ACE, CLUTCH).
  - *Voiceover / Caption:* "Auto-detect multi-kills, clutches, and AWP flicks across every round."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`02_studio_step2_players.png`, `03_studio_step3_radar.png`).
- **Scene 4 (Interactive 2D Replay & Utility Timers):**
  - *Visual:* Dynamic zoom into `06_tactical_replay_2d.png`. Show animated vector player trails, live countdown timers on smoke and incendiary grenades (e.g. 5.3s smoke ring), and bomb site plants.
  - *Voiceover / Caption:* "Deep 2D tactical playback with live smoke timers and zero dead freeze-time."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`06_tactical_replay_2d.png`).

---

### Act 3: Esports Grade Video Customization (0:20 – 0:30)
- **Concept:** Full director control over camera, format, and visuals without touching HLAE config files.
- **Scene 5 (Esports 4:3 & Progressive FPS):**
  - *Visual:* Close-up on `04_studio_step4_export.png`. Highlight the **4:3 Stretched** toggle (*"models 33% wider"*), progressive FPS selector (**30 / 60 / 120 FPS**), and **POV Director** (*"Главный Герой"* vs *"Килл-кам PRO"*).
  - *Voiceover / Caption:* "Esports 4:3 stretched. 120 FPS ultra-smooth slow motion. Pro Killcam directing."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`04_studio_step4_export.png`).
- **Scene 6 (Crosshair Customizer):**
  - *Visual:* Transition to `12_clip_settings_modal.png` showcasing live crosshair simulator positioned directly under the interactive weapon preview.
  - *Voiceover / Caption:* "Match your exact competitive crosshair and HUD style."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`12_clip_settings_modal.png`).

---

### Act 4: The Payoff — Real Clips & Seamless Montage (0:30 – 0:45)
- **Concept:** The rendering engine produces broadcast-quality frag clips and stitches them into a full montage.
- **Scene 7 (Render Queue Action):**
  - *Visual:* Flash of `11_render_queue_modal.png` with completed rendering badges, then cutting directly to the finished clip.
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`11_render_queue_modal.png`).
- **Scene 8 (Explosive Gameplay Payoff):**
  - *Visual:* Full-screen video drop into `01_highlight_mirage_frag.mp4` (120 FPS crisp AWP/rifle frag with synchronized audio), cutting to `02_highlight_nuke_kill.mp4`.
  - *Voiceover / Caption:* "Flawless capture. Zero spectator lag. Pure competitive adrenaline."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`01_highlight_mirage_frag.mp4`, `02_highlight_nuke_kill.mp4`).
- **Scene 9 (In-App Player & Final Reel):**
  - *Visual:* Quick cut to `08_video_player_modal.png` showing the clip playing within the app, then expanding to `03_montage_reel_preview.mp4` with a rapid-fire sequence of frags.
  - *Voiceover / Caption:* "One click to compile your full montage."
  - *Classification:* 🟢 **ACCESSIBLE NOW** (`08_video_player_modal.png`, `03_montage_reel_preview.mp4`).
- **Scene 10 (End Card & Call to Action):**
  - *Visual:* Clean return to `01_showcase_hero.png` branding with dem.Toshka | pytoshka logo, GitHub / local repository link, and headline: *"CS2 Highlights Studio — From Demo to Fragmovie."*
  - *Classification:* 🟢 **ACCESSIBLE NOW**.

---

## Elements to Exclude From Video

1. 🔴 **Do Not Show Windows Desktop or Developer Consoles:**
   Never show terminal windows, PowerShell prompts, Uvicorn logs, or Vite dev server messages. The product must feel like a dedicated standalone esports software suite.
2. 🔴 **Do Not Claim Synthetic "HLTV Rating 3.0":**
   Per project rules (`AGENTS.md`), do not display invented HLTV algorithms. Focus on verified metrics: K/D, ADR, Headshot %, and frag clusters.
3. 🔴 **Do Not Attempt Live In-Game CS2 Launch During Promo Shooting:**
   Launching CS2 via HLAE requires specific GPU drivers, `-insecure` credentials, and active Steam sessions. Use the verified pre-rendered MP4 clips in `assets/footage/` and in-app video playback instead.

