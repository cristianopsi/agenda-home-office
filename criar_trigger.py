import sqlite3

conn = sqlite3.connect("agenda.db")  # ajuste se o nome do banco for outro
cursor = conn.cursor()

cursor.executescript("""
CREATE TRIGGER IF NOT EXISTS bloqueia_fim_semana
BEFORE INSERT ON agenda
WHEN strftime('%w', NEW.data) IN ('0','6')
BEGIN
  SELECT RAISE(ABORT, 'Fim de semana não permitido');
END;
""")

conn.commit()
conn.close()

print("✔️ Trigger criada com sucesso")
