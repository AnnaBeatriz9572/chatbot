import telebot as tb
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = tb.TeleBot("8620872096:AAEK4ZvC34_VjdwahJnae3exiSSNeuIdEYM")

@bot.message_handler(commands=['start'])
def boasvindas(mensagem):
    teclado = InlineKeyboardMarkup()
    # Link do seu sistema web no GitHub Pages
    url_web = "https://annabeatriz9572.github.io/chatbot/"
    
    botao = InlineKeyboardButton(text="🔐 Abrir Sistema de Autenticação", url=url_web)
    teclado.add(botao)
    
    bot.send_message(
        mensagem.chat.id, 
        "Olá! Bem-vinda ao portal de autenticação da IC.\n\nClique abaixo para validar sua identidade no navegador:", 
        reply_markup=teclado
    )

print("Bot aguardando comandos...")
bot.infinity_polling()