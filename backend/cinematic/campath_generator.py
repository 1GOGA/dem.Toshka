"""Campath XML Generator for HLAE Source 2.

Translates high-level CameraPath objects into exact HLAE-compliant XML files.
Supports cubic/linear interpolation, orientation quaternion/Euler, and disk persistence.
"""

from __future__ import annotations

import pathlib
from typing import Optional

from backend.cinematic.models import CameraPath, InterpolationMode


class CampathValidationError(Exception):
    """Raised when camera path data fails HLAE structural rules."""


def validate_campath(campath: CameraPath) -> None:
    """Validate camera path against HLAE Source 2 AfxHookSource2 constraints."""
    if not campath.points:
        raise CampathValidationError("Camera path cannot be empty.")

    # HLAE requirement for cubic / sCubic evaluation
    if (
        campath.position_interp in (InterpolationMode.CUBIC, InterpolationMode.SCUBIC)
        or campath.rotation_interp in (InterpolationMode.CUBIC, InterpolationMode.SCUBIC)
    ):
        if len(campath.points) < 4:
            raise CampathValidationError(
                f"HLAE cubic interpolation requires at least 4 keyframes, got {len(campath.points)}."
            )

    # Ensure strictly increasing time
    for i in range(1, len(campath.points)):
        prev_t = campath.points[i - 1].time
        curr_t = campath.points[i].time
        if curr_t < prev_t:
            raise CampathValidationError(
                f"Campath point timestamps must be non-decreasing: point {i-1} ({prev_t}s) > point {i} ({curr_t}s)."
            )


def export_campath_xml(
    campath: CameraPath,
    output_path: pathlib.Path,
) -> str:
    """Validate and write camera path XML to disk.
    
    Returns the generated XML string.
    """
    validate_campath(campath)
    xml_content = campath.to_xml()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_content, encoding="utf-8")
    return xml_content
