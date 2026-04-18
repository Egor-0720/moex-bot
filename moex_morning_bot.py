import requests

TOKEN = "твой_токен"
CHAT_ID = 173362390

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

send("🚀 Бот запущен")
