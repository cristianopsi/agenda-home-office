from flask import Flask, render_template, request, redirect, jsonify, Response
import sqlite3
from datetime import date, timedelta, datetime, time
import calendar
import uuid

# Semana iniciando na segunda-feira
calendar.setfirstweekday(calendar.MONDAY)

app = Flask(__name__, static_folder="static")

COLABORADOR_ID = 1  # simulação de usuário logado

MESES_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# ===================== DB =====================
def db():
    con = sqlite3.connect("agenda.db", timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            modalidade TEXT CHECK(modalidade IN ('HOME','PRESENCIAL'))
        )
    """)
    con.commit()
    con.close()


# ===================== PERÍODO =====================
def periodo_datas(periodo, ano, mes):
    if periodo == "MES":
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    elif periodo == "SEMESTRE":
        if mes <= 6:
            inicio = date(ano, 1, 1)
            fim = date(ano, 6, 30)
        else:
            inicio = date(ano, 7, 1)
            fim = date(ano, 12, 31)
    else:
        inicio = date(ano, 1, 1)
        fim = date(ano, 12, 31)
    return inicio, fim


# ===================== REGRAS =====================
def aplicar_regras(dias_home, dias_presencial, inverter, periodo, ano, mes):
    con = db()
    inicio, fim = periodo_datas(periodo, ano, mes)

    con.execute("""
        DELETE FROM agenda
        WHERE colaborador_id = ?
        AND data BETWEEN ? AND ?
    """, (COLABORADOR_ID, inicio.isoformat(), fim.isoformat()))

    ref = inicio
    while ref.weekday() != 0:
        ref += timedelta(days=1)

    atual = inicio
    while atual <= fim:
        if atual.weekday() < 5:
            delta_semanas = (atual - ref).days // 7
            inverter_semana = inverter and (
                delta_semanas % 2 == 1 if ref.day <= 3 else delta_semanas % 2 == 0
            )

            if not inverter_semana:
                modalidade = (
                    "HOME" if atual.weekday() in dias_home else
                    "PRESENCIAL" if atual.weekday() in dias_presencial else None
                )
            else:
                modalidade = (
                    "PRESENCIAL" if atual.weekday() in dias_home else
                    "HOME" if atual.weekday() in dias_presencial else None
                )

            if modalidade:
                con.execute("""
                    INSERT INTO agenda (colaborador_id, data, modalidade)
                    VALUES (?, ?, ?)
                """, (COLABORADOR_ID, atual.isoformat(), modalidade))
        atual += timedelta(days=1)

    con.commit()
    con.close()


# ===================== CALENDÁRIO =====================
def calendario_mes(ano, mes):
    con = db()
    semanas = calendar.monthcalendar(ano, mes)
    calendario = []

    for semana in semanas:
        linha = []
        for dia in semana:
            if dia == 0:
                linha.append(None)
            else:
                data = date(ano, mes, dia).isoformat()
                reg = con.execute("""
                    SELECT modalidade FROM agenda
                    WHERE colaborador_id = ? AND data = ?
                """, (COLABORADOR_ID, data)).fetchone()

                linha.append({
                    "dia": dia,
                    "data": data,
                    "modalidade": reg["modalidade"] if reg else None
                })
        calendario.append(linha)

    con.close()
    return calendario


# ===================== ICS (CALENDÁRIO EXCLUSIVO) =====================
def gerar_ics(colaborador_id, inicio, fim):
    con = db()
    registros = con.execute("""
        SELECT data, modalidade
        FROM agenda
        WHERE colaborador_id = ?
        AND data BETWEEN ? AND ?
        ORDER BY data
    """, (colaborador_id, inicio.isoformat(), fim.isoformat())).fetchall()
    con.close()

    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "PRODID:-//Agenda Home Office//Corporativo//PT-BR",
        "X-WR-CALNAME:Agenda Home Office",
        "X-WR-CALDESC:Planejamento de Home Office e Presencial",
        "X-WR-TIMEZONE:America/Sao_Paulo"
    ]

    for r in registros:
        data_base = datetime.strptime(r["data"], "%Y-%m-%d").date()

        if r["modalidade"] == "HOME":
            inicio_evt = datetime.combine(data_base, time(8, 0))
            fim_evt = datetime.combine(data_base, time(17, 0))
            titulo = "🏠 Home Office"
            categoria = "HOME"
        else:
            inicio_evt = datetime.combine(data_base, time(9, 0))
            fim_evt = datetime.combine(data_base, time(18, 0))
            titulo = "🏢 Trabalho Presencial"
            categoria = "PRESENCIAL"

        linhas.extend([
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@agenda-home-office",
            f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{inicio_evt.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{fim_evt.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{titulo}",
            f"CATEGORIES:{categoria}",
            "TRANSP:OPAQUE",
            "END:VEVENT"
        ])

    linhas.append("END:VCALENDAR")
    return "\r\n".join(linhas)


@app.route("/exportar")
def exportar():
    hoje = date.today()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    periodo = request.args.get("periodo", "MES")

    inicio, fim = periodo_datas(periodo, ano, mes)
    conteudo = gerar_ics(COLABORADOR_ID, inicio, fim)

    return Response(
        conteudo,
        mimetype="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=agenda_home_office.ics"
        }
    )

@app.route("/editar-dia", methods=["POST"])
def editar_dia():
    dados = request.get_json()
    data = dados["data"]
    modalidade = dados["modalidade"]

    con = db()

    con.execute("""
        DELETE FROM agenda
        WHERE colaborador_id = ? AND data = ?
    """, (COLABORADOR_ID, data))

    if modalidade:
        con.execute("""
            INSERT INTO agenda (colaborador_id, data, modalidade)
            VALUES (?, ?, ?)
        """, (COLABORADOR_ID, data, modalidade))

    con.commit()
    con.close()

    return jsonify({"status": "ok"})

@app.route("/", methods=["GET", "POST"])
def index():
    hoje = date.today()

    ano = int(request.form.get("ano", hoje.year))
    mes = int(request.form.get("mes", hoje.month))
    periodo = request.form.get("periodo", "MES")

    if request.method == "POST":
        dias_home = list(map(int, request.form.getlist("home")))
        dias_presencial = list(map(int, request.form.getlist("presencial")))
        inverter = "inverter" in request.form

        aplicar_regras(
            dias_home,
            dias_presencial,
            inverter,
            periodo,
            ano,
            mes
        )

    calendarios = []
    inicio, fim = periodo_datas(periodo, ano, mes)

    atual = date(inicio.year, inicio.month, 1)
    while atual <= fim:
        calendarios.append({
            "nome_mes": MESES_PT[atual.month],
            "semanas": calendario_mes(atual.year, atual.month)
        })

        if atual.month == 12:
            atual = date(atual.year + 1, 1, 1)
        else:
            atual = date(atual.year, atual.month + 1, 1)

    return render_template(
        "index.html",
        titulo="Agenda Home Office",
        calendarios=calendarios,
        meses=MESES_PT,
        ano=ano,
        mes=mes,
        periodo=periodo
    )


# ===================== MAIN =====================
if __name__ == "__main__":
    # init_db()
    # app.run(debug=True)
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
