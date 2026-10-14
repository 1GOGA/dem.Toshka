"""Unit tests for Match Analytics (Stage E).

Verifies K/D/A, HS%, weapon distribution, and handling of special kills
(suicides, teamkills, bomb explosions) on synthetic data.
"""

from __future__ import annotations

import pytest

from backend.analytics.match_stats import compute_match_stats
from backend.parser.models import KillEvent, PlayerInfo, RoundInfo


def make_player(name: str, steam_id: str | None, team: str) -> PlayerInfo:
    return PlayerInfo(name=name, steam_id=steam_id, team=team)


def make_round(round_num: int, winner: str) -> RoundInfo:
    return RoundInfo(
        round_num=round_num,
        start_tick=1000,
        freeze_end_tick=1200,
        end_tick=5000,
        official_end_tick=5200,
        winner=winner,
        reason="elimination",
        bomb_plant_tick=None,
        bomb_site=None,
    )


def make_kill(
    attacker: PlayerInfo,
    victim: PlayerInfo,
    assister: PlayerInfo | None = None,
    weapon: str = "ak47",
    headshot: bool = False,
    round_num: int = 1,
) -> KillEvent:
    return KillEvent(
        tick=2000,
        round_num=round_num,
        attacker_name=attacker.name,
        attacker_steam_id=attacker.steam_id,
        attacker_team=attacker.team,
        victim_name=victim.name,
        victim_steam_id=victim.steam_id,
        victim_team=victim.team,
        weapon=weapon,
        headshot=headshot,
        hitgroup="head" if headshot else "chest",
        noscope=False,
        thru_smoke=False,
        attacker_blind=False,
        wallbang=False,
        assister_name=assister.name if assister else None,
        assister_steam_id=assister.steam_id if assister else None,
    )


class TestAnalyticsScoreboard:
    def test_basic_kda(self):
        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")
        p_charlie = make_player("Charlie", "C", "ct")

        rounds = [make_round(1, "ct")]
        kills = [
            make_kill(attacker=p_alice, victim=p_bob, assister=p_charlie, weapon="m4a1"),
        ]

        stats = compute_match_stats([p_alice, p_bob, p_charlie], rounds, kills)

        assert stats.total_rounds == 1
        assert stats.score == {"ct": 1}

        players_by_name = {p.name: p for p in stats.players}

        alice = players_by_name["Alice"]
        assert alice.kills == 1
        assert alice.deaths == 0
        assert alice.assists == 0
        assert alice.kd_ratio == 1.0  # 1 / max(1, 0)

        bob = players_by_name["Bob"]
        assert bob.kills == 0
        assert bob.deaths == 1
        assert bob.kd_ratio == 0.0

        charlie = players_by_name["Charlie"]
        assert charlie.assists == 1
        assert charlie.kills == 0
        assert charlie.deaths == 0

    def test_headshot_percentage(self):
        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")

        # 3 kills: 2 headshots, 1 bodyshot
        kills = [
            make_kill(attacker=p_alice, victim=p_bob, headshot=True),
            make_kill(attacker=p_alice, victim=p_bob, headshot=True),
            make_kill(attacker=p_alice, victim=p_bob, headshot=False),
        ]

        stats = compute_match_stats([p_alice, p_bob], [make_round(1, "ct")], kills)
        alice = [p for p in stats.players if p.name == "Alice"][0]
        assert alice.kills == 3
        assert alice.headshots == 2
        assert alice.headshot_pct == 66.7

    def test_suicide_excluded_from_kills_and_counted_in_deaths(self):
        p_alice = make_player("Alice", "A", "ct")
        rounds = [make_round(1, "t")]

        # Alice dies to fall damage (weapon='world')
        k_suicide = KillEvent(
            tick=2000,
            round_num=1,
            attacker_name="Alice",
            attacker_steam_id="A",
            attacker_team="ct",
            victim_name="Alice",
            victim_steam_id="A",
            victim_team="ct",
            weapon="world",
            headshot=False,
            hitgroup="generic",
            noscope=False,
            thru_smoke=False,
            attacker_blind=False,
            wallbang=False,
            assister_name=None,
            assister_steam_id=None,
        )

        stats = compute_match_stats([p_alice], rounds, [k_suicide])
        alice = stats.players[0]
        assert alice.kills == 0       # Suicide must NOT count as a kill
        assert alice.suicides == 1    # Tracked explicitly
        assert alice.deaths == 1      # Counted as death

    def test_teamkill_excluded_from_kills(self):
        p_alice = make_player("Alice", "A", "ct")
        p_charlie = make_player("Charlie", "C", "ct")

        # Alice kills teammate Charlie
        k_tk = KillEvent(
            tick=2000,
            round_num=1,
            attacker_name="Alice",
            attacker_steam_id="A",
            attacker_team="ct",
            victim_name="Charlie",
            victim_steam_id="C",
            victim_team="ct",
            weapon="awp",
            headshot=False,
            hitgroup="chest",
            noscope=False,
            thru_smoke=False,
            attacker_blind=False,
            wallbang=False,
            assister_name=None,
            assister_steam_id=None,
        )

        stats = compute_match_stats([p_alice, p_charlie], [make_round(1, "t")], [k_tk])
        alice = [p for p in stats.players if p.name == "Alice"][0]
        charlie = [p for p in stats.players if p.name == "Charlie"][0]

        assert alice.kills == 0
        assert alice.teamkills == 1
        assert charlie.deaths == 1

    def test_adr_is_explicitly_none(self):
        p_alice = make_player("Alice", "A", "ct")
        stats = compute_match_stats([p_alice], [make_round(1, "ct")], [])
        assert stats.players[0].adr is None

    def test_weapon_summary(self):
        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")

        kills = [
            make_kill(attacker=p_alice, victim=p_bob, weapon="ak47"),
            make_kill(attacker=p_alice, victim=p_bob, weapon="ak47"),
            make_kill(attacker=p_alice, victim=p_bob, weapon="deagle"),
        ]

        stats = compute_match_stats([p_alice, p_bob], [make_round(1, "ct")], kills)
        alice = stats.players[0]
        assert alice.weapon_kills == {"ak47": 2, "deagle": 1}
        assert stats.weapon_summary == {"ak47": 2, "deagle": 1}

    def test_kills_by_round(self):
        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")

        rounds = [make_round(1, "ct"), make_round(2, "ct")]
        kills = [
            make_kill(attacker=p_alice, victim=p_bob, round_num=1),
            make_kill(attacker=p_alice, victim=p_bob, round_num=2),
            make_kill(attacker=p_alice, victim=p_bob, round_num=2),
        ]

        stats = compute_match_stats([p_alice, p_bob], rounds, kills)
        alice = stats.players[0]
        assert alice.kills_by_round == {1: 1, 2: 2}


class TestPlayerAnalyticsDeep:
    def test_compute_player_analytics_basic(self):
        from backend.analytics.player_analytics import compute_player_analytics

        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")
        p_charlie = make_player("Charlie", "C", "ct")
        p_david = make_player("David", "D", "t")

        rounds = [make_round(1, "ct"), make_round(2, "t")]

        # Round 1: Alice opens duel on Bob (opening win), then Charlie kills David
        k1 = make_kill(attacker=p_alice, victim=p_bob, headshot=True, round_num=1)
        k1.tick = 2000
        k2 = make_kill(attacker=p_charlie, victim=p_david, headshot=False, round_num=1)
        k2.tick = 2500

        # Round 2: Bob kills Charlie, Alice kills Bob (trade kill within 2s), David kills Alice
        k3 = make_kill(attacker=p_bob, victim=p_charlie, round_num=2)
        k3.tick = 3000
        k4 = make_kill(attacker=p_alice, victim=p_bob, headshot=True, round_num=2)
        k4.tick = 3100  # 100 ticks = ~1.5s at 64 tick -> trade kill!
        k5 = make_kill(attacker=p_david, victim=p_alice, round_num=2)
        k5.tick = 3800

        analytics = compute_player_analytics(
            target_steam_id_or_name="A",
            players=[p_alice, p_bob, p_charlie, p_david],
            rounds=rounds,
            kills=[k1, k2, k3, k4, k5],
            tickrate=64,
        )

        assert analytics is not None
        assert analytics.name == "Alice"
        assert analytics.kills == 2
        assert analytics.deaths == 1
        assert analytics.opening_duels_won == 1
        assert analytics.opening_duels_lost == 0
        assert analytics.trade_kills == 1
        assert analytics.kast_pct == 100.0  # R1 survived + kill, R2 got kill
        assert analytics.headshot_pct == 100.0
        assert analytics.performance_rating > 1.0
        assert len(analytics.strengths) > 0

    def test_compute_player_analytics_errors(self):
        from backend.analytics.player_analytics import compute_player_analytics

        p_alice = make_player("Alice", "A", "ct")
        p_bob = make_player("Bob", "B", "t")
        p_charlie = make_player("Charlie", "C", "ct")
        p_david = make_player("David", "D", "ct")

        rounds = [make_round(1, "t")]

        # Team CT has 3 players (Alice, Charlie, David) vs T (Bob).
        # Charlie and David kill nobody yet. Bob kills Alice while Alice is CT defense first death!
        k1 = make_kill(attacker=p_bob, victim=p_alice, round_num=1)
        k1.tick = 2000

        analytics = compute_player_analytics(
            target_steam_id_or_name="Alice",
            players=[p_alice, p_bob, p_charlie, p_david],
            rounds=rounds,
            kills=[k1],
            tickrate=64,
        )

        assert analytics is not None
        assert analytics.deaths == 1
        # Alice had an unforced first death on CT side
        error_types = [e.error_type for e in analytics.errors]
        assert "unforced_first_death" in error_types

    def test_compute_match_stats_faceit_fields(self):
        p_alice = make_player("Alice", "76561198000000001", "ct")
        p_bob = make_player("Bob", "76561198000000002", "t")

        rounds = [make_round(1, "ct"), make_round(2, "ct")]

        # Round 1: Alice kills Bob (opening kill)
        k1 = make_kill(attacker=p_alice, victim=p_bob, round_num=1)
        k1.tick = 2000
        # Round 2: Alice kills Bob (opening kill + 2k in match)
        k2 = make_kill(attacker=p_alice, victim=p_bob, round_num=2)
        k2.tick = 2100

        stats = compute_match_stats(
            players=[p_alice, p_bob],
            rounds=rounds,
            kills=[k1, k2],
        )

        assert stats.total_rounds == 2
        alice_stats = next(p for p in stats.players if p.name == "Alice")
        assert alice_stats.kills == 2
        assert alice_stats.deaths == 0
        assert alice_stats.kpr == 1.0  # 2 kills / 2 rounds
        assert alice_stats.differential == 2  # 2 - 0
        assert alice_stats.opening_kills == 2
        assert alice_stats.faceit_level >= 5
        assert alice_stats.performance_rating >= 1.0
        assert alice_stats.kast_pct == 100.0


