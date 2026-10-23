"""CS2 User Configuration Backup, Restoration & Anti-Pollution Shield.

Ensures that any convars modified during demo rendering (such as crosshair,
HUD, audio volume, demo UI, X-Ray, binds) are completely prevented from polluting
or overwriting the user's authentic CS2 configuration files.

Multi-Layer Immunity Architecture:
1. Steam Userdata Discovery (Registry + standard paths).
2. Deep Snapshot of both `local/cfg/` and `remote/` directories.
3. Windows Read-Only Attribute Locking during render execution (CS2 cannot write on exit).
4. Timestamp-Bump Restoration on CS2 exit (forces Steam Cloud to accept restored files as freshest).
5. Automatic Autoexec & Console `restore_user.cfg` creation.
"""

from __future__ import annotations

import logging
import os
import pathlib
import shutil
import stat
import tempfile
import time
from typing import Optional

logger = logging.getLogger("demtoshka.cfg_backup")

DEFAULT_STEAM_USERDATA = pathlib.Path(r"C:\Program Files (x86)\Steam\userdata")
DEFAULT_CSGO_CFG_DIR = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"
)


def detect_steam_userdata_dir() -> pathlib.Path:
    """Detect Steam userdata path using Windows Registry or standard paths."""
    # 1. Try Windows Registry (HKCU\Software\Valve\Steam -> SteamPath)
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam_path_str, _ = winreg.QueryValueEx(key, "SteamPath")
            if steam_path_str:
                p = pathlib.Path(steam_path_str) / "userdata"
                if p.is_dir():
                    return p
    except Exception:
        pass

    # 2. Check standard installation directories
    candidates = [
        pathlib.Path(r"C:\Program Files (x86)\Steam\userdata"),
        pathlib.Path(r"C:\Program Files\Steam\userdata"),
        pathlib.Path(r"D:\Steam\userdata"),
        pathlib.Path(r"E:\Steam\userdata"),
    ]
    for c in candidates:
        if c.is_dir():
            return c

    return DEFAULT_STEAM_USERDATA


def detect_csgo_cfg_dir() -> pathlib.Path:
    """Detect Counter-Strike Global Offensive/game/csgo/cfg directory."""
    candidates = [
        pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"),
        pathlib.Path(r"C:\Program Files\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"),
        pathlib.Path(r"D:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"),
        pathlib.Path(r"E:\SteamLibrary\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return DEFAULT_CSGO_CFG_DIR


class ConfigBackupManager:
    """Manages snapshotting, write-protection and restoring CS2 user configuration files."""

    def __init__(
        self,
        userdata_dir: Optional[pathlib.Path] = None,
        csgo_cfg_dir: Optional[pathlib.Path] = None,
        enable_readonly_lock: bool = True,
    ) -> None:
        self.userdata_dir = userdata_dir or detect_steam_userdata_dir()
        self.csgo_cfg_dir = csgo_cfg_dir or detect_csgo_cfg_dir()
        self.enable_readonly_lock = enable_readonly_lock
        self._backup_dir: Optional[pathlib.Path] = None
        # List of (original_file_path, backup_file_path)
        self._tracked_files: list[tuple[pathlib.Path, pathlib.Path]] = []
        self._locked_files: set[pathlib.Path] = set()

    def backup(self) -> int:
        """Create a snapshot of all user CS2 config files and apply Read-Only protection.

        Returns the number of backed up files.
        """
        self._backup_dir = pathlib.Path(tempfile.mkdtemp(prefix="demtoshka_cfg_backup_"))
        self._tracked_files.clear()
        self._locked_files.clear()

        # 1. Backup all user configs in Steam userdata/*/730/local/cfg/ and userdata/*/730/remote/
        if self.userdata_dir.exists():
            for user_dir in self.userdata_dir.iterdir():
                if not user_dir.is_dir() or not user_dir.name.isdigit():
                    continue

                # 1a. local/cfg/
                cs2_local_cfg = user_dir / "730" / "local" / "cfg"
                if cs2_local_cfg.is_dir():
                    for cfg_file in cs2_local_cfg.glob("*.vcfg"):
                        if cfg_file.is_file():
                            self._track_and_copy(user_dir.name, "local_cfg", cfg_file)
                    for txt_file in cs2_local_cfg.glob("*.txt"):
                        if txt_file.is_file():
                            self._track_and_copy(user_dir.name, "local_cfg", txt_file)

                # 1b. remote/
                cs2_remote = user_dir / "730" / "remote"
                if cs2_remote.is_dir():
                    for cfg_file in cs2_remote.glob("*.vcfg"):
                        if cfg_file.is_file():
                            self._track_and_copy(user_dir.name, "remote", cfg_file)
                    remote_cfg = cs2_remote / "cfg"
                    if remote_cfg.is_dir():
                        for cfg_file in remote_cfg.glob("*.txt"):
                            if cfg_file.is_file():
                                self._track_and_copy(user_dir.name, "remote_cfg", cfg_file)

        # 2. Backup autoexec.cfg and restore_user.cfg in game/csgo/cfg/ if present
        if self.csgo_cfg_dir.exists():
            for cfg_name in ("autoexec.cfg", "restore_user.cfg"):
                cfg_path = self.csgo_cfg_dir / cfg_name
                if cfg_path.is_file():
                    dest = self._backup_dir / f"csgo_{cfg_name}"
                    try:
                        shutil.copy2(cfg_path, dest)
                        self._tracked_files.append((cfg_path, dest))
                    except Exception as e:
                        logger.warning("Could not backup %s: %s", cfg_name, e)

        # 3. Apply Read-Only file lock on Windows so CS2 cannot overwrite on shutdown
        if self.enable_readonly_lock:
            self.lock_readonly()

        logger.info(
            "Backed up %d CS2 configuration file(s) to %s (Read-Only locked: %d)",
            len(self._tracked_files),
            self._backup_dir,
            len(self._locked_files),
        )
        return len(self._tracked_files)

    def _track_and_copy(self, user_id: str, group: str, source_file: pathlib.Path) -> None:
        assert self._backup_dir is not None
        dest_filename = f"{user_id}_{group}_{source_file.name}"
        dest = self._backup_dir / dest_filename
        try:
            shutil.copy2(source_file, dest)
            self._tracked_files.append((source_file, dest))
        except Exception as e:
            logger.warning("Could not backup %s: %s", source_file, e)

    def lock_readonly(self) -> None:
        """Mark all tracked CS2 config files as read-only.

        When CS2 exits, Windows will reject all write operations with ERROR_ACCESS_DENIED,
        preventing in-engine session convars from polluting disk.
        """
        for original_file, _ in self._tracked_files:
            if original_file.is_file():
                try:
                    # Windows read-only flag
                    os.chmod(original_file, stat.S_IREAD)
                    self._locked_files.add(original_file)
                except Exception as e:
                    logger.debug("Failed to set read-only on %s: %s", original_file, e)

    def unlock_readonly(self) -> None:
        """Restore normal write permissions on all locked files."""
        for locked_file in list(self._locked_files):
            if locked_file.exists():
                try:
                    os.chmod(locked_file, stat.S_IWRITE | stat.S_IREAD)
                except Exception as e:
                    logger.debug("Failed to unlock %s: %s", locked_file, e)
        self._locked_files.clear()

        # Also ensure all tracked files have write permissions
        for original_file, _ in self._tracked_files:
            if original_file.exists():
                try:
                    os.chmod(original_file, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass

    def restore(self) -> int:
        """Restore all tracked configuration files to their original locations.

        Bumps modification timestamps so Steam Cloud treats restored files as freshest.
        Returns the number of restored files.
        """
        if not self._backup_dir or not self._tracked_files:
            logger.debug("No active config backup to restore")
            return 0

        # 1. Remove Read-Only locks first
        self.unlock_readonly()

        # 2. Restore files and update timestamp
        restored_count = 0
        future_time = time.time() + 5.0  # slightly in the future to ensure Steam Cloud sees it as newer

        for original_file, backup_file in self._tracked_files:
            if backup_file.is_file():
                try:
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    # Remove read-only if it was set
                    if original_file.exists():
                        try:
                            os.chmod(original_file, stat.S_IWRITE | stat.S_IREAD)
                        except Exception:
                            pass
                    shutil.copy2(backup_file, original_file)
                    # Bump mtime so Steam Cloud recognizes local changes as freshest
                    try:
                        os.utime(original_file, (future_time, future_time))
                    except Exception:
                        pass
                    restored_count += 1
                except Exception as e:
                    logger.error("Failed to restore %s from %s: %s", original_file, backup_file, e)

        # 3. Clean up temporary backup directory
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


def restore_user_gameplay_config() -> dict[str, int | str | bool]:
    """1-Click Restoration of clean user gameplay settings.

    Restores:
    - User keybindings (removes all demo recording binds)
    - Radar convars (rotating, centered, 0.7 scale)
    - autoexec.cfg and restore_user.cfg in game/csgo/cfg/
    - Updates mtimes for Steam Cloud synchronization.
    """
    userdata_dir = detect_steam_userdata_dir()
    csgo_cfg_dir = detect_csgo_cfg_dir()
    restored_files = 0

    # 1. Remove demo binds from all user keys files
    clean_bindings = (
        '"config"\n'
        '{\n'
        '\t"bindings"\n'
        '\t{\n'
        '\t\t"6"\t\t"<unbound>"\n'
        '\t\t"x"\t\t"slot6"\n'
        '\t\t"4"\t\t"slot7"\n'
        '\t\t"7"\t\t"<unbound>"\n'
        '\t\t"8"\t\t"<unbound>"\n'
        '\t\t"z"\t\t"slot8"\n'
        '\t\t"0"\t\t"<unbound>"\n'
        '\t\t"c"\t\t"+duck"\n'
        '\t\t"MOUSE4"\t\t"<unbound>"\n'
        '\t\t"MOUSE5"\t\t"+voicerecord"\n'
        '\t\t"n"\t\t"noclip"\n'
        '\t\t"MWHEELUP"\t\t"+jump"\n'
        '\t\t"MWHEELDOWN"\t\t"+jump"\n'
        '\t\t"v"\t\t"<unbound>"\n'
        '\t\t"CTRL"\t\t"slot10"\n'
        '\t\t"]"\t\t"slot4"\n'
        '\t\t"SHIFT"\t\t"+sprint"\n'
        '\t\t"MOUSE3"\t\t"player_ping"\n'
        '\t\t"MOUSE1"\t\t"+attack"\n'
        '\t\t"SPACE"\t\t"+jump"\n'
        '\t\t"/"\t\t"radio"\n'
        '\t\t"h"\t\t"switchhands"\n'
        '\t\t"ALT"\t\t"+speed_mouse"\n'
        '\t\t"F1"\t\t"vote option1"\n'
        '\t\t"F3"\t\t"autobuy"\n'
        '\t\t"F4"\t\t"<unbound>"\n'
        '\t\t"l"\t\t"say ☠"\n'
        '\t\t"CAPSLOCK"\t\t"incrementvar cl_radar_scale 0.25 1 0.75"\n'
        '\t}\n'
        '}\n'
    )

    clean_cfg_text = (
        "// ====================================================================\n"
        "// CS2 Highlights Studio — Clean User Gameplay Configuration\n"
        "// Restores standard competitive settings, radar, audio, and player binds\n"
        "// Usage in CS2 console: exec restore_user\n"
        "// ====================================================================\n\n"
        "// --- 1. MOUSE & SENSITIVITY ---\n"
        "sensitivity 1.44\n"
        "zoom_sensitivity_ratio 1.0\n"
        "m_pitch 0.022\n"
        "m_yaw 0.022\n\n"
        "// --- 2. VIEWMODEL (User Settings) ---\n"
        "viewmodel_fov 68\n"
        "viewmodel_offset_x 2.5\n"
        "viewmodel_offset_y 0\n"
        "viewmodel_offset_z -1.5\n"
        "cl_prefer_lefthanded 0\n\n"
        "// --- 3. RADAR & MINIMAP (Standard Competitive Rotating Radar) ---\n"
        "cl_radar_always_centered 1\n"
        "cl_radar_rotate 1\n"
        "cl_radar_scale 0.70\n"
        "cl_hud_radar_scale 1.05\n"
        "cl_radar_icon_scale_min 0.70\n"
        "cl_radar_square_when_spectating 0\n"
        "cl_radar_square_always 0\n"
        "cl_radar_square_with_scoreboard 1\n\n"
        "// --- 4. HUD & DISPLAY ---\n"
        "cl_drawhud 1\n"
        "cl_draw_only_deathnotices 0\n"
        "hud_showtargetid 1\n"
        "hud_scaling 0.95\n"
        "safezonex 0.88\n"
        "safezoney 0.80\n"
        "fps_max 400\n"
        "fps_max_ui 144\n\n"
        "// --- 5. AUDIO ---\n"
        "volume 0.25\n"
        "snd_gamevolume 1.0\n"
        "snd_gamevoicevolume 1.0\n"
        "snd_voipvolume 1.0\n"
        "snd_menumusic_volume 0.0\n"
        "snd_roundstart_volume 0.0\n"
        "snd_roundaction_volume 0.0\n"
        "snd_roundend_volume 0.16\n"
        "snd_mvp_volume 0.16\n"
        "snd_mapobjective_volume 0.04\n"
        "snd_tensecondwarning_volume 0.04\n"
        "snd_deathcamera_volume 0.16\n"
        "snd_mute_losefocus 0\n\n"
        "// --- 6. USER CUSTOM KEYBINDS ---\n"
        'bind "MWHEELUP" "+jump"\n'
        'bind "MWHEELDOWN" "+jump"\n'
        'bind "SPACE" "+jump"\n'
        'bind "c" "+duck"\n'
        'bind "SHIFT" "+sprint"\n'
        'bind "MOUSE1" "+attack"\n'
        'bind "MOUSE3" "player_ping"\n'
        'bind "MOUSE5" "+voicerecord"\n\n'
        '// Grenade Quick Binds\n'
        'bind "x" "slot6"       // HE Grenade\n'
        'bind "4" "slot7"       // Flashbang\n'
        'bind "z" "slot8"       // Smoke\n'
        'bind "CTRL" "slot10"   // Molotov / Incendiary\n'
        'bind "]" "slot4"       // Cycle Grenades\n\n'
        '// Tactical Binds\n'
        'bind "h" "switchhands"\n'
        'bind "n" "noclip"\n'
        'bind "l" "say ☠"\n'
        'bind "CAPSLOCK" "incrementvar cl_radar_scale 0.25 1 0.75"\n\n'
        "// --- 7. CLEAN UP DEMO RECORDING BINDS ---\n"
        'unbind "i"\n'
        'unbind "o"\n'
        'unbind "p"\n'
        'unbind "UPARROW"\n'
        'unbind "LEFTARROW"\n'
        'unbind "DOWNARROW"\n'
        'unbind "RIGHTARROW"\n'
        'unbind "F2"\n'
        'unbind "F5"\n'
        'unbind "F6"\n'
        'unbind "F7"\n'
        'unbind "F8"\n\n'
        "// Persist to local steam profile\n"
        "host_writeconfig\n\n"
        'echo ">>> [dem.Toshka] User CS2 Config Successfully Applied! <<<"\n'
    )

    future_time = time.time() + 5.0

    if userdata_dir.exists():
        for user_dir in userdata_dir.iterdir():
            if not user_dir.is_dir() or not user_dir.name.isdigit():
                continue

            # Clean keys in local/cfg
            local_cfg = user_dir / "730" / "local" / "cfg"
            if local_cfg.is_dir():
                for key_file in local_cfg.glob("cs2_user_keys*.vcfg"):
                    try:
                        os.chmod(key_file, stat.S_IWRITE | stat.S_IREAD)
                        key_file.write_text(clean_bindings, encoding="utf-8")
                        os.utime(key_file, (future_time, future_time))
                        restored_files += 1
                    except Exception as e:
                        logger.warning("Could not rewrite %s: %s", key_file, e)

                # Reset radar in cs2_machine_convars.vcfg
                machine_cfg = local_cfg / "cs2_machine_convars.vcfg"
                if machine_cfg.is_file():
                    try:
                        content = machine_cfg.read_text(encoding="utf-8")
                        content = content.replace(
                            '"cl_radar_always_centered"\t\t"false"',
                            '"cl_radar_always_centered"\t\t"true"',
                        )
                        content = content.replace(
                            '"cl_radar_rotate"\t\t"false"',
                            '"cl_radar_rotate"\t\t"true"',
                        )
                        content = content.replace(
                            '"cl_radar_scale"\t\t"0.25"',
                            '"cl_radar_scale"\t\t"0.7"',
                        )
                        content = content.replace(
                            '"cl_radar_square_with_scoreboard"\t\t"false"',
                            '"cl_radar_square_with_scoreboard"\t\t"true"',
                        )
                        os.chmod(machine_cfg, stat.S_IWRITE | stat.S_IREAD)
                        machine_cfg.write_text(content, encoding="utf-8")
                        os.utime(machine_cfg, (future_time, future_time))
                        restored_files += 1
                    except Exception as e:
                        logger.warning("Could not patch %s: %s", machine_cfg, e)

            # Clean keys in remote/
            remote_dir = user_dir / "730" / "remote"
            if remote_dir.is_dir():
                for key_file in remote_dir.glob("cs2_user_keys*.vcfg"):
                    try:
                        os.chmod(key_file, stat.S_IWRITE | stat.S_IREAD)
                        key_file.write_text(clean_bindings, encoding="utf-8")
                        os.utime(key_file, (future_time, future_time))
                        restored_files += 1
                    except Exception as e:
                        logger.warning("Could not rewrite remote %s: %s", key_file, e)

    # 2. Write autoexec.cfg and restore_user.cfg in game/csgo/cfg/
    if csgo_cfg_dir.exists():
        for filename in ("autoexec.cfg", "restore_user.cfg"):
            target = csgo_cfg_dir / filename
            try:
                if target.exists():
                    os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
                target.write_text(clean_cfg_text, encoding="utf-8")
                os.utime(target, (future_time, future_time))
                restored_files += 1
            except Exception as e:
                logger.warning("Could not write %s: %s", target, e)

    return {
        "success": True,
        "restored_files_count": restored_files,
        "message": f"Конфиг CS2 успешно восстановлен ({restored_files} файлов). Radar, Binds и Audio приведены в боевой режим. Доступна команда 'exec restore_user' в консоли.",
    }
