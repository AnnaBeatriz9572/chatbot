from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot

app = Flask(__name__)
CORS(app) # Crucial para permitir a conexão do site com o seu Python

bot = telebot.TeleBot("8620872096:AAEK4ZvC34_VjdwahJnae3exiSSNeuIdEYM")
CHAT_ID_ADMIN = "5616654763" # Use seu ID real aqui

@app.route('/validar', methods=['POST'])
def validar_mfa():
    dados = request.json
    print(f"--- Nova Tentativa de Login ---")
    print(f"Dados recebidos: {dados}")

    cpf = dados.get("cpf")
    senha = dados.get("senha")
    qr_code = dados.get("qr_code")

    # Lógica de validação da sua IC
    if cpf == "123" and senha == "456":
        mensagem_confirmacao = (
            f"✅ **MFA APROVADO**\n"
            f"Profissional Autenticado via Web\n"
            f"CPF: {cpf}\n"
            f"CRM/QR: {qr_code}"
        )
        bot.send_message(CHAT_ID_ADMIN, mensagem_confirmacao, parse_mode="Markdown")
        
        return jsonify({"status": "sucesso", "mensagem": "Autenticação concluída! Verifique o Telegram."}), 200
    else:
        return jsonify({"status": "erro", "mensagem": "Credenciais inválidas."}), 401

if __name__ == '__main__':
    # Rodando em 0.0.0.0 para aceitar conexões do celular na mesma rede
    app.run(host='0.0.0.0', debug=True, port=5000)