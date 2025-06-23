import time
import requests
import os
import datetime
import pytz
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

print("Replit Labubu Stock Checker is starting...")


def check_popmart_stock():
    url = "https://www.popmart.com/us/products/2155?isAppShare=true"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text().lower()

    in_stock_keywords = ["add to cart", "buy now", "in stock", "available now"]
    out_of_stock_keywords = [
        "sold out", "temporarily out of stock", "restocking soon"
    ]

    if any(word in page_text for word in in_stock_keywords) and not any(
            word in page_text for word in out_of_stock_keywords):
        return True
    return False


def check_amazon_stock():
    url = "https://www.amazon.com/POP-MART-Big-into-Energy/dp/B0DT44TSM2?ref_=ast_sto_dp&th=1"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text().lower()

    in_stock_keywords = ["add to cart", "buy now", "in stock", "available now"]
    out_of_stock_keywords = [
        "sold out", "temporarily out of stock", "restocking soon"
    ]

    if any(word in page_text for word in in_stock_keywords) and not any(
            word in page_text for word in out_of_stock_keywords):
        return True
    return False


def send_discord_alert(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ No webhook URL set in environment variables!")
        return

    try:
        response = requests.post(webhook_url, json={"content": message})
        if response.status_code != 204:
            print(
                f"⚠️ Failed to send alert: {response.status_code} - {response.text}"
            )
    except Exception as e:
        print(f"⚠️ Exception sending alert: {e}")


app = Flask(__name__)


@app.route('/')
def home():
    return "Replit Labubu Stock Checker is running!"


def run_flask():
    print("🌐 Starting Flask server on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)


Thread(target=run_flask).start()

# Give Flask server time to start
print("⏳ Waiting for Flask server to initialize...")
time.sleep(3)
print("🚀 Starting stock monitoring...")

last_popmart_status = None
last_amazon_status = None
last_heartbeat_hour = None

while True:
    try:
        est = pytz.timezone('US/Eastern')
        now = datetime.datetime.now(est)
        current_time = now.strftime('%H:%M')

        # --- Check Pop Mart ---
        popmart_in_stock = check_popmart_stock()
        if popmart_in_stock and last_popmart_status is not True:
            print("🎉 Labubu is in stock on Pop Mart!")
            send_discord_alert(
                "🎉 Labubu is in stock on Pop Mart!\n🛍 https://www.popmart.com/us/products/2155?isAppShare=true"
            )
            last_popmart_status = True
        elif not popmart_in_stock and last_popmart_status is not False:
            print("❌ Labubu is still sold out on Pop Mart.")
            last_popmart_status = False

        # --- Check Amazon ---
        amazon_in_stock = check_amazon_stock()
        if amazon_in_stock and last_amazon_status is not True:
            print("🎉 Labubu is in stock on Amazon!")
            send_discord_alert(
                "🎉 Labubu is in stock on Amazon!\n🛒 https://www.amazon.com/dp/B0DT44TSM2"
            )
            last_amazon_status = True
        elif not amazon_in_stock and last_amazon_status is not False:
            print("❌ Labubu is still sold out on Amazon.")
            last_amazon_status = False

        # --- Hourly Heartbeat ---
        if current_time.endswith(
                ":00") and current_time != last_heartbeat_hour:
            send_discord_alert(
                f"✅ Labubu bot is still running! ({now.strftime('%I:%M %p')})")
            last_heartbeat_hour = current_time

        time.sleep(5)
    except Exception as e:
        print("⚠️ Error:", e)
        time.sleep(5)
