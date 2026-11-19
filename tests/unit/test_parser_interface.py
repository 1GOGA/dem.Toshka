"""Unit tests for demo parser interface, normalization, and tick indexing."""

from backend.parser.adapter import AwpyDemoParser
from backend.parser.models import KillEvent, ParsedDemo, RoundInfo
from backend.parser.normalizer import EventNormalizer, TickIndex
from backend.parser.parser_interface import DemoParserInterface
from backend.parser.replay import radar_percent_to_world, world_to_radar_percent


def test_parser_interface_contract():
    parser = AwpyDemoParser()
    assert isinstance(parser, DemoParserInterface)
    assert parser.get_backend_name() == "awpy"


def test_event_normalizer():
    assert EventNormalizer.clean_weapon_name("weapon_ak47") == "ak47"
    assert EventNormalizer.clean_weapon_name("weapon_m4a1_silencer") == "m4a1_silencer"
    assert EventNormalizer.clean_weapon_name("inferno") == "molotov"
    assert EventNormalizer.clean_weapon_name(None) == "unknown"

    assert EventNormalizer.normalize_team("CounterTerrorists") == "ct"
    assert EventNormalizer.normalize_team("TERRORIST") == "t"
    assert EventNormalizer.normalize_team(None) == "unknown"

    fall_kill = KillEvent(
        tick=1000,
        round_num=1,
        attacker_name="Player",
        attacker_steam_id="76561198000000001",
        attacker_team="ct",
        victim_name="Player",
        victim_steam_id="76561198000000001",
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
    assert EventNormalizer.is_fall_damage(fall_kill) is True


def test_tick_index():
    rounds = [
        RoundInfo(round_num=1, start_tick=1000, end_tick=2000, freeze_end_tick=1100, official_end_tick=2100, winner="ct", reason="elim", bomb_plant_tick=None, bomb_site=None),
        RoundInfo(round_num=2, start_tick=2200, end_tick=3200, freeze_end_tick=2300, official_end_tick=3300, winner="t", reason="bomb", bomb_plant_tick=None, bomb_site=None),
    ]

    kills = [
        KillEvent(1200, 1, "P1", "STEAM_1", "ct", "V1", "STEAM_V1", "t", "ak47", True, "head", False, False, False, False, None, None),
        KillEvent(1500, 1, "P1", "STEAM_1", "ct", "V2", "STEAM_V2", "t", "ak47", False, "chest", False, False, False, False, None, None),
        KillEvent(2500, 2, "P2", "STEAM_2", "t", "V3", "STEAM_1", "ct", "awp", False, "chest", False, False, False, False, None, None),
    ]

    demo = ParsedDemo(
        schema_version="1",
        demo_path="test.dem",
        map_name="de_dust2",
        tickrate=64,
        rounds=rounds,
        players=[],
        kills=kills,
        _raw_header={"map_name": "de_dust2", "tickrate": 64},
    )

    index = TickIndex(demo)

    # Round lookup
    r1 = index.get_round_for_tick(1500)
    assert r1 is not None
    assert r1.round_num == 1

    r_none = index.get_round_for_tick(2150)
    assert r_none is None

    # Kills range lookup
    range_kills = index.get_kills_in_range(1100, 1600)
    assert len(range_kills) == 2

    # Nearest kill
    near = index.get_nearest_kill(1210)
    assert near is not None
    assert near.tick == 1200

    # Attacker kills
    p1_kills = index.get_kills_by_attacker("STEAM_1")
    assert len(p1_kills) == 2


def test_radar_coordinate_transforms():
    map_name = "de_dust2"
    orig_x, orig_y = -1000.0, 1500.0
    pct_x, pct_y = world_to_radar_percent(orig_x, orig_y, map_name=map_name)

    rec_x, rec_y, _ = radar_percent_to_world(pct_x, pct_y, map_name=map_name)

    # Check precision within 1% radar tolerance
    assert abs(rec_x - orig_x) < 50.0
    assert abs(rec_y - orig_y) < 50.0
