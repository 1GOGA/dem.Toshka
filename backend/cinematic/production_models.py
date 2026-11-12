"""
Production models and state machine for dem.Toshka Cinematic Studio Phase 3.3.

Implements:
1. Strict Timeline Lock State Machine (Phase B: Event-First Production Architecture)
2. Precise Event-to-Timeline Mapping Model
3. Capture & HUD Profiles with convar investigation (Phase C)
4. 9 Scene Categories & Director Storyboard Manifest (Phase E)
5. Dynamic Transitions & VFX Catalog (Phase F)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


# ============================================================================
# PHASE B: Strict Production Ordering & Timeline Lock State Machine
# ============================================================================

class TimelineLockState(str, Enum):
    """Timeline lock states enforcing strict event-first production ordering."""
    UNINITIALIZED = "UNINITIALIZED"
    FOOTAGE_CAPTURING = "FOOTAGE_CAPTURING"
    TIMELINE_DRAFTING = "TIMELINE_DRAFTING"
    PENDING_TIMELINE_LOCK = "PENDING_TIMELINE_LOCK"  # Kill feed CANNOT generate in this state
    LOCKED = "LOCKED"                              # Timeline is frozen, kill feed can calculate
    RENDERED = "RENDERED"                          # Final deliverable rendered
    INVALIDATED = "INVALIDATED"                    # Timeline modified after lock, overlays invalidated


@dataclass
class EventTimelineMapping:
    """Exact mapping of a game demo event to its final timeline video frame.
    
    Guarantees:
    - Event timestamps originate strictly from real demo tick / second data.
    - Music beats NEVER modify kill event timestamps.
    - Preserves source in/out and retiming curves.
    """
    event_id: str
    event_type: str                         # "kill", "headshot", "clutch_win", "ace_climax", "bomb_defused"
    demo_tick: int
    demo_time_seconds: float
    capture_source_timestamp: float         # Raw timestamp inside the captured take
    source_frame: int                       # Frame index in raw capture (at capture FPS)
    capture_start_tick: int
    source_in: float                        # Trim start in source video (seconds)
    source_out: float                       # Trim end in source video (seconds)
    timeline_clip_id: str                   # ID of the clip holding this event on V1/V2
    timeline_start: float                   # Start of clip on the master timeline (seconds)
    retiming_curve: str                     # e.g., "1.0x_linear", "optical_slowmo_0.5x"
    final_timeline_frame: int               # Exact frame in final 60 FPS master
    final_timeline_timestamp: float         # Exact second in master video
    overlay_visibility_range: tuple[int, int]  # (start_frame, end_frame)
    attacker_name: str
    victim_name: str
    weapon: str
    is_headshot: bool
    is_wallbang: bool = False
    is_noscope: bool = False
    is_blind: bool = False
    is_through_smoke: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "demo_tick": self.demo_tick,
            "demo_time_seconds": round(self.demo_time_seconds, 3),
            "capture_source_timestamp": round(self.capture_source_timestamp, 3),
            "source_frame": self.source_frame,
            "capture_start_tick": self.capture_start_tick,
            "source_in": round(self.source_in, 3),
            "source_out": round(self.source_out, 3),
            "timeline_clip_id": self.timeline_clip_id,
            "timeline_start": round(self.timeline_start, 3),
            "retiming_curve": self.retiming_curve,
            "final_timeline_frame": self.final_timeline_frame,
            "final_timeline_timestamp": round(self.final_timeline_timestamp, 3),
            "overlay_visibility_range": list(self.overlay_visibility_range),
            "attacker_name": self.attacker_name,
            "victim_name": self.victim_name,
            "weapon": self.weapon,
            "is_headshot": self.is_headshot,
            "is_wallbang": self.is_wallbang,
            "is_noscope": self.is_noscope,
            "is_blind": self.is_blind,
            "is_through_smoke": self.is_through_smoke,
        }


# ============================================================================
# PHASE C: HUD & Capture Profiles
# ============================================================================

class HudCaptureProfile(str, Enum):
    """Capture profiles for CS2 demo playback and cinematics."""
    ORIGINAL_HUD = "ORIGINAL_HUD"        # Native CS2 HUD + native killfeed, no custom overlays
    MINIMAL_HUD = "MINIMAL_HUD"          # cl_draw_only_deathnotices 1, native killfeed + crosshair
    CUSTOM_KILLFEED = "CUSTOM_KILLFEED"  # cl_drawhud 0 (sv_cheats 1), custom tournament killfeed
    CLEAN_CINEMATIC = "CLEAN_CINEMATIC"  # 100% clean footage, cl_drawhud 0, crosshair 0, no overlays


@dataclass
class HudElementToggles:
    """Fine-grained toggle configuration for HUD elements.
    
    CS2 Source 2 Convar Reality Audit:
    - cl_drawhud (0/1): Global HUD suppression. Requires sv_cheats 1 in local demo playback. (Fully supported)
    - cl_draw_only_deathnotices (0/1): Suppresses radar, health, ammo, retains only death notices and crosshair. (Supported)
    - crosshair (0/1): Toggles crosshair independently. (Fully supported)
    - r_drawviewmodel (0/1): Hides first-person weapon model (Useful for clean cinematics). Requires sv_cheats 1. (Supported)
    - spec_show_xray (0/1): Toggles observer x-ray glow through walls. (Supported)
    - mirv_deathmsg (HLAE convar): Advanced deathnotice filtering if HLAE is active.
    - Dem.Toshka Watermark: Software overlay switch (0% / OFF by default for clean masters).
    """
    native_killfeed: bool = False
    custom_killfeed: bool = True
    crosshair: bool = True
    radar: bool = False
    player_hud: bool = False
    weapon_viewmodel: bool = True
    xray: bool = False
    observer_controls: bool = False
    watermark: bool = False

    def to_convars(self, profile: HudCaptureProfile) -> dict[str, str]:
        """Generate accurate CS2 console commands for this configuration."""
        cmds: dict[str, str] = {}
        
        if profile == HudCaptureProfile.ORIGINAL_HUD:
            cmds["sv_cheats"] = "1"
            cmds["cl_drawhud"] = "1"
            cmds["cl_draw_only_deathnotices"] = "0"
            cmds["crosshair"] = "1"
            cmds["r_drawviewmodel"] = "1"
            cmds["spec_show_xray"] = "1" if self.xray else "0"
        elif profile == HudCaptureProfile.MINIMAL_HUD:
            cmds["sv_cheats"] = "1"
            cmds["cl_drawhud"] = "1"
            cmds["cl_draw_only_deathnotices"] = "1"
            cmds["crosshair"] = "1" if self.crosshair else "0"
            cmds["r_drawviewmodel"] = "1" if self.weapon_viewmodel else "0"
            cmds["spec_show_xray"] = "1" if self.xray else "0"
        elif profile == HudCaptureProfile.CUSTOM_KILLFEED:
            cmds["sv_cheats"] = "1"
            cmds["cl_drawhud"] = "0"
            cmds["cl_draw_only_deathnotices"] = "0"
            cmds["crosshair"] = "1" if self.crosshair else "0"
            cmds["r_drawviewmodel"] = "1" if self.weapon_viewmodel else "0"
            cmds["spec_show_xray"] = "1" if self.xray else "0"
        elif profile == HudCaptureProfile.CLEAN_CINEMATIC:
            cmds["sv_cheats"] = "1"
            cmds["cl_drawhud"] = "0"
            cmds["cl_draw_only_deathnotices"] = "0"
            cmds["crosshair"] = "0"
            cmds["r_drawviewmodel"] = "1" if self.weapon_viewmodel else "0"
            cmds["spec_show_xray"] = "0"
            
        return cmds

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ============================================================================
# PHASE E: 9 Scene Categories & Director Storyboard
# ============================================================================

class SceneCategory(str, Enum):
    """The 9 narrative scene types recognized by Cinematic Scene Director V2."""
    ESTABLISHING = "ESTABLISHING"        # Intro map flythrough, zone overview, match intro
    APPROACH = "APPROACH"                # Player rotation, shoulder tracking, tactical advance
    TENSION = "TENSION"                  # Pre-contact hold, corner slice, silent footsteps, heartbeat
    ENGAGEMENT = "ENGAGEMENT"            # First weapon fire, bullet velocity, initial damage trades
    SPRAY_TRANSFER = "SPRAY_TRANSFER"    # Rapid consecutive target acquisition, recoil control
    MULTIKILL = "MULTIKILL"              # Rapid sequence of eliminations (double, triple, quad)
    CLUTCH = "CLUTCH"                    # 1vX isolation, high-stakes decision, defuse denial
    ACE_CLIMAX = "ACE_CLIMAX"            # Round-ending 5th kill, orbital freeze/slow-mo, trophy moment
    AFTERMATH = "AFTERMATH"              # Post-round celebration, bomb explosion, weapon inspect


@dataclass
class StoryboardSceneCard:
    """A narrative scene block in the Director Storyboard."""
    scene_id: str
    scene_number: int
    category: SceneCategory
    start_tick: int
    end_tick: int
    start_time: float
    end_time: float
    duration_seconds: float
    hero_player: str
    hero_position: tuple[float, float, float]
    active_participants: list[str]
    map_zone: str
    contained_events: list[dict[str, Any]]
    suggested_camera_type: str
    camera_fov: float
    desired_pacing: str                 # "slow_burn", "mounting", "explosive", "cadenced", "slowmo_release"
    suggested_transition: str           # "Whip Pan", "Radial Zoom Blur", "Impact Flash", "Ice Snap Cut"
    suggested_sound_treatment: str      # "Atmospheric Drone", "808 Sub Punch", "Metallic Slice", "Reverse Suction"
    thumbnail_path: Optional[str] = None
    approval_status: str = "APPROVED"   # "PENDING", "APPROVED", "REJECTED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "scene_number": self.scene_number,
            "category": self.category.value,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
            "duration_seconds": round(self.duration_seconds, 3),
            "hero_player": self.hero_player,
            "hero_position": list(self.hero_position),
            "active_participants": self.active_participants,
            "map_zone": self.map_zone,
            "contained_events": self.contained_events,
            "suggested_camera_type": self.suggested_camera_type,
            "camera_fov": self.camera_fov,
            "desired_pacing": self.desired_pacing,
            "suggested_transition": self.suggested_transition,
            "suggested_sound_treatment": self.suggested_sound_treatment,
            "thumbnail_path": self.thumbnail_path,
            "approval_status": self.approval_status,
        }


# ============================================================================
# PHASE F: Dynamic Editing & Transition Engine
# ============================================================================

class TransitionFamily(str, Enum):
    CAMERA = "CAMERA"      # Whip Pan, Camera Push, Orbit Reveal, Match Motion Cut
    ZOOM = "ZOOM"          # Radial Zoom, Directional Zoom, Punch In / Punch Out
    IMPACT = "IMPACT"      # Impact Flash, Freeze Accent, Controlled Glow
    MASK = "MASK"          # Luma Wipe, Shape Reveal, Occlusion Transition
    MOTION = "MOTION"      # Speed Ramp, Optical Flow, Motion Blur, Directional Blur
    DIGITAL = "DIGITAL"    # Chromatic Aberration, RGB Split, Controlled Glitch


@dataclass
class TransitionDefinition:
    id: str
    name: str
    family: TransitionFamily
    duration_frames: int
    shutter_angle: float                # 180° = standard, 240°–360° = intense motion blur
    fusion_comp_template: Optional[str]
    description: str
    best_used_for: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "family": self.family.value,
            "duration_frames": self.duration_frames,
            "shutter_angle": self.shutter_angle,
            "fusion_comp_template": self.fusion_comp_template,
            "description": self.description,
            "best_used_for": self.best_used_for,
        }


TRANSITION_REGISTRY: list[TransitionDefinition] = [
    TransitionDefinition(
        id="trans_whip_pan_blur",
        name="Whip Pan with Motion Blur",
        family=TransitionFamily.CAMERA,
        duration_frames=14,
        shutter_angle=270.0,
        fusion_comp_template="WhipPan_MotionBlur.comp",
        description="High-velocity horizontal camera pan across player angle changes",
        best_used_for="Transitioning from Approach/Shoulder to Hero POV engagement",
    ),
    TransitionDefinition(
        id="trans_camera_push",
        name="Dynamic Camera Push",
        family=TransitionFamily.CAMERA,
        duration_frames=18,
        shutter_angle=200.0,
        fusion_comp_template="CameraPush_Linear.comp",
        description="Forward momentum push tracking player rush into contested area",
        best_used_for="Site entry and approach runs",
    ),
    TransitionDefinition(
        id="trans_orbit_reveal",
        name="Orbit Reveal Climax",
        family=TransitionFamily.CAMERA,
        duration_frames=30,
        shutter_angle=180.0,
        fusion_comp_template="OrbitReveal_Smooth.comp",
        description="Panoramic 360-degree rotational arc orbiting player model",
        best_used_for="ACE round climax, trophy showcase, bomb plant celebration",
    ),
    TransitionDefinition(
        id="trans_radial_zoom_blur",
        name="Radial Zoom Blur",
        family=TransitionFamily.ZOOM,
        duration_frames=10,
        shutter_angle=300.0,
        fusion_comp_template="Directional_ZoomBlur.comp",
        description="High-speed optical expansion centered on crosshair",
        best_used_for="Flipping to victim reaction POV during fatal gunshot",
    ),
    TransitionDefinition(
        id="trans_punch_in_out",
        name="Micro Punch In / Out",
        family=TransitionFamily.ZOOM,
        duration_frames=6,
        shutter_angle=180.0,
        fusion_comp_template="PunchInOut_Snappy.comp",
        description="Rapid 1.15x scale pop resetting to unity on muzzle discharge",
        best_used_for="Single-tap Deagle or AWP sniper shot accents",
    ),
    TransitionDefinition(
        id="trans_impact_flash_chroma",
        name="Impact Flash with RGB Split",
        family=TransitionFamily.IMPACT,
        duration_frames=8,
        shutter_angle=180.0,
        fusion_comp_template="Impact_Flash_Chroma.comp",
        description="Impulse exposure burst (Gain 3.6x) with SoftGlow and prism dispersion",
        best_used_for="Headshot dink confirmation and critical fatal frags",
    ),
    TransitionDefinition(
        id="trans_freeze_accent",
        name="Hold Frame Freeze Accent",
        family=TransitionFamily.IMPACT,
        duration_frames=6,
        shutter_angle=0.0,
        fusion_comp_template="FreezeAccent_Grain.comp",
        description="3-frame optical hold on precise fatal bullet release",
        best_used_for="Mid-air knife kill or jumping scout shot",
    ),
    TransitionDefinition(
        id="trans_luma_wipe",
        name="Luma Contrast Wipe",
        family=TransitionFamily.MASK,
        duration_frames=16,
        shutter_angle=180.0,
        fusion_comp_template="LumaWipe_Threshold.comp",
        description="Luminance-driven diagonal wipe masking shadow into light",
        best_used_for="Indoor-to-outdoor site transition (e.g. Anubis Canal to B Site)",
    ),
    TransitionDefinition(
        id="trans_speed_ramp_blur",
        name="Speed Ramp Retime with Directional Blur",
        family=TransitionFamily.MOTION,
        duration_frames=24,
        shutter_angle=250.0,
        fusion_comp_template="SpeedRamp_Smooth.comp",
        description="4x speed burst decelerating into 0.35x slow-motion on kill tick",
        best_used_for="Spray transfer transitions between multiple enemies",
    ),
    TransitionDefinition(
        id="trans_controlled_glitch",
        name="Controlled Digital Glitch",
        family=TransitionFamily.DIGITAL,
        duration_frames=8,
        shutter_angle=180.0,
        fusion_comp_template="DigitalGlitch_RGB.comp",
        description="RGB scanline jitter and horizontal displacement slice",
        best_used_for="Flashbang recovery or wallbang penetration kill",
    ),
]


# ============================================================================
# PHASE G: Production Workbench State
# ============================================================================

@dataclass
class ProductionWorkbenchState:
    """Current state of the entire Cinematic Production Workbench."""
    project_id: str
    project_name: str
    demo_file: str
    highlight_id: str
    timeline_lock_state: TimelineLockState
    active_hud_profile: HudCaptureProfile
    hud_toggles: HudElementToggles
    storyboard_scenes: list[StoryboardSceneCard]
    event_mappings: list[EventTimelineMapping]
    active_soundtrack_name: str
    soundtrack_bpm: float
    soundtrack_drop_time: float
    total_timeline_duration: float
    timeline_fps: int = 60
    has_render_master: bool = False
    master_video_path: Optional[str] = None
    tiktok_video_path: Optional[str] = None
    preview_video_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "demo_file": self.demo_file,
            "highlight_id": self.highlight_id,
            "timeline_lock_state": self.timeline_lock_state.value,
            "active_hud_profile": self.active_hud_profile.value,
            "hud_toggles": self.hud_toggles.to_dict(),
            "storyboard_scenes": [s.to_dict() for s in self.storyboard_scenes],
            "event_mappings": [m.to_dict() for m in self.event_mappings],
            "active_soundtrack_name": self.active_soundtrack_name,
            "soundtrack_bpm": self.soundtrack_bpm,
            "soundtrack_drop_time": round(self.soundtrack_drop_time, 3),
            "total_timeline_duration": round(self.total_timeline_duration, 3),
            "timeline_fps": self.timeline_fps,
            "has_render_master": self.has_render_master,
            "master_video_path": self.master_video_path,
            "tiktok_video_path": self.tiktok_video_path,
            "preview_video_path": self.preview_video_path,
        }
