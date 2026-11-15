"""Fire Almanac - backend Flask (rotas de páginas + controller da API)."""
import calendar
from datetime import date

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ANO_MINIMO = 2000  # ajuste conforme o início da sua base de dados


# ---------- Rotas de páginas ----------
@app.route("/")
def landing():
    """Landing page."""
    return render_template("landing.html")


@app.route("/mapa")
def mapa():
    """Página do mapa com painel de filtros."""
    return render_template("mapa.html")


# ---------- Validação ----------
def validar_filtros(payload: dict):
    """Valida ano/mes/dia. Retorna (dados_limpos, erro)."""
    try:
        ano = int(payload.get("ano"))
        mes = int(payload.get("mes"))
    except (TypeError, ValueError):
        return None, "Ano e mês são obrigatórios e devem ser números."

    if not ANO_MINIMO <= ano <= date.today().year:
        return None, f"Ano deve estar entre {ANO_MINIMO} e {date.today().year}."
    if not 1 <= mes <= 12:
        return None, "Mês deve estar entre 1 e 12."

    dia = payload.get("dia")
    if dia in (None, ""):
        dia = None  # dia é opcional: sem dia = mês inteiro
    else:
        try:
            dia = int(dia)
        except (TypeError, ValueError):
            return None, "Dia deve ser um número."
        if not 1 <= dia <= calendar.monthrange(ano, mes)[1]:
            return None, f"Dia inválido para {mes:02d}/{ano}."

    return {"ano": ano, "mes": mes, "dia": dia}, None


# ---------- Controller da API ----------
@app.route("/api/focos", methods=["POST"])
def api_focos():
    """Recebe os filtros do JS, valida e (por enquanto) apenas imprime."""
    payload = request.get_json(silent=True) or {}
    filtros, erro = validar_filtros(payload)

    if erro:
        return jsonify({"status": "error", "message": erro}), 400

    # TODO: consultar o dataframe pandas / banco com `filtros`
    print(f"[API /api/focos] ano={filtros['ano']} mes={filtros['mes']} dia={filtros['dia']}")

    return jsonify({
        "status": "success",
        "message": "Filtros aplicados",
        "data_recebida": filtros,
    })


if __name__ == "__main__":
    app.run(debug=True)
