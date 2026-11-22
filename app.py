import os
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, request, jsonify
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("A variável de ambiente MONGO_URI não foi configurada.")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client["meu_app_db"]

COLECOES_PERMITIDAS = {
    "dados_compartilhados": db["dados_compartilhados"],
    "sebo": db["sebo"],
    "farinha": db["farinha"],
    "quimicos": db["quimicos"],
    "embalagens": db["embalagens"],
}


def obter_colecao(nome: str):
    if not nome or not isinstance(nome, str):
        return None
    return COLECOES_PERMITIDAS.get(nome.strip().lower())


def converter_id(id_str: str):
    try:
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        return None


def serializar_doc(doc: dict) -> dict:
    """Converte _id para string e garante serialização segura em JSON."""
    if not doc:
        return {}
    resultado = dict(doc)
    if "_id" in resultado:
        resultado["_id"] = str(resultado["_id"])
    return resultado


def resposta_colecao_invalida():
    return jsonify({
        "erro": "Coleção inválida",
        "colecoes_validas": list(COLECOES_PERMITIDAS.keys()),
    }), 400


@app.errorhandler(PyMongoError)
def tratar_erro_mongo(err):
    return jsonify({
        "erro": "Erro de comunicação com o banco de dados",
        "detalhe": str(err),
    }), 503


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "mensagem": "Servidor funcionando com sucesso!",
        "colecoes": list(COLECOES_PERMITIDAS.keys()),
    }), 200


@app.route("/health", methods=["GET"])
def health():
    client.admin.command("ping")
    return jsonify({"status": "ok", "database": "conectado"}), 200


# 1. INSERIR: POST /salvar/sebo
@app.route("/salvar/<nome_colecao>", methods=["POST"])
def salvar_dados(nome_colecao):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return resposta_colecao_invalida()

    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        return jsonify({"erro": "Envie um objeto JSON válido"}), 400

    dados.pop("_id", None)
    if not dados:
        return jsonify({"erro": "O JSON não contém campos para salvar"}), 400

    resultado = colecao.insert_one(dados)
    return jsonify({
        "mensagem": f"Salvo na coleção '{nome_colecao.strip().lower()}'!",
        "id": str(resultado.inserted_id),
    }), 201


# 2. BUSCAR TODOS: GET /buscar/sebo
@app.route("/buscar/<nome_colecao>", methods=["GET"])
def buscar_dados(nome_colecao):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return resposta_colecao_invalida()

    itens = [serializar_doc(doc) for doc in colecao.find()]
    return jsonify(itens), 200


# 3. BUSCAR UM POR ID: GET /buscar/sebo/<id>
@app.route("/buscar/<nome_colecao>/<id>", methods=["GET"])
def buscar_por_id(nome_colecao, id):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return resposta_colecao_invalida()

    oid = converter_id(id)
    if oid is None:
        return jsonify({"erro": "ID inválido"}), 400

    doc = colecao.find_one({"_id": oid})
    if not doc:
        return jsonify({"erro": "Registro não encontrado"}), 404

    return jsonify(serializar_doc(doc)), 200


# 4. ALTERAR POR ID: PUT ou PATCH /atualizar/sebo/<id>
@app.route("/atualizar/<nome_colecao>/<id>", methods=["PUT", "PATCH"])
def atualizar_dado(nome_colecao, id):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return resposta_colecao_invalida()

    oid = converter_id(id)
    if oid is None:
        return jsonify({"erro": "ID inválido"}), 400

    dados = request.get_json(silent=True)
    if not dados or not isinstance(dados, dict):
        return jsonify({"erro": "Envie um objeto JSON válido para atualizar"}), 400

    dados.pop("_id", None)
    if not dados:
        return jsonify({"erro": "Nenhum campo para atualizar foi enviado"}), 400

    resultado = colecao.update_one({"_id": oid}, {"$set": dados})
    if resultado.matched_count == 0:
        return jsonify({"erro": "Registro não encontrado"}), 404

    doc_atualizado = colecao.find_one({"_id": oid})
    if not doc_atualizado:
        return jsonify({"mensagem": "Registro atualizado, mas não está mais disponível."}), 200

    return jsonify({
        "mensagem": "Registro atualizado com sucesso!",
        "dados": serializar_doc(doc_atualizado),
    }), 200


# 5. APAGAR POR ID: DELETE /deletar/sebo/<id>
@app.route("/deletar/<nome_colecao>/<id>", methods=["DELETE"])
def deletar_dado(nome_colecao, id):
    colecao = obter_colecao(nome_colecao)
    if colecao is None:
        return resposta_colecao_invalida()

    oid = converter_id(id)
    if oid is None:
        return jsonify({"erro": "ID inválido"}), 400

    resultado = colecao.delete_one({"_id": oid})
    if resultado.deleted_count == 0:
        return jsonify({"erro": "Registro não encontrado"}), 404

    return jsonify({"mensagem": "Registro apagado com sucesso!"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
