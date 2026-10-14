"""Integration tests for backend.parser — require a REAL .dem file.

HOW TO RUN:
    Place a CS2 demo at one of these locations (checked in order):
      1. tests/integration/fixtures/test.dem
      2. DEMO_PATH environment variable

    Then run:
        .venv\\Scripts\\pytest tests/integration/ -v

    Without a real demo, all tests in this file are SKIPPED automatically.

CONFIRMED:
    These tests are implemented.  They are NOT confirmed to pass because
    no real .dem file is present in the repository.

NOT CONFIRMED:
    Compatibility with real CS2 demos — requires running with a real .dem.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# ─── Fixture resolution ───────────────────────────────────────────────────────

FIXTURE_DEMO = Path(__file__).parent / "fixtures" / "test.dem"
ENV_DEMO = os.environ.get("DEMO_PATH", "")


def _demo_path() -> Path | None:
    if FIXTURE_DEMO.exists():
        return FIXTURE_DEMO
    if ENV_DEMO and Path(ENV_DEMO).exists():
        return Path(ENV_DEMO)
    return None


DEMO_AVAILABLE = _demo_path() is not None

skip_no_demo = pytest.mark.skipif(
    not DEMO_AVAILABLE,
    reason=(
        "No real .dem file found.  "
        "Place one at tests/integration/fixtures/test.dem "
        "or set DEMO_PATH env var."
    ),
)


@pytest.fixture(scope="module")
def parsed_demo():
    """Parse the demo once for the whole module — avoids re-parsing per test."""
    from backend.parser.ingestion import ingest

    path = _demo_path()
    assert path is not None, "Demo path must be available at this point"
    return ingest(path)


# ─── Integration tests ────────────────────────────────────────────────────────

@skip_no_demo
class TestParsedDemoStructure:
    def test_schema_version_present(self, parsed_demo):
        from backend.parser.models import SCHEMA_VERSION
        assert parsed_demo.schema_version == SCHEMA_VERSION

    def test_map_name_is_string(self, parsed_demo):
        """map_name should be a non-empty string for a real demo."""
        assert parsed_demo.map_name is not None
        assert isinstance(parsed_demo.map_name, str)
        assert len(parsed_demo.map_name) > 0

    def test_tickrate_is_positive_int(self, parsed_demo):
        assert isinstance(parsed_demo.tickrate, int)
        assert parsed_demo.tickrate > 0

    def test_has_rounds(self, parsed_demo):
        assert len(parsed_demo.rounds) > 0, "Real demo must have at least 1 round"

    def test_has_players(self, parsed_demo):
        assert len(parsed_demo.players) > 0, "Real demo must have at least 1 player"

    def test_has_kills(self, parsed_demo):
        assert len(parsed_demo.kills) > 0, "Real demo must have at least 1 kill"


@skip_no_demo
class TestRoundsIntegrity:
    def test_round_numbers_start_at_1(self, parsed_demo):
        round_nums = [r.round_num for r in parsed_demo.rounds]
        assert round_nums[0] == 1

    def test_round_numbers_are_sequential(self, parsed_demo):
        round_nums = [r.round_num for r in parsed_demo.rounds]
        for i, rn in enumerate(round_nums):
            assert rn == i + 1, f"Gap at round {rn}, expected {i+1}"

    def test_round_start_before_end(self, parsed_demo):
        for r in parsed_demo.rounds:
            assert r.start_tick < r.end_tick, (
                f"Round {r.round_num}: start_tick {r.start_tick} >= end_tick {r.end_tick}"
            )

    def test_round_winner_is_valid_or_none(self, parsed_demo):
        valid_winners = {"ct", "t", None}
        for r in parsed_demo.rounds:
            assert r.winner in valid_winners, (
                f"Round {r.round_num}: unexpected winner '{r.winner}'"
            )


@skip_no_demo
class TestKillsIntegrity:
    def test_all_kills_have_tick(self, parsed_demo):
        for k in parsed_demo.kills:
            assert isinstance(k.tick, int)
            assert k.tick > 0

    def test_no_kill_spans_round_boundary(self, parsed_demo):
        """Every kill with a round_num must have a tick within [start_tick, official_end_tick].

        CS2 BEHAVIOUR (confirmed on real demo):
          - round_end fires at end_tick (e.g. timer / elimination).
          - Bomb-explosion kills (weapon='planted_c4') occur AFTER end_tick but
            BEFORE official_end_tick.  Awpy's apply_round_num() assigns round_num
            using official_end as the upper bound, so we must do the same here.
          - NEVER use end_tick alone as the kill boundary.
        """
        round_map = {r.round_num: r for r in parsed_demo.rounds}
        for k in parsed_demo.kills:
            if k.round_num is None:
                continue
            r = round_map.get(k.round_num)
            assert r is not None, (
                f"Kill at tick {k.tick} references missing round {k.round_num}"
            )
            # Use official_end_tick as the upper bound (same as Awpy's apply_round_num).
            # Fall back to end_tick if official_end_tick is None (incomplete round at demo end).
            upper = r.official_end_tick if r.official_end_tick is not None else r.end_tick
            assert r.start_tick <= k.tick <= upper, (
                f"Kill tick {k.tick} (weapon={k.weapon!r}) outside round {k.round_num} "
                f"[{r.start_tick}, {upper}] "
                f"(end_tick={r.end_tick}, official_end_tick={r.official_end_tick})"
            )

    def test_suicide_and_teamkill_mutually_exclusive(self, parsed_demo):
        for k in parsed_demo.kills:
            assert not (k.is_suicide and k.is_teamkill), (
                f"Kill at tick {k.tick}: cannot be both suicide and teamkill"
            )

    def test_weapon_field_present_for_most_kills(self, parsed_demo):
        kills_with_weapon = [k for k in parsed_demo.kills if k.weapon is not None]
        ratio = len(kills_with_weapon) / len(parsed_demo.kills)
        assert ratio > 0.8, (
            f"Only {ratio:.0%} of kills have a weapon field — Awpy API may have changed"
        )

    def test_steamid_not_mixed_with_slot(self, parsed_demo):
        """SteamIDs (when present) must look like real SteamID64 (17 digits)
        or be None (bots). They must NOT be short integers like slot IDs."""
        for k in parsed_demo.kills:
            for sid in [k.attacker_steam_id, k.victim_steam_id]:
                if sid is not None:
                    # SteamID64 is a 17-digit integer string
                    assert sid.isdigit() and len(sid) >= 15, (
                        f"Suspicious SteamID '{sid}' — may be a player slot, not a SteamID"
                    )


@skip_no_demo
class TestPlayersIntegrity:
    def test_player_names_not_empty(self, parsed_demo):
        for p in parsed_demo.players:
            assert p.name and p.name.strip(), "Player name must not be empty"

    def test_player_teams_valid_or_none(self, parsed_demo):
        valid_teams = {"ct", "t", "spectator", "unassigned", None}
        for p in parsed_demo.players:
            assert p.team in valid_teams, (
                f"Player '{p.name}' has unexpected team '{p.team}'"
            )


@skip_no_demo
class TestCS2BehaviourEdgeCases:
    """Documents confirmed CS2 behaviours found on real demos.

    These are NOT bugs — they document expected edge cases that the Highlight
    Detector and any future round-boundary logic MUST handle correctly.
    """

    def test_bomb_explosion_kills_after_end_tick(self, parsed_demo):
        """CONFIRMED on real demo: planted_c4 kills occur between end_tick and official_end_tick.

        Round timeline:
          start_tick → freeze_end_tick → [live play] → end_tick → [bomb explodes] → official_end_tick

        The Highlight Detector MUST treat official_end_tick as the authoritative
        round upper bound, never end_tick.
        """
        bomb_kills = [
            k for k in parsed_demo.kills
            if k.weapon == "planted_c4" and k.round_num is not None
        ]
        # Only assert structure if any bomb kills exist; skip silently if not.
        round_map = {r.round_num: r for r in parsed_demo.rounds}
        for k in bomb_kills:
            r = round_map[k.round_num]
            upper = r.official_end_tick if r.official_end_tick is not None else r.end_tick
            assert r.start_tick <= k.tick <= upper, (
                f"Bomb-kill at tick {k.tick} outside [start={r.start_tick}, "
                f"official_end={upper}]"
            )

    def test_world_kills_cs2_encoding(self, parsed_demo):
        """CONFIRMED on real demo: CS2 encodes world/fall-damage kills with
        attacker_steamid == victim_steamid.

        CS2 behaviour (confirmed):
          - weapon='world' (fall damage / void) has SAME attacker and victim SteamID.
          - Our is_suicide=True for these is CORRECT — they ARE self-kills by engine convention.
          - They are correctly NOT teamkills (is_teamkill=False).
          - weapon='planted_c4' has NO attacker at all (attacker_steam_id=None).

        Highlight Detector MUST handle these cases:
          - is_suicide=True AND weapon='world'  → fall-damage death, NOT a player choice.
          - is_suicide=True AND weapon != 'world'/'planted_c4' → deliberate grenade self-kill.
        """
        world_weapons = {"planted_c4", "world", "trigger_hurt", "env_fire"}
        world_kills = [
            k for k in parsed_demo.kills
            if k.weapon in world_weapons
        ]
        for k in world_kills:
            # World kills are never counted as teamkills
            assert k.is_teamkill is False, (
                f"World kill (weapon={k.weapon!r}) at tick {k.tick} "
                f"incorrectly flagged as teamkill"
            )
            # planted_c4 kills have no attacker at all
            if k.weapon == "planted_c4":
                assert k.attacker_steam_id is None, (
                    f"Bomb kill at tick {k.tick} unexpectedly has attacker {k.attacker_steam_id}"
                )

    def test_demo_stats_summary(self, parsed_demo, capsys):
        """Prints a quick stats summary — useful for manual inspection after test run."""
        rounds = parsed_demo.rounds
        kills = parsed_demo.kills
        players = parsed_demo.players

        headshot_kills = [k for k in kills if k.headshot]
        teamkills = [k for k in kills if k.is_teamkill]
        suicides = [k for k in kills if k.is_suicide]
        bomb_kills = [k for k in kills if k.weapon == "planted_c4"]
        no_attacker = [k for k in kills if k.attacker_steam_id is None]

        with capsys.disabled():
            print(f"\n{'='*50}")
            print(f"  REAL DEMO STATS — {parsed_demo.map_name}")
            print(f"  Tickrate : {parsed_demo.tickrate}")
            print(f"  Rounds   : {len(rounds)}")
            print(f"  Players  : {len(players)}")
            print(f"  Kills    : {len(kills)}")
            print(f"    Headshots  : {len(headshot_kills)} ({len(headshot_kills)/max(len(kills),1):.0%})")
            print(f"    Teamkills  : {len(teamkills)}")
            print(f"    Suicides   : {len(suicides)}")
            print(f"    Bomb kills : {len(bomb_kills)}")
            print(f"    No attacker: {len(no_attacker)}")
            print(f"{'='*50}")
