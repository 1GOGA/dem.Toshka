import sys
sys.path.insert(0, ".")
from pathlib import Path
from awpy.demo import Demo

demo_path = Path("demos/1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem")
dem = Demo(str(demo_path.resolve()))
dem.parse()

# Check kills DataFrame
print("Kills columns in awpy:")
print(dem.kills.columns)

kills_r19 = dem.kills.filter(dem.kills["round_num"] == 19)
print(f"\nKills in R19 count: {len(kills_r19)}")
for row in kills_r19.to_dicts():
    if row.get("attacker_name") == "pytoshka_":
        print(f"Kill at tick {row.get('tick')}: {row.get('attacker_name')} -> {row.get('victim_name')} ({row.get('weapon')})")
        print(f"  Attacker 3D: X={row.get('attacker_X') or row.get('attacker_x')}, Y={row.get('attacker_Y') or row.get('attacker_y')}, Z={row.get('attacker_Z') or row.get('attacker_z')}")
        print(f"  Victim 3D:   X={row.get('victim_X') or row.get('victim_x')}, Y={row.get('victim_Y') or row.get('victim_y')}, Z={row.get('victim_Z') or row.get('victim_z')}")

# Check ticks columns
print("\nTicks columns in awpy:")
print(dem.ticks.columns)
