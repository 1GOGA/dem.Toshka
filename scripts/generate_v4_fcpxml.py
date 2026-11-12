import pathlib

V4_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT").resolve()
TAKES_DIR = pathlib.Path("renders/cinematic_studio_phase3/takes").resolve()
AUDIO_DIR = V4_DIR / "audio"

p_shoulder = str(TAKES_DIR / "shot_anubis_ace_r19_02_shoulder_approach.mp4").replace("\\", "/")
p_hero = str(TAKES_DIR / "shot_anubis_ace_r19_01_hero_pov.mp4").replace("\\", "/")
p_orbit = str(TAKES_DIR / "shot_anubis_ace_r19_04_climax_orbit.mp4").replace("\\", "/")
p_audio = str(AUDIO_DIR / "audio_master_v4.wav").replace("\\", "/")

fcpxml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<fcpxml version="1.9">
  <resources>
    <format id="r1" name="FFVideoFormat1080p60" frameDuration="1/60s" width="1920" height="1080"/>
    <asset id="r2" name="shot_anubis_ace_r19_02_shoulder_approach" src="file:///{p_shoulder}" format="r1" duration="982/60s" hasVideo="1" hasAudio="1"/>
    <asset id="r3" name="shot_anubis_ace_r19_01_hero_pov" src="file:///{p_hero}" format="r1" duration="1969/60s" hasVideo="1" hasAudio="1"/>
    <asset id="r4" name="shot_anubis_ace_r19_04_climax_orbit" src="file:///{p_orbit}" format="r1" duration="360/60s" hasVideo="1" hasAudio="1"/>
    <asset id="r5" name="audio_master_v4" src="file:///{p_audio}" duration="900/60s" hasAudio="1"/>
  </resources>
  <library>
    <event name="demToshka_Cinematics">
      <project name="ACE_FINAL_V4_MASTER_CUT">
        <sequence format="r1" tcStart="0s" duration="900/60s">
          <spine>
            <!-- Clip 1: Shoulder Approach (0.0s - 2.20s = 132 frames) -->
            <clip name="01_Shoulder_Approach" ref="r2" duration="132/60s" start="0s">
              <marker start="30/60s" duration="1/60s" value="Intro: pytoshka_ // ANUBIS ACE" color="blue"/>
            </clip>
            
            <!-- Clip 2A: Hero POV normal (source 5.20s - 9.95s, dur 4.75s = 285 frames) -->
            <clip name="02A_Hero_POV_Kills_1_2" ref="r3" duration="285/60s" start="312/60s">
              <marker start="29/60s" duration="1/60s" value="KILL 1: pytoshka_ [M4A1] Tiger07 (First Blood)" color="green"/>
              <marker start="186/60s" duration="1/60s" value="KILL 2: pytoshka_ [M4A1] zuuuuuhhhhn (Double Kill)" color="cyan"/>
            </clip>

            <!-- Clip 2B: Hero POV Headshot 50% Slow-mo (source 9.95s - 10.20s, retime 2x = 30 frames) -->
            <clip name="02B_Headshot_OpticalFlow_SlowMo" ref="r3" duration="30/60s" start="597/60s">
              <marker start="8/60s" duration="1/60s" value="KILL 3: pytoshka_ [M4A1] ProfyfGames (HEADSHOT 50% Slow-Mo)" color="red"/>
            </clip>

            <!-- Clip 2C: Hero POV Rapid Multikill (source 10.20s - 11.80s, dur 1.60s = 96 frames) -->
            <clip name="02C_Hero_POV_Kill_4_Rapid" ref="r3" duration="96/60s" start="612/60s">
              <marker start="42/60s" duration="1/60s" value="KILL 4: pytoshka_ [M4A1] freekjkeee (Rapid Multikill)" color="magenta"/>
            </clip>

            <!-- Clip 3: Climax Orbit (source 0.0s - 5.95s = 357 frames) -->
            <clip name="03_Climax_Orbit_ACE" ref="r4" duration="357/60s" start="0s">
              <marker start="6/60s" duration="1/60s" value="KILL 5 / ACE DOMINATION: pytoshka_ [M4A1] axuenchik002" color="yellow"/>
            </clip>
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
"""

out_fcpxml = V4_DIR / "ACE_FINAL_V4.fcpxml"
out_fcpxml.write_text(fcpxml_content, encoding="utf-8")
print(f"Generated FCPXML 1.9 for DaVinci Resolve: {out_fcpxml}")
