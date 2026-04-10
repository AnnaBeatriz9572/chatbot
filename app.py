from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot

app = Flask(__name__)
CORS(app) # Permite que o seu site no GitHub fale com este servidor

# Opcional: Mantemos o bot apenas para NOTIFICAR o sucesso
bot = telebot.TeleBot("8620872096:AAEK4ZvC34_VjdwahJnae3exiSSNeuIdEYM")
CHAT_ID_ADMIN = "SEU_ID_AQUI" 

@app.route('/validar', methods=['POST'])
def validar_mfa():
    dados = request.json
    cpf = dados.get("cpf")
    senha = dados.get("senha")
    qr_code = dados.get("qr_code")

    # Mantemos a sua lógica de validação da IC
    if cpf == "123" and senha == "456":
        mensagem = f"✅ Autenticação Web confirmada!\nCPF: {cpf}\nQR: {qr_code}"
        
        # Notifica o Gabriel/Pesquisador no Telegram
        bot.send_message(CHAT_ID_ADMIN, mensagem) 
        
        return jsonify({"status": "sucesso", "mensagem": "Login concluído com sucesso!"}), 200
    else:
        return jsonify({"status": "erro", "mensagem": "CPF ou Senha inválidos."}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5000)