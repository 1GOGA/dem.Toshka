import sqlite3
conn = sqlite3.connect('demtoshka.db')
c = conn.cursor()
c.execute("PRAGMA table_info(rounds)")
print("rounds columns:", [col[1] for col in c.fetchall()])
