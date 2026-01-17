from flask import Flask
import threading
import requests
import time
import re

TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

app = Flask(__name__)

@app.route('/')
def index():
    return "Funcionando"

active_cycle = False
stop_requested = False

def send_message(channel_id, content):
    headers = {'Authorization': TOKEN}
    url = f'https://discord.com/api/v9/channels/{channel_id}/messages'
    response = requests.post(url, headers=headers, data={'content': content})
    return response.status_code == 200

def get_chat_messages(last_message_id):
    headers = {'Authorization': TOKEN}
    url = f'https://discord.com/api/v9/channels/{CHANNEL_ID}/messages'
    params = {'limit': 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            messages = response.json()
            if messages:
                current_last_id = messages[0]['id']
                if current_last_id != last_message_id:
                    return messages[0], current_last_id
    except:
        pass
    return None, last_message_id

def repeat_message(text, target_channel, times, author_username):
    global active_cycle, stop_requested
    
    active_cycle = True
    stop_requested = False
    
    send_message(CHANNEL_ID, f"✅ Iniciando ciclo de repetición de \"{text}\" en el canal <#{target_channel}> {times} veces")
    
    for i in range(times):
        if stop_requested:
            send_message(CHANNEL_ID, "⏹️ Ciclo detenido por solicitud")
            break
        
        success = send_message(target_channel, text)
        if not success:
            send_message(CHANNEL_ID, f"❌ Error al enviar mensaje {i+1}/{times}")
        
        time.sleep(5)
    
    if not stop_requested:
        send_message(CHANNEL_ID, f"✅ Ciclo completado: {text} enviado {min(i+1, times)} veces")
    
    active_cycle = False
    stop_requested = False

def process_command(message_content, author_username):
    global active_cycle, stop_requested
    
    if message_content.startswith('!stop'):
        if active_cycle:
            stop_requested = True
            return "🔄 Deteniendo ciclo actual..."
        else:
            return "ℹ️ No hay ciclo activo para detener"
    
    if message_content.startswith('!repite'):
        pattern = r'!repite\s+"([^"]+)"\s+(\d+)\s+(\d+)'
        match = re.search(pattern, message_content)
        
        if not match:
            return "❌ Formato incorrecto. Usa: !repite \"texto\" canal_id veces"
        
        text = match.group(1)
        target_channel = match.group(2)
        times = int(match.group(3))
        
        if times <= 0 or times > 1000:
            return "❌ El número de veces debe estar entre 1 y 1000"
        
        if active_cycle:
            return "🔄 Nuevo ciclo programado al acabar el actual"
        
        thread = threading.Thread(
            target=repeat_message,
            args=(text, target_channel, times, author_username),
            daemon=True
        )
        thread.start()
        return f"✅ Ciclo programado: \"{text}\" en canal {target_channel} {times} veces"
    
    return None

def monitor_and_respond():
    last_message_id = None
    
    while True:
        message, last_message_id = get_chat_messages(last_message_id)
        
        if message:
            content = message.get('content', '')
            author = message.get('author', {})
            author_username = author.get('username', 'Desconocido')
            
            if content.startswith(('!repite', '!stop')):
                response = process_command(content, author_username)
                if response:
                    send_message(CHANNEL_ID, response)
        
        time.sleep(2)

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def run_bot():
    print("🤖 Bot de repetición iniciado")
    print(f"📊 Monitoreando canal: {CHANNEL_ID}")
    print("Comandos disponibles:")
    print("  !repite \"texto\" canal_id veces")
    print("  !stop")
    monitor_and_respond()

if __name__ == '__main__':
    print("🚀 Iniciando sistema integrado...")
    print("🌐 Servidor Flask en http://0.0.0.0:5000")
    print("🤖 Bot Discord activo")
    print("\nPresiona Ctrl+C para salir\n")
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    
    flask_thread.start()
    bot_thread.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Sistema detenido")
