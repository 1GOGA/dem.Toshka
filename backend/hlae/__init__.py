"""HLAE and AfxHookSource2 Subsystem for Counter-Strike 2.

Provides deterministic tick command generation, Catmull-Rom spline camera paths,
multi-pass stream capture, and process lifecycle supervision.
"""

from backend.hlae.campath import CamKeyframe, HLAECampathManager
from backend.hlae.command_builder import HLAECommandBuilder, ScheduledCommand
from backend.hlae.controller import HLAEController
from backend.hlae.streams import HLAEStreamManager, StreamLayer, StreamProfile
from backend.hlae.version import HLAECapabilities, HLAEVersionDetector

__all__ = [
    "CamKeyframe",
    "HLAECampathManager",
    "HLAECommandBuilder",
    "ScheduledCommand",
    "HLAEController",
    "HLAEStreamManager",
    "StreamLayer",
    "StreamProfile",
    "HLAECapabilities",
    "HLAEVersionDetector",
]
