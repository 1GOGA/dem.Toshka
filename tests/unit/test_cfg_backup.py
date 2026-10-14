"""Unit tests for CS2 Config Backup & Restoration Manager."""

from __future__ import annotations

import pathlib
import pytest

from backend.render.cfg_backup import ConfigBackupManager


class TestConfigBackupManager:
    def test_backup_and_restore_cycle(self, tmp_path):
        # Create fake Steam userdata structure
        userdata_dir = tmp_path / "userdata"
        user1 = userdata_dir / "123456" / "730" / "local" / "cfg"
        user1.mkdir(parents=True)
        cs2_user_cfg = user1 / "cs2_user_keys.vcfg"
        cs2_user_cfg.write_text('"config" { "bind" "mouse1" "+attack" }', encoding="utf-8")

        # Create fake game csgo cfg
        game_cfg_dir = tmp_path / "game" / "csgo" / "cfg"
        game_cfg_dir.mkdir(parents=True)
        autoexec = game_cfg_dir / "autoexec.cfg"
        autoexec.write_text('echo "my custom autoexec"', encoding="utf-8")

        # Pass custom directories
        manager = ConfigBackupManager(userdata_dir=userdata_dir, csgo_cfg_dir=game_cfg_dir)
        
        # Test backup
        count = manager.backup()
        assert count == 2
        assert len(manager._tracked_files) == 2

        # Simulate CS2 / HLAE modifying or deleting user files
        cs2_user_cfg.write_text('"config" { "OVERWRITTEN" "1" }', encoding="utf-8")
        autoexec.unlink()  # File deleted

        # Restore
        restored_count = manager.restore()
        assert restored_count == 2
        assert cs2_user_cfg.read_text(encoding="utf-8") == '"config" { "bind" "mouse1" "+attack" }'
        assert autoexec.exists()
        assert autoexec.read_text(encoding="utf-8") == 'echo "my custom autoexec"'
        assert manager._backup_dir is None

    def test_context_manager_restores_on_exception(self, tmp_path):
        userdata_dir = tmp_path / "userdata"
        user1 = userdata_dir / "999" / "730" / "local" / "cfg"
        user1.mkdir(parents=True)
        cfg_file = user1 / "cs2_machine_convars.vcfg"
        cfg_file.write_text("volume 0.5", encoding="utf-8")

        manager = ConfigBackupManager(userdata_dir=userdata_dir, csgo_cfg_dir=tmp_path)

        with pytest.raises(RuntimeError, match="Simulated crash"):
            with manager:
                cfg_file.write_text("volume 1.0 (corrupted)", encoding="utf-8")
                raise RuntimeError("Simulated crash")

        # Must be restored back to volume 0.5
        assert cfg_file.read_text(encoding="utf-8") == "volume 0.5"

    def test_backup_handles_missing_paths_gracefully(self, tmp_path):
        nonexistent = tmp_path / "nonexistent_steam"
        manager = ConfigBackupManager(userdata_dir=nonexistent, csgo_cfg_dir=nonexistent)
        count = manager.backup()
        assert count == 0
        restored = manager.restore()
        assert restored == 0

