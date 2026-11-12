# PYTOSHKA FRAGMOVIE STYLE GUIDE
## Authoritative Directing, Editing & Post-Production Standards for dem.Toshka Cinematic Studio

---

## 1. Executive Summary & Brand Identity

The **PYTOSHKA Style** is an AI-assisted, director-grade visual language engineered for Counter-Strike 2 competitive highlights. It bridges the gap between high-tempo esports fragmovies and cinematic video art.

### Core Principles
1. **100% In-Engine Authenticity**: Every piece of gameplay footage originates from genuine CS2 demo files (`.dem`) played back in real-time through HLAE and recorded at 60 FPS uncompressed. No generative AI fake gameplay.
2. **Event-First Synchronization**: Music beats and sound design adapt to match real gameplay events—never the other way around. Gunshots, muzzle flashes, and kill confirmations dictate cut points and transient peaks.
3. **Clean Master Policy**: Master renders prioritize visual immersion. Massive in-game HUDs (radar, chat, health/ammo boxes) are suppressed via clean 16:9 framing (`crop=1600:900:160:90,scale=1920:1080:flags=lanczos`) and `cl_drawhud 0`.
4. **Licensed & Original Sound**: Strictly professional sound assets from the official **Sonniss GDC 2026 Game Audio Bundle** (24-bit/96kHz & 192kHz). No cheap synthetic sine waves or copyright-infringing rips.

---

## 2. The Three Editorial Profiles

| Metric / Dimension | `HYPE` Profile | `CINEMATIC` Profile | `HYBRID` Profile (Default ⭐) |
| :--- | :--- | :--- | :--- |
| **Pacing / Cut Speed** | Rapid, aggressive ($0.8$s – $1.8$s per cut) | Deliberate, smooth ($2.5$s – $4.5$s per cut) | Dynamic curve ($1.2$s – $3.2$s per cut) |
| **Camera Movement** | Snappy first-person snaps, rapid POVs | Wide establishing sweeps, slow 3rd-person glides | Approach on shoulder, action on POV, victory orbit |
| **Transitions** | Whip pans (270° blur), flash cuts, RGB splits | Smooth cross-dissolves, luma wipes | Whip pan on approach, zoom on headshot, smooth orbit |
| **Speed Ramping** | Aggressive optical flow ($4.0$x acceleration) | Subtle timescale retiming ($0.7$x slow-mo) | Fast-forward inter-frag ($3.5$x) + 1.0x duels |
| **Killfeed Graphics** | Tournament stacked badges, high prominence | Off / None (100% clean cinematic footage) | Toggleable: Pure Clean by default, Broadcast on demand |
| **Color Grading** | Cold Esports or Cyber Contrast (+15% Sat) | Warm Sandstone Film Emulation (Soft S-Curve) | Rich Sandstone Cinematic with organic contrast |
| **Audio Treatment** | Heavy 808 sub-bass, metallic snaps on every kill | Atmospheric drones, room tone, distant gunshot echoes | Punchy 808 drop, crisp rifle cracks, sub downers |

---

## 3. Narrative Pacing & The 9 Storyboard Scenes

Professional fragmovie editing follows an intentional dramatic arc rather than random montage cuts:

```
[1. ESTABLISHING] ──> [2. APPROACH] ──> [3. TENSION] ──> [4. ENGAGEMENT]
      (Wide flyby)        (Shoulder Cam)     (Corner hold)      (808 Drop / 1st Frag)
                                                                       │
[8. ACE CLIMAX] <── [7. CLUTCH] <── [6. MULTIKILL] <── [5. SPRAY TRANSFER]
(Hero 360° Orbit)    (1vX Duel)       (Rapid kills)       (Speed-ramped flick)
      │
[9. AFTERMATH] (Victory Card & Fade)
```

1. **Scene 1 — ESTABLISHING**: Wide architectural flyby introducing the map, skybox, and tactical situation (1.5s–2.5s).
2. **Scene 2 — APPROACH**: Third-person shoulder cam (`SHOULDER_CAM`) tracking behind the hero advancing toward the site.
3. **Scene 3 — TENSION**: Smooth transition into First-Person POV (`FIRST_PERSON`) as hero approaches the corner. Trailer alarm riser builds anticipation.
4. **Scene 4 — ENGAGEMENT**: The exact beat drop of the soundtrack hits simultaneously with the first weapon muzzle flash. Muzzle punch-in zoom ($1.04$x) and kill confirmation.
5. **Scene 5 — SPRAY TRANSFER / REPOSITION**: Speed ramp ($3.5$x–$4.0$x) covering player repositioning across empty space with directional motion blur and air whoosh.
6. **Scene 6 — MULTIKILL**: Consecutive rapid frags maintained on primary hero POV to preserve spatial orientation and recoil mastery.
7. **Scene 7 — CLUTCH / VICTIM REACTION**: Dynamic zoom-in snap to victim POV on a highlight headshot dink.
8. **Scene 8 — ACE CLIMAX**: 3rd-person circular camera path revolving 120°–180° around the hero celebrating the 5K Ace. Slow-motion ($0.7$x) with extended sub decay.
9. **Scene 9 — AFTERMATH**: Golden ACE domination victory badge, gradual fade to black over $1.0$s.

---

## 4. Camera Choreography Matrix

| Camera Type | Role & Narrative Purpose | Ideal FOV | Motion Characteristics |
| :--- | :--- | :---: | :--- |
| **FIRST_PERSON** | Combat engagement, recoil mastery, spatial authenticity | $90^\circ$ | Native in-engine player viewmodel and crosshair. |
| **SHOULDER_CAM** | Tactical approach, corridor walkup, setting the stage | $92^\circ$ | Positioned $+22$ units right, $-48$ units back, $+14$ units above player eye. |
| **VICTIM_POV** | Reaction to fatal headshot, dramatic impact | $90^\circ$ | Centered on victim until fatal bullet dink, camera drops with ragdoll. |
| **ORBIT_CAMERA** | Round victory celebration, Ace domination payoff | $94^\circ$ | Smooth circular path around hero ($180^\circ$ arc, radius 140 units, speed $45^\circ$/s). |
| **FREECAM_FLYBY** | Map overview, dramatic perspective | $85^\circ$ | Low-altitude spline flyby through bomb site. |

---

## 5. Visual Transitions & Fusion Recipes

### 1. Directional Whip Pan (270° Shutter)
* **Usage**: Switching from Shoulder Approach to Hero First-Person view.
* **Duration**: $0.20$s ($12$ frames @ 60 FPS).
* **Fusion Recipe**:
  ```
  [MediaIn1] -> [DirectionalBlur: Length=0.08, Angle=180] -> [Transform: CenterX anim] -> [Dissolve] -> [MediaIn2]
  ```
* **Audio**: `whoosh_air_blast_clean.wav` peaking 2 frames prior to the cut.

### 2. Radial Zoom-In Snap
* **Usage**: Cutting from Hero POV into Victim POV on headshots.
* **Duration**: $0.15$s ($9$ frames @ 60 FPS).
* **Fusion Recipe**:
  ```
  [MediaIn1] -> [Transform: Size 1.0 -> 1.38 (Exp Ease)] -> [RadialBlur: Blur=0.12] -> [MediaIn2]
  ```
* **Audio**: `transition_wind_whip_turbulent.wav` + metallic snap on impact.

### 3. Luma Contrast Impact Flash
* **Usage**: Synchronized with sniper shots, heavy rifle cracks, and music beat drops.
* **Duration**: $0.06$s ($3$–$4$ frames).
* **Color Page Recipe**: Gain keyframed $+35\%$ for 2 frames, decaying over 4 frames with soft halation.

---

## 6. Speed Ramping & Motion Design

### Inter-Frag Traversal Rule
* Never subject the viewer to $> 2.0$ seconds of empty walking or corridor repositioning without action.
* Retime dead space using **Optical Flow Speed Ramps** ($3.0$x to $4.5$x speed factor).
* Transition back to normal $1.0$x speed $0.25$ seconds before the hero sights the next enemy.

### Micro Punch-In Camera Shake
* Keyframe crop zoom on impact frames:
  ```python
  crop=w='iw*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30))':
       h='ih*(1-0.04*between(t,7.71,7.85)-0.06*between(t,12.18,12.30))':
       x='(iw-ow)/2':y='(ih-oh)/2',scale=1920:1080:flags=bicubic
  ```
* Instant $1.04$x–$1.06$x scale punch on the exact impact frame, cubic ease-out recovery in $0.12$s.

---

## 7. Color Grading Architecture

### Egyptian Sandstone Cinematic (`.cube` LUT)
* **Highlights**: Warm golden sandstone (`#f4ecd8`), soft highlight rolloff preventing blown-out skybox.
* **Midtones**: Balanced natural flesh tones and weapon finishes with enhanced texture separation.
* **Shadows**: Deep rich teal-charcoal (`#1a1d24`) providing modern filmic contrast without crushed blacks.
* **Halation**: Subtle $5\%$ luma diffusion on bright sun reflections and muzzle flares.

---

## 8. Fairlight 6-Track Sound Design Architecture

| Track | Stems & Content | Source & Characteristics | Target Level | Processing |
| :--- | :--- | :--- | :---: | :--- |
| **A1** | CS2 Gameplay | In-engine demo audio (segmented) | $+2.6$ dB | HPF 80 Hz, $+1.5$ dB @ 5 kHz for rifle bite. |
| **A2** | Soundtrack | Phonk / Trap / Electronic (140–145 BPM) | $-4.5$ dB | Sidechained to gameplay kicks; drop locked to 1st kill. |
| **A3** | Cinematic Impacts | Sonniss GDC 2026 Bass Drops & Downers | $-4.0$ dB | Fast16 sub-downers (< 80 Hz) on kills; metal slice on 1K. |
| **A4** | Transition Whooshes| Sonniss Air Designed & Swishes | $-8.0$ dB | Fast stereo air sweeps leading into camera cuts. |
| **A5** | Risers & Accents | Federico Soler Trailer Alarms | $-7.5$ dB | Exponential tension riser into the drop; carabiner click on HS. |
| **A6** | Atmosphere | Dark Spell Ambient Drones | $-14.0$ dB | Subtle room tone bed under opening approach. |

---

## 9. Typography & Overlay Standards

* **Pure Cinematic Mode (Default)**: Overlays disabled during combat. Only narrative intro lower-third (0.3s–2.0s) and glowing Ace celebration card (16.6s–18.5s).
* **Esports Broadcast Mode (On Demand)**: High-resolution alpha badges stacked frame-locked to kills:
  * 1K: Orange `#ff8c00` badge at $7.83$s
  * 2K: Bright Orange `#ff5a00` badge at $10.45$s
  * 3K: Red `#ef4444` Headshot badge at $12.20$s
  * 4K: Purple `#dc2626` badge at $13.50$s
  * 5K: Gold `#ffd700` ACE badge strictly at $16.50$s (upon final kill confirmation in orbit)

---

## 10. Empirical Synthesis & Cross-Reference Comparison (Phase 3.4)

Analysis of 5 verified community reference edits revealed key editorial trade-offs and best practices:

### Cross-Reference Comparative Matrix
| Reference Clip | Duration | Cuts | BPM | Primary Style & Signature Technique | Reusable Lesson for dem.Toshka |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `ssstik.io_...531192.mp4` | 20.6s | 5 | 187.5 | Inferno 60 FPS dynamic montage with micro punch-ins | 60 FPS temporal resolution preserves crisp muzzle flashes; 1.05x punch-in accentuates rifle sprays. |
| `ssstik.io_...695954.mp4` | 29.5s | 0 | 105.3 | Continuous single-take desert site flow | Unbroken POV flow creates maximum narrative suspense before the first engagement. |
| `ssstik.io_...752764.mp4` | 15.7s | 6 | 187.5 | Fast sniper flick with directional whip transition | Directional blur (270° shutter) masks crosshair flick rotation into next frag cleanly. |
| `Друзей не меняют на бабло` | 60.1s | 39 | 105.3 | High-tempo 39-cut beat-sync montage under rap vocal | Snapping every cut to drum kicks creates viral pacing; requires sidechain ducking on gameplay cracks. |
| `Моя голова винтом ❤️` | 60.1s | 33 | 105.3 | Rotational spin flow & whip-pan transitions | Combining camera rotation with bass drops elevates momentum; avoid over-spinning to preserve readability. |

### Core Evolutionary Rules for dem.Toshka
1. **Pacing Balance**: Do not exceed 0.65 cuts/second continuously. Use the **Tension-Release cycle** (Scene 2 Approach -> Scene 3 Tension -> Scene 4 Drop -> Scene 6 Multikill Burst -> Scene 8 Climax).
2. **Sidechain Rule**: Whenever heavy vocal rap or phonk music is used, duck the music stem by $-3.5$ dB to $-4.5$ dB on lethal shots to preserve the mechanical impact of CS2 gunfire.
3. **Transition Discretion**: Use whip pans only during fast traversal or post-spray transfers; never insert whip pans during the fatal trigger-pull moment.
4. **Color Authenticity**: Keep weapon finishes (skins) color-accurate while applying filmic S-curve contrast to map geometry.

