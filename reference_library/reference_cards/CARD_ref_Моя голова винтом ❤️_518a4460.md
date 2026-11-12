# REFERENCE CARD — Моя голова винтом ❤️.mp4
**Reference ID**: `ref_Моя голова винтом ❤️_518a4460`  
**Analyzed**: `2026-11-12T13:55:33Z`  
**Technical Bitstream**: `640x360 @ 30.0 FPS` | `683 kbps` | `60.12s`  
**Auto Categories**: `Fast Beat-Sync Edit`, `Gritty Contrast Grade`, `Impact & Flash Accents`, `Mid-Tempo Groove`, `Speed Ramping & Retiming`, `Spin & Whip-Pan Flow`, `Viral Russian Rap Edit`, `Widescreen 16:9`  
**User Feedback**: `None`  

---

## 1. Executive Summary
Reference analysis for Моя голова винтом ❤️.mp4: 33 cuts, BPM 120.0, 4 repeatable editing patterns extracted. Categories: Fast Beat-Sync Edit, Gritty Contrast Grade, Impact & Flash Accents, Mid-Tempo Groove, Speed Ramping & Retiming, Spin & Whip-Pan Flow, Viral Russian Rap Edit, Widescreen 16:9.

## 2. Visual Contact Sheet
![Contact Sheet](C:\Users\pyPypy\Documents\MySCOPE\demToshka\reference_library\contact_sheets\ref_Моя голова винтом ❤️_518a4460_contact_sheet.png)

## 3. Timestamped Breakdown (OBSERVED vs INFERRED vs IMPLEMENTATION)
| Time (s) | Event | OBSERVED (What is Visible) | INFERRED (Likely Technique) | IMPLEMENTATION (DaVinci Resolve 21 Recipe) |
| :--- | :--- | :--- | :--- | :--- |
| **1.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 1.00s to 1.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **1.50s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 1.50s to 2.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **2.50s** | `MOTION_SPEED_RAMP_ACCEL` | Speed factor 2.5x (SPEED_RAMP_ACCEL) from 2.50s to 3.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **3.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 3.00s to 3.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **3.07s** | `TRANSITION_WHIP_PAN` | Cut at 3.07s (WHIP_PAN) with frame intensity diff 38.2. | Whip-pan rotation matched with camera velocity vector | `DaVinci Fusion: DirectionalBlur (Angle=0, Length=0.08) with 270° shutter angle.` |
| **3.50s** | `MOTION_SPEED_RAMP_ACCEL` | Speed factor 2.5x (SPEED_RAMP_ACCEL) from 3.50s to 4.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **3.80s** | `TRANSITION_HARD_CUT` | Cut at 3.80s (HARD_CUT) with frame intensity diff 51.6. | Instant angle cut precisely on musical drum transient or weapon discharge | `DaVinci Edit: Hard Razor cut aligned to frame; no dissolve.` |
| **4.00s** | `MOTION_SPEED_RAMP_ACCEL` | Speed factor 2.5x (SPEED_RAMP_ACCEL) from 4.00s to 4.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **4.33s** | `TRANSITION_WHIP_PAN` | Cut at 4.33s (WHIP_PAN) with frame intensity diff 43.7. | Whip-pan rotation matched with camera velocity vector | `DaVinci Fusion: DirectionalBlur (Angle=0, Length=0.08) with 270° shutter angle.` |
| **4.64s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 4.64s (estimated 120.0 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **5.07s** | `TRANSITION_WHIP_PAN` | Cut at 5.07s (WHIP_PAN) with frame intensity diff 42.1. | Whip-pan rotation matched with camera velocity vector | `DaVinci Fusion: DirectionalBlur (Angle=0, Length=0.08) with 270° shutter angle.` |
| **5.15s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 5.15s (estimated 120.0 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |

## 4. Color Grading Analysis
* **Dominant Palette**: `#eab991`, `#020100`, `#533728`, `#886650`, `#92b1cc`
* **Shadow Tint**: `#0a0604` | **Highlight Tint**: `#e3be9f`
* **Saturation**: `0.25` | **Contrast**: `0.22`
* **OBSERVED**: Palette centered on ['#eab991', '#020100', '#533728'], shadows tinted #0a0604, highlights at #e3be9f, avg sat 0.25.
* **INFERRED**: Desaturated high-contrast esports grade accentuating player silhouettes.
* **IMPLEMENTATION**: `DaVinci Color Page: Node 1 Primaries Lift -0.015, Gain 1.04; Node 2 Custom Curves S-curve; Node 3 Tint shadows slightly toward #1a1e28 and highlights toward #f6edd8.`

## 5. Sound Design & Audio Sync
* **BPM**: `120.0`
* **OBSERVED**: Estimated tempo: 120.0 BPM with 4 primary drops and 8 sub-bass hits.
* **INFERRED**: High-impact trap/hip-hop beat with gameplay gunshot cracks layered on downbeats and ducked music.
* **IMPLEMENTATION**: `DaVinci Fairlight Page: Track A1 (CS2 Gameplay) Sidechain Send to Track A2 (Music Track). Insert Dynamics Compressor on Track A2, enable Sidechain Listen, Threshold -18 dB, Ratio 3.5:1, Fast Attack 2ms.`

## 6. Extracted Reusable Editing Patterns
### Headshot Micro Punch-In with Impact Flash (`PAT_HS_PUNCH_ref_Моя `)
* **Category**: `DIRECTING` | **Confidence**: `OBSERVED` | **Profiles**: HYBRID, HYPE
* **Description**: Sudden 1.05x-1.08x camera crop zoom with a 3-frame luma flash accentuating a lethal headshot or sniper frag.
* **Technique**: Micro zoom-in (scale 1.06x) for 0.12s duration, snapping back to 1.0x with cubic ease-out.
* **DaVinci Resolve Recipe** (Fusion Page):
```
MediaIn1 -> Transform1 (Size=1.06, Keyframe in 2f, out 7f) -> ColorCorrector1 (Gain=1.35) -> MediaOut1
```

### Inter-Frag Speed Ramp with Directional Blur (`PAT_RAMP_ref_Моя `)
* **Category**: `SPEED_RAMP` | **Confidence**: `OBSERVED` | **Profiles**: HYBRID, HYPE
* **Description**: Fast-forward retime (2.5x to 4.0x) covering player rotation or corridor traversal between separate kills.
* **Technique**: Optical Flow speed ramp accelerating to 3.5x for 0.8s, returning to 1.0x on enemy appearance.
* **DaVinci Resolve Recipe** (Edit Page):
```
Speed Point at T1 (100%), Speed Point at T2 (350%), Speed Point at T3 (100%), Retime Process: Optical Flow
```

### 808 Beat Drop / Fatal Gunshot Synchronization (`PAT_DROP_ref_Моя `)
* **Category**: `SOUND_DESIGN` | **Confidence**: `VERIFIED_IN_RESOLVE` | **Profiles**: HYBRID, HYPE, CINEMATIC
* **Description**: Locking the primary musical drop (808 kick / trap snare) frame-accurately to the first lethal trigger pull.
* **Technique**: Timeline audio grid alignment ensuring music drop transient matches the exact weapon fire frame.
* **DaVinci Resolve Recipe** (Fairlight Page):
```
Audio Track 1 (CS2) Sidechained to Track 2 (Music), Ducking: -3.5dB on drop hit.
```

### Smooth Hero Orbit Climax (`PAT_ORBIT_ref_Моя `)
* **Category**: `CAMERA_WORK` | **Confidence**: `INFERRED` | **Profiles**: HYBRID, CINEMATIC
* **Description**: 3rd-person circular camera path revolving 120-180 degrees around the hero to celebrate a round-winning Ace.
* **Technique**: Slow orbital camera glide with smooth ease-in/out, keeping hero in golden ratio third.
* **DaVinci Resolve Recipe** (Color Page):
```
Node 1 (Balance) -> Node 2 (LUT) -> Node 3 (Circular Power Window on Hero + Vignette)
```
