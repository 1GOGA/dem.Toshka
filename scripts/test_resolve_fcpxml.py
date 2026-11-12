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

takes_dir = pathlib.Path("renders/cinematic_studio_phase2/takes").resolve()

# Test valid FCPXML with anchored connected clips inside the main clip
p_a = str(takes_dir / "A_FIRST_PERSON.mp4").replace("\\", "/")
p_b = str(takes_dir / "B_VICTIM_POV.mp4").replace("\\", "/")
p_d = str(takes_dir / "D_SHOULDER_CAM.mp4").replace("\\", "/")

test_fcpxml = f"""<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.9">
  <resources>
    <format id="r1" name="FFVideoFormat1080p60" frameDuration="1/60s" width="1920" height="1080"/>
    <asset id="r2" name="A_FIRST_PERSON" src="file:///{p_a}" format="r1" duration="248/60s" hasVideo="1" hasAudio="1"/>
    <asset id="r3" name="B_VICTIM_POV" src="file:///{p_b}" format="r1" duration="248/60s" hasVideo="1" hasAudio="1"/>
    <asset id="r4" name="D_SHOULDER_CAM" src="file:///{p_d}" format="r1" duration="248/60s" hasVideo="1" hasAudio="1"/>
  </resources>
  <library>
    <event name="Cinematics_Test">
      <project name="Anubis_MultiTrack_Test">
        <sequence format="r1" tcStart="0s">
          <spine>
            <clip name="Hero_A_FIRST_PERSON" ref="r2" duration="248/60s" start="0s">
              <marker start="142/60s" duration="1/60s" value="KILL: pytoshka_ [usp_silencer] ram1x1" color="green"/>
              <clip name="Connected_SHOULDER_CAM" ref="r4" lane="1" offset="0s" duration="248/60s" start="0s"/>
              <clip name="Connected_VICTIM_POV" ref="r3" lane="2" offset="0s" duration="248/60s" start="0s"/>
            </clip>
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>"""

test_path = pathlib.Path("renders/cinematic_studio_phase2/davinci_resolve_project/test_connected.fcpxml")
test_path.write_text(test_fcpxml, encoding="utf-8")

tl = mp.ImportTimelineFromFile(str(test_path.resolve()))
print("Import result:", tl)
if tl:
    print("Timeline:", tl.GetName())
    print("V Track count:", tl.GetTrackCount("video"))
    for t in range(1, tl.GetTrackCount("video") + 1):
        items = tl.GetItemListInTrack("video", t) or []
        print(f"  Track V{t}: {len(items)} clips")
        for it in items:
            print(f"    - {it.GetName()} ({it.GetDuration()} frames)")
    print("Markers:", tl.GetMarkers())
