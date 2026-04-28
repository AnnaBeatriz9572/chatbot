"""
app.py — Servidor Flask para o sistema MFA de saúde.

COMO RODAR:
  1. pip install -r requirements.txt
  2. Preencha o .env com seu BOT_TOKEN
  3. python app.py
  4. Acesse http://localhost:5000
"""

import os
import io
import base64
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import telebot
import pyotp
import qrcode

# ─────────────────────────────────────────────
#  Carrega .env
# ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).parent / ".env")
    print("[INFO] Arquivo .env carregado.")
except ImportError:
    print("[AVISO] Instale python-dotenv: pip install python-dotenv")

# ─────────────────────────────────────────────
#  Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("mfa_server")

# ─────────────────────────────────────────────
#  Variáveis de ambiente
# ─────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "\n[ERRO] BOT_TOKEN não encontrado!\n"
        "Crie o arquivo .env com:  BOT_TOKEN=seu_token_aqui\n"
    )

CPF_VALIDO    = os.environ.get("CPF_DEMO", "12345678901")
SENHA_VALIDA  = os.environ.get("SENHA_DEMO", "senha123")
SESSION_HOURS = int(os.environ.get("SESSION_DURATION_HOURS", "5"))
PORTAL_NOME   = os.environ.get("PORTAL_NOME", "Portal de Saúde")

# ─────────────────────────────────────────────
#  TOTP — Google Authenticator
# ─────────────────────────────────────────────
TOTP_SECRET = os.environ.get("TOTP_SECRET")
if not TOTP_SECRET:
    TOTP_SECRET = pyotp.random_base32()
    print("\n" + "=" * 60)
    print("  ATENÇÃO: TOTP_SECRET gerado automaticamente!")
    print(f"  Salve isso no seu .env:")
    print(f"  TOTP_SECRET={TOTP_SECRET}")
    print("=" * 60 + "\n")

totp = pyotp.TOTP(TOTP_SECRET)

# ─────────────────────────────────────────────
#  Flask
# ─────────────────────────────────────────────
app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ─────────────────────────────────────────────
#  Telegram
# ─────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ─────────────────────────────────────────────
#  Sessões (thread-safe)
# ─────────────────────────────────────────────
_lock_sessoes = threading.Lock()
sessoes_ativas: dict = {}

# ─────────────────────────────────────────────
#  Rate limiting por IP
# ─────────────────────────────────────────────
_lock_rate    = threading.Lock()
_historico    = {}
MAX_TENTATIVAS   = 5
JANELA_SEGUNDOS  = 300

def _dentro_do_limite(ip: str) -> bool:
    agora = datetime.now()
    with _lock_rate:
        hist = [t for t in _historico.get(ip, [])
                if (agora - t).total_seconds() < JANELA_SEGUNDOS]
        if len(hist) >= MAX_TENTATIVAS:
            _historico[ip] = hist
            return False
        hist.append(agora)
        _historico[ip] = hist
        return True

# ─────────────────────────────────────────────
#  Notificação Telegram (assíncrona)
# ─────────────────────────────────────────────
def _enviar(chat_id: str, texto: str) -> None:
    try:
        bot.send_message(chat_id, texto, parse_mode="Markdown")
        logger.info("Telegram enviado → chat_id=%s", chat_id)
    except Exception as e:
        logger.error("Erro Telegram chat_id=%s: %s", chat_id, e)

def notificar(chat_id: str, texto: str) -> None:
    threading.Thread(target=_enviar, args=(chat_id, texto), daemon=True).start()

# ─────────────────────────────────────────────
#  Rotas
# ─────────────────────────────────────────────

@app.route("/")
def index():
    """Serve a página de login."""
    return send_file("index.html")


@app.route("/qrcode-img")
def gerar_qrcode():
    """Gera o QR Code do TOTP para o Google Authenticator (usando pypng, sem Pillow)."""
    import qrcode.image.pure
    uri = totp.provisioning_uri(name=CPF_VALIDO, issuer_name=PORTAL_NOME)
    img = qrcode.make(uri, image_factory=qrcode.image.pure.PyPNGImage)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    return jsonify({"qrcode": f"data:image/png;base64,{encoded}"})


@app.route("/validar", methods=["POST"])
def validar():
    """Valida CPF + senha + código TOTP e envia notificação Telegram."""
    ip = request.remote_addr

    if not _dentro_do_limite(ip):
        return jsonify({
            "status": "erro",
            "mensagem": "Muitas tentativas. Aguarde 5 minutos."
        }), 429

    dados       = request.get_json(silent=True) or {}
    cpf         = (dados.get("cpf")          or "").strip()
    senha       = (dados.get("senha")        or "").strip()
    chat_id     = (dados.get("chat_id")      or "").strip()
    codigo_totp = (dados.get("codigo_totp")  or "").strip()

    if not all([cpf, senha, chat_id, codigo_totp]):
        return jsonify({"status": "erro", "mensagem": "Preencha todos os campos."}), 400

    # ── Credenciais corretas ──
    if cpf == CPF_VALIDO and senha == SENHA_VALIDA:
        if totp.verify(codigo_totp, valid_window=1):
            exp = datetime.now() + timedelta(hours=SESSION_HOURS)
            with _lock_sessoes:
                sessoes_ativas[chat_id] = exp

            notificar(chat_id,
                f"✅ *Login Realizado com Sucesso!*\n\n"
                f"Acesso ao *{PORTAL_NOME}* confirmado.\n"
                f"Sessão ativa por *{SESSION_HOURS} horas*.\n\n"
                f"_Se não foi você, altere sua senha imediatamente._"
            )
            logger.info("Login OK → chat_id=%s", chat_id)
            return jsonify({
                "status": "sucesso",
                "mensagem": "Autenticado com sucesso!",
                "expira_em": exp.isoformat()
            }), 200

        # Código TOTP errado
        notificar(chat_id,
            f"⚠️ *Código de autenticação inválido!*\n\n"
            f"Tentativa de acesso ao *{PORTAL_NOME}* com código QR incorreto.\n"
            f"_Verifique o Google Authenticator e tente novamente._"
        )
        return jsonify({"status": "erro", "mensagem": "Código QR inválido ou expirado."}), 401

    # ── Credenciais erradas ──
    if chat_id:
        notificar(chat_id,
            f"🚨 *Tentativa de Login Recusada!*\n\n"
            f"Credenciais incorretas usadas no *{PORTAL_NOME}*.\n"
            f"_Se não foi você, contate o suporte imediatamente._"
        )
    logger.warning("Login FALHOU → ip=%s chat_id=%s", ip, chat_id)
    return jsonify({"status": "erro", "mensagem": "CPF ou senha incorretos."}), 401


@app.route("/status/<string:chat_id>", methods=["GET"])
def status(chat_id: str):
    """Verifica se há sessão ativa para o chat_id."""
    agora = datetime.now()
    with _lock_sessoes:
        exp = sessoes_ativas.get(chat_id)
    if exp and agora < exp:
        return jsonify({"logado": True, "expira_em": exp.isoformat()})
    return jsonify({"logado": False})


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Acesse: http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)