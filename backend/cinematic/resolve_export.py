"""DaVinci Resolve Handoff & FCPXML / EDL Exporter.

Generates multi-track FCPXML project files with timeline markers at exact kill events,
separate tracks for POV, Cinematic B-Roll, Victim inserts, Overlays, and Audio stems,
as well as direct Python automation scripts for DaVinci Resolve API.
"""

from __future__ import annotations

import pathlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional

from backend.cinematic.models import (
    CinematicProductionPackage,
    CinematicShot,
    EditDecisionClip,
    OverlayKillEvent,
)


def _format_time_fraction(seconds: float, fps: int = 60) -> str:
    """Format seconds into FCPXML fraction format, e.g. '120/60s'."""
    frames = int(round(seconds * fps))
    return f"{frames}/{fps}s"


def generate_fcpxml(
    package: CinematicProductionPackage,
    fps: int = 60,
    output_path: Optional[pathlib.Path] = None,
) -> str:
    """Generate professional multi-track FCPXML for DaVinci Resolve.
    
    Structure:
    - Track 1 (Lane 0 / Spine): Hero Master First-Person POV
    - Track 2 (Lane 1): Cinematic Camera B-Roll (Shoulder Cam / Orbit / Flyby)
    - Track 3 (Lane 2): Victim POV reaction cut-aways
    - Timeline Markers on exact kill ticks with color-coded tags
    """
    root = ET.Element("fcpxml", version="1.9")
    resources = ET.SubElement(root, "resources")

    # Format resource
    ET.SubElement(
        resources,
        "format",
        id="r1",
        name="FFVideoFormat1080p60",
        frameDuration=f"1/{fps}s",
        width="1920",
        height="1080",
    )

    # Register media assets
    media_id_map: dict[str, str] = {}
    for idx, shot in enumerate(package.shots):
        r_id = f"r_asset_{idx + 2}"
        media_id_map[shot.shot_id] = r_id
        src_url = f"file:///{pathlib.Path(shot.output_filename).as_posix()}"
        ET.SubElement(
            resources,
            "asset",
            id=r_id,
            name=shot.output_filename or f"Shot_{shot.shot_id}",
            src=src_url,
            format="r1",
            duration=_format_time_fraction(shot.duration_seconds, fps),
            hasVideo="1",
            hasAudio="1",
        )

    # Library -> Event -> Project -> Sequence
    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name=f"CS2_{package.map_name}_Cinematics")
    project = ET.SubElement(event, "project", name=package.resolve_project_name or f"CS2 {package.map_name} Movie")
    sequence = ET.SubElement(project, "sequence", format="r1", tcStart="0s")
    spine = ET.SubElement(sequence, "spine")

    # 1. Place Primary Action Hero POV shots onto Main Spine (Track 1)
    hero_shots = [s for s in package.shots if s.purpose.value in ("PRIMARY_ACTION", "OUTRO")]
    broll_shots = [s for s in package.shots if s.purpose.value in ("APPROACH", "CLIMAX_ACCENT", "ESTABLISH", "TRANSITION")]
    victim_shots = [s for s in package.shots if s.purpose.value == "VICTIM_REACTION"]

    timeline_pos_frames = 0

    for s in hero_shots:
        asset_id = media_id_map.get(s.shot_id, "r1")
        dur_str = _format_time_fraction(s.duration_seconds, fps)
        clip_elem = ET.SubElement(
            spine,
            "clip",
            name=s.output_filename or f"Hero_{s.shot_id}",
            ref=asset_id,
            duration=dur_str,
            start="0s",
        )

        # Attach kill markers to this clip if any kills happen during this shot
        for k in package.overlay_events:
            k_time = k.time_seconds
            if s.start_time <= k_time <= s.end_time:
                rel_time = k_time - s.start_time
                marker_color = "Gold" if k.is_ace else ("Green" if k.headshot else "Red")
                m_elem = ET.SubElement(
                    clip_elem,
                    "marker",
                    start=_format_time_fraction(rel_time, fps),
                    duration=f"1/{fps}s",
                    value=f"KILL: {k.killer_name} [{k.weapon}] {k.victim_name}",
                )
                m_elem.set("color", marker_color)

        timeline_pos_frames += int(round(s.duration_seconds * fps))

    # 2. Attach Secondary Storyline (Track 2: Cinematic B-Roll) connected to spine
    for s in broll_shots:
        asset_id = media_id_map.get(s.shot_id, "r1")
        dur_str = _format_time_fraction(s.duration_seconds, fps)
        rel_offset_sec = max(0.0, s.start_time - (hero_shots[0].start_time if hero_shots else 0.0))
        ET.SubElement(
            spine,
            "clip",
            name=f"B-Roll_{s.camera_type.value}",
            ref=asset_id,
            lane="1",  # Track 2 above master
            offset=_format_time_fraction(rel_offset_sec, fps),
            duration=dur_str,
            start="0s",
        )

    # 3. Attach Victim Reaction Cutaways (Track 3: Lane 2)
    for s in victim_shots:
        asset_id = media_id_map.get(s.shot_id, "r1")
        dur_str = _format_time_fraction(s.duration_seconds, fps)
        rel_offset_sec = max(0.0, s.start_time - (hero_shots[0].start_time if hero_shots else 0.0))
        ET.SubElement(
            spine,
            "clip",
            name="Victim_Reaction",
            ref=asset_id,
            lane="2",  # Track 3 above B-Roll
            offset=_format_time_fraction(rel_offset_sec, fps),
            duration=dur_str,
            start="0s",
        )

    raw_xml = ET.tostring(root, encoding="utf-8")
    pretty_xml = minidom.parseString(raw_xml).toprettyxml(indent="  ")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pretty_xml, encoding="utf-8")

    return pretty_xml


def generate_cmx3600_edl(
    package: CinematicProductionPackage,
    fps: int = 60,
    output_path: Optional[pathlib.Path] = None,
) -> str:
    """Generate standard CMX 3600 EDL text file."""
    lines = [
        f"TITLE: {package.resolve_project_name or 'CS2_Cinematic_Edit'}",
        "FCM: NON-DROP FRAME",
        "",
    ]

    event_num = 1
    timeline_sec = 0.0

    def _sec_to_tc(secs: float) -> str:
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        s = int(secs % 60)
        f = int(round((secs - int(secs)) * fps))
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    for shot in package.shots:
        src_in = 0.0
        src_out = shot.duration_seconds
        tl_in = timeline_sec
        tl_out = timeline_sec + shot.duration_seconds
        lines.append(
            f"{event_num:03d}  AX       V     C        "
            f"{_sec_to_tc(src_in)} {_sec_to_tc(src_out)} {_sec_to_tc(tl_in)} {_sec_to_tc(tl_out)}"
        )
        lines.append(f"* FROM CLIP NAME: {shot.output_filename or shot.shot_id}")
        lines.append(f"* CAMERA: {shot.camera_type.value} PURPOSE: {shot.purpose.value}")
        lines.append("")
        timeline_sec = tl_out
        event_num += 1

    content = "\n".join(lines)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
    return content


def generate_davinci_resolve_python_script(
    package: CinematicProductionPackage,
    music_file: Optional[pathlib.Path] = None,
    output_script_path: Optional[pathlib.Path] = None,
    takes_directory: Optional[pathlib.Path] = None,
) -> str:
    """Generate an executable standalone Python script driving DaVinci Resolve Studio / Free API.
    
    Creates:
    - 4 Video Tracks: V1 Hero POV, V2 Cinematic B-Roll, V3 Victim Reaction, V4 Overlays
    - 4 Audio Tracks: A1 Game Audio, A2 Music (128 BPM), A3 Impacts, A4 Transitions
    - Media Pool imports
    - Synchronized colored kill markers
    """
    proj_name = package.resolve_project_name or f"CS2_{package.map_name}_Production"

    takes_dir = takes_directory or pathlib.Path("renders/cinematic_studio_phase3/takes")
    clip_paths = []
    for s in package.shots:
        fn = s.output_filename or f"{s.shot_id}.mp4"
        candidate = takes_dir / fn
        if not candidate.exists():
            candidate = pathlib.Path(fn)
        clip_paths.append(str(candidate.resolve()).replace("\\", "/"))

    music_str = str(music_file.resolve()).replace("\\", "/") if music_file and music_file.exists() else ""

    script_lines = [
        "#!/usr/bin/env python",
        "# Auto-generated DaVinci Resolve Production Script by dem.Toshka Cinematic Studio",
        "import sys, os",
        "",
        "# 1. Resolve Script API Setup",
        "script_api = r'C:\\ProgramData\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting'",
        "script_lib = r'C:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\fusionscript.dll'",
        "os.environ['RESOLVE_SCRIPT_API'] = script_api",
        "os.environ['RESOLVE_SCRIPT_LIB'] = script_lib",
        "sys.path.append(os.path.join(script_api, 'Modules'))",
        "",
        "try:",
        "    import DaVinciResolveScript as dvr",
        "    resolve = dvr.scriptapp('Resolve')",
        "    if not resolve:",
        "        print('ERROR: DaVinci Resolve is not running or scripting is disabled.')",
        "        sys.exit(1)",
        "except Exception as e:",
        "    print(f'ERROR loading DaVinci Resolve API: {e}')",
        "    sys.exit(1)",
        "",
        "pm = resolve.GetProjectManager()",
        f"proj = pm.CreateProject('{proj_name}') or pm.LoadProject('{proj_name}')",
        "if not proj:",
        "    print('Could not create or load project.')",
        "    sys.exit(1)",
        "",
        "# Set project frame rate to 60 fps",
        "proj.SetSetting('timelineFrameRate', '60')",
        "proj.SetSetting('timelineResolutionWidth', '1920')",
        "proj.SetSetting('timelineResolutionHeight', '1080')",
        "",
        "mp = proj.GetMediaPool()",
        "root_folder = mp.GetRootFolder()",
        "",
        "# Import media files",
        f"clips_to_import = {clip_paths!r}",
        f"music_path = {music_str!r}",
        "if music_path:",
        "    clips_to_import.append(music_path)",
        "",
        "imported_items = mp.ImportMedia(clips_to_import)",
        "print(f'Imported {len(imported_items)} media items into DaVinci Media Pool.')",
        "",
        "# Create 4-Video / 4-Audio Timeline",
        f"timeline = mp.CreateEmptyTimeline('CS2_Cinematic_Director_Cut')",
        "if not timeline:",
        "    print('Timeline already exists or could not be created; fetching current timeline.')",
        "    timeline = proj.GetCurrentTimeline()",
        "",
        "if timeline:",
        "    # Configure 4 Video Tracks",
        "    while timeline.GetTrackCount('video') < 4:",
        "        timeline.AddTrack('video')",
        "    timeline.SetTrackName('video', 1, 'Hero POV (Master)')",
        "    timeline.SetTrackName('video', 2, 'Cinematic B-Roll')",
        "    timeline.SetTrackName('video', 3, 'Victim Reaction')",
        "    timeline.SetTrackName('video', 4, 'Overlays & Killfeed')",
        "",
        "    # Configure 4 Audio Tracks",
        "    while timeline.GetTrackCount('audio') < 4:",
        "        timeline.AddTrack('audio')",
        "    timeline.SetTrackName('audio', 1, 'Game Audio')",
        "    timeline.SetTrackName('audio', 2, 'Music (128 BPM)')",
        "    timeline.SetTrackName('audio', 3, 'Kill Impacts')",
        "    timeline.SetTrackName('audio', 4, 'Transitions & FX')",
        "",
        "    # Append media clips to timeline",
        "    clips_in_pool = [c for c in root_folder.GetClipList() if 'шкала' not in c.GetClipProperty('Type').lower() and 'timeline' not in c.GetClipProperty('Type').lower()]",
        "    mp.AppendToTimeline(clips_in_pool)",
        "",
        "    # Add Kill Event Markers offset by timeline base start frame",
        "    base_frame = timeline.GetStartFrame() if hasattr(timeline, 'GetStartFrame') else 0",
    ]

    for ev in package.overlay_events:
        frame_idx = int(round(ev.time_seconds * 60))
        color = "Yellow" if ev.is_ace else ("Green" if ev.headshot else "Cyan")
        note = f"KILL #{ev.kill_number_in_round}: {ev.killer_name} [{ev.weapon}] {ev.victim_name}"
        script_lines.append(
            f"    timeline.AddMarker(base_frame + {frame_idx}, '{color}', 'Kill Event', '{note}', 1, '')"
        )

    script_lines.extend([
        "",
        "    print('Successfully built 4-Video / 4-Audio production timeline with synchronized kill markers.')",
        "    pm.SaveProject()",
        "else:",
        "    print('Could not initialize timeline in project.')",
    ])

    content = "\n".join(script_lines)
    if output_script_path:
        output_script_path.parent.mkdir(parents=True, exist_ok=True)
        output_script_path.write_text(content, encoding="utf-8")

    return content
