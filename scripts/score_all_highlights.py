import sys
sys.path.insert(0, ".")
import sqlite3
import json
from backend.cinematic.shot_director import HighlightScorer

conn = sqlite3.connect('demtoshka.db')
c = conn.cursor()

scorer = HighlightScorer()

c.execute("""
    SELECT h.id, h.demo_id, d.file_path, d.map_name, h.highlight_type, h.round_num,
           h.pov_name, h.pov_steam_id, h.kill_start_tick, h.kill_end_tick, h.kill_count
    FROM highlights h
    JOIN demos d ON h.demo_id = d.id
    WHERE h.kill_count >= 3
""")
candidates = c.fetchall()
scored = []
for row in candidates:
    hid, did, dpath, dmap, htype, rnum, pname, psteam, kstart, kend, kcount = row
    c.execute("""
        SELECT headshot, wallbang, noscope, thru_smoke, attacker_blind
        FROM kill_events
        WHERE demo_id = ? AND round_num = ? AND attacker_steam_id = ? AND tick >= ? AND tick <= ?
    """, (did, rnum, psteam, kstart, kend))
    krows = c.fetchall()
    klist = []
    for kr in krows:
        klist.append({
            "headshot": bool(kr[0]),
            "wallbang": bool(kr[1]),
            "noscope": bool(kr[2]),
            "thrusmoke": bool(kr[3]),
            "attackerblind": bool(kr[4]),
        })
    score = scorer.score_highlight(htype, klist)
    scored.append((score, hid, dpath, dmap, htype, rnum, pname, kcount, kstart, kend))

scored.sort(key=lambda x: x[0], reverse=True)
print("Top 10 Highlights Across All Demos:")
for s in scored[:10]:
    print(f"Score {s[0]:.1f} | {s[4].upper():12} | {s[6]} ({s[7]} kills) | {s[3]} R{s[5]} | ticks {s[8]}-{s[9]} | demo: {s[2]}")
