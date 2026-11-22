import os
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# Pega o link do seu MongoDB que vamos configurar lá no Render
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)

# Nome do banco e da coleção (tabela) que serão criados automaticamente no Atlas
db = client["meu_app_db"]
colecao = db["dados_compartilhados"]
colecao = db["sebo"]
colecao = db["Farinha"]
colecao = db["quimicos"]
colecao = db["embalagens"]





@app.route("/", methods=["GET"])
def home():
  return jsonify(
      {"status": "online", "mensagem": "Servidor funcionando com sucesso!"}
  )


# Rota para o celular ENVIAR dados para o MongoDB
@app.route("/salvar", methods=["POST"])
def salvar_dados():
  dados = request.get_json()
  if not dados:
    return jsonify({"erro": "Nenhum dado enviado"}), 400

  resultado = colecao.insert_one(dados)
  return (
      jsonify({
          "mensagem": "Salvo no MongoDB!",
          "id": str(resultado.inserted_id),
      }),
      201,
  )


# Rota para o celular BUSCAR os dados do MongoDB
@app.route("/buscar", methods=["GET"])
def buscar_dados():
  itens = []
  for doc in colecao.find():
    doc["_id"] = str(doc["_id"])  # Converte o ID do Mongo para texto
    itens.append(doc)
  return jsonify(itens), 200


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
