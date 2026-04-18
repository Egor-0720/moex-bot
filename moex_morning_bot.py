print("Bot is starting...")  # Проверка, выводим сообщение, что бот начал запуск
import time
time.sleep(5)  # Задержка в 5 секунд, чтобы мы могли увидеть сообщение в логах
import requests
import time

TOKEN = "8386523259:AAFyI25gMsunMf4VLC-EJ-jT4nE1ITu6hec"
CHAT_ID = 173362390

URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send(msg):
    requests.post(URL, data={"chat_id": CHAT_ID, "text": msg})

send("🚀 Бот запущен")