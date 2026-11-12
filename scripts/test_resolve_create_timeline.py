import os
import sys
import pathlib

os.environ["RESOLVE_SCRIPT_API"] = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
os.environ["RESOLVE_SCRIPT_LIB"] = r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")

import DaVinciResolveScript as bmd
resolve = bmd.scriptapp("Resolve")
cur = resolve.GetProjectManager().GetCurrentProject()
mp = cur.GetMediaPool()
root_folder = mp.GetRootFolder()
clips = root_folder.GetClipList()

print(f"Media Pool has {len(clips)} clips:")
for c in clips:
    print(f"  - {c.GetName()} ({c.GetClipProperty('Duration')})")

# Create timeline directly with media items
tl_name = "demToshka_Cinematic_Director_Cut"
tl = mp.CreateEmptyTimeline(tl_name)
print("Created empty timeline:", tl.GetName())

# Append clips to timeline
appended = mp.AppendToTimeline(clips)
print("Appended clips to timeline:", len(appended) if appended else 0)

# Check tracks and items
print("Timeline tracks V:", tl.GetTrackCount("video"))
print("Timeline tracks A:", tl.GetTrackCount("audio"))

items_v1 = tl.GetItemListInTrack("video", 1) or []
print(f"Items on Track V1 ({len(items_v1)}):")
for it in items_v1:
    print(f"  Clip: {it.GetName()} | Duration: {it.GetDuration()} | Start: {it.GetStart()} | End: {it.GetEnd()}")

# Add marker at kill tick 9354 (approx 2.37s in, at 60fps = frame 142)
tl.AddMarker(142, "Green", "KILL: pytoshka_ [USP-S] ram1x1", "Headshot elimination in Middle", 1)
print("Markers after adding:", tl.GetMarkers())
