import time
import requests
import os
from dotenv import load_dotenv
from threading import Thread

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = 173362390

URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send(msg):
    try:
        requests.post(URL, data={"chat_id": CHAT_ID, "text": msg})
        print(f"Отправлено: {msg}")
    except Exception as e:
        print(f"Ошибка: {e}")

# Простой HTTP-сервер, чтобы Render видел, что приложение живо
def http_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    server.serve_forever()

# Запускаем сервер в фоновом потоке
thread = Thread(target=http_server, daemon=True)
thread.start()

# Отправляем сообщение о запуске
send("🚀 Бот запущен и работает!")

# Бесконечный цикл — бот не завершится
while True:
    time.sleep(60)