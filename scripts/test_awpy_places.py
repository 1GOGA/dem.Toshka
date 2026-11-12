import sys
sys.path.insert(0, ".")
from pathlib import Path
from awpy.demo import Demo

demo_path = Path("demos/1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem")
dem = Demo(str(demo_path.resolve()))
dem.parse()

kills_r19 = dem.kills.filter(dem.kills["round_num"] == 19)
for row in kills_r19.to_dicts():
    if row.get("attacker_name") == "pytoshka_":
        print(f"{row.get('tick')}: {row.get('attacker_name')} [{row.get('attacker_place')}] -> {row.get('victim_name')} [{row.get('victim_place')}] with {row.get('weapon')}")
