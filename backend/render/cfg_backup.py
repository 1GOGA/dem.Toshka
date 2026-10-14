"""CS2 User Configuration Backup & Restore Manager.

Ensures that any convars modified during demo rendering (such as crosshair,
HUD, audio volume, demo UI, X-Ray) are reliably restored to the user's original
settings when the rendering session finishes.
"""

from __future__ import annotations

import logging
import pathlib
import shutil
import tempfile
from typing import Optional

logger = logging.getLogger("demtoshka.cfg_backup")

DEFAULT_STEAM_USERDATA = pathlib.Path(r"C:\Program Files (x86)\Steam\userdata")
DEFAULT_CSGO_CFG_DIR = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"
)


class ConfigBackupManager:
    """Manages snapshotting and restoring CS2 user configuration files."""

    def __init__(
        self,
        userdata_dir: pathlib.Path = DEFAULT_STEAM_USERDATA,
        csgo_cfg_dir: pathlib.Path = DEFAULT_CSGO_CFG_DIR,
    ) -> None:
        self.userdata_dir = userdata_dir
        self.csgo_cfg_dir = csgo_cfg_dir
        self._backup_dir: Optional[pathlib.Path] = None
        self._tracked_files: list[tuple[pathlib.Path, pathlib.Path]] = []

    def backup(self) -> int:
        """Create a snapshot of all user CS2 config files.

        Returns the number of backed up files.
        """
        self._backup_dir = pathlib.Path(tempfile.mkdtemp(prefix="demtoshka_cfg_backup_"))
        self._tracked_files.clear()

        # 1. Backup all user configs in Steam userdata/*/730/local/cfg/
        if self.userdata_dir.exists():
            for user_dir in self.userdata_dir.iterdir():
                if not user_dir.is_dir() or not user_dir.name.isdigit():
                    continue
                cs2_cfg_dir = user_dir / "730" / "local" / "cfg"
                if cs2_cfg_dir.is_dir():
                    for cfg_file in cs2_cfg_dir.glob("*"):
                        if cfg_file.is_file():
                            rel_sub = f"user_{user_dir.name}_{cfg_file.name}"
                            dest = self._backup_dir / rel_sub
                            try:
                                shutil.copy2(cfg_file, dest)
                                self._tracked_files.append((cfg_file, dest))
                            except Exception as e:
                                logger.warning("Could not backup %s: %s", cfg_file, e)

        # 2. Backup autoexec.cfg in game/csgo/cfg/ if present
        if self.csgo_cfg_dir.exists():
            autoexec = self.csgo_cfg_dir / "autoexec.cfg"
            if autoexec.is_file():
                dest = self._backup_dir / "autoexec.cfg"
                try:
                    shutil.copy2(autoexec, dest)
                    self._tracked_files.append((autoexec, dest))
                except Exception as e:
                    logger.warning("Could not backup autoexec.cfg: %s", e)

        logger.info(
            "Backed up %d CS2 user configuration file(s) to %s",
            len(self._tracked_files),
            self._backup_dir,
        )
        return len(self._tracked_files)

    def restore(self) -> int:
        """Restore all tracked configuration files to their original locations.

        Returns the number of restored files.
        """
        if not self._backup_dir or not self._tracked_files:
            logger.debug("No active config backup to restore")
            return 0

        restored_count = 0
        for original_file, backup_file in self._tracked_files:
            if backup_file.is_file():
                try:
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_file, original_file)
                    restored_count += 1
                except Exception as e:
                    logger.error("Failed to restore %s from %s: %s", original_file, backup_file, e)

        # Remove temporary backup directory
        if self._backup_dir.exists():
            shutil.rmtree(self._backup_dir, ignore_errors=True)
        self._backup_dir = None
        self._tracked_files.clear()

        logger.info("Successfully restored %d CS2 user config file(s)", restored_count)
        return restored_count

    def __enter__(self) -> ConfigBackupManager:
        self.backup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.restore()

