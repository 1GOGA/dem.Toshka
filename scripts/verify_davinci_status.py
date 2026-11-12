import os
import sys

os.environ['RESOLVE_SCRIPT_API'] = r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting'
os.environ['RESOLVE_SCRIPT_LIB'] = r'C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll'
sys.path.append(r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules')

import DaVinciResolveScript as bmd
resolve = bmd.scriptapp('Resolve')
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
print('Active Project:', proj.GetName() if proj else 'None')
print('Timeline Count:', proj.GetTimelineCount() if proj else 0)
tl = proj.GetCurrentTimeline() if proj else None
print('Current Timeline:', tl.GetName() if tl else 'None')
if tl:
    v_count = tl.GetTrackCount('video')
    a_count = tl.GetTrackCount('audio')
    print('  Video Tracks:', v_count)
    print('  Audio Tracks:', a_count)
    for i in range(1, v_count + 1):
        print(f"    Track V{i}: {tl.GetTrackName('video', i)}")
    for i in range(1, a_count + 1):
        print(f"    Track A{i}: {tl.GetTrackName('audio', i)}")
    markers = tl.GetMarkers()
    print(f'  Markers Count: {len(markers)}')
    for frame, m in list(markers.items())[:10]:
        print(f"    Frame {frame}: [{m.get('color')}] {m.get('name')} - {m.get('note')}")
