import os
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("A variável de ambiente MONGO_URI não foi configurada.")

client = MongoClient(MONGO_URI)
db = client["meu_app_db"]

COLECOES_PERMITIDAS = {
    "dados_compartilhados": db["dados_compartilhados"],
    "sebo": db["sebo"],
    "farinha": db["farinha"],
    "quimicos": db["quimicos"],
    "embalagens": db["embalagens"],
}


def obter_colecao(nome):
    if not nome:
        return None
    return COLECOES_PERMITIDAS.get(nome.strip().lower())


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "online", "mensagem": "Servidor funcionando com sucesso!"}), 200


# Exemplo: POST /salvar/sebo com corpo JSON {"peso": 120, "unidade": "kg"}
@app.route("/salvar/<nome_colecao>", methods=["POST"])
def salvar_dados(nome_colecao):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return jsonify({
            "erro": "Coleção inválida",
            "colecoes_validas": list(COLECOES_PERMITIDAS.keys())
        }), 400

    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        return jsonify({"erro": "Envie um objeto JSON válido"}), 400

    resultado = colecao.insert_one(dados)
    return jsonify({
        "mensagem": f"Salvo na coleção '{nome_colecao.lower()}'!",
        "id": str(resultado.inserted_id),
    }), 201


# Exemplo: GET /buscar/sebo
@app.route("/buscar/<nome_colecao>", methods=["GET"])
def buscar_dados(nome_colecao):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return jsonify({
            "erro": "Coleção inválida",
            "colecoes_validas": list(COLECOES_PERMITIDAS.keys())
        }), 400

    itens = []
    for doc in colecao.find():
        doc["_id"] = str(doc["_id"])
        itens.append(doc)

    return jsonify(itens), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
