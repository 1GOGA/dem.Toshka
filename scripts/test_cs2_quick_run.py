import os
import sys
import shutil
import subprocess
import time
import pathlib

cs2_exe = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe")
csgo_dir = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo")
cfg_dir = csgo_dir / "cfg"
hlae_exe = pathlib.Path(r"C:\Users\pyPypy\Documents\MySCOPE\demToshka\tools\hlae\HLAE.exe")
hook_dll = pathlib.Path(r"C:\Users\pyPypy\Documents\MySCOPE\demToshka\tools\hlae\x64\AfxHookSource2.dll")
out_dir = pathlib.Path(r"C:\Users\pyPypy\Documents\MySCOPE\demToshka\renders\test_quick")

if out_dir.exists():
    shutil.rmtree(out_dir, ignore_errors=True)
out_dir.mkdir(parents=True, exist_ok=True)

staged_demo = csgo_dir / "temp_test_quick.dem"
if not staged_demo.exists():
    print("Staging demo...")
    shutil.copy2("demos/anubis1410.dem", staged_demo)

cfg_path = cfg_dir / "temp_test_quick.cfg"
out_dir_str = str(out_dir.resolve()).replace("\\", "/")
cfg_lines = [
    "sv_cheats 1",
    "volume 0",
    "host_framerate 60",
    "fps_max 0",
    "mat_powersavingsmode 0",
    "mirv_cvar_unhide_all",
    "r_show_build_info 0",
    "cl_trueview_show_status 0",
    "demo_ui_mode 0",
    "cl_spec_show_bindings 0",
    "spec_autodirector 0",
    "safezonex 1.0",
    "safezoney 1.0",
    "cl_drawhud 0",
    f'mirv_streams record name "{out_dir_str}"',
    "mirv_streams record fps 60",
    "mirv_streams record screen enabled 1",
    "mirv_streams record screen settings afxFfmpegYuv420p",
    "mirv_cmd clear",
    'mirv_cmd addAtTick 5 "demo_gototick 9300; demo_resume"',
    'mirv_cmd addAtTick 9320 "spec_mode 4; spec_lock_to_accountid 1076140204; demo_resume"',
    'mirv_cmd addAtTick 9340 "mirv_streams record start"',
    'mirv_cmd addAtTick 9380 "mirv_streams record end; quit"',
    "demo_resume",
]
cfg_path.write_text("\n".join(cfg_lines), encoding="utf-8")
print(f"CFG written to {cfg_path}")

cs2_args = (
    "-steam -insecure +sv_lan 1 -console -condebug -novid -nojoy -high "
    "+fps_max 0 +mat_powersavingsmode 0 -sw -w 1280 -h 720 -afxDisableSteamStorage "
    "+exec temp_test_quick.cfg +playdemo temp_test_quick"
)

cmd = [
    str(hlae_exe),
    "-customLoader",
    "-noGui",
    "-autoStart",
    "-hookDllPath",
    str(hook_dll),
    "-programPath",
    str(cs2_exe),
    "-cmdLine",
    cs2_args,
]

print("Launching HLAE with CS2...")
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
start_t = time.time()
cs2_seen = False

while time.time() - start_t < 90:
    res = subprocess.run(["tasklist", "/FI", "IMAGENAME eq cs2.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True)
    if "cs2.exe" in res.stdout:
        if not cs2_seen:
            print("CS2 process detected and running!")
            cs2_seen = True
    elif cs2_seen:
        print("CS2 process exited normally!")
        break
    time.sleep(1.0)

time.sleep(2.0)
print("Checking output folder:")
found_files = list(out_dir.rglob("*"))
if not found_files:
    print("  No files generated.")
for item in found_files:
    if item.is_file():
        print(f"  {item.name}: {item.stat().st_size} bytes")
