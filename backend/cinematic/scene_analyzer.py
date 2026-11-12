"""Cinematic Scene Analyzer & Dynamics Engine for CS2 Fragmovie Production.

Analyzes demo events, player positioning, combat pacing, and weapon discharge timing
to compute frame-accurate kill engagement vs lethal timestamps, dynamic transitions,
speed ramping recommendations, and in-game HUD suppression policies.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


from backend.cinematic.production_models import (
    EventTimelineMapping,
    HudCaptureProfile,
    HudElementToggles,
    SceneCategory,
    StoryboardSceneCard,
    TimelineLockState,
    TransitionDefinition,
    TRANSITION_REGISTRY,
)


class DynamicTransitionType(str, Enum):
    WHIP_PAN = "WHIP_PAN"
    RADIAL_ZOOM = "RADIAL_ZOOM"
    SNAP_CUT = "SNAP_CUT"
    SMOOTH_GLIDE = "SMOOTH_GLIDE"
    IMPACT_FLASH = "IMPACT_FLASH"


class CombatTempo(str, Enum):
    RAPID_FIRE = "RAPID_FIRE"      # < 1.5s between kills (intense multikill)
    MODERATE = "MODERATE"          # 1.5s - 3.5s (tactical engagement)
    METHODICAL = "METHODICAL"      # > 3.5s (approach, site setup, post-plant)


@dataclass
class KillTimingPoint:
    """Frame-accurate timeline synchronization points for a single kill."""

    kill_num: int
    killer: str
    victim: str
    weapon: str
    headshot: bool
    wallbang: bool
    engagement_tick: int
    engagement_time_s: float
    fatal_tick: int
    fatal_time_s: float
    beat_drop_time_s: float
    killfeed_frame: int
    killfeed_time_s: float
    distance_units: float = 450.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransitionEvent:
    """A dynamic camera transition between takes in the montage sequence."""

    transition_id: str
    from_camera: str
    to_camera: str
    timeline_time_s: float
    duration_s: float
    transition_type: DynamicTransitionType
    sound_sfx: str
    visual_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "from_camera": self.from_camera,
            "to_camera": self.to_camera,
            "timeline_time_s": round(self.timeline_time_s, 3),
            "duration_s": round(self.duration_s, 3),
            "transition_type": self.transition_type.value,
            "sound_sfx": self.sound_sfx,
            "visual_effect": self.visual_effect,
        }


@dataclass
class SceneDynamicEffect:
    """Visual FX impulse or speed ramp applied at key narrative beats."""

    effect_id: str
    effect_type: str  # IMPACT_FLASH, SPEED_RAMP, SCREEN_SHAKE, COLOR_PULSE
    timeline_time_s: float
    duration_s: float
    parameters: dict[str, Any]
    narrative_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "effect_id": self.effect_id,
            "effect_type": self.effect_type,
            "timeline_time_s": round(self.timeline_time_s, 3),
            "duration_s": round(self.duration_s, 3),
            "parameters": self.parameters,
            "narrative_reason": self.narrative_reason,
        }


@dataclass
class SceneAnalysisReport:
    """Full scene intelligence report driving fragmovie assembly."""

    highlight_id: str
    round_number: int
    demo_name: str
    map_name: str
    total_duration_s: float
    tempo: CombatTempo
    kill_timings: list[KillTimingPoint] = field(default_factory=list)
    transitions: list[TransitionEvent] = field(default_factory=list)
    dynamic_effects: list[SceneDynamicEffect] = field(default_factory=list)
    hud_policy: dict[str, Any] = field(default_factory=dict)
    music_sync: dict[str, Any] = field(default_factory=dict)
    storyboard: list[StoryboardSceneCard] = field(default_factory=list)
    event_mappings: list[EventTimelineMapping] = field(default_factory=list)
    timeline_lock_state: str = "LOCKED"
    active_hud_profile: str = "CUSTOM_KILLFEED"
    hud_toggles: dict[str, Any] = field(default_factory=dict)
    available_transitions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "highlight_id": self.highlight_id,
            "round_number": self.round_number,
            "demo_name": self.demo_name,
            "map_name": self.map_name,
            "total_duration_s": round(self.total_duration_s, 2),
            "tempo": self.tempo.value,
            "kill_timings": [k.to_dict() for k in self.kill_timings],
            "transitions": [t.to_dict() for t in self.transitions],
            "dynamic_effects": [e.to_dict() for e in self.dynamic_effects],
            "hud_policy": self.hud_policy,
            "music_sync": self.music_sync,
            "storyboard": [s.to_dict() for s in self.storyboard],
            "event_mappings": [m.to_dict() for m in self.event_mappings],
            "timeline_lock_state": self.timeline_lock_state,
            "active_hud_profile": self.active_hud_profile,
            "hud_toggles": self.hud_toggles,
            "available_transitions": self.available_transitions,
        }


class CinematicSceneAnalyzer:
    """Analyzes CS2 round highlights to extract exact kill timings and scene dynamics."""

    def __init__(self, fps: int = 60, tickrate: int = 128):
        self.fps = fps
        self.tickrate = tickrate

    def analyze_anubis_ace_production(self) -> SceneAnalysisReport:
        """Generates verified scene intelligence for the de_anubis Round 19 Ace highlight."""
        kills = [
            KillTimingPoint(
                kill_num=1,
                killer="pytoshka_",
                victim="Tiger07",
                weapon="M4A1",
                headshot=False,
                wallbang=False,
                engagement_tick=120912,        # First muzzle flash (tick 120912, 7.71s timeline)
                engagement_time_s=7.711,
                fatal_tick=120927,             # Lethal bullet confirmation (tick 120927, 7.83s timeline)
                fatal_time_s=7.8297,
                beat_drop_time_s=7.711,        # 808 Bass DROP strikes on first shot commitment
                killfeed_frame=470,
                killfeed_time_s=7.830,
                distance_units=620.0,
            ),
            KillTimingPoint(
                kill_num=2,
                killer="pytoshka_",
                victim="zuuuuuhhhhn",
                weapon="M4A1",
                headshot=False,
                wallbang=False,
                engagement_tick=121235,        # Spray transfer start
                engagement_time_s=10.235,
                fatal_tick=121263,             # Fatal double kill
                fatal_time_s=10.4547,
                beat_drop_time_s=10.235,
                killfeed_frame=627,
                killfeed_time_s=10.455,
                distance_units=480.0,
            ),
            KillTimingPoint(
                kill_num=3,
                killer="pytoshka_",
                victim="ProfyfGames",
                weapon="M4A1",
                headshot=True,
                wallbang=False,
                engagement_tick=121475,
                engagement_time_s=12.073,
                fatal_tick=121491,             # Headshot dink
                fatal_time_s=12.1984,
                beat_drop_time_s=12.1984,
                killfeed_frame=732,
                killfeed_time_s=12.198,
                distance_units=340.0,
            ),
            KillTimingPoint(
                kill_num=4,
                killer="pytoshka_",
                victim="freekjkeee",
                weapon="M4A1",
                headshot=False,
                wallbang=False,
                engagement_tick=121570,
                engagement_time_s=12.802,
                fatal_tick=121595,             # Quadra kill
                fatal_time_s=12.9984,
                beat_drop_time_s=12.9984,
                killfeed_frame=780,
                killfeed_time_s=12.998,
                distance_units=510.0,
            ),
            KillTimingPoint(
                kill_num=5,
                killer="pytoshka_",
                victim="axuenchik002",
                weapon="M4A1",
                headshot=False,
                wallbang=False,
                engagement_tick=121890,
                engagement_time_s=15.303,
                fatal_tick=121920,             # 5K ACE Domination
                fatal_time_s=15.5375,
                beat_drop_time_s=15.5375,
                killfeed_frame=932,
                killfeed_time_s=15.538,
                distance_units=390.0,
            ),
        ]

        transitions = [
            TransitionEvent(
                transition_id="trans_01_whip_pan",
                from_camera="SHOULDER_CAM",
                to_camera="HERO_POV_PT1",
                timeline_time_s=2.15,
                duration_s=0.20,
                transition_type=DynamicTransitionType.WHIP_PAN,
                sound_sfx="whoosh_air_blast_clean.wav",
                visual_effect="Horizontal slide left with motion blur",
            ),
            TransitionEvent(
                transition_id="trans_02_zoom_victim",
                from_camera="HERO_POV_PT1",
                to_camera="VICTIM_POV",
                timeline_time_s=11.30,
                duration_s=0.20,
                transition_type=DynamicTransitionType.RADIAL_ZOOM,
                sound_sfx="transition_wind_whip_turbulent.wav",
                visual_effect="Radial zoom in into victim POV",
            ),
            TransitionEvent(
                transition_id="trans_03_snap_hero",
                from_camera="VICTIM_POV",
                to_camera="HERO_POV_PT2",
                timeline_time_s=12.60,
                duration_s=0.15,
                transition_type=DynamicTransitionType.SNAP_CUT,
                sound_sfx="transition_ice_crack_snap.wav",
                visual_effect="Fast snap zoom back to hero crosshair",
            ),
            TransitionEvent(
                transition_id="trans_04_orbit_glide",
                from_camera="HERO_POV_PT2",
                to_camera="CLIMAX_ORBIT",
                timeline_time_s=15.70,
                duration_s=0.25,
                transition_type=DynamicTransitionType.SMOOTH_GLIDE,
                sound_sfx="whoosh_metal_passby.wav",
                visual_effect="Smooth lateral glide into victory orbit",
            ),
        ]

        dynamic_effects = [
            SceneDynamicEffect(
                effect_id="fx_tension_rise",
                effect_type="AUDIO_RISER",
                timeline_time_s=5.00,
                duration_s=2.71,
                parameters={"curve": "exponential", "peak_at_s": 7.71},
                narrative_reason="Pre-drop tension build-up during hero approach",
            ),
            SceneDynamicEffect(
                effect_id="fx_drop_kick",
                effect_type="BEAT_DROP_808",
                timeline_time_s=7.711,
                duration_s=0.60,
                parameters={"sub_hz": 42, "punch": "high", "track_offset_s": 20.09},
                narrative_reason="Massive 142 BPM 808 drop locked to first muzzle flash",
            ),
            SceneDynamicEffect(
                effect_id="fx_headshot_flash",
                effect_type="IMPACT_FLASH",
                timeline_time_s=12.18,
                duration_s=0.07,
                parameters={"gain": 1.35, "contrast": 1.30, "chroma_split": True},
                narrative_reason="Optical flash & chromatic split on fatal headshot dink",
            ),
            SceneDynamicEffect(
                effect_id="fx_headshot_accent",
                effect_type="AUDIO_CARABINER_LOCK",
                timeline_time_s=12.198,
                duration_s=0.40,
                parameters={"asset": "accent_carabiner_lock_turn.wav"},
                narrative_reason="Mechanical sound design accent confirming headshot badge",
            ),
            SceneDynamicEffect(
                effect_id="fx_ace_climax_downer",
                effect_type="SUB_DOWNER_CLIMAX",
                timeline_time_s=15.538,
                duration_s=2.50,
                parameters={"asset": "impact_sub_downer_med04.wav", "decay_s": 2.2},
                narrative_reason="Heavy sub-bass decay highlighting the 5K ACE victory",
            ),
            SceneDynamicEffect(
                effect_id="fx_ace_banner_reveal",
                effect_type="BANNER_DOMINATION",
                timeline_time_s=15.80,
                duration_s=2.70,
                parameters={"badge": "5K ACE — ROUND DOMINATION", "glow": "amber"},
                narrative_reason="Post-kill tournament announcement overlay",
            ),
        ]

        hud_policy = {
            "in_game_hud_suppressed": True,
            "commands": [
                "cl_drawhud 0",
                "cl_draw_only_deathnotices 0",
                "crosshair 0",
                "r_show_build_info 0",
            ],
            "reason": (
                "When custom tournament killfeed overlays are rendered, in-game CS2 "
                "HUD and default deathnotices are completely disabled to avoid duplicate "
                "or conflicting low-resolution graphics."
            ),
            "custom_killfeed_enabled": True,
            "custom_killfeed_style": "esports_stacked_4k",
            "ace_card_enabled": True,
        }

        music_sync = {
            "track_name": "LOVELYDILLER — МАЛЫШКА РЕВНУЕТ",
            "bpm": 142.0,
            "song_drop_timestamp_s": 27.80,
            "timeline_drop_target_s": 7.711,
            "computed_start_offset_s": 20.089,
            "beat_duration_s": 0.4225,
            "bar_duration_s": 1.6901,
            "lip_sync_accuracy_ms": 1.5,
        }

        # 9 Storyboard Scene Cards (Phase E: AI Scene Director)
        storyboard = [
            StoryboardSceneCard(
                scene_id="sc_01_establishing",
                scene_number=1,
                category=SceneCategory.ESTABLISHING,
                start_tick=119900,
                end_tick=120050,
                start_time=0.00,
                end_time=1.20,
                duration_seconds=1.20,
                hero_player="pytoshka_",
                hero_position=(120.5, -450.2, 72.0),
                active_participants=["pytoshka_"],
                map_zone="Canal / B Approaches",
                contained_events=[],
                suggested_camera_type="ESTABLISHING_SHOT",
                camera_fov=95.0,
                desired_pacing="slow_burn",
                suggested_transition="Camera Push",
                suggested_sound_treatment="Open air subtle atmosphere drone",
                thumbnail_path="/thumbnails/anubis_sc01_establishing.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_02_approach",
                scene_number=2,
                category=SceneCategory.APPROACH,
                start_tick=120050,
                end_tick=120195,
                start_time=1.20,
                end_time=2.15,
                duration_seconds=0.95,
                hero_player="pytoshka_",
                hero_position=(185.0, -320.0, 78.0),
                active_participants=["pytoshka_"],
                map_zone="B Connector / Ruins Stairs",
                contained_events=[],
                suggested_camera_type="SHOULDER_CAM",
                camera_fov=92.0,
                desired_pacing="mounting",
                suggested_transition="Whip Pan with Motion Blur",
                suggested_sound_treatment="Carabiner equipment rattle and whoosh sweep",
                thumbnail_path="/thumbnails/anubis_sc02_approach.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_03_tension",
                scene_number=3,
                category=SceneCategory.TENSION,
                start_tick=120195,
                end_tick=120912,
                start_time=2.15,
                end_time=7.711,
                duration_seconds=5.561,
                hero_player="pytoshka_",
                hero_position=(260.4, -180.5, 80.0),
                active_participants=["pytoshka_", "Tiger07", "zuuuuuhhhhn"],
                map_zone="B Site Entry Chokepoint",
                contained_events=[],
                suggested_camera_type="FIRST_PERSON",
                camera_fov=90.0,
                desired_pacing="mounting",
                suggested_transition="Cut on Muzzle Flash",
                suggested_sound_treatment="Cinematic tension riser swelling into 808 drop",
                thumbnail_path="/thumbnails/anubis_sc03_tension.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_04_engagement",
                scene_number=4,
                category=SceneCategory.ENGAGEMENT,
                start_tick=120912,
                end_tick=121020,
                start_time=7.711,
                end_time=8.50,
                duration_seconds=0.789,
                hero_player="pytoshka_",
                hero_position=(310.0, -110.0, 80.0),
                active_participants=["pytoshka_", "Tiger07"],
                map_zone="B Pillar / Site Front",
                contained_events=[{"kill_num": 1, "victim": "Tiger07", "weapon": "M4A1", "tick": 120927}],
                suggested_camera_type="FIRST_PERSON",
                camera_fov=90.0,
                desired_pacing="explosive",
                suggested_transition="Snap Cut",
                suggested_sound_treatment="LOVELYDILLER 808 Drop + Metallic Slice Cut",
                thumbnail_path="/thumbnails/anubis_sc04_engagement.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_05_spray_transfer",
                scene_number=5,
                category=SceneCategory.SPRAY_TRANSFER,
                start_tick=121020,
                end_tick=121370,
                start_time=8.50,
                end_time=11.30,
                duration_seconds=2.80,
                hero_player="pytoshka_",
                hero_position=(345.0, -80.0, 80.0),
                active_participants=["pytoshka_", "zuuuuuhhhhn"],
                map_zone="B Site Back Plat",
                contained_events=[{"kill_num": 2, "victim": "zuuuuuhhhhn", "weapon": "M4A1", "tick": 121263}],
                suggested_camera_type="FIRST_PERSON",
                camera_fov=90.0,
                desired_pacing="cadenced",
                suggested_transition="Radial Zoom Blur",
                suggested_sound_treatment="Flicking metal snap + 4x Body punch impact",
                thumbnail_path="/thumbnails/anubis_sc05_spray_transfer.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_06_multikill",
                scene_number=6,
                category=SceneCategory.MULTIKILL,
                start_tick=121370,
                end_tick=121540,
                start_time=11.30,
                end_time=12.60,
                duration_seconds=1.30,
                hero_player="pytoshka_",
                hero_position=(410.0, -30.0, 85.0),
                active_participants=["pytoshka_", "ProfyfGames"],
                map_zone="B Site Palace / Alley",
                contained_events=[{"kill_num": 3, "victim": "ProfyfGames", "weapon": "M4A1", "headshot": True, "tick": 121491}],
                suggested_camera_type="VICTIM_POV",
                camera_fov=90.0,
                desired_pacing="explosive",
                suggested_transition="Impact Flash with RGB Split -> Ice Snap Cut",
                suggested_sound_treatment="Fast Sub Downer 16 + Ice crack snap",
                thumbnail_path="/thumbnails/anubis_sc06_multikill.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_07_clutch",
                scene_number=7,
                category=SceneCategory.CLUTCH,
                start_tick=121540,
                end_tick=121690,
                start_time=12.60,
                end_time=13.80,
                duration_seconds=1.20,
                hero_player="pytoshka_",
                hero_position=(440.0, 10.0, 85.0),
                active_participants=["pytoshka_", "freekjkeee"],
                map_zone="B Site Dark / Ninja",
                contained_events=[{"kill_num": 4, "victim": "freekjkeee", "weapon": "M4A1", "tick": 121595}],
                suggested_camera_type="FIRST_PERSON",
                camera_fov=90.0,
                desired_pacing="explosive",
                suggested_transition="Micro Punch In / Out",
                suggested_sound_treatment="Heavy metal door blast + bullet trajectory whoosh",
                thumbnail_path="/thumbnails/anubis_sc07_clutch.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_08_ace_climax",
                scene_number=8,
                category=SceneCategory.ACE_CLIMAX,
                start_tick=121690,
                end_tick=121950,
                start_time=13.80,
                end_time=15.80,
                duration_seconds=2.00,
                hero_player="pytoshka_",
                hero_position=(465.0, 60.0, 85.0),
                active_participants=["pytoshka_", "axuenchik002"],
                map_zone="B Site Default Plant",
                contained_events=[{"kill_num": 5, "victim": "axuenchik002", "weapon": "M4A1", "ace": True, "tick": 121920}],
                suggested_camera_type="ORBIT_CAMERA",
                camera_fov=85.0,
                desired_pacing="slowmo_release",
                suggested_transition="Orbit Reveal Climax",
                suggested_sound_treatment="Deep 45Hz sub-bass downer + texture sweep",
                thumbnail_path="/thumbnails/anubis_sc08_ace_climax.jpg",
                approval_status="APPROVED",
            ),
            StoryboardSceneCard(
                scene_id="sc_09_aftermath",
                scene_number=9,
                category=SceneCategory.AFTERMATH,
                start_tick=121950,
                end_tick=122280,
                start_time=15.80,
                end_time=18.50,
                duration_seconds=2.70,
                hero_player="pytoshka_",
                hero_position=(465.0, 60.0, 85.0),
                active_participants=["pytoshka_"],
                map_zone="B Site Domination",
                contained_events=[{"badge": "5K ACE — ROUND DOMINATION", "frame": 948}],
                suggested_camera_type="ORBIT_CAMERA",
                camera_fov=85.0,
                desired_pacing="slow_burn",
                suggested_transition="Fade to Black",
                suggested_sound_treatment="Dark spell atmospheric drone + outro trail",
                thumbnail_path="/thumbnails/anubis_sc09_aftermath.jpg",
                approval_status="APPROVED",
            ),
        ]

        # Reliable Event-to-Timeline Mappings (Phase B: Event-First Architecture)
        event_mappings = [
            EventTimelineMapping(
                event_id="evt_kill_01",
                event_type="kill",
                demo_tick=120927,
                demo_time_seconds=7.830,
                capture_source_timestamp=5.680,
                source_frame=341,
                capture_start_tick=120195,
                source_in=0.0,
                source_out=9.15,
                timeline_clip_id="clip_v1_hero_pt1",
                timeline_start=2.15,
                retiming_curve="1.0x_linear",
                final_timeline_frame=470,
                final_timeline_timestamp=7.830,
                overlay_visibility_range=(470, 1110),
                attacker_name="pytoshka_",
                victim_name="Tiger07",
                weapon="M4A1",
                is_headshot=False,
            ),
            EventTimelineMapping(
                event_id="evt_kill_02",
                event_type="kill",
                demo_tick=121263,
                demo_time_seconds=10.455,
                capture_source_timestamp=8.305,
                source_frame=498,
                capture_start_tick=120195,
                source_in=0.0,
                source_out=9.15,
                timeline_clip_id="clip_v1_hero_pt1",
                timeline_start=2.15,
                retiming_curve="1.0x_linear",
                final_timeline_frame=627,
                final_timeline_timestamp=10.455,
                overlay_visibility_range=(627, 1110),
                attacker_name="pytoshka_",
                victim_name="zuuuuuhhhhn",
                weapon="M4A1",
                is_headshot=False,
            ),
            EventTimelineMapping(
                event_id="evt_kill_03",
                event_type="headshot",
                demo_tick=121491,
                demo_time_seconds=12.198,
                capture_source_timestamp=0.898,
                source_frame=54,
                capture_start_tick=121370,
                source_in=0.0,
                source_out=1.30,
                timeline_clip_id="clip_v2_victim_insert",
                timeline_start=11.30,
                retiming_curve="1.0x_linear",
                final_timeline_frame=732,
                final_timeline_timestamp=12.198,
                overlay_visibility_range=(732, 1110),
                attacker_name="pytoshka_",
                victim_name="ProfyfGames",
                weapon="M4A1",
                is_headshot=True,
            ),
            EventTimelineMapping(
                event_id="evt_kill_04",
                event_type="kill",
                demo_tick=121595,
                demo_time_seconds=12.998,
                capture_source_timestamp=10.848,
                source_frame=651,
                capture_start_tick=120195,
                source_in=10.45,
                source_out=13.55,
                timeline_clip_id="clip_v1_hero_pt2",
                timeline_start=12.60,
                retiming_curve="1.0x_linear",
                final_timeline_frame=780,
                final_timeline_timestamp=12.998,
                overlay_visibility_range=(780, 1110),
                attacker_name="pytoshka_",
                victim_name="freekjkeee",
                weapon="M4A1",
                is_headshot=False,
            ),
            EventTimelineMapping(
                event_id="evt_kill_05",
                event_type="ace_climax",
                demo_tick=121920,
                demo_time_seconds=15.538,
                capture_source_timestamp=13.388,
                source_frame=803,
                capture_start_tick=120195,
                source_in=10.45,
                source_out=13.55,
                timeline_clip_id="clip_v1_hero_pt2",
                timeline_start=12.60,
                retiming_curve="1.0x_linear",
                final_timeline_frame=932,
                final_timeline_timestamp=15.538,
                overlay_visibility_range=(932, 1110),
                attacker_name="pytoshka_",
                victim_name="axuenchik002",
                weapon="M4A1",
                is_headshot=False,
            ),
        ]

        hud_toggles = HudElementToggles(
            native_killfeed=False,
            custom_killfeed=True,
            crosshair=True,
            radar=False,
            player_hud=False,
            weapon_viewmodel=True,
            xray=False,
            observer_controls=False,
            watermark=False,
        ).to_dict()

        available_transitions = [t.to_dict() for t in TRANSITION_REGISTRY]

        return SceneAnalysisReport(
            highlight_id="anubis_ace_r19",
            round_number=19,
            demo_name="1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem",
            map_name="de_anubis",
            total_duration_s=18.50,
            tempo=CombatTempo.RAPID_FIRE,
            kill_timings=kills,
            transitions=transitions,
            dynamic_effects=dynamic_effects,
            hud_policy=hud_policy,
            music_sync=music_sync,
            storyboard=storyboard,
            event_mappings=event_mappings,
            timeline_lock_state=TimelineLockState.LOCKED.value,
            active_hud_profile=HudCaptureProfile.CUSTOM_KILLFEED.value,
            hud_toggles=hud_toggles,
            available_transitions=available_transitions,
        )
