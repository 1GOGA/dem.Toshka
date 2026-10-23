"""Configuration paths and defaults for CS2 Video Rendering."""

from __future__ import annotations

import pathlib
import sys

_file_root = pathlib.Path(__file__).resolve().parent.parent.parent
if getattr(sys, "frozen", False):
    _exe_root = pathlib.Path(sys.executable).resolve().parent
    if (_exe_root / "tools" / "hlae").exists():
        REPO_ROOT = _exe_root
    elif (_exe_root / "_internal" / "tools" / "hlae").exists():
        REPO_ROOT = _exe_root / "_internal"
    else:
        REPO_ROOT = _file_root
else:
    REPO_ROOT = _file_root

DEFAULT_CS2_EXE = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe"
)

DEFAULT_CSGO_DIR = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo"
)

DEFAULT_CFG_DIR = DEFAULT_CSGO_DIR / "cfg"

DEFAULT_HLAE_EXE = REPO_ROOT / "tools" / "hlae" / "HLAE.exe"
DEFAULT_HOOK_DLL = REPO_ROOT / "tools" / "hlae" / "x64" / "AfxHookSource2.dll"

_local_ffmpeg = REPO_ROOT / "tools" / "hlae" / "ffmpeg" / "bin" / "ffmpeg.exe"
_local_ffprobe = REPO_ROOT / "tools" / "hlae" / "ffmpeg" / "bin" / "ffprobe.exe"
FFMPEG_BIN = str(_local_ffmpeg) if _local_ffmpeg.exists() else "ffmpeg"
FFPROBE_BIN = str(_local_ffprobe) if _local_ffprobe.exists() else "ffprobe"


def ensure_hlae_ffmpeg_ini() -> None:
    """Ensure HLAE's ffmpeg.ini points to the valid ffmpeg.exe binary."""
    if _local_ffmpeg.exists():
        ini_path = REPO_ROOT / "tools" / "hlae" / "ffmpeg" / "ffmpeg.ini"
        content = f"[Ffmpeg]\nPath={_local_ffmpeg.resolve()}\n"
        try:
            if not ini_path.exists() or ini_path.read_text(encoding="utf-8").strip() != content.strip():
                ini_path.parent.mkdir(parents=True, exist_ok=True)
                ini_path.write_text(content, encoding="utf-8")
        except Exception:
            pass


ensure_hlae_ffmpeg_ini()

RENDER_OUTPUT_DIR = REPO_ROOT / "renders"

DEFAULT_WATERMARK_PNG = REPO_ROOT / "logo_video.png"
