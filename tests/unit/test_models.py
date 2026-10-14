"""Unit tests for backend.parser.models.

Tests cover:
- KillEvent derived flags (is_suicide, is_teamkill)
- Edge cases: missing SteamID, bots, same-team kills, self-kills
- ParsedDemo construction with empty collections
- SCHEMA_VERSION is a non-empty string
"""

from __future__ import annotations

import pytest

from backend.parser.models import (
    SCHEMA_VERSION,
    KillEvent,
    ParsedDemo,
    PlayerInfo,
    RoundInfo,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def make_kill(
    *,
    tick: int = 1000,
    round_num: int | None = 1,
    attacker_name: str | None = "Attacker",
    attacker_steam_id: str | None = "76561198000000001",
    attacker_team: str | None = "ct",
    victim_name: str | None = "Victim",
    victim_steam_id: str | None = "76561198000000002",
    victim_team: str | None = "t",
    weapon: str | None = "ak47",
    headshot: bool | None = True,
    hitgroup: str | None = "head",
    noscope: bool | None = False,
    thru_smoke: bool | None = False,
    attacker_blind: bool | None = False,
    wallbang: bool | None = False,
    assister_name: str | None = None,
    assister_steam_id: str | None = None,
) -> KillEvent:
    return KillEvent(
        tick=tick,
        round_num=round_num,
        attacker_name=attacker_name,
        attacker_steam_id=attacker_steam_id,
        attacker_team=attacker_team,
        victim_name=victim_name,
        victim_steam_id=victim_steam_id,
        victim_team=victim_team,
        weapon=weapon,
        headshot=headshot,
        hitgroup=hitgroup,
        noscope=noscope,
        thru_smoke=thru_smoke,
        attacker_blind=attacker_blind,
        wallbang=wallbang,
        assister_name=assister_name,
        assister_steam_id=assister_steam_id,
    )


# ─── KillEvent: is_suicide ────────────────────────────────────────────────────

class TestKillEventSuicide:
    def test_normal_kill_is_not_suicide(self):
        k = make_kill(
            attacker_steam_id="76561198000000001",
            victim_steam_id="76561198000000002",
        )
        assert k.is_suicide is False

    def test_same_steamid_is_suicide(self):
        k = make_kill(
            attacker_steam_id="76561198000000001",
            victim_steam_id="76561198000000001",
        )
        assert k.is_suicide is True

    def test_no_attacker_steamid_not_suicide(self):
        """Missing attacker (world kill e.g. fall damage) — not classified as suicide."""
        k = make_kill(attacker_steam_id=None)
        assert k.is_suicide is False

    def test_no_victim_steamid_not_suicide(self):
        k = make_kill(victim_steam_id=None)
        assert k.is_suicide is False

    def test_both_none_not_suicide(self):
        k = make_kill(attacker_steam_id=None, victim_steam_id=None)
        assert k.is_suicide is False


# ─── KillEvent: is_teamkill ──────────────────────────────────────────────────

class TestKillEventTeamkill:
    def test_normal_cross_team_kill_not_teamkill(self):
        k = make_kill(attacker_team="ct", victim_team="t")
        assert k.is_teamkill is False

    def test_same_team_different_player_is_teamkill(self):
        k = make_kill(
            attacker_steam_id="76561198000000001",
            victim_steam_id="76561198000000002",
            attacker_team="ct",
            victim_team="ct",
        )
        assert k.is_teamkill is True

    def test_suicide_is_not_teamkill(self):
        """A suicide (same player) should NOT be counted as a teamkill."""
        k = make_kill(
            attacker_steam_id="76561198000000001",
            victim_steam_id="76561198000000001",
            attacker_team="t",
            victim_team="t",
        )
        assert k.is_suicide is True
        assert k.is_teamkill is False

    def test_missing_attacker_team_not_teamkill(self):
        k = make_kill(attacker_team=None, victim_team="t")
        assert k.is_teamkill is False

    def test_missing_victim_team_not_teamkill(self):
        k = make_kill(attacker_team="ct", victim_team=None)
        assert k.is_teamkill is False

    def test_bot_kill_no_steamid_not_teamkill(self):
        """Bot may have None SteamID; cross-team kill still not teamkill."""
        k = make_kill(
            attacker_steam_id=None,
            victim_steam_id=None,
            attacker_team="ct",
            victim_team="t",
        )
        assert k.is_teamkill is False


# ─── KillEvent: optional fields ──────────────────────────────────────────────

class TestKillEventOptionalFields:
    def test_all_optional_fields_can_be_none(self):
        k = make_kill(
            headshot=None,
            hitgroup=None,
            noscope=None,
            thru_smoke=None,
            attacker_blind=None,
            wallbang=None,
            assister_name=None,
            assister_steam_id=None,
            round_num=None,
        )
        assert k.headshot is None
        assert k.hitgroup is None
        assert k.noscope is None
        assert k.wallbang is None
        assert k.round_num is None

    def test_round_num_none_for_non_match_tick(self):
        k = make_kill(round_num=None)
        assert k.round_num is None


# ─── ParsedDemo ──────────────────────────────────────────────────────────────

class TestParsedDemo:
    def test_empty_demo_constructs(self):
        demo = ParsedDemo(
            schema_version=SCHEMA_VERSION,
            demo_path="/some/path.dem",
            map_name=None,
            tickrate=128,
            rounds=[],
            players=[],
            kills=[],
        )
        assert demo.schema_version == SCHEMA_VERSION
        assert demo.kills == []
        assert demo.rounds == []
        assert demo.players == []

    def test_schema_version_is_string(self):
        assert isinstance(SCHEMA_VERSION, str)
        assert len(SCHEMA_VERSION) > 0

    def test_demo_with_data(self):
        r = RoundInfo(
            round_num=1,
            start_tick=0,
            freeze_end_tick=128 * 15,
            end_tick=128 * 115,
            official_end_tick=128 * 116,
            winner="ct",
            reason="bomb defused",
            bomb_plant_tick=128 * 80,
            bomb_site="bombsite_a",
        )
        p = PlayerInfo(name="s1mple", steam_id="76561198044045107", team="t")
        k = make_kill()
        demo = ParsedDemo(
            schema_version=SCHEMA_VERSION,
            demo_path="/demo.dem",
            map_name="de_mirage",
            tickrate=128,
            rounds=[r],
            players=[p],
            kills=[k],
        )
        assert len(demo.rounds) == 1
        assert len(demo.players) == 1
        assert len(demo.kills) == 1
        assert demo.map_name == "de_mirage"


# ─── PlayerInfo ──────────────────────────────────────────────────────────────

class TestPlayerInfo:
    def test_bot_has_no_steamid(self):
        bot = PlayerInfo(name="BOT Hans", steam_id=None, team="t")
        assert bot.steam_id is None

    def test_player_fields(self):
        p = PlayerInfo(name="zywoo", steam_id="76561198172878785", team="ct")
        assert p.name == "zywoo"
        assert p.steam_id == "76561198172878785"
        assert p.team == "ct"


# ─── RoundInfo ───────────────────────────────────────────────────────────────

class TestRoundInfo:
    def test_round_construction(self):
        r = RoundInfo(
            round_num=5,
            start_tick=500,
            freeze_end_tick=1500,
            end_tick=15000,
            official_end_tick=15200,
            winner="t",
            reason="target bombed",
            bomb_plant_tick=12000,
            bomb_site="bombsite_b",
        )
        assert r.round_num == 5
        assert r.winner == "t"
        assert r.bomb_site == "bombsite_b"

    def test_round_optional_fields_none(self):
        r = RoundInfo(
            round_num=1,
            start_tick=0,
            freeze_end_tick=None,
            end_tick=1000,
            official_end_tick=None,
            winner=None,
            reason=None,
            bomb_plant_tick=None,
            bomb_site=None,
        )
        assert r.freeze_end_tick is None
        assert r.winner is None
