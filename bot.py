# bibliotecas
import telebot as tb
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
import json

chave_api = "8620872096:AAEK4ZvC34_VjdwahJnae3exiSSNeuIdEYM"
bot = tb.TeleBot(chave_api)
print(f"O token atual começa com: {chave_api[:10]}...")

# --- 1. COMANDO START ---

@bot.message_handler(commands=['start'])
def boasvindas(mensagem):
    # Mudamos para ReplyKeyboardMarkup (o botão que fica fixo embaixo)
    teclado = ReplyKeyboardMarkup(resize_keyboard=True) 
    url_mini_app = "https://annabeatriz9572.github.io/chatbot/" 
    
    # Mudamos para KeyboardButton
    botao_scanner = KeyboardButton(
        text="📷 Escanear CRM", 
        web_app=WebAppInfo(url=url_mini_app)
    )
    
    teclado.add(botao_scanner)
    texto = 'Olá! Bem-vindo ao sistema de MFA da IC 2025-2026.'
    bot.send_message(mensagem.chat.id, texto, reply_markup=teclado)


# --- 2. NOVO: RECEBER OS DADOS DO MINI APP ---
@bot.message_handler(content_types=['web_app_data'])
def receber_dados(mensagem):
    print("Recebi um /start!")
    # Pega o "pacotinho" de texto enviado pelo site e transforma em variáveis no Python
    dados_recebidos = mensagem.web_app_data.data
    pacote = json.loads(dados_recebidos)
    
    cpf_digitado = pacote.get("cpf")
    senha_digitada = pacote.get("senha")
    qr_code_lido = pacote.get("qr_code")

    # --- SIMULAÇÃO DA API ---
    # No futuro do projeto, aqui entrará a conexão via "requests" para validação 
    # na API dos Conselhos Regionais de Medicina (CRM).
    # Por enquanto, teste o sucesso com CPF 123 e Senha 456 no seu Mini App!
    
    if cpf_digitado == "123" and senha_digitada == "456":
        
        texto_sucesso = f"✅ Identidade validada com sucesso!"
        bot.send_message(mensagem.chat.id, texto_sucesso)
        
    else:
        
        # Cria o botão de novo para o caso de erro
        teclado_erro = InlineKeyboardMarkup()
        url_mini_app = "https://annabeatriz9572.github.io" 
        botao_tentar = InlineKeyboardButton(
            text="🔄 Tentar Novamente", 
            web_app=WebAppInfo(url=url_mini_app)
        )
        teclado_erro.add(botao_tentar)
        
        texto_erro = "❌ Erro na autenticação: CPF ou Senha não conferem. Por favor, tente novamente."
        bot.send_message(mensagem.chat.id, texto_erro, reply_markup=teclado_erro)


# --- 3. MOTOR DO BOT (Sempre a última linha) ---
bot.infinity_polling()