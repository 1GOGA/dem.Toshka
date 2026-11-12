import json
import os
import sys
import pathlib

sys.path.insert(0, ".")

from backend.cinematic.models import CinematicProductionPackage, CinematicShot, OverlayKillEvent
from backend.cinematic.resolve_export import generate_davinci_resolve_python_script

manifest_path = pathlib.Path("renders/cinematic_studio_phase3/production_package.json")
data = json.loads(manifest_path.read_text(encoding="utf-8"))

shots = []
for s in data["shots"]:
    shots.append(
        CinematicShot(
            shot_id=s["shot_id"],
            highlight_id=s["highlight_id"],
            round_number=s["round_number"],
            camera_type=s["camera_type"],
            purpose=s["purpose"],
            start_tick=s["start_tick"],
            end_tick=s["end_tick"],
            start_time=s["start_time"],
            end_time=s["end_time"],
            duration_seconds=s["duration_seconds"],
            output_filename=s["output_filename"],
        )
    )

overlay_events = []
for e in data["overlay_events"]:
    overlay_events.append(
        OverlayKillEvent(
            tick=e["tick"],
            time_seconds=e["time_seconds"],
            round_number=e["round_number"],
            killer_name=e["killer_name"],
            killer_steam_id=e["killer_steam_id"],
            victim_name=e["victim_name"],
            victim_steam_id=e["victim_steam_id"],
            weapon=e["weapon"],
            headshot=e["headshot"],
            wallbang=e["wallbang"],
            noscope=e["noscope"],
            thrusmoke=e["thrusmoke"],
            attackerblind=e["attackerblind"],
            kill_number_in_round=e["kill_number_in_round"],
            is_ace=e.get("is_ace", False),
        )
    )

pkg = CinematicProductionPackage(
    package_id=data["package_id"],
    demo_id=data["demo_id"],
    demo_name=data["demo_name"],
    map_name=data["map_name"],
    created_at=data["created_at"],
    shots=shots,
    overlay_events=overlay_events,
    resolve_project_name="demToshka_Anubis_Ace_Production",
)

music_file = pathlib.Path("renders/cinematic_studio_phase3/soundtrack_128bpm.wav")
script_out = pathlib.Path("renders/cinematic_studio_phase3/create_davinci_resolve_timeline.py")

generate_davinci_resolve_python_script(pkg, music_file=music_file, output_script_path=script_out)
print("Regenerated:", script_out)
