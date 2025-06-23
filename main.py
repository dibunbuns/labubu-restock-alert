import time
import requests
import os
import datetime
import pytz
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

print("🛒 Labubu Stock Checker is starting...")


def check_popmart_stock():
    url = "https://www.popmart.com/us/products/2155?isAppShare=true"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text().lower()
    in_stock = any(word in page_text for word in ["add to cart", "buy now", "in stock", "available now"])
    out_of_stock = any(word in page_text for word in ["sold out", "temporarily out of stock", "restocking soon"])
    return in_stock and not out_of_stock


def check_amazon_stock():
    url = "https://www.amazon.com/dp/B0DT44TSM2"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    page_text = soup.get_text().lower()
    in_stock = any(word in page_text for word in ["add to cart", "buy now", "in stock", "available now"])
    out_of_stock = any(word in page_text for word in ["sold out", "temporarily out of stock", "restocking soon"])
    return in_stock and not out_of_stock


def send_discord_alert(message):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Missing DISCORD_WEBHOOK_URL in environment.")
        return
    try:
        response = requests.post(webhook_url, json={"content": message})
        if response.status_code != 204:
            print(f"⚠️ Alert failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"⚠️ Exception sending alert: {e}")


# Monitoring loop
last_popmart = None
last_amazon = None
last_heartbeat = None

print("✅ Monitoring loop starting...")

while True:
    try:
        now = datetime.datetime.now(pytz.timezone("US/Eastern"))
        current_time = now.strftime("%H:%M")

        # Pop Mart
        popmart_stock = check_popmart_stock()
        if popmart_stock and last_popmart is not True:
            send_discord_alert("🎉 Labubu is in stock on Pop Mart!\nhttps://www.popmart.com/us/products/2155?isAppShare=true")
            print("✅ Pop Mart in stock alert sent.")
            last_popmart = True
        elif not popmart_stock and last_popmart is not False:
            print("❌ Pop Mart still sold out.")
            last_popmart = False

        # Amazon
        amazon_stock = check_amazon_stock()
        if amazon_stock and last_amazon is not True:
            send_discord_alert("🎉 Labubu is in stock on Amazon!\nhttps://www.amazon.com/dp/B0DT44TSM2")
            print("✅ Amazon in stock alert sent.")
            last_amazon = True
        elif not amazon_stock and last_amazon is not False:
            print("❌ Amazon still sold out.")
            last_amazon = False

        # Hourly heartbeat
        if current_time.endswith(":00") and current_time != last_heartbeat:
            send_discord_alert(f"✅ Bot is running. ({now.strftime('%I:%M %p')})")
            print(f"🕒 Heartbeat sent at {current_time}")
            last_heartbeat = current_time

        time.sleep(5)

    except Exception as e:
        print("⚠️ Error in loop:", e)
        time.sleep(10)
