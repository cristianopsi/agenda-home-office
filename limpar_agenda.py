import sqlite3

conn = sqlite3.connect("agenda.db")  # ajuste o nome se for diferente
cursor = conn.cursor()

cursor.execute("""
DELETE FROM agenda
WHERE strftime('%w', data) IN ('0','6')
""")

conn.commit()
conn.close()

print("✔️ Domingos e sábados removidos com sucesso")
