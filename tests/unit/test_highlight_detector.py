"""Unit tests for the Highlight Detector (Stage D).

Tests use synthetic KillEvent / RoundInfo objects — no real demo required.
All edge cases from the design specification are covered.
"""

from __future__ import annotations

import pytest

from backend.parser.models import KillEvent, ParsedDemo, PlayerInfo, RoundInfo, SCHEMA_VERSION
from backend.detector.models import DetectorSettings, HighlightType
from backend.detector.highlight_detector import (
    detect_highlights,
    _extract_tags,
    _find_maximal_multikill_sequences,
    _make_clip_bounds,
    _deduplicate,
)
from backend.detector.models import HighlightCandidate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TICKRATE = 128
DEFAULT_SETTINGS = DetectorSettings(
    multikill_window_ticks=TICKRATE * 15,
    pre_roll_ticks=TICKRATE * 7,
    post_roll_ticks=TICKRATE * 4,
    min_clutch_enemies=2,
    round_team_size=5,
)


def make_kill(
    tick: int,
    round_num: int | None = 1,
    attacker_id: str | None = "A",
    attacker_name: str | None = "Alice",
    attacker_team: str | None = "ct",
    victim_id: str | None = "V1",
    victim_name: str | None = "Victim1",
    victim_team: str | None = "t",
    weapon: str | None = "ak47",
    headshot: bool | None = False,
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
        attacker_steam_id=attacker_id,
        attacker_team=attacker_team,
        victim_name=victim_name,
        victim_steam_id=victim_id,
        victim_team=victim_team,
        weapon=weapon,
        headshot=headshot,
        hitgroup="chest",
        noscope=noscope,
        thru_smoke=thru_smoke,
        attacker_blind=attacker_blind,
        wallbang=wallbang,
        assister_name=assister_name,
        assister_steam_id=assister_steam_id,
    )


def make_round(
    round_num: int = 1,
    start_tick: int = 1000,
    end_tick: int = 10000,
    official_end_tick: int | None = 10500,
    freeze_end_tick: int | None = 1500,
    winner: str | None = "ct",
) -> RoundInfo:
    return RoundInfo(
        round_num=round_num,
        start_tick=start_tick,
        freeze_end_tick=freeze_end_tick,
        end_tick=end_tick,
        official_end_tick=official_end_tick,
        winner=winner,
        reason=None,
        bomb_plant_tick=None,
        bomb_site=None,
    )


def make_demo(
    kills: list[KillEvent],
    rounds: list[RoundInfo],
    players: list[PlayerInfo] | None = None,
) -> ParsedDemo:
    return ParsedDemo(
        schema_version=SCHEMA_VERSION,
        demo_path="test.dem",
        map_name="de_test",
        tickrate=TICKRATE,
        rounds=rounds,
        players=players or [],
        kills=kills,
    )


# ---------------------------------------------------------------------------
# Single kill
# ---------------------------------------------------------------------------


class TestSingleKill:
    def test_single_kill_produces_kill_highlight(self):
        round_ = make_round(start_tick=1000, end_tick=5000, official_end_tick=5200)
        kill = make_kill(tick=3000, round_num=1)
        demo = make_demo([kill], [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        assert len(highlights) == 1
        assert highlights[0].highlight_type == HighlightType.KILL
        assert highlights[0].kill_count == 1

    def test_single_kill_clip_bounds_clamped_to_round(self):
        # kill at start of round — pre-roll should be clamped to round start
        round_ = make_round(start_tick=1000, end_tick=5000, official_end_tick=5200)
        kill = make_kill(tick=1100, round_num=1)  # only 100 ticks after start
        demo = make_demo([kill], [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        assert highlights[0].clip_start_tick == 1000  # clamped to round start

    def test_single_kill_clip_end_clamped_to_official_end(self):
        round_ = make_round(start_tick=1000, end_tick=5000, official_end_tick=5050)
        kill = make_kill(tick=5000, round_num=1)  # 50 ticks before official_end
        demo = make_demo([kill], [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        assert highlights[0].clip_end_tick == 5050  # clamped to official_end_tick

    def test_single_kill_uses_official_end_not_end_tick(self):
        """When official_end_tick is present, it must be used as the upper bound."""
        round_ = make_round(end_tick=5000, official_end_tick=5500)
        kill = make_kill(tick=4900)
        demo = make_demo([kill], [round_])
        h = detect_highlights(demo, DEFAULT_SETTINGS)[0]
        # post_roll = 128*4 = 512; 4900+512=5412 < 5500
        assert h.clip_end_tick == 4900 + DEFAULT_SETTINGS.post_roll_ticks
        assert h.clip_end_tick <= 5500


# ---------------------------------------------------------------------------
# Multi-kill detection
# ---------------------------------------------------------------------------


class TestMultiKill:
    def _make_sequence(self, n: int, first_tick: int = 3000, spacing: int = 50) -> list[KillEvent]:
        return [
            make_kill(
                tick=first_tick + i * spacing,
                victim_id=f"V{i}",
                victim_name=f"Victim{i}",
            )
            for i in range(n)
        ]

    def test_double_kill(self):
        round_ = make_round()
        kills = self._make_sequence(2)
        demo = make_demo(kills, [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        mk = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_2K]
        assert len(mk) == 1
        assert mk[0].kill_count == 2

    def test_triple_kill(self):
        round_ = make_round()
        kills = self._make_sequence(3)
        demo = make_demo(kills, [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        mk = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_3K]
        assert len(mk) == 1
        assert mk[0].kill_count == 3

    def test_4k(self):
        round_ = make_round()
        kills = self._make_sequence(4)
        demo = make_demo(kills, [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        mk = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_4K]
        assert len(mk) == 1
        assert mk[0].kill_count == 4

    def test_ace(self):
        round_ = make_round()
        kills = self._make_sequence(5)
        demo = make_demo(kills, [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        aces = [h for h in highlights if h.highlight_type == HighlightType.ACE]
        assert len(aces) == 1
        assert aces[0].kill_count == 5

    def test_6_kills_still_ace(self):
        """More than 5 kills (e.g. extended round) still produces ACE."""
        round_ = make_round()
        kills = self._make_sequence(6)
        demo = make_demo(kills, [round_])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        aces = [h for h in highlights if h.highlight_type == HighlightType.ACE]
        assert len(aces) >= 1
        assert aces[0].kill_count >= 5


# ---------------------------------------------------------------------------
# Round boundary
# ---------------------------------------------------------------------------


class TestRoundBoundary:
    def test_kills_in_different_rounds_not_merged(self):
        r1 = make_round(round_num=1, start_tick=1000, end_tick=5000, official_end_tick=5200)
        r2 = make_round(round_num=2, start_tick=6000, end_tick=10000, official_end_tick=10200)
        k1 = make_kill(tick=4900, round_num=1, victim_id="V1")
        k2 = make_kill(tick=6100, round_num=2, victim_id="V2")
        demo = make_demo([k1, k2], [r1, r2])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        # Two separate single kills — never merged
        assert all(h.kill_count == 1 for h in highlights if h.highlight_type == HighlightType.KILL)
        round_nums = {h.round_num for h in highlights}
        assert 1 in round_nums
        assert 2 in round_nums

    def test_clip_end_never_exceeds_round_official_end(self):
        r = make_round(round_num=1, start_tick=1000, end_tick=5000, official_end_tick=5200)
        kills = [make_kill(tick=5100 + i * 10, round_num=1, victim_id=f"V{i}") for i in range(3)]
        demo = make_demo(kills, [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        for h in highlights:
            assert h.clip_end_tick <= 5200, f"clip_end {h.clip_end_tick} > official_end 5200"

    def test_clip_start_never_before_round_start(self):
        r = make_round(round_num=1, start_tick=1000, end_tick=5000, official_end_tick=5200)
        kill = make_kill(tick=1010, round_num=1)  # very early kill
        demo = make_demo([kill], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        for h in highlights:
            assert h.clip_start_tick >= 1000


# ---------------------------------------------------------------------------
# Same-tick kills
# ---------------------------------------------------------------------------


class TestSameTick:
    def test_two_kills_at_same_tick(self):
        """Two kills at identical tick → both counted, should be 2K."""
        r = make_round()
        k1 = make_kill(tick=3000, victim_id="V1")
        k2 = make_kill(tick=3000, victim_id="V2")
        demo = make_demo([k1, k2], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        mk2 = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_2K]
        assert len(mk2) == 1
        assert mk2[0].kill_count == 2


# ---------------------------------------------------------------------------
# Missing / None fields
# ---------------------------------------------------------------------------


class TestMissingFields:
    def test_kill_with_none_attacker_skipped_for_multikill(self):
        """Kills with no attacker (bomb, world) are not attributed to anyone."""
        r = make_round()
        k1 = make_kill(tick=3000, attacker_id=None, attacker_name=None, attacker_team=None)
        demo = make_demo([k1], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        # No attacker → no highlight attributed to a player
        assert all(h.pov_steam_id is not None for h in highlights if h.highlight_type != HighlightType.CLUTCH_CANDIDATE)

    def test_kill_with_none_round_num_skipped(self):
        r = make_round()
        k = make_kill(tick=3000, round_num=None)
        demo = make_demo([k], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        assert highlights == []

    def test_kill_with_none_team_not_is_teamkill(self):
        """When team info is None, teamkill should not be set."""
        k = make_kill(tick=100, attacker_team=None, victim_team=None)
        assert not k.is_teamkill

    def test_tags_none_fields_not_included(self):
        """Tags from None fields must not appear."""
        k = make_kill(tick=100, headshot=None, noscope=None, wallbang=None)
        tags = _extract_tags([k])
        assert "headshot" not in tags
        assert "noscope" not in tags
        assert "wallbang" not in tags


# ---------------------------------------------------------------------------
# Teamkill handling
# ---------------------------------------------------------------------------


class TestTeamkill:
    def test_teamkill_not_counted_as_enemy_kill(self):
        r = make_round()
        # Normal kill + teamkill
        k_enemy = make_kill(tick=3000, victim_id="V1", victim_team="t")
        k_team = make_kill(tick=3100, victim_id="V2", attacker_id="A",
                           victim_team="ct")  # same team as attacker
        assert k_team.is_teamkill
        demo = make_demo([k_enemy, k_team], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        # Teamkill excluded → only 1 enemy kill → KILL (not 2K)
        kill_highlights = [h for h in highlights if h.pov_steam_id == "A"]
        types = [h.highlight_type for h in kill_highlights]
        assert HighlightType.MULTIKILL_2K not in types
        assert HighlightType.KILL in types

    def test_pure_teamkill_produces_no_highlight(self):
        r = make_round()
        k = make_kill(tick=3000, victim_id="V1", victim_team="ct")  # teamkill
        assert k.is_teamkill
        demo = make_demo([k], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        # Teamkill alone produces no highlights attributed to attacker
        attacker_highlights = [h for h in highlights if h.pov_steam_id == "A"]
        assert attacker_highlights == []


# ---------------------------------------------------------------------------
# Suicide handling
# ---------------------------------------------------------------------------


class TestSuicide:
    def test_world_kill_is_suicide_not_counted(self):
        """World/fall-damage kills are is_suicide=True but not a deliberate action."""
        r = make_round()
        # World kill: attacker_id == victim_id
        k_world = make_kill(tick=3000, attacker_id="A", victim_id="A",
                            weapon="world", victim_team="ct", attacker_team="ct")
        assert k_world.is_suicide
        # Also add an enemy kill to ensure it doesn't get combined with suicide
        k_enemy = make_kill(tick=3100, attacker_id="A", victim_id="V1")
        demo = make_demo([k_world, k_enemy], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        attacker_highlights = [h for h in highlights if h.pov_steam_id == "A"]
        # Only 1 valid enemy kill → KILL (not 2K)
        types = [h.highlight_type for h in attacker_highlights]
        assert HighlightType.MULTIKILL_2K not in types
        assert HighlightType.KILL in types

    def test_self_grenade_suicide_not_counted(self):
        """Deliberate grenade self-kill: attacker_id == victim_id."""
        r = make_round()
        k = make_kill(tick=3000, attacker_id="A", victim_id="A",
                      weapon="hegrenade", victim_team="ct", attacker_team="ct")
        assert k.is_suicide
        demo = make_demo([k], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        attacker_highlights = [h for h in highlights if h.pov_steam_id == "A"]
        assert attacker_highlights == []


# ---------------------------------------------------------------------------
# Multikill window boundary
# ---------------------------------------------------------------------------


class TestWindowBoundary:
    def test_kill_just_inside_window(self):
        window = DEFAULT_SETTINGS.multikill_window_ticks  # 1920
        settings = DetectorSettings(multikill_window_ticks=window, max_kill_gap_ticks=window)
        r = make_round()
        k1 = make_kill(tick=3000, victim_id="V1")
        k2 = make_kill(tick=3000 + window, victim_id="V2")  # exactly at window edge
        demo = make_demo([k1, k2], [r])
        highlights = detect_highlights(demo, settings)
        mk2 = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_2K]
        assert len(mk2) == 1  # both inside window (inclusive)

    def test_kill_just_outside_window(self):
        window = DEFAULT_SETTINGS.multikill_window_ticks  # 1920
        settings = DetectorSettings(multikill_window_ticks=window, max_kill_gap_ticks=window)
        r = make_round()
        k1 = make_kill(tick=3000, victim_id="V1")
        k2 = make_kill(tick=3000 + window + 1, victim_id="V2")  # 1 tick outside
        demo = make_demo([k1, k2], [r])
        highlights = detect_highlights(demo, settings)
        mk2 = [h for h in highlights if h.highlight_type == HighlightType.MULTIKILL_2K]
        assert len(mk2) == 0
  # should NOT merge


# ---------------------------------------------------------------------------
# Clutch candidates
# ---------------------------------------------------------------------------


class TestClutch:
    def _make_clutch_scenario(
        self,
        *,
        ct_alive: int = 1,
        t_alive: int = 3,
        n_kills: int = 2,
    ) -> tuple[ParsedDemo, list[KillEvent]]:
        """Build a scenario where CT player is outnumbered vs T."""
        # Simulate the state where only ct_alive CTs remain at round start.
        # We pre-kill (ct_alive_deaths) CTs with world kills so the alive count is low.
        r = make_round(round_num=1, start_tick=1000, end_tick=10000, official_end_tick=10200)
        kills: list[KillEvent] = []
        tick = 2000

        # Kill enough CT players to bring ct_alive down from 5 to the target
        for i in range(5 - ct_alive):
            # world kill on CT (reduces ct_alive)
            k = make_kill(
                tick=tick,
                attacker_id=f"CT_DEAD_{i}",
                victim_id=f"CT_DEAD_{i}",
                attacker_name=f"CT_Dead{i}",
                victim_name=f"CT_Dead{i}",
                weapon="world",
                attacker_team="ct",
                victim_team="ct",
            )
            kills.append(k)
            tick += 10

        # Kill enough T players to bring t_alive down from 5 to the target
        # We need them killed by someone else, not by our hero
        for i in range(5 - t_alive):
            k = make_kill(
                tick=tick,
                attacker_id="OTHER_CT",
                victim_id=f"T_DEAD_{i}",
                attacker_name="OtherCT",
                victim_name=f"T_Dead{i}",
                attacker_team="ct",
                victim_team="t",
            )
            kills.append(k)
            tick += 10

        # Now the hero (1 CT) faces t_alive Ts
        hero_kills: list[KillEvent] = []
        for i in range(n_kills):
            k = make_kill(
                tick=tick,
                attacker_id="HERO",
                victim_id=f"T_VICTIM_{i}",
                attacker_name="Hero",
                victim_name=f"T_Victim{i}",
                attacker_team="ct",
                victim_team="t",
            )
            hero_kills.append(k)
            kills.append(k)
            tick += 50

        return make_demo(kills, [r]), hero_kills

    def test_clutch_2v1_detected(self):
        """1 CT vs 2 Ts: hero kills 2 Ts → clutch candidate."""
        demo, _ = self._make_clutch_scenario(ct_alive=1, t_alive=2, n_kills=2)
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        clutches = [h for h in highlights if h.highlight_type == HighlightType.CLUTCH_CANDIDATE]
        assert len(clutches) >= 1
        hero_clutches = [c for c in clutches if c.pov_steam_id == "HERO"]
        assert len(hero_clutches) == 1
        assert hero_clutches[0].is_heuristic

    def test_clutch_5v1_detected(self):
        """1 CT vs 5 Ts (maximum outnumbered)."""
        demo, _ = self._make_clutch_scenario(ct_alive=1, t_alive=5, n_kills=2)
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        clutches = [h for h in highlights if h.pov_steam_id == "HERO"
                    and h.highlight_type == HighlightType.CLUTCH_CANDIDATE]
        assert len(clutches) == 1

    def test_no_clutch_when_equal_numbers(self):
        """Equal sides (2 vs 2): attacker_alive == enemy_alive → not outnumbered."""
        demo, _ = self._make_clutch_scenario(ct_alive=2, t_alive=2, n_kills=2)
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        clutches = [h for h in highlights if h.highlight_type == HighlightType.CLUTCH_CANDIDATE
                    and h.pov_steam_id == "HERO"]
        assert clutches == []

    def test_no_clutch_when_not_enough_enemies(self):
        """Hero kills only 1 enemy but min_clutch_enemies=2 → no clutch."""
        settings = DetectorSettings(min_clutch_enemies=2, round_team_size=5)
        demo, _ = self._make_clutch_scenario(ct_alive=1, t_alive=3, n_kills=1)
        highlights = detect_highlights(demo, settings)
        clutches = [h for h in highlights if h.highlight_type == HighlightType.CLUTCH_CANDIDATE
                    and h.pov_steam_id == "HERO"]
        assert clutches == []

    def test_clutch_is_always_heuristic(self):
        demo, _ = self._make_clutch_scenario(ct_alive=1, t_alive=3, n_kills=2)
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        for h in highlights:
            if h.highlight_type == HighlightType.CLUTCH_CANDIDATE:
                assert h.is_heuristic is True


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class TestTags:
    def test_headshot_tag(self):
        k = make_kill(tick=100, headshot=True)
        assert "headshot" in _extract_tags([k])

    def test_wallbang_tag(self):
        k = make_kill(tick=100, wallbang=True)
        assert "wallbang" in _extract_tags([k])

    def test_noscope_tag(self):
        k = make_kill(tick=100, noscope=True)
        assert "noscope" in _extract_tags([k])

    def test_thru_smoke_tag(self):
        k = make_kill(tick=100, thru_smoke=True)
        assert "thru_smoke" in _extract_tags([k])

    def test_blind_tag(self):
        k = make_kill(tick=100, attacker_blind=True)
        assert "blind" in _extract_tags([k])

    def test_false_fields_not_tagged(self):
        k = make_kill(tick=100, headshot=False, wallbang=False, noscope=False)
        tags = _extract_tags([k])
        assert "headshot" not in tags
        assert "wallbang" not in tags
        assert "noscope" not in tags

    def test_none_fields_not_tagged(self):
        k = make_kill(tick=100, headshot=None, wallbang=None)
        tags = _extract_tags([k])
        assert "headshot" not in tags
        assert "wallbang" not in tags

    def test_tags_are_sorted(self):
        k = make_kill(tick=100, headshot=True, wallbang=True, noscope=True)
        tags = _extract_tags([k])
        assert tags == sorted(tags)

    def test_tags_combined_from_sequence(self):
        """Tags from entire sequence, not just first kill."""
        k1 = make_kill(tick=100, headshot=True)
        k2 = make_kill(tick=200, wallbang=True)
        tags = _extract_tags([k1, k2])
        assert "headshot" in tags
        assert "wallbang" in tags


# ---------------------------------------------------------------------------
# Clip bounds helper
# ---------------------------------------------------------------------------


class TestClipBounds:
    def test_normal_bounds(self):
        r = make_round(start_tick=1000, end_tick=10000, official_end_tick=10500)
        s = DetectorSettings(pre_roll_ticks=100, post_roll_ticks=50)
        start, end = _make_clip_bounds(5000, 5200, r, s)
        assert start == 4900
        assert end == 5250

    def test_start_clamped_to_round_start(self):
        r = make_round(start_tick=1000, end_tick=10000, official_end_tick=10500)
        s = DetectorSettings(pre_roll_ticks=5000, post_roll_ticks=50)
        start, _ = _make_clip_bounds(1050, 1100, r, s)
        assert start == 1000

    def test_end_clamped_to_official_end(self):
        r = make_round(start_tick=1000, end_tick=10000, official_end_tick=10500)
        s = DetectorSettings(pre_roll_ticks=100, post_roll_ticks=5000)
        _, end = _make_clip_bounds(9900, 10000, r, s)
        assert end == 10500

    def test_fallback_to_end_tick_when_official_end_none(self):
        r = make_round(start_tick=1000, end_tick=10000, official_end_tick=None)
        s = DetectorSettings(pre_roll_ticks=100, post_roll_ticks=5000)
        _, end = _make_clip_bounds(9500, 9600, r, s)
        assert end == 10000


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


class TestDeduplicate:
    def _make_candidate(self, id_: str, hl_type: HighlightType) -> HighlightCandidate:
        return HighlightCandidate(
            id=id_,
            highlight_type=hl_type,
            round_num=1,
            pov_steam_id="A",
            pov_name="Alice",
            kill_start_tick=3000,
            kill_end_tick=3100,
            clip_start_tick=2900,
            clip_end_tick=3600,
            kill_count=1,
        )

    def test_no_duplicates_unchanged(self):
        c1 = self._make_candidate("1_kill_A_3000", HighlightType.KILL)
        c2 = self._make_candidate("1_kill_B_3000", HighlightType.KILL)
        result = _deduplicate([c1, c2])
        assert len(result) == 2

    def test_duplicate_id_keeps_higher_priority(self):
        c_kill = self._make_candidate("id", HighlightType.KILL)
        c_2k = self._make_candidate("id", HighlightType.MULTIKILL_2K)
        result = _deduplicate([c_kill, c_2k])
        assert len(result) == 1
        assert result[0].highlight_type == HighlightType.MULTIKILL_2K

    def test_ace_beats_4k_on_same_id(self):
        c_4k = self._make_candidate("id", HighlightType.MULTIKILL_4K)
        c_ace = self._make_candidate("id", HighlightType.ACE)
        result = _deduplicate([c_4k, c_ace])
        assert result[0].highlight_type == HighlightType.ACE


# ---------------------------------------------------------------------------
# Window sequences
# ---------------------------------------------------------------------------


class TestFindMaximalSequences:
    def _kills(self, ticks: list[int]) -> list[KillEvent]:
        return [make_kill(tick=t, victim_id=f"V{i}") for i, t in enumerate(ticks)]

    def test_single_kill_one_sequence(self):
        seqs = _find_maximal_multikill_sequences(self._kills([100]), 1920)
        assert len(seqs) == 1
        assert len(seqs[0]) == 1

    def test_all_within_window(self):
        seqs = _find_maximal_multikill_sequences(self._kills([100, 200, 300]), 1920)
        assert len(seqs) == 1
        assert len(seqs[0]) == 3

    def test_two_separate_sequences(self):
        seqs = _find_maximal_multikill_sequences(self._kills([100, 200, 3000, 3100]), 1920)
        assert len(seqs) == 2
        assert len(seqs[0]) == 2
        assert len(seqs[1]) == 2

    def test_empty_kills(self):
        seqs = _find_maximal_multikill_sequences([], 1920)
        assert seqs == []

    def test_gap_exceeding_4_seconds_splits_sequence(self):
        # 128 * 4 = 512 ticks max gap. Kills at 100 and 700 have gap 600 (> 512)
        seqs = _find_maximal_multikill_sequences(self._kills([100, 700]), window_ticks=1920, max_kill_gap_ticks=512)
        assert len(seqs) == 2
        assert len(seqs[0]) == 1
        assert len(seqs[1]) == 1


# ---------------------------------------------------------------------------
# Deterministic IDs
# ---------------------------------------------------------------------------


class TestDeterministicIds:
    def test_all_ids_unique_on_real_data(self):
        r = make_round()
        kills = [make_kill(tick=3000 + i * 50, victim_id=f"V{i}") for i in range(5)]
        demo = make_demo(kills, [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        ids = [h.id for h in highlights]
        assert len(ids) == len(set(ids)), f"Duplicate IDs found: {ids}"

    def test_id_contains_round_and_type(self):
        r = make_round(round_num=7)
        k = make_kill(tick=4000, round_num=7)
        demo = make_demo([k], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        assert any("7" in h.id for h in highlights)

    def test_id_is_reproducible(self):
        r = make_round()
        k = make_kill(tick=3000)
        demo = make_demo([k], [r])
        h1 = detect_highlights(demo, DEFAULT_SETTINGS)
        h2 = detect_highlights(demo, DEFAULT_SETTINGS)
        assert [h.id for h in h1] == [h.id for h in h2]


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_no_kills_no_highlights(self):
        r = make_round()
        demo = make_demo([], [r])
        assert detect_highlights(demo, DEFAULT_SETTINGS) == []

    def test_no_rounds_no_highlights(self):
        k = make_kill(tick=3000, round_num=1)
        # Kill references round 1 but rounds list is empty → skipped
        demo = make_demo([k], [])
        assert detect_highlights(demo, DEFAULT_SETTINGS) == []

    def test_kill_round_num_not_in_rounds_skipped(self):
        r = make_round(round_num=5)
        k = make_kill(tick=3000, round_num=99)  # round 99 doesn't exist
        demo = make_demo([k], [r])
        assert detect_highlights(demo, DEFAULT_SETTINGS) == []

    def test_two_players_each_get_independent_highlights(self):
        r = make_round()
        k1 = make_kill(tick=3000, attacker_id="A", victim_id="V1", victim_team="t")
        k2 = make_kill(tick=3100, attacker_id="B", attacker_name="Bob",
                       victim_id="V2", victim_team="t", attacker_team="ct")
        demo = make_demo([k1, k2], [r])
        highlights = detect_highlights(demo, DEFAULT_SETTINGS)
        steam_ids = {h.pov_steam_id for h in highlights if h.highlight_type == HighlightType.KILL}
        assert "A" in steam_ids
        assert "B" in steam_ids
