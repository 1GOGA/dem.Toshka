"""Configuration paths and defaults for CS2 Video Rendering."""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

DEFAULT_CS2_EXE = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
)

DEFAULT_CSGO_DIR = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo"
)

DEFAULT_CFG_DIR = DEFAULT_CSGO_DIR / "cfg"

DEFAULT_HLAE_EXE = REPO_ROOT / "tools" / "hlae" / "HLAE.exe"
DEFAULT_HOOK_DLL = REPO_ROOT / "tools" / "hlae" / "x64" / "AfxHookSource2.dll"

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

RENDER_OUTPUT_DIR = REPO_ROOT / "renders"
