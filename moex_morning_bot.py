import time
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, time as dt_time
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

load_dotenv()

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "173362390"
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

MOEX_MARKET_URL = "https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json"
MOEX_HISTORY_URL = "https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities"

first_hit_time = {}
last_alert_time = {}
evening_close_cache = {}

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; MOEX Bot/1.0)'})

def send(msg):
    try:
        requests.post(URL, data={"chat_id": CHAT_ID, "text": msg}, timeout=15)
        print(f"Отправлено: {msg}")
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")

def get_evening_close(ticker):
    today_str = datetime.now().strftime('%Y-%m-%d')
    cache_key = f"{ticker}_{today_str}"
    if cache_key in evening_close_cache:
        return evening_close_cache[cache_key]

    try:
        url = f"{MOEX_HISTORY_URL}/{ticker}.json"
        params = {'from': today_str, 'limit': 1}
        response = session.get(url, params=params, timeout=15)
        data = response.json()
        history = data.get('history', {}).get('data', [])
        if history and history[0][7] is not None:
            close_price = float(history[0][7])
            evening_close_cache[cache_key] = close_price
            return close_price
        return None
    except Exception as e:
        print(f"Ошибка получения закрытия {ticker}: {e}")
        return None

def get_all_market_data():
    try:
        response = session.get(MOEX_MARKET_URL, timeout=15)
        data = response.json()

        if 'marketdata' not in data:
            print("⚠️ API вернул неожиданную структуру (нет marketdata)")
            return None

        market_data = data.get('marketdata', {}).get('data', [])
        
        result = {}
        for row in market_data:
            ticker = row[0]
            if ticker in STOCKS:
                open_price = float(row[3]) if row[3] else None
                current_price = float(row[10]) if row[10] else None
                result[ticker] = {
                    'open': open_price,
                    'current': current_price
                }
        return result
    except Exception as e:
        print(f"Ошибка получения рыночных данных: {e}")
        return None

def check_signals():
    market_prices = get_all_market_data()
    if not market_prices:
        return

    current_ts = time.time()

    for ticker, name in STOCKS.items():
        prices = market_prices.get(ticker)
        if not prices or not prices['current']:
            continue

        current_price = prices['current']
        morning_open = prices['open']
        evening_close = get_evening_close(ticker)

        base_price = None
        if evening_close and morning_open:
            base_price = max(evening_close, morning_open)
        elif evening_close:
            base_price = evening_close
        elif morning_open:
            base_price = morning_open
        else:
            continue

        if not base_price or base_price == 0:
            continue

        deviation = ((current_price - base_price) / base_price) * 100

        if deviation >= 0.7:
            last_time = last_alert_time.get(ticker, 0)
            minutes_since_last = (current_ts - last_time) / 60 if last_time > 0 else 999
            if minutes_since_last < 15:
                continue

            if ticker not in first_hit_time:
                first_hit_time[ticker] = current_ts
            else:
                elapsed = current_ts - first_hit_time[ticker]
                if elapsed >= 5:
                    msg = (f"🚨 СИГНАЛ ПО {name} ({ticker})!\n"
                           f"📈 Отклонение: {deviation:.2f}%\n"
                           f"💰 Базовая цена: {base_price:.2f}\n"
                           f"💵 Текущая цена: {current_price:.2f}\n"
                           f"✅ Подтверждение 5 секунд\n"
                           f"⏰ Следующий сигнал: через 15 минут")
                    send(msg)
                    last_alert_time[ticker] = current_ts
                    del first_hit_time[ticker]
        else:
            if ticker in first_hit_time:
                del first_hit_time[ticker]

def is_weekend():
    return datetime.now().weekday() >= 5

def morning_monitor():
    send("📊 MOEX бот запущен. Работает по БУДНЯМ с 7:00 до 9:00 МСК")
    
    while True:
        if is_weekend():
            print("Выходной день, бот спит...")
            time.sleep(3600)
            continue

        now_time = datetime.now().time()
        start_time = dt_time(7, 0)
        end_time = dt_time(9, 0)

        if start_time <= now_time <= end_time:
            check_signals()
            time.sleep(5)
        else:
            first_hit_time.clear()
            time.sleep(60)

# --- МИНИМАЛЬНЫЙ ВЕБ-СЕРВЕР ДЛЯ AMVERA ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        pass

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), Handler)
    server.serve_forever()

Thread(target=run_web_server, daemon=True).start()

morning_monitor()
