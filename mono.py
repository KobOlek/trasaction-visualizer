import time

import requests

import os
from dotenv import load_dotenv

load_dotenv()

def activate_webhook():
    TOKEN = os.getenv("API_KEY")

    headers = {
        "X-Token": TOKEN,
    }

    WEBHOOK_URL = "https://trasaction-visualizer.onrender.com/mono-webhook"
    payload = {
        "webHookUrl": WEBHOOK_URL
    }

    mono_api_url = "https://api.monobank.ua/personal/webhook"

    print(f"⏳ Реєстрація вебхука в Monobank: {WEBHOOK_URL}...")

    response = requests.post(mono_api_url, headers=headers, json=payload)

    if response.status_code == 200:
        print("✅ Вебхук успішно активовано в Monobank!")
    else:
        print(f"❌ Помилка активації: {response.status_code}")
        print(response.json())

def get_jar() -> dict:
    url = "https://api.monobank.ua/personal/client-info"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        clientInfo = response.json()
        for jar in clientInfo['jars']:
            if jar['id'] == 'nwxAv5X9hnzaHWK6y7P86axFL9FG91g':
                jar['balance'] = str(float(jar['balance'])/100)
                return jar
    return {}

def get_jar_history(jar_id: str) -> dict:
    time_to = int(time.time())
    time_from = time_to - (31*24*60*60)

    url = f"https://api.monobank.ua/personal/statement/{jar_id}/{time_from}/{time_to}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        res = response.json()
        for r in res:
            r['amount'] /= 100
        return res
    return {}
