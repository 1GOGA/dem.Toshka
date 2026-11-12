import os
import pathlib
import sys

# Resolve Script API Setup
script_api = r'C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting'
script_lib = r'C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll'
os.environ['RESOLVE_SCRIPT_API'] = script_api
os.environ['RESOLVE_SCRIPT_LIB'] = script_lib
sys.path.append(os.path.join(script_api, 'Modules'))

V4_DIR = pathlib.Path("renders/ACE_FINAL_V4_MASTER_CUT").resolve()

def setup_resolve_v4():
    try:
        import DaVinciResolveScript as dvr
        resolve = dvr.scriptapp('Resolve')
        if not resolve:
            print('INFO: DaVinci Resolve is not currently running. FCPXML is ready for manual import.')
            return False
    except Exception as e:
        print(f'INFO: DaVinci Resolve API not initialized: {e}')
        return False

    pm = resolve.GetProjectManager()
    proj_name = 'demToshka_Anubis_Ace_V4_Master'
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

    subfolders = root_folder.GetSubFolderList()
    v4_folder = None
    for sf in subfolders:
        if sf.GetName() == 'ACE_FINAL_V4':
            v4_folder = sf
            break
    if not v4_folder:
        v4_folder = mp.AddSubFolder(root_folder, 'ACE_FINAL_V4')
    
    mp.SetCurrentFolder(v4_folder)

    fcpxml_path = V4_DIR / "ACE_FINAL_V4.fcpxml"
    if fcpxml_path.exists():
        tl = mp.ImportTimelineFromFile(str(fcpxml_path))
        if tl:
            print(f"Successfully imported timeline into DaVinci Resolve: {tl.GetName()}")
            return True

    print("Media pool prepared.")
    return True

if __name__ == '__main__':
    setup_resolve_v4()
