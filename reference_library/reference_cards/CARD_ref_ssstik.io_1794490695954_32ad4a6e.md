# REFERENCE CARD — ssstik.io_1794490695954.mp4
**Reference ID**: `ref_ssstik.io_1794490695954_32ad4a6e`  
**Analyzed**: `2026-11-12T13:55:16Z`  
**Technical Bitstream**: `1024x576 @ 30.0 FPS` | `1808 kbps` | `29.47s`  
**Auto Categories**: `Continuous POV Flow`, `Mid-Tempo Groove`, `Speed Ramping & Retiming`, `Vibrant Saturated Grade`, `Widescreen 16:9`  
**User Feedback**: `None`  

---

## 1. Executive Summary
Reference analysis for ssstik.io_1794490695954.mp4: 0 cuts, BPM 105.3, 4 repeatable editing patterns extracted. Categories: Continuous POV Flow, Mid-Tempo Groove, Speed Ramping & Retiming, Vibrant Saturated Grade, Widescreen 16:9.

## 2. Visual Contact Sheet
![Contact Sheet](C:\Users\pyPypy\Documents\MySCOPE\demToshka\reference_library\contact_sheets\ref_ssstik.io_1794490695954_32ad4a6e_contact_sheet.png)

## 3. Timestamped Breakdown (OBSERVED vs INFERRED vs IMPLEMENTATION)
| Time (s) | Event | OBSERVED (What is Visible) | INFERRED (Likely Technique) | IMPLEMENTATION (DaVinci Resolve 21 Recipe) |
| :--- | :--- | :--- | :--- | :--- |
| **0.42s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 0.42s (estimated 105.3 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **0.50s** | `MOTION_SPEED_RAMP_ACCEL` | Speed factor 2.5x (SPEED_RAMP_ACCEL) from 0.50s to 1.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **1.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 1.00s to 1.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **1.16s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 1.16s (estimated 105.3 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **2.65s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 2.65s (estimated 105.3 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **3.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 3.00s to 3.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **3.25s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 3.25s (estimated 105.3 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **3.50s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 3.50s to 4.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **4.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 4.00s to 4.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **5.50s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 5.50s to 6.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |

## 4. Color Grading Analysis
* **Dominant Palette**: `#332a1e`, `#715b3b`, `#a88b58`, `#d7d774`, `#a2daee`
* **Shadow Tint**: `#322418` | **Highlight Tint**: `#c8dfa0`
* **Saturation**: `0.49` | **Contrast**: `0.25`
* **OBSERVED**: Palette centered on ['#332a1e', '#715b3b', '#a88b58'], shadows tinted #322418, highlights at #c8dfa0, avg sat 0.49.
* **INFERRED**: Warm sandstone desert grade with compressed shadow blacks and soft highlight rolloff.
* **IMPLEMENTATION**: `DaVinci Color Page: Node 1 Primaries Lift -0.015, Gain 1.04; Node 2 Custom Curves S-curve; Node 3 Tint shadows slightly toward #1a1e28 and highlights toward #f6edd8.`

## 5. Sound Design & Audio Sync
* **BPM**: `105.3`
* **OBSERVED**: Estimated tempo: 105.3 BPM with 4 primary drops and 8 sub-bass hits.
* **INFERRED**: High-impact trap/hip-hop beat with gameplay gunshot cracks layered on downbeats and ducked music.
* **IMPLEMENTATION**: `DaVinci Fairlight Page: Track A1 (CS2 Gameplay) Sidechain Send to Track A2 (Music Track). Insert Dynamics Compressor on Track A2, enable Sidechain Listen, Threshold -18 dB, Ratio 3.5:1, Fast Attack 2ms.`

## 6. Extracted Reusable Editing Patterns
### Headshot Micro Punch-In with Impact Flash (`PAT_HS_PUNCH_ref_ssst`)
* **Category**: `DIRECTING` | **Confidence**: `OBSERVED` | **Profiles**: HYBRID, HYPE
* **Description**: Sudden 1.05x-1.08x camera crop zoom with a 3-frame luma flash accentuating a lethal headshot or sniper frag.
* **Technique**: Micro zoom-in (scale 1.06x) for 0.12s duration, snapping back to 1.0x with cubic ease-out.
* **DaVinci Resolve Recipe** (Fusion Page):
```
MediaIn1 -> Transform1 (Size=1.06, Keyframe in 2f, out 7f) -> ColorCorrector1 (Gain=1.35) -> MediaOut1
```

### Inter-Frag Speed Ramp with Directional Blur (`PAT_RAMP_ref_ssst`)
* **Category**: `SPEED_RAMP` | **Confidence**: `OBSERVED` | **Profiles**: HYBRID, HYPE
* **Description**: Fast-forward retime (2.5x to 4.0x) covering player rotation or corridor traversal between separate kills.
* **Technique**: Optical Flow speed ramp accelerating to 3.5x for 0.8s, returning to 1.0x on enemy appearance.
* **DaVinci Resolve Recipe** (Edit Page):
```
Speed Point at T1 (100%), Speed Point at T2 (350%), Speed Point at T3 (100%), Retime Process: Optical Flow
```

### 808 Beat Drop / Fatal Gunshot Synchronization (`PAT_DROP_ref_ssst`)
* **Category**: `SOUND_DESIGN` | **Confidence**: `VERIFIED_IN_RESOLVE` | **Profiles**: HYBRID, HYPE, CINEMATIC
* **Description**: Locking the primary musical drop (808 kick / trap snare) frame-accurately to the first lethal trigger pull.
* **Technique**: Timeline audio grid alignment ensuring music drop transient matches the exact weapon fire frame.
* **DaVinci Resolve Recipe** (Fairlight Page):
```
Audio Track 1 (CS2) Sidechained to Track 2 (Music), Ducking: -3.5dB on drop hit.
```

### Smooth Hero Orbit Climax (`PAT_ORBIT_ref_ssst`)
* **Category**: `CAMERA_WORK` | **Confidence**: `INFERRED` | **Profiles**: HYBRID, CINEMATIC
* **Description**: 3rd-person circular camera path revolving 120-180 degrees around the hero to celebrate a round-winning Ace.
* **Technique**: Slow orbital camera glide with smooth ease-in/out, keeping hero in golden ratio third.
* **DaVinci Resolve Recipe** (Color Page):
```
Node 1 (Balance) -> Node 2 (LUT) -> Node 3 (Circular Power Window on Hero + Vignette)
```
