import sys
sys.path.insert(0, ".")
import sqlite3
from backend.cinematic.shot_director import HighlightScorer

conn = sqlite3.connect('demtoshka.db')
c = conn.cursor()

c.execute("""
    SELECT id, demo_id, highlight_type, round_num, pov_name, pov_steam_id,
           kill_start_tick, kill_end_tick, clip_start_tick, clip_end_tick, kill_count, tags_json
    FROM highlights
    WHERE id = '19_ace_76561199036405932_120927'
""")
h_row = c.fetchone()
print("Highlight row:", h_row)

c.execute("""
    SELECT id, tick, attacker_name, attacker_steam_id, victim_name, victim_steam_id,
           weapon, headshot, wallbang, noscope, thru_smoke, attacker_blind, is_teamkill, is_suicide
    FROM kill_events
    WHERE demo_id = ? AND round_num = ? AND attacker_steam_id = ?
    ORDER BY tick ASC
""", (h_row[1], h_row[3], h_row[5]))

kills = c.fetchall()
print(f"\nFound {len(kills)} kills by {h_row[4]} in Round {h_row[3]}:")
kill_dicts = []
for k in kills:
    kd = {
        "id": k[0],
        "tick": k[1],
        "attacker": k[2],
        "attacker_steam_id": k[3],
        "victim": k[4],
        "victim_steam_id": k[5],
        "weapon": k[6],
        "headshot": bool(k[7]),
        "wallbang": bool(k[8]),
        "noscope": bool(k[9]),
        "thrusmoke": bool(k[10]),
        "attackerblind": bool(k[11]),
    }
    kill_dicts.append(kd)
    print(f"  Tick {kd['tick']} (rel: +{(kd['tick']-kills[0][1])/128:.2f}s): "
          f"{kd['attacker']} eliminated {kd['victim']} with [{kd['weapon']}] "
          f"(Headshot={kd['headshot']}, Wallbang={kd['wallbang']}, Smoke={kd['thrusmoke']})")

c.execute("""
    SELECT round_num, start_tick, freeze_end_tick, end_tick, official_end_tick, winner, reason
    FROM rounds
    WHERE demo_id = ? AND round_num = ?
""", (h_row[1], h_row[3]))
r_bounds = c.fetchone()
print(f"\nRound bounds: round {r_bounds[0]}: start={r_bounds[1]}, freeze_end={r_bounds[2]}, end={r_bounds[3]}, official_end={r_bounds[4]}, winner={r_bounds[5]}, reason={r_bounds[6]}")

c.execute("SELECT id, file_path, map_name, tickrate, duration_seconds FROM demos WHERE id = ?", (h_row[1],))
d_info = c.fetchone()
print(f"Demo info: ID={d_info[0]}, path={d_info[1]}, map={d_info[2]}, tickrate={d_info[3]}, duration={d_info[4]:.1f}s")

scorer = HighlightScorer()
score = scorer.score_highlight("ace", kill_dicts, is_clutch=False, clutch_enemies=0, has_flick=False)
print(f"\nHighlight Score: {score}")
