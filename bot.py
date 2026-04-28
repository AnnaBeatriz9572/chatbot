
import os
import logging
from pathlib import Path
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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
logger = logging.getLogger("mfa_bot")

# ─────────────────────────────────────────────
#  Variáveis de ambiente
# ─────────────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN")
PORTAL_URL = os.environ.get("PORTAL_URL", "http://localhost:5000")

if not BOT_TOKEN:
    raise RuntimeError(
        "\n[ERRO] BOT_TOKEN não encontrado!\n"
        "Crie o arquivo .env com:  BOT_TOKEN=seu_token_aqui\n"
    )

# ─────────────────────────────────────────────
#  Bot
# ─────────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
logger.info("Bot conectado. Aguardando mensagens...")


@bot.message_handler(commands=["start", "ajuda"])
def handle_start(message: telebot.types.Message) -> None:
    chat_id = str(message.chat.id)
    nome    = message.from_user.first_name or "Usuário"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🌐 Acessar o Portal", url=PORTAL_URL))

    bot.send_message(
        message.chat.id,
        f"👋 Olá, *{nome}*!\n\n"
        f"Este bot envia notificações de acesso ao *Portal de Saúde*.\n\n"
        f"🔑 *Seu Chat ID é:*\n"
        f"`{chat_id}`\n\n"
        f"📋 Copie este código e cole no campo *Chat ID* do portal ao fazer login.\n\n"
        f"_Você receberá um aviso aqui a cada tentativa de acesso._",
        parse_mode="Markdown",
        reply_markup=markup,
    )
    logger.info("/start → chat_id=%s nome=%s", chat_id, nome)


@bot.message_handler(commands=["meu_id"])
def handle_id(message: telebot.types.Message) -> None:
    chat_id = str(message.chat.id)
    bot.send_message(
        message.chat.id,
        f"🆔 Seu Chat ID: `{chat_id}`",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda msg: True)
def handle_desconhecido(message: telebot.types.Message) -> None:
    bot.send_message(
        message.chat.id,
        "🤖 Este bot é exclusivo para *notificações de autenticação*.\n\n"
        "Use /start para ver seu Chat ID.",
        parse_mode="Markdown",
    )


if __name__ == "__main__":
    logger.info("Bot rodando. Pressione Ctrl+C para parar.")
    bot.infinity_polling(
        timeout=30,
        long_polling_timeout=20,
        logger_level=logging.WARNING,
    )
