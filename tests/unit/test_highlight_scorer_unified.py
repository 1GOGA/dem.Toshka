"""Unit tests for explainable multi-factor highlight scoring."""

from backend.detector.highlight_scorer import SmartHighlightScorer
from backend.parser.models import KillEvent


def _make_kill(tick: int, weapon: str = "ak47", headshot: bool = False, wallbang: bool = False, noscope: bool = False, thru_smoke: bool = False):
    return KillEvent(
        tick=tick,
        round_num=1,
        attacker_name="pytoshka",
        attacker_steam_id="76561198000000001",
        attacker_team="ct",
        victim_name="Victim",
        victim_steam_id="76561198000000002",
        victim_team="t",
        weapon=weapon,
        headshot=headshot,
        hitgroup="head" if headshot else "chest",
        noscope=noscope,
        thru_smoke=thru_smoke,
        attacker_blind=False,
        wallbang=wallbang,
        assister_name=None,
        assister_steam_id=None,
    )


def test_scorer_ace_and_headshots():
    scorer = SmartHighlightScorer(tickrate=64.0)

    # 5 kills within 6 seconds, all headshots with Deagle
    kills = [
        _make_kill(1000, weapon="deagle", headshot=True),
        _make_kill(1064, weapon="deagle", headshot=True),
        _make_kill(1128, weapon="deagle", headshot=True),
        _make_kill(1192, weapon="deagle", headshot=True),
        _make_kill(1256, weapon="deagle", headshot=True),
    ]

    breakdown = scorer.score_sequence(kills)

    assert breakdown.total_score >= 100.0
    assert "ACE" in breakdown.badges
    assert "100% HS" in breakdown.badges
    assert "DEAGLE FOCUS" in breakdown.badges
    assert "Rapid Tempo" in breakdown.badges
    assert len(breakdown.factors) >= 5


def test_scorer_wallbang_and_noscope():
    scorer = SmartHighlightScorer(tickrate=64.0)

    kills = [
        _make_kill(1000, weapon="awp", wallbang=True, noscope=True),
    ]

    breakdown = scorer.score_sequence(kills)
    assert "Wallbang" in breakdown.badges
    assert "Noscope" in breakdown.badges
    assert any(f.name == "Wallbang" for f in breakdown.factors)
    assert any(f.name == "Noscope" for f in breakdown.factors)


def test_scorer_clutch():
    scorer = SmartHighlightScorer(tickrate=64.0)

    kills = [
        _make_kill(1000),
        _make_kill(1200),
        _make_kill(1400),
    ]

    breakdown = scorer.score_sequence(kills, clutch_opponents=3)
    assert "1v3 Clutch" in breakdown.badges
    assert any("1v3" in f.name for f in breakdown.factors)
