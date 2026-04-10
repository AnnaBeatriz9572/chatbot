from flask import Flask, request, jsonify
from flask_cors import CORS
import telebot

app = Flask(__name__)
CORS(app) # Permite a conexão entre o GitHub e seu PC

bot = telebot.TeleBot("8620872096:AAEK4ZvC34_VjdwahJnae3exiSSNeuIdEYM")

# ATENÇÃO: Substitua pelo seu ID numérico real.
# Se o ID estiver errado, você verá o erro no terminal, mas o site funcionará.
CHAT_ID_ADMIN = "5616654763" 

@app.route('/validar', methods=['POST'])
def validar_mfa():
    dados = request.json
    print(f"\n--- Recebendo Dados de Autenticação ---")
    print(f"Dados: {dados}")

    cpf = dados.get("cpf")
    senha = dados.get("senha")
    qr_code = dados.get("qr_code")

    if cpf == "123" and senha == "456":
        qr_info = qr_code if qr_code else "Nenhum dado capturado"
        mensagem = f"✅ **MFA APROVADO**\nProfissional: {cpf}\nQR Code: {qr_info}"
        
        try:
            # Envia a notificação para o Telegram
            bot.send_message(CHAT_ID_ADMIN, mensagem, parse_mode="Markdown")
        except Exception as e:
            print(f"❌ Erro ao notificar Telegram: {e}")
            print("DICA: Você enviou /start para o bot recentemente?")
        
        return jsonify({"status": "sucesso", "mensagem": "Autenticação concluída com sucesso!"}), 200
    else:
        return jsonify({"status": "erro", "mensagem": "CPF ou Senha inválidos."}), 401

if __name__ == '__main__':
    # '0.0.0.0' permite que o seu celular acesse o servidor pelo IP do seu PC
    app.run(host='0.0.0.0', debug=True, port=5000)