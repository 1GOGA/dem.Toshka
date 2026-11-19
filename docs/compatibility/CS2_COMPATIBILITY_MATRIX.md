# CS2 & Tool Compatibility Matrix — dem.Toshka

**Date:** 2026-11-19  
**Document Status:** COMPLETE & VERIFIED  
**CS2 Engine:** Source 2 (64-bit Windows)

---

## 1. Tool Compatibility Status Overview

| Tool / Component | Bundled / Detected Version | Target CS2 Build / Protocol | Compatibility Status | Verified Features | Known Limitations & Action Required |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **HLAE (`HLAE.exe`)** | `v2.192.7.0` (commit `385e10c0`) | CS2 Release Builds (Nov 2026) | **VERIFIED** | Custom loader launch, command line injection, `playdemo`, `mirv_cmd`, headless rendering. | Must be launched with `-customLoader` and `-hookDllPath` pointing to `AfxHookSource2.dll`. Direct GUI attachment deprecated for automation. |
| **AfxHookSource2 (`AfxHookSource2.dll`)** | `v0.42.0` (DirectX 11 Hook) | CS2 Build 14000+ / Source 2 Engine | **VERIFIED** | Direct3D 11 interception, `mirv_streams` video & audio capture, `mirv_campath` drawing, `mirv_deathmsg` filters. | Direct GDI BitBlt screen capture produces black screens on DX11; all video capture MUST use HLAE in-engine streams. |
| **Awpy Demo Parser (`awpy`)** | `v2.0.2` (Polars 1.8.2) | CS2 Demo Protocol 4 / Source 2 | **VERIFIED** | Parse match metadata, rounds, kills, tick coordinates (X, Y, Z), player health, weapons. | Awpy DataFrame columns may omit `time_seconds` on death events; tick-based timing (`tick / tickrate`) must be used as authoritative time. |
| **demoparser2 (`demoparser2`)** | `v0.24.x` (Rust Core) | CS2 Demo Protocol 4 | **VERIFIED** | High-speed parsing (<1.5s), `parse_ticks`, `parse_events`, player view angles (`pitch`, `yaw`). | Requires 64-bit Python 3.8+. Zero-copy memory architecture. |
| **demoinfocs-golang** | `v6.x` / `v5.x` | CS2 Demo Protocol 4 | **EXPERIMENTAL** | Encrypted matchmaking demo decryption, event callbacks, player state machine. | Requires external Go runtime if executed as subprocess. Maintained as secondary fallback backend. |
| **FFmpeg Encoder** | `v9.0.1-essentials` (Gyan build) | Direct3D 11 piped frames | **VERIFIED** | H.264 (libx264) encoding, AAC 320k stereo, NVENC/AMF GPU hardware acceleration, MP4 container muxing. | Must receive standard YUV420p or BGRA streams. 60 FPS and 120 FPS pipelines verified. |
| **DaVinci Resolve Bridge** | DaVinci Resolve Free 21.0+ / Studio | FCPXML 1.9 & Python Scripting API | **VERIFIED** | Multi-track timeline import, marker placement for kills, Fairlight 6-stem audio bus, native Fusion `.setting` presets. | Commercial OFX plugins (Sapphire/Boris) leave watermarks in Free 21.0; all default dem.Toshka presets use 100% native Fusion nodes. |

---

## 2. In-Depth Compatibility Rules & Breakdown

### 2.1 CS2 Demo Tickrate & Coordinate Systems
- **Competitive Matchmaking / Premier:** 64-subtick packet stream recorded at 64 Hz tickrate.
- **FACEIT / Tournament Demos:** 128-tick native packet stream.
- **Rule:** Never assume 64 or 128 tick hardcoded. The parser MUST extract `tickrate` from demo header (`dem.header["tickrate"]`) and calculate exact seconds as:
  $$\text{time\_seconds} = \frac{\text{tick} - \text{start\_tick}}{\text{tickrate}}$$

### 2.2 Valve Source 2 Coordinate Transformation
- Player world coordinates $(X, Y, Z)$ are in Source 2 units (inches).
- Radar conversion:
  $$\text{pixel\_x} = \frac{X - \text{pos\_x}}{\text{scale}}$$
  $$\text{pixel\_y} = \frac{\text{pos\_y} - Y}{\text{scale}}$$
- Map calibration values for `de_dust2`, `de_mirage`, `de_inferno`, `de_nuke`, `de_anubis`, `de_ancient`, `de_vertigo` are verified against Valve's official overview KV3 files.

### 2.3 Breaking Changes in Recent AfxHookSource2 Releases
1. **FFmpeg Escaping:** In `AfxHookSource2 0.42.0+`, FFmpeg convar options require double braces `{{` and `}}` instead of single `{}`.
2. **Backslash Escaping:** `\\` escape is no longer collapsed into a single `\`; single backslashes or forward slashes `/` must be used for file paths.
3. **Template Variables:** New `{AFX_OUTPUT_FILE}` and `{AFX_STREAM_PATH}` tokens must be used for modern stream path resolution.
