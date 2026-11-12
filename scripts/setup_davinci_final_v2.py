import os
import pathlib
import sys

# 1. Resolve Script API Setup
script_api = r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting'
script_lib = r'C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll'
os.environ['RESOLVE_SCRIPT_API'] = script_api
os.environ['RESOLVE_SCRIPT_LIB'] = script_lib
sys.path.append(os.path.join(script_api, 'Modules'))

OUT_DIR = pathlib.Path("renders/ACE_FINAL_V2_COLOR_VFX").resolve()

def setup_resolve():
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

    # Create subfolder in media pool for Phase 3.1 V2 assets
    subfolders = root_folder.GetSubFolderList()
    v2_folder = None
    for sf in subfolders:
        if sf.GetName() == 'ACE_FINAL_V2':
            v2_folder = sf
            break
    if not v2_folder:
        v2_folder = mp.AddSubFolder(root_folder, 'ACE_FINAL_V2')
    
    mp.SetCurrentFolder(v2_folder)

    # Media items to import
    takes_dir = pathlib.Path("renders/cinematic_studio_phase3/takes").resolve()
    audio_dir = OUT_DIR / "audio"
    overlays_dir = OUT_DIR / "overlays"

    media_to_import = [
        str(takes_dir / "shot_anubis_ace_r19_01_hero_pov.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_02_shoulder_approach.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_03_victim_reaction.mp4").replace("\\", "/"),
        str(takes_dir / "shot_anubis_ace_r19_04_climax_orbit.mp4").replace("\\", "/"),
        str(audio_dir / "stem_a1_gameplay.wav").replace("\\", "/"),
        str(audio_dir / "stem_a2_music.wav").replace("\\", "/"),
        str(audio_dir / "stem_a3_sub_bass.wav").replace("\\", "/"),
        str(audio_dir / "stem_a4_whooshes.wav").replace("\\", "/"),
        str(audio_dir / "stem_a5_risers.wav").replace("\\", "/"),
        str(audio_dir / "audio_master_5track.wav").replace("\\", "/"),
        str(overlays_dir / "badge_16x9_kill_1.png").replace("\\", "/"),
        str(overlays_dir / "badge_16x9_kill_2.png").replace("\\", "/"),
        str(overlays_dir / "badge_16x9_kill_3.png").replace("\\", "/"),
        str(overlays_dir / "badge_16x9_kill_4.png").replace("\\", "/"),
        str(overlays_dir / "badge_16x9_kill_5.png").replace("\\", "/"),
        str(overlays_dir / "ace_card_16x9.png").replace("\\", "/"),
        str(overlays_dir / "intro_card_16x9.png").replace("\\", "/")
    ]

    imported_items = mp.ImportMedia(media_to_import)
    print(f"Imported {len(imported_items)} assets into Media Pool / ACE_FINAL_V2.")

    # Create timeline ACE_FINAL_V2_Master_Edit
    tl_name = 'ACE_FINAL_V2_Master_Edit'
    # Delete previous timeline with same name if exists
    for i in range(1, proj.GetTimelineCount() + 1):
        tl = proj.GetTimelineByIndex(i)
        if tl and tl.GetName() == tl_name:
            proj.SetCurrentTimeline(tl)
            break
            
    timeline = mp.CreateEmptyTimeline(tl_name)
    if not timeline:
        timeline = proj.GetCurrentTimeline()

    if timeline:
        # Set track counts
        while timeline.GetTrackCount('video') < 4:
            timeline.AddTrack('video')
        timeline.SetTrackName('video', 1, 'Hero POV (Master)')
        timeline.SetTrackName('video', 2, 'Cinematic Paths (Shoulder/Orbit)')
        timeline.SetTrackName('video', 3, 'Victim Reaction POV')
        timeline.SetTrackName('video', 4, 'Motion Graphics & Badges')

        while timeline.GetTrackCount('audio') < 5:
            timeline.AddTrack('audio')
        timeline.SetTrackName('audio', 1, 'A1: Gameplay Audio')
        timeline.SetTrackName('audio', 2, 'A2: Music 142BPM (LOVELYDILLER)')
        timeline.SetTrackName('audio', 3, 'A3: Sub-Bass 808 Impacts')
        timeline.SetTrackName('audio', 4, 'A4: Transition Whooshes')
        timeline.SetTrackName('audio', 5, 'A5: Tension Risers & Swells')

        # Add synchronized kill markers
        base_frame = timeline.GetStartFrame() if hasattr(timeline, 'GetStartFrame') else 0
        markers = [
            (491, 'Green', 'Beat Drop / Kill 1', 'KILL #1: pytoshka_ [m4a1] Tiger07 (Drop Kick)'),
            (643, 'Yellow', 'Kill 2', 'KILL #2: pytoshka_ [m4a1] zuuuuuhhhhn (Double Kill)'),
            (745, 'Red', 'Headshot / Kill 3', 'KILL #3: pytoshka_ [m4a1] ProfyfGames (HEADSHOT DINK)'),
            (795, 'Yellow', 'Kill 4', 'KILL #4: pytoshka_ [m4a1] freekjkeee (Quadra Kill)'),
            (947, 'Cyan', 'ACE Climax / Kill 5', 'KILL #5: pytoshka_ [m4a1] axuenchik002 (5K ACE DOMINATION)')
        ]
        for f_offset, color, name, note in markers:
            timeline.AddMarker(base_frame + f_offset, color, name, note, 1, '')

        print(f"Configured timeline '{tl_name}' with 4 Video, 5 Audio tracks, and 5 kill markers.")
        
        # Export FCPXML
        fcpxml_out = str(OUT_DIR / "ACE_FINAL_V2.fcpxml").replace("\\", "/")
        try:
            timeline.Export(fcpxml_out, resolve.EXPORT_FCPXML_1_8)
            print(f"Exported FCPXML: {fcpxml_out}")
        except Exception as ex:
            print(f"FCPXML export notice: {ex}")

        pm.SaveProject()
        print("DaVinci Resolve project saved successfully.")
        return True
    return False

if __name__ == '__main__':
    setup_resolve()
