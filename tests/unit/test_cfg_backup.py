"""Unit tests for CS2 Config Backup & Restoration Manager."""

from __future__ import annotations

import os
import pathlib
import stat
import pytest

from backend.render.cfg_backup import ConfigBackupManager, restore_user_gameplay_config


class TestConfigBackupManager:
    def test_readonly_locking_prevents_file_overwrite(self, tmp_path):
        """Verifies that Read-Only locking blocks writes on Windows and restore() unlocks them."""
        userdata_dir = tmp_path / "userdata"
        user1 = userdata_dir / "123456" / "730" / "local" / "cfg"
        user1.mkdir(parents=True)
        cs2_user_cfg = user1 / "cs2_user_keys_0_slot0.vcfg"
        cs2_user_cfg.write_text('"config" { "bind" "space" "+jump" }', encoding="utf-8")

        game_cfg_dir = tmp_path / "game" / "csgo" / "cfg"
        game_cfg_dir.mkdir(parents=True)
        autoexec = game_cfg_dir / "autoexec.cfg"
        autoexec.write_text('echo "my autoexec"', encoding="utf-8")

        manager = ConfigBackupManager(
            userdata_dir=userdata_dir,
            csgo_cfg_dir=game_cfg_dir,
            enable_readonly_lock=True,
        )

        # 1. Backup and lock
        count = manager.backup()
        assert count == 2

        # 2. Writing to read-only file should fail with PermissionError on Windows
        with pytest.raises(PermissionError):
            cs2_user_cfg.write_text('"config" { "corrupted" "1" }', encoding="utf-8")

        # 3. Restore unlocks files and brings them back to writable state
        restored = manager.restore()
        assert restored == 2

        # File is now writable again and original contents are intact
        cs2_user_cfg.write_text('"config" { "bind" "space" "+jump" }', encoding="utf-8")
        assert cs2_user_cfg.read_text(encoding="utf-8") == '"config" { "bind" "space" "+jump" }'
        assert autoexec.read_text(encoding="utf-8") == 'echo "my autoexec"'

    def test_backup_and_restore_cycle_unlocked(self, tmp_path):
        """Verifies full restore cycle when files are modified."""
        userdata_dir = tmp_path / "userdata"
        user1_local = userdata_dir / "123456" / "730" / "local" / "cfg"
        user1_local.mkdir(parents=True)
        local_cfg = user1_local / "cs2_user_keys_0_slot0.vcfg"
        local_cfg.write_text('"config" { "bind" "mouse1" "+attack" }', encoding="utf-8")

        user1_remote = userdata_dir / "123456" / "730" / "remote"
        user1_remote.mkdir(parents=True)
        remote_cfg = user1_remote / "cs2_user_keys.vcfg"
        remote_cfg.write_text('"config" { "bind" "mouse1" "+attack" }', encoding="utf-8")

        game_cfg_dir = tmp_path / "game" / "csgo" / "cfg"
        game_cfg_dir.mkdir(parents=True)
        autoexec = game_cfg_dir / "autoexec.cfg"
        autoexec.write_text('echo "original autoexec"', encoding="utf-8")

        manager = ConfigBackupManager(
            userdata_dir=userdata_dir,
            csgo_cfg_dir=game_cfg_dir,
            enable_readonly_lock=False,
        )

        count = manager.backup()
        assert count == 3

        # Simulate modifications
        local_cfg.write_text('"config" { "corrupted" "1" }', encoding="utf-8")
        remote_cfg.write_text('"config" { "corrupted" "1" }', encoding="utf-8")
        autoexec.unlink()

        restored_count = manager.restore()
        assert restored_count == 3
        assert local_cfg.read_text(encoding="utf-8") == '"config" { "bind" "mouse1" "+attack" }'
        assert remote_cfg.read_text(encoding="utf-8") == '"config" { "bind" "mouse1" "+attack" }'
        assert autoexec.exists()
        assert autoexec.read_text(encoding="utf-8") == 'echo "original autoexec"'
        assert manager._backup_dir is None

    def test_context_manager_restores_on_exception(self, tmp_path):
        userdata_dir = tmp_path / "userdata"
        user1 = userdata_dir / "999" / "730" / "local" / "cfg"
        user1.mkdir(parents=True)
        cfg_file = user1 / "cs2_machine_convars.vcfg"
        cfg_file.write_text("volume 0.5", encoding="utf-8")

        manager = ConfigBackupManager(
            userdata_dir=userdata_dir,
            csgo_cfg_dir=tmp_path,
            enable_readonly_lock=False,
        )

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

    def test_restore_user_gameplay_config(self, tmp_path, monkeypatch):
        fake_userdata = tmp_path / "userdata"
        user_cfg = fake_userdata / "123" / "730" / "local" / "cfg"
        user_cfg.mkdir(parents=True)
        keys_file = user_cfg / "cs2_user_keys_0_slot0.vcfg"
        keys_file.write_text('"config" { "bindings" { "i" "demo_gototick" } }', encoding="utf-8")
        machine_file = user_cfg / "cs2_machine_convars.vcfg"
        machine_file.write_text(
            '"cl_radar_always_centered"\t\t"false"\n"cl_radar_rotate"\t\t"false"\n"cl_radar_scale"\t\t"0.25"',
            encoding="utf-8",
        )

        fake_game_cfg = tmp_path / "game" / "csgo" / "cfg"
        fake_game_cfg.mkdir(parents=True)

        monkeypatch.setattr("backend.render.cfg_backup.detect_steam_userdata_dir", lambda: fake_userdata)
        monkeypatch.setattr("backend.render.cfg_backup.detect_csgo_cfg_dir", lambda: fake_game_cfg)

        res = restore_user_gameplay_config()
        assert res["success"] is True
        assert res["restored_files_count"] >= 3

        # Keys should no longer have demo_gototick
        assert "demo_gototick" not in keys_file.read_text(encoding="utf-8")
        assert "slot6" in keys_file.read_text(encoding="utf-8")

        # Machine convars should have true for radar
        machine_text = machine_file.read_text(encoding="utf-8")
        assert '"cl_radar_always_centered"\t\t"true"' in machine_text
        assert '"cl_radar_rotate"\t\t"true"' in machine_text

        # autoexec and restore_user should exist in game cfg
        assert (fake_game_cfg / "autoexec.cfg").is_file()
        assert (fake_game_cfg / "restore_user.cfg").is_file()

