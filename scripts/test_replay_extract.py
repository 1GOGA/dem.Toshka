import sys
sys.path.insert(0, ".")
from pathlib import Path
from backend.parser.replay import extract_round_replay_data

demo_path = Path("demos/1-31bfc53c-127b-43f0-b786-107a5b32dc72-1-1.dem")
data = extract_round_replay_data(demo_path, round_num=19)
print(f"Round 19 Replay Data: map={data['map_name']}, tickrate={data['tickrate']}, frames={len(data['frames'])}, kills={len(data['kills'])}")
print("Players in round:")
for sid, p in data['players'].items():
    print(f"  {p['name']} ({p['side']}) - SteamID: {sid}")

print("\nKills in round:")
for k in data['kills']:
    print(f"  Tick {k['tick']}: {k['attacker_name']} eliminated {k['victim_name']} with {k['weapon']} (HS={k['headshot']})")
    print(f"    Attacker pos: ({k.get('attacker_x')}, {k.get('attacker_y')}) Victim pos: ({k.get('victim_x')}, {k.get('victim_y')})")
