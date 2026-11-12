# REFERENCE CARD — ssstik.io_1794490752764.mp4
**Reference ID**: `ref_ssstik.io_1794490752764_d1588444`  
**Analyzed**: `2026-11-12T13:55:21Z`  
**Technical Bitstream**: `1024x576 @ 30.0 FPS` | `1900 kbps` | `15.70s`  
**Auto Categories**: `Dynamic Montage`, `Mid-Tempo Groove`, `Speed Ramping & Retiming`, `Spin & Whip-Pan Flow`, `Vibrant Saturated Grade`, `Widescreen 16:9`  
**User Feedback**: `None`  

---

## 1. Executive Summary
Reference analysis for ssstik.io_1794490752764.mp4: 6 cuts, BPM 98.4, 4 repeatable editing patterns extracted. Categories: Dynamic Montage, Mid-Tempo Groove, Speed Ramping & Retiming, Spin & Whip-Pan Flow, Vibrant Saturated Grade, Widescreen 16:9.

## 2. Visual Contact Sheet
![Contact Sheet](C:\Users\pyPypy\Documents\MySCOPE\demToshka\reference_library\contact_sheets\ref_ssstik.io_1794490752764_d1588444_contact_sheet.png)

## 3. Timestamped Breakdown (OBSERVED vs INFERRED vs IMPLEMENTATION)
| Time (s) | Event | OBSERVED (What is Visible) | INFERRED (Likely Technique) | IMPLEMENTATION (DaVinci Resolve 21 Recipe) |
| :--- | :--- | :--- | :--- | :--- |
| **0.09s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 0.09s (estimated 98.4 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **0.50s** | `MOTION_SPEED_RAMP_ACCEL` | Speed factor 2.5x (SPEED_RAMP_ACCEL) from 0.50s to 1.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **0.68s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 0.68s (estimated 98.4 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **1.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 1.00s to 1.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **1.32s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 1.32s (estimated 98.4 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **1.92s** | `AUDIO_SUB_BASS_DROP` | Sub-bass 808 drop / heavy kick transient at 1.92s (estimated 98.4 BPM). | Fatal gunshot / kill confirmation intentionally timed to hit the musical downbeat. | `DaVinci Fairlight: Timeline audio grid set to BPM, snap gunshot audio transient to sub-bass transient.` |
| **2.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 2.00s to 2.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **2.50s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 2.50s to 3.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **2.60s** | `TRANSITION_WHIP_PAN` | Cut at 2.60s (WHIP_PAN) with frame intensity diff 39.6. | Whip-pan rotation matched with camera velocity vector | `DaVinci Fusion: DirectionalBlur (Angle=0, Length=0.08) with 270° shutter angle.` |
| **3.00s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 3.00s to 3.50s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **3.50s** | `MOTION_PUNCH_IN_SHAKE` | Speed factor 1.05x (PUNCH_IN_SHAKE) from 3.50s to 4.00s. | Fast-forward repositioning between separate engagements or slow-mo bullet impact accent. | `DaVinci Edit: Retime Curve -> Speed Points with Optical Flow processing.` |
| **8.13s** | `TRANSITION_HARD_CUT` | Cut at 8.13s (HARD_CUT) with frame intensity diff 38.1. | Instant angle cut precisely on musical drum transient or weapon discharge | `DaVinci Edit: Hard Razor cut aligned to frame; no dissolve.` |

## 4. Color Grading Analysis
* **Dominant Palette**: `#956436`, `#170e11`, `#d5a762`, `#78a2bc`, `#5b402e`
* **Shadow Tint**: `#251516` | **Highlight Tint**: `#d8c591`
* **Saturation**: `0.54` | **Contrast**: `0.36`
* **OBSERVED**: Palette centered on ['#956436', '#170e11', '#d5a762'], shadows tinted #251516, highlights at #d8c591, avg sat 0.54.
* **INFERRED**: Warm sandstone desert grade with compressed shadow blacks and soft highlight rolloff.
* **IMPLEMENTATION**: `DaVinci Color Page: Node 1 Primaries Lift -0.015, Gain 1.04; Node 2 Custom Curves S-curve; Node 3 Tint shadows slightly toward #1a1e28 and highlights toward #f6edd8.`

## 5. Sound Design & Audio Sync
* **BPM**: `98.4`
* **OBSERVED**: Estimated tempo: 98.4 BPM with 4 primary drops and 8 sub-bass hits.
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
