import os
import pathlib
import sys

# 1. Resolve Script API Setup
script_api = r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting'
script_lib = r'C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll'
os.environ['RESOLVE_SCRIPT_API'] = script_api
os.environ['RESOLVE_SCRIPT_LIB'] = script_lib
sys.path.append(os.path.join(script_api, 'Modules'))

V3_DIR = pathlib.Path("renders/ACE_FINAL_V3_AUDIO_KILLFEED").resolve()

def setup_resolve_v3():
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp('Resolve')
        if not resolve:
            print('ERROR: DaVinci Resolve is not running or scripting is disabled.')
            return False
    except Exception as e:
        print(f'ERROR loading DaVinci Resolve API: {e}')
        return False

    pm = resolve.GetProjectManager()
    proj_name = 'demToshka_Anubis_Ace_Production'
    proj = pm.LoadProject(proj_name)
    if not proj:
        proj = pm.CreateProject(proj_name)
    if not proj:
        print('Could not load or create project.')
        return False

    proj.SetSetting('timelineFrameRate', '60')
    proj.SetSetting('timelineResolutionWidth', '1920')
    proj.SetSetting('timelineResolutionHeight', '1080')

    mp = proj.GetMediaPool()
    root_folder = mp.GetRootFolder()

    # Create subfolder in media pool for Phase 3.2 V3 assets
    subfolders = root_folder.GetSubFolderList()
    v3_folder = None
    for sf in subfolders:
        if sf.GetName() == 'ACE_FINAL_V3':
            v3_folder = sf
            break
    if not v3_folder:
        v3_folder = mp.AddSubFolder(root_folder, 'ACE_FINAL_V3')
    
    mp.SetCurrentFolder(v3_folder)

    # Media items to import
    takes_dir = pathlib.Path("renders/cinematic_studio_phase3/takes").resolve()
    audio_dir = V3_DIR / "audio"
    overlays_dir = V3_DIR / "overlays"
    sfx_dir = V3_DIR / "sfx_library"

    media_to_import = [
        str(takes_dir / "shot_anubis_ace_r19_01_hero_pov.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_02_shoulder_approach.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_03_victim_reaction.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_04_climax_orbit.mp4").replace("\\", "/"),
        str(audio_dir / "stem_a1_gameplay.wav").replace("\\", "/"),
        str(audio_dir / "stem_a2_music_142bpm.wav").replace("\\", "/"),
        str(audio_dir / "stem_a3_cinematic_impacts.wav").replace("\\", "/"),
        str(audio_dir / "stem_a4_transition_whooshes.wav").replace("\\", "/"),
        str(audio_dir / "stem_a5_risers_accents.wav").replace("\\", "/"),
        str(audio_dir / "stem_a6_atmosphere.wav").replace("\\", "/"),
        str(audio_dir / "audio_master_v3.wav").replace("\\", "/"),
        str(overlays_dir / "killfeed_16x9_state_1_kill1.png").replace("\\", "/"),
        str(overlays_dir / "killfeed_16x9_state_2_kill1_2.png").replace("\\", "/"),
        str(overlays_dir / "killfeed_16x9_state_3_kill1_2_3.png").replace("\\", "/"),
        str(overlays_dir / "killfeed_16x9_state_4_kill2_3_4.png").replace("\\", "/"),
        str(overlays_dir / "killfeed_16x9_state_5_kill3_4_5.png").replace("\\", "/"),
        str(overlays_dir / "ace_card_16x9.png").replace("\\", "/"),
        str(overlays_dir / "intro_card_16x9.png").replace("\\", "/")
    ]

    imported_items = mp.ImportMedia(media_to_import)
    print(f"Imported {len(imported_items)} Phase 3.2 assets into Media Pool / ACE_FINAL_V3.")

    tl_name = 'ACE_FINAL_V3_Master_Edit'
    for i in range(1, proj.GetTimelineCount() + 1):
        tl = proj.GetTimelineByIndex(i)
        if tl and tl.GetName() == tl_name:
            proj.SetCurrentTimeline(tl)
            break
            
    timeline = mp.CreateEmptyTimeline(tl_name)
    if not timeline:
        timeline = proj.GetCurrentTimeline()

    if timeline:
        # Set track counts: 4 Video, 6 Audio
        while timeline.GetTrackCount('video') < 4:
            timeline.AddTrack('video')
        timeline.SetTrackName('video', 1, 'Hero POV (Master)')
        timeline.SetTrackName('video', 2, 'Cinematic Paths (Shoulder/Orbit)')
        timeline.SetTrackName('video', 3, 'Victim Reaction POV')
        timeline.SetTrackName('video', 4, 'Event-Driven Stacked Killfeed')

        while timeline.GetTrackCount('audio') < 6:
            timeline.AddTrack('audio')
        timeline.SetTrackName('audio', 1, 'A1: Gameplay Audio')
        timeline.SetTrackName('audio', 2, 'A2: Soundtrack (LOVELYDILLER 142BPM)')
        timeline.SetTrackName('audio', 3, 'A3: Real Cinematic Impacts (Sonniss)')
        timeline.SetTrackName('audio', 4, 'A4: Real Transition Whooshes (Sonniss)')
        timeline.SetTrackName('audio', 5, 'A5: Real Risers & Accents (Sonniss)')
        timeline.SetTrackName('audio', 6, 'A6: Atmospheric Texture Layer (Sonniss)')

        # Add PRECISE DEMO-SYNCHRONIZED Kill Markers (Exact Event Frames)
        base_frame = timeline.GetStartFrame() if hasattr(timeline, 'GetStartFrame') else 0
        markers = [
            (470, 'Green', 'Kill 1 (Hit Frame)', 'KILL #1 (Tick 120927): pytoshka_ [M4A1] Tiger07 (Drop Kick)'),
            (627, 'Yellow', 'Kill 2 (Hit Frame)', 'KILL #2 (Tick 121263): pytoshka_ [M4A1] zuuuuuhhhhn (Double Kill)'),
            (732, 'Red', 'Kill 3 (Headshot Dink)', 'KILL #3 (Tick 121491): pytoshka_ [M4A1] ProfyfGames (HEADSHOT)'),
            (780, 'Yellow', 'Kill 4 (Hit Frame)', 'KILL #4 (Tick 121595): pytoshka_ [M4A1] freekjkeee (Quadra Kill)'),
            (932, 'Cyan', 'Kill 5 (ACE Climax)', 'KILL #5 (Tick 121920): pytoshka_ [M4A1] axuenchik002 (5K ACE DOMINATION)')
        ]
        for f_offset, color, name, note in markers:
            timeline.AddMarker(base_frame + f_offset, color, name, note, 1, '')

        print(f"Configured timeline '{tl_name}' with 4 Video, 6 Audio tracks, and 5 exact event markers.")
        
        # Export FCPXML
        fcpxml_out = str(V3_DIR / "ACE_FINAL_V3.fcpxml").replace("\\", "/")
        try:
            timeline.Export(fcpxml_out, resolve.EXPORT_FCPXML_1_8)
            print(f"Exported FCPXML: {fcpxml_out}")
        except Exception as ex:
            print(f"FCPXML export notice: {ex}")

        # Export DRP project archive
        drp_out = str(V3_DIR / "ACE_FINAL_V3.drp")
        try:
            res_drp = pm.ExportProject(proj_name, drp_out)
            print(f"Exported DRP project: {drp_out} (Success: {res_drp})")
        except Exception as ex:
            print(f"DRP export notice: {ex}")

        pm.SaveProject()
        print("DaVinci Resolve project saved successfully.")
        return True
    return False

if __name__ == '__main__':
    setup_resolve_v3()
