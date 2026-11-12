"""Verify DaVinci Resolve FCPXML 1.9 timeline import in real DaVinci Resolve Free 21.0."""

from __future__ import annotations

import json
import os
import pathlib
import sys

os.environ["RESOLVE_SCRIPT_API"] = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
os.environ["RESOLVE_SCRIPT_LIB"] = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")

import DaVinciResolveScript as bmd

fcpxml_path = pathlib.Path("renders/cinematic_studio_phase2/davinci_resolve_project/DaVinci_Resolve_Project.fcpxml").resolve()

resolve = bmd.scriptapp("Resolve")
if not resolve:
    print("ERROR: Could not connect to DaVinci Resolve instance.")
    sys.exit(1)

pm = resolve.GetProjectManager()

project_name = "demToshka_Cinematic_Runtime_Verification"
# Close or delete existing disposable test project if exists
try:
    pm.DeleteProject(project_name)
except Exception:
    pass

project = pm.CreateProject(project_name)
if not project:
    project = pm.LoadProject(project_name)

print(f"Active Project: {project.GetName()}")

media_pool = project.GetMediaPool()

# Import FCPXML Timeline
print(f"Importing timeline from {fcpxml_path}...")
timeline = media_pool.ImportTimelineFromFile(str(fcpxml_path))

if not timeline:
    print("ERROR: Failed to import timeline from FCPXML.")
    sys.exit(1)

print(f"SUCCESS: Timeline imported: '{timeline.GetName()}'")
print(f"  Start Frame: {timeline.GetStartFrame()}")
print(f"  End Frame: {timeline.GetEndFrame()}")
print(f"  Track Count (Video): {timeline.GetTrackCount('video')}")
print(f"  Track Count (Audio): {timeline.GetTrackCount('audio')}")

# Inspect Video Tracks
video_tracks = {}
for t in range(1, timeline.GetTrackCount("video") + 1):
    items = timeline.GetItemListInTrack("video", t)
    video_tracks[f"V{t}"] = []
    if items:
        for it in items:
            mp_item = it.GetMediaPoolItem()
            clip_path = mp_item.GetClipProperty("File Path") if mp_item else "Unknown"
            video_tracks[f"V{t}"].append({
                "name": it.GetName(),
                "duration": it.GetDuration(),
                "start": it.GetStart(),
                "end": it.GetEnd(),
                "file_path": clip_path,
            })

# Inspect Audio Tracks
audio_tracks = {}
for t in range(1, timeline.GetTrackCount("audio") + 1):
    items = timeline.GetItemListInTrack("audio", t)
    audio_tracks[f"A{t}"] = []
    if items:
        for it in items:
            audio_tracks[f"A{t}"].append({
                "name": it.GetName(),
                "duration": it.GetDuration(),
                "start": it.GetStart(),
                "end": it.GetEnd(),
            })

# Inspect Markers
markers = timeline.GetMarkers()
print(f"  Total Markers: {len(markers)}")
marker_list = []
for frame, m in markers.items():
    print(f"    Frame {frame}: [{m.get('color')}] {m.get('name')} - {m.get('note')}")
    marker_list.append({
        "frame": frame,
        "color": m.get("color"),
        "name": m.get("name"),
        "note": m.get("note"),
    })

report = {
    "project_name": project.GetName(),
    "timeline_name": timeline.GetName(),
    "start_frame": timeline.GetStartFrame(),
    "end_frame": timeline.GetEndFrame(),
    "video_tracks": video_tracks,
    "audio_tracks": audio_tracks,
    "markers": marker_list,
}

report_file = pathlib.Path("renders/cinematic_studio_phase2/davinci_resolve_project/davinci_import_verification.json")
report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"DaVinci import verification saved to {report_file}")
