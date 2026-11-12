"""dem.Toshka Cinematic Studio — Phase 3.5 VFX Decision Engine.

Provides automated, context-aware visual effects intelligence:
- Evaluates scene type, camera choreography, weapon/player visibility, and temporal cadence
- Selects appropriate VFX treatments while actively enforcing "less is better"
- Rejects inappropriate effects with actionable reasoning
- Generates 3 treatment tiers: Clean Original, Subtle VFX, Strong Cinematic
- Respects user Like/Dislike feedback
"""

from __future__ import annotations

import json
import logging
import pathlib
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("demtoshka.cinematic.vfx_decision_engine")

EFFECT_CATALOG_PATH = pathlib.Path("reference_library/effect_intelligence/effect_catalog.json")


@dataclass
class VfxSceneContext:
    """Multi-dimensional context describing a scene or shot."""
    scene_id: str
    scene_category: str  # ESTABLISHING, APPROACH, TENSION, ENGAGEMENT, SPRAY_TRANSFER, MULTIKILL, CLUTCH, ACE_CLIMAX, AFTERMATH
    camera_type: str     # FIRST_PERSON, SHOULDER_CAM, ORBIT_CAMERA, VICTIM_POV, FREE_CAM
    fps: float
    time_seconds: float
    duration_seconds: float
    is_kill_event: bool = False
    is_headshot: bool = False
    is_ace_kill: bool = False
    is_clutch: bool = False
    player_visible: bool = True
    enemy_visible: bool = False
    weapon_visible: bool = True
    is_outdoor_sky_visible: bool = False
    has_music_drop: bool = False
    rapid_kill_interval: Optional[float] = None  # seconds since prior kill (if < 0.9s -> rapid sequence)
    current_editing_intensity: float = 0.5       # 0.0 (calm) to 1.0 (hyper-frenetic)
    user_liked_effects: List[str] = field(default_factory=list)
    user_disliked_effects: List[str] = field(default_factory=list)


@dataclass
class SelectedEffectItem:
    effect_id: str
    name: str
    category: str
    intensity: float  # 0.0 to 1.0
    timing_range: str
    justification: str
    fusion_preset: str
    confidence: str


@dataclass
class RejectedEffectItem:
    effect_id: str
    name: str
    category: str
    rejection_reason: str


@dataclass
class VfxDecision:
    """Actionable decision output for a specific shot or scene."""
    decision_id: str
    scene_id: str
    treatment_tier: str  # CLEAN, SUBTLE, STRONG_CINEMATIC
    selected_effects: List[SelectedEffectItem]
    rejected_effects: List[RejectedEffectItem]
    fusion_macro_recipe: str
    color_page_grade: str
    fairlight_audio_ducking_db: float
    summary: str


class VfxDecisionEngine:
    """Directorial intelligence engine that selects and coordinates VFX."""

    def __init__(self, catalog_path: pathlib.Path = EFFECT_CATALOG_PATH):
        self.catalog_path = pathlib.Path(catalog_path)
        self.catalog: Dict[str, Any] = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        if not self.catalog_path.exists():
            logger.warning("Effect catalog %s not found. Using empty catalog.", self.catalog_path)
            return {}
        try:
            with open(self.catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load effect catalog: %s", e)
            return {}

    def decide_vfx(self, context: VfxSceneContext, requested_tier: str = "SUBTLE") -> VfxDecision:
        """Determines optimal VFX treatments for a given shot context."""
        selected: List[SelectedEffectItem] = []
        rejected: List[RejectedEffectItem] = []

        is_subtle = (requested_tier.upper() == "SUBTLE")
        is_clean = (requested_tier.upper() == "CLEAN")

        if is_clean:
            return VfxDecision(
                decision_id=f"vfx_{context.scene_id}_clean",
                scene_id=context.scene_id,
                treatment_tier="CLEAN",
                selected_effects=[],
                rejected_effects=[
                    RejectedEffectItem(
                        effect_id="ALL_VFX",
                        name="All Effects",
                        category="ALL",
                        rejection_reason="Clean Original mode selected. 100% in-engine authenticity preserved."
                    )
                ],
                fusion_macro_recipe="MediaIn1 -> MediaOut1 (Pass-through)",
                color_page_grade="Rec.709 Standard Clean Pass",
                fairlight_audio_ducking_db=0.0,
                summary="Clean unedited in-engine footage pass."
            )

        # ---------------- 1. RULE: SLOW MOTION DECISION ----------------
        slowmo_candidate = self.catalog.get("EFF_TIME_OPTICAL_FLOW_SLOWMO")
        if slowmo_candidate:
            if "EFF_TIME_OPTICAL_FLOW_SLOWMO" in context.user_disliked_effects:
                rejected.append(RejectedEffectItem(
                    effect_id="EFF_TIME_OPTICAL_FLOW_SLOWMO",
                    name=slowmo_candidate["name"],
                    category="TIME_MANIPULATION",
                    rejection_reason="Suppressed by user preference (Disliked)."
                ))
            elif context.rapid_kill_interval is not None and context.rapid_kill_interval < 0.85:
                rejected.append(RejectedEffectItem(
                    effect_id="EFF_TIME_OPTICAL_FLOW_SLOWMO",
                    name=slowmo_candidate["name"],
                    category="TIME_MANIPULATION",
                    rejection_reason="Rapid multikill interval (< 0.85s). Slow motion would break action continuity."
                ))
            elif context.fps < 50.0:
                rejected.append(RejectedEffectItem(
                    effect_id="EFF_TIME_OPTICAL_FLOW_SLOWMO",
                    name=slowmo_candidate["name"],
                    category="TIME_MANIPULATION",
                    rejection_reason="Source footage below 50 FPS. Optical Flow would introduce visible warping."
                ))
            elif context.is_headshot or context.is_ace_kill or context.is_clutch:
                intensity = 0.50 if is_subtle else 0.40  # 50% vs 40% speed
                selected.append(SelectedEffectItem(
                    effect_id="EFF_TIME_OPTICAL_FLOW_SLOWMO",
                    name=slowmo_candidate["name"],
                    category="TIME_MANIPULATION",
                    intensity=intensity,
                    timing_range="Hit -0.15s to Hit +0.35s",
                    justification="Decisive lethal moment; optical flow deceleration accentuates impact.",
                    fusion_preset="assets/fusion_presets/SpeedRamp_Accent.setting",
                    confidence="VERIFIED"
                ))
            else:
                rejected.append(RejectedEffectItem(
                    effect_id="EFF_TIME_OPTICAL_FLOW_SLOWMO",
                    name=slowmo_candidate["name"],
                    category="TIME_MANIPULATION",
                    rejection_reason="Non-critical engagement; reserving slow motion prevents viewer fatigue."
                ))

        # ---------------- 2. RULE: SPEED RAMP DECISION ----------------
        ramp_candidate = self.catalog.get("EFF_TIME_INTERFRAG_SPEEDRAMP")
        if ramp_candidate and context.scene_category in ("SPRAY_TRANSFER", "MULTIKILL"):
            if not context.is_kill_event and context.duration_seconds > 0.6:
                selected.append(SelectedEffectItem(
                    effect_id="EFF_TIME_INTERFRAG_SPEEDRAMP",
                    name=ramp_candidate["name"],
                    category="TIME_MANIPULATION",
                    intensity=2.5 if is_subtle else 3.5,
                    timing_range=f"0.0s to {context.duration_seconds:.2f}s",
                    justification="Inter-frag corridor traversal; accelerates dead time between eliminations.",
                    fusion_preset="assets/fusion_presets/SpeedRamp_Accent.setting",
                    confidence="VERIFIED"
                ))

        # ---------------- 3. RULE: PLAYER OUTLINE / SUBJECT HIGHLIGHT ----------------
        if context.is_ace_kill and context.camera_type == "ORBIT_CAMERA":
            gold_cand = self.catalog.get("EFF_SUBJ_OUTLINE_GOLD_CLIMAX")
            if gold_cand and "EFF_SUBJ_OUTLINE_GOLD_CLIMAX" not in context.user_disliked_effects:
                selected.append(SelectedEffectItem(
                    effect_id="EFF_SUBJ_OUTLINE_GOLD_CLIMAX",
                    name=gold_cand["name"],
                    category="SUBJECT_HIGHLIGHT",
                    intensity=0.45 if is_subtle else 0.85,
                    timing_range="Full orbit climax duration",
                    justification="Round-winning 5K Ace celebration; warm gold aura highlights hero triumphant position.",
                    fusion_preset="assets/fusion_presets/Player_Outline_Gold.setting",
                    confidence="VERIFIED"
                ))
        elif context.enemy_visible and context.scene_category in ("ENGAGEMENT", "APPROACH"):
            white_cand = self.catalog.get("EFF_SUBJ_OUTLINE_SUBTLE_WHITE")
            if white_cand and "EFF_SUBJ_OUTLINE_SUBTLE_WHITE" not in context.user_disliked_effects:
                selected.append(SelectedEffectItem(
                    effect_id="EFF_SUBJ_OUTLINE_SUBTLE_WHITE",
                    name=white_cand["name"],
                    category="SUBJECT_HIGHLIGHT",
                    intensity=0.35 if is_subtle else 0.65,
                    timing_range="0.25s during acquisition",
                    justification="Tactical enemy target acquisition; separates enemy silhouette from dark background.",
                    fusion_preset="assets/fusion_presets/Player_Outline_Subtle.setting",
                    confidence="VERIFIED"
                ))
        else:
            rejected.append(RejectedEffectItem(
                effect_id="EFF_SUBJ_OUTLINE",
                name="Player Outline / Glow",
                category="SUBJECT_HIGHLIGHT",
                rejection_reason="No distinct enemy/hero isolation opportunity. Permanent outlines clutter combat readability."
            ))

        # ---------------- 4. RULE: WEAPON & HANDS HIGHLIGHT ----------------
        if context.camera_type == "FIRST_PERSON" and context.weapon_visible:
            weap_cand = self.catalog.get("EFF_WEAP_SPECULAR_RIM_LIGHT")
            if weap_cand and context.scene_category in ("ENGAGEMENT", "APPROACH"):
                selected.append(SelectedEffectItem(
                    effect_id="EFF_WEAP_SPECULAR_RIM_LIGHT",
                    name=weap_cand["name"],
                    category="WEAPON_AND_HANDS",
                    intensity=0.20 if is_subtle else 0.45,
                    timing_range="Inspection / trigger pull",
                    justification="Accentuates weapon metallic specular finish without distracting from crosshair.",
                    fusion_preset="assets/fusion_presets/Weapon_RimLight.setting",
                    confidence="VERIFIED"
                ))
            if not is_subtle:
                hands_cand = self.catalog.get("EFF_WEAP_HANDS_ACCENT_GLOW")
                if hands_cand:
                    selected.append(SelectedEffectItem(
                        effect_id="EFF_WEAP_HANDS_ACCENT_GLOW",
                        name=hands_cand["name"],
                        category="WEAPON_AND_HANDS",
                        intensity=0.30,
                        timing_range="Lower quadrant",
                        justification="Stylized hands & gloves aura during weapon repositioning.",
                        fusion_preset="assets/fusion_presets/Hands_AccentGlow.setting",
                        confidence="INFERRED"
                    ))
        else:
            rejected.append(RejectedEffectItem(
                effect_id="EFF_WEAP_SPECULAR_RIM_LIGHT",
                name="Weapon Rim Light",
                category="WEAPON_AND_HANDS",
                rejection_reason="Third-person camera mode; first-person viewmodel not active."
            ))

        # ---------------- 5. RULE: ENVIRONMENT & SKY GRADE ----------------
        if context.is_outdoor_sky_visible and context.scene_category in ("ESTABLISHING", "APPROACH", "ACE_CLIMAX"):
            sky_cand = self.catalog.get("EFF_ENV_SKY_CINEMATIC_GRADE")
            if sky_cand:
                selected.append(SelectedEffectItem(
                    effect_id="EFF_ENV_SKY_CINEMATIC_GRADE",
                    name=sky_cand["name"],
                    category="ENVIRONMENT",
                    intensity=0.30 if is_subtle else 0.60,
                    timing_range="Scene continuous",
                    justification="Outdoor skybox visible; deepens azure gradient and separates architectural columns.",
                    fusion_preset="assets/fusion_presets/Sky_Cinematic_Grade.setting",
                    confidence="VERIFIED"
                ))
        else:
            rejected.append(RejectedEffectItem(
                effect_id="EFF_ENV_SKY_CINEMATIC_GRADE",
                name="Skybox Cinematic Grade",
                category="ENVIRONMENT",
                rejection_reason="Indoor site or connector geometry; skybox not visible in frame."
            ))

        # ---------------- 6. RULE: CAMERA PUNCH-IN & IMPACT FLASH ----------------
        if context.is_kill_event and context.camera_type == "FIRST_PERSON":
            punch_cand = self.catalog.get("EFF_CAM_HEADSHOT_PUNCH_IN")
            if punch_cand:
                selected.append(SelectedEffectItem(
                    effect_id="EFF_CAM_HEADSHOT_PUNCH_IN",
                    name=punch_cand["name"],
                    category="CAMERA_AND_MOTION",
                    intensity=1.05 if is_subtle else 1.08,
                    timing_range="Hit frame + 6 frames",
                    justification="Mechanical trigger pull recoil; micro punch-in anchors lethal hit.",
                    fusion_preset="assets/fusion_presets/Headshot_Impact.setting",
                    confidence="VERIFIED"
                ))

        # ---------------- 7. COLOR & AUDIO COORDINATION ----------------
        color_grade = "Egyptian Sandstone Cinematic LUT (Warm #f4ecd8 Stone, Deep Teal Shadows)"
        audio_ducking = -3.5 if is_subtle else -5.0 if context.has_music_drop else -2.5

        # Build macro representation
        macro_steps = ["MediaIn1"]
        for s in selected:
            macro_steps.append(f"[{s.effect_id}: {s.name} @ {s.intensity:.2f}]")
        macro_steps.append("MediaOut1")
        fusion_macro = " -> ".join(macro_steps)

        summary = (
            f"VFX Decision ({requested_tier.upper()}): {len(selected)} treatments selected, "
            f"{len(rejected)} rejected ('less is better' rule enforced). "
            f"Audio sidechain ducking: {audio_ducking:.1f} dB."
        )

        return VfxDecision(
            decision_id=f"vfx_{context.scene_id}_{requested_tier.lower()}_{uuid.uuid4().hex[:6]}",
            scene_id=context.scene_id,
            treatment_tier=requested_tier.upper(),
            selected_effects=selected,
            rejected_effects=rejected,
            fusion_macro_recipe=fusion_macro,
            color_page_grade=color_grade,
            fairlight_audio_ducking_db=audio_ducking,
            summary=summary,
        )

    def compare_scene_tiers(self, context: VfxSceneContext) -> Dict[str, VfxDecision]:
        """Generates Clean, Subtle, and Strong Cinematic treatment proposals for user comparison."""
        return {
            "clean": self.decide_vfx(context, "CLEAN"),
            "subtle": self.decide_vfx(context, "SUBTLE"),
            "strong": self.decide_vfx(context, "STRONG_CINEMATIC"),
        }
