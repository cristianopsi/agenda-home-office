import sqlite3

con = sqlite3.connect("agenda.db")
cur = con.cursor()

cur.executescript("""
DROP TABLE IF EXISTS colaboradores;
DROP TABLE IF EXISTS agenda;

CREATE TABLE colaboradores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT
);

CREATE TABLE agenda (
    data DATE,
    colaborador_id INTEGER,
    modalidade TEXT
);
""")

cur.execute("INSERT INTO colaboradores (nome) VALUES ('Usuário Logado')")

con.commit()
con.close()

print("Banco criado.")
