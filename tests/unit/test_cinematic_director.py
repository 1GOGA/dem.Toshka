"""Unit tests for Automatic Shot Director and Highlight Scoring."""

from backend.cinematic.models import CameraType, ShotPurpose
from backend.cinematic.shot_director import (
    AutomaticShotDirector,
    HighlightScorer,
    detect_quick_flick,
)


class TestHighlightScorer:
    def test_scoring_ace_with_headshots_and_wallbang(self):
        scorer = HighlightScorer()
        kills = [
            {"headshot": True, "wallbang": False},
            {"headshot": True, "wallbang": True},
            {"headshot": False, "noscope": True},
            {"headshot": False, "wallbang": False},
            {"headshot": True, "wallbang": False},
        ]
        score = scorer.score_highlight("ACE", kills=kills)
        # 100 (ace) + 3*8 (headshots) + 18 (wallbang) + 22 (noscope) = 164.0
        assert score == 164.0

    def test_scoring_clutch(self):
        scorer = HighlightScorer()
        score = scorer.score_highlight("clutch", kills=[], is_clutch=True, clutch_enemies=3)
        assert score >= 90.0

    def test_flick_detection(self):
        # Normal steady aim
        steady_ticks = [
            {"tick": 100, "pitch": 5.0, "yaw": 40.0},
            {"tick": 101, "pitch": 5.1, "yaw": 40.2},
            {"tick": 102, "pitch": 5.0, "yaw": 40.4},
        ]
        assert not detect_quick_flick(steady_ticks, kill_tick=102)

        # High angular velocity flick (e.g. 35 degrees in 2 ticks)
        flick_ticks = [
            {"tick": 100, "pitch": 5.0, "yaw": 40.0},
            {"tick": 101, "pitch": 10.0, "yaw": 60.0},
            {"tick": 102, "pitch": 15.0, "yaw": 78.0},
        ]
        assert detect_quick_flick(flick_ticks, kill_tick=102)


class TestAutomaticShotDirector:
    def test_director_plans_ace_choreography(self):
        director = AutomaticShotDirector()
        kills = [
            {"tick": 1050, "headshot": True, "victim_steamid": "76561198000000001", "victim_name": "Vic1"},
            {"tick": 1100, "headshot": False, "victim_steamid": "76561198000000002", "victim_name": "Vic2"},
            {"tick": 1150, "headshot": True, "victim_steamid": "76561198000000003", "victim_name": "Vic3"},
            {"tick": 1200, "headshot": False, "victim_steamid": "76561198000000004", "victim_name": "Vic4"},
            {"tick": 1250, "headshot": True, "victim_steamid": "76561198000000005", "victim_name": "Vic5"},
        ]
        player_ticks = [
            {"tick": 900 + i * 16, "X": 100.0, "Y": 200.0, "Z": 0.0, "pitch": 0.0, "yaw": 0.0}
            for i in range(25)
        ]
        shots = director.plan_shots_for_highlight(
            highlight_id="hl_ace_01",
            round_number=5,
            start_tick=1000,
            end_tick=1300,
            hero_steam_id="76561197999999999",
            hero_name="AceHero",
            kills=kills,
            highlight_type="ACE",
            player_ticks=player_ticks,
        )

        types = [s.camera_type for s in shots]
        assert CameraType.FIRST_PERSON in types
        assert CameraType.VICTIM_POV in types
        assert CameraType.SHOULDER_CAM in types
        assert CameraType.ORBIT_CAMERA in types

        # Check that master hero POV covers the entire event
        hero_shot = next(s for s in shots if s.camera_type == CameraType.FIRST_PERSON)
        assert hero_shot.start_tick == 1000
        assert hero_shot.end_tick == 1300
        assert hero_shot.purpose == ShotPurpose.PRIMARY_ACTION
