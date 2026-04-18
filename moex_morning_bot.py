import time
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, time as dt_time
from threading import Thread

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = 173362390
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

STOCKS = {
    "GAZP": "Газпром",
    "SBER": "Сбер",
    "LKOH": "Лукойл",
    "TATN": "Татнефть",
    "NVTK": "Новатэк",
    "ROSN": "Роснефть",
    "SNGSP": "Сургутнефтегаз преф",
    "VTBR": "ВТБ",
    "GMKN": "Норникель"
}

first_hit_time = {}
last_alert_time = {}

def send(msg):
    try:
        requests.post(URL, data={"chat_id": CHAT_ID, "text": msg})
        print(f"Отправлено: {msg}")
    except Exception as e:
        print(f"Ошибка: {e}")

def get_evening_close(ticker):
    try:
        url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        params = {'from': datetime.now().strftime('%Y-%m-%d'), 'limit': 1}
        response = requests.get(url, params=params)
        data = response.json()
        history = data['history']['data']
        if history:
            close_price = history[0][7]
            return float(close_price) if close_price else None
        return None
    except Exception as e:
        print(f"Ошибка получения закрытия {ticker}: {e}")
        return None

def get_morning_open(ticker):
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        response = requests.get(url)
        data = response.json()
        market_data = data['marketdata']['data']
        for row in market_data:
            if row[0] == ticker:
                open_price = row[3]
                return float(open_price) if open_price else None
        return None
    except Exception as e:
        print(f"Ошибка получения открытия {ticker}: {e}")
        return None

def get_current_price(ticker):
    try:
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
        response = requests.get(url)
        data = response.json()
        market_data = data['marketdata']['data']
        for row in market_data:
            if row[0] == ticker:
                current_price = row[10]
                return float(current_price) if current_price else None
        return None
    except Exception as e:
        print(f"Ошибка получения текущей цены {ticker}: {e}")
        return None

def check_signal(ticker):
    evening_close = get_evening_close(ticker)
    morning_open = get_morning_open(ticker)
    current_price = get_current_price(ticker)
    
    if not current_price:
        return None, None, None
    
    base_price = None
    if evening_close and morning_open:
        base_price = max(evening_close, morning_open)
    elif evening_close:
        base_price = evening_close
    elif morning_open:
        base_price = morning_open
    else:
        return None, None, None
    
    deviation = ((current_price - base_price) / base_price) * 100
    return deviation, base_price, current_price

def is_weekend():
    """Проверяет, выходной ли сегодня (суббота или воскресенье)"""
    return datetime.now().weekday() >= 5

def morning_monitor():
    send("📊 Бот запущен. Работает по БУДНЯМ с 7:00 до 9:00 МСК")
    send("📅 Суббота и воскресенье — бот полностью спит (0 часов работы)")
    send("🛡️ Защита от проколов: 5 секунд")
    send("⏰ Повторный сигнал по акции: не чаще 1 раза в 15 минут")
    
    while True:
        # Проверяем, выходной ли сегодня
        if is_weekend():
            # Выходной — спим 24 часа, потом проверим день недели снова
            print("Выходной день, бот спит до понедельника...")
            time.sleep(86400)  # 24 часа
            continue
        
        # Будний день — работаем по расписанию
        now_time = datetime.now().time()
        current_ts = time.time()
        
        start_time = dt_time(7, 0)
        end_time = dt_time(9, 0)
        
        if start_time <= now_time <= end_time:
            for ticker, name in STOCKS.items():
                deviation, base_price, current_price = check_signal(ticker)
                
                if deviation is not None and deviation >= 0.8:
                    last_time = last_alert_time.get(ticker, 0)
                    minutes_since_last = (current_ts - last_time) / 60 if last_time > 0 else 999
                    
                    if minutes_since_last < 15:
                        continue
                    
                    if ticker not in first_hit_time:
                        first_hit_time[ticker] = current_ts
                    else:
                        elapsed = current_ts - first_hit_time[ticker]
                        if elapsed >= 5:
                            msg = f"""🚨 СИГНАЛ ПО {name} ({ticker})!
📈 Отклонение: {deviation:.2f}%
💰 Базовая цена: {base_price:.2f}
💵 Текущая цена: {current_price:.2f}
✅ Подтверждение 5 секунд
⏰ Следующий сигнал: через 15 минут
"""
                            send(msg)
                            last_alert_time[ticker] = current_ts
                            del first_hit_time[ticker]
                else:
                    if ticker in first_hit_time:
                        del first_hit_time[ticker]
            
            time.sleep(5)
        else:
            # Вне рабочего времени (до 7:00 или после 9:00)
            first_hit_time.clear()
            time.sleep(60)

def http_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")
    server = HTTPServer(('0.0.0.0', 8080), Handler)
    server.serve_forever()

thread = Thread(target=http_server, daemon=True)
thread.start()
morning_monitor()