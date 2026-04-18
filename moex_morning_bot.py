import time
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Загружаем переменные из .env файла

TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получаем токен из .env
CHAT_ID = 173362390  # ID чата

URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

def send(msg):
    requests.post(URL, data={"chat_id": CHAT_ID, "text": msg})

send("🚀 Бот запущен")  # Отправляем сообщение о запуске бота