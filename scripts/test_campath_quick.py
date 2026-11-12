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
out_dir = pathlib.Path(r"C:\Users\pyPypy\Documents\MySCOPE\demToshka\renders\test_campath")

if out_dir.exists():
    shutil.rmtree(out_dir, ignore_errors=True)
out_dir.mkdir(parents=True, exist_ok=True)

staged_demo = csgo_dir / "temp_test_quick.dem"
if not staged_demo.exists():
    shutil.copy2("demos/anubis1410.dem", staged_demo)

# Build a test campath with 6 points in Quake coordinates around Anubis Middle (X=111, Y=1208, Z=-31)
# At 128 tickrate:
# tick 9300 -> 72.65625
# tick 9380 -> 73.28125
campath_xml = cfg_dir / "test_campath.xml"
xml_str = """<?xml version="1.0" encoding="utf-8"?>
<campath>
  <positionInterp>cubic</positionInterp>
  <rotationInterp>sCubic</rotationInterp>
  <fovInterp>cubic</fovInterp>
  <offset>0.000</offset>
  <hold>0</hold>
  <points>
    <p>
      <t>72.6562</t>
      <x>150.0</x>
      <y>1350.0</y>
      <z>50.0</z>
      <rx>0.0</rx>
      <ry>15.0</ry>
      <rz>-80.0</rz>
      <fov>90.0</fov>
    </p>
    <p>
      <t>72.7812</t>
      <x>140.0</x>
      <y>1300.0</y>
      <z>45.0</z>
      <rx>0.0</rx>
      <ry>12.0</ry>
      <rz>-82.0</rz>
      <fov>88.0</fov>
    </p>
    <p>
      <t>72.9062</t>
      <x>130.0</x>
      <y>1250.0</y>
      <z>40.0</z>
      <rx>0.0</rx>
      <ry>10.0</ry>
      <rz>-85.0</rz>
      <fov>86.0</fov>
    </p>
    <p>
      <t>73.0312</t>
      <x>120.0</x>
      <y>1200.0</y>
      <z>35.0</z>
      <rx>0.0</rx>
      <ry>8.0</ry>
      <rz>-88.0</rz>
      <fov>85.0</fov>
    </p>
    <p>
      <t>73.1562</t>
      <x>110.0</x>
      <y>1150.0</y>
      <z>30.0</z>
      <rx>0.0</rx>
      <ry>5.0</ry>
      <rz>-90.0</rz>
      <fov>84.0</fov>
    </p>
    <p>
      <t>73.2812</t>
      <x>100.0</x>
      <y>1100.0</y>
      <z>25.0</z>
      <rx>0.0</rx>
      <ry>5.0</ry>
      <rz>-92.0</rz>
      <fov>83.0</fov>
    </p>
  </points>
</campath>"""
campath_xml.write_text(xml_str, encoding="utf-8")
campath_xml_str = str(campath_xml.resolve()).replace("\\", "/")

cfg_path = cfg_dir / "temp_test_campath.cfg"
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
    "cl_drawhud 0",
    f'mirv_streams record name "{out_dir_str}"',
    "mirv_streams record fps 60",
    "mirv_streams record screen enabled 1",
    "mirv_streams record screen settings afxFfmpegYuv420p",
    "mirv_cmd clear",
    'mirv_cmd addAtTick 5 "demo_gototick 9280; demo_resume"',
    f'mirv_cmd addAtTick 9290 "spec_mode 6; mirv_campath load \\"{campath_xml_str}\\"; mirv_campath enable 1; mirv_campath print; demo_resume"',
    'mirv_cmd addAtTick 9300 "mirv_streams record start; mirv_campath enable 1"',
    'mirv_cmd addAtTick 9370 "mirv_streams record end; mirv_campath enable 0; mirv_campath clear; quit"',
    "demo_resume",
]
cfg_path.write_text("\n".join(cfg_lines), encoding="utf-8")
print(f"Campath CFG written to {cfg_path}")

cs2_args = (
    "-steam -insecure +sv_lan 1 -console -condebug -novid -nojoy -high "
    "+fps_max 0 +mat_powersavingsmode 0 -sw -w 1280 -h 720 -afxDisableSteamStorage "
    "+exec temp_test_campath.cfg +playdemo temp_test_quick"
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

print("Launching HLAE with Campath...")
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
        print("CS2 process finished!")
        break
    time.sleep(1.0)

time.sleep(2.0)
print("Checking output folder:")
for item in out_dir.rglob("*"):
    if item.is_file():
        print(f"  {item.name}: {item.stat().st_size} bytes")
