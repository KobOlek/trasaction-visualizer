import os
os.environ["LC_ALL"] = "en_US.UTF-8"

import psycopg

from mono import get_jar, get_jar_history
from datetime import datetime

def sync_history():
    jar = get_jar()

    if not jar:
        print("Error. Jar was not found.")
        return

    jar_id = jar['id']

    history = get_jar_history(jar_id)

    if not history:
        print("History is empty.")
        return

    print(f"{len(history)} trasactions received.")

    conn = psycopg.connect(dbname="monobank", user="postgres", password="25092008Olek", host="localhost", port=5432)
    cursor = conn.cursor()

    added_count = 0

    # Monobank віддає транзакції від новіших до старіших.
    # Щоб у базі вони йшли в правильному хронологічному порядку (і правильними ID),
    # ми перевернемо список за допомогою reversed()
    for tx in reversed(history):
        # amount вже поділено на 100 у вашому mono.py, тому беремо як є
        amount = tx['amount']
        description = tx.get('description', 'Поповнення банки')

        # Monobank віддає час у форматі Unix timestamp (напр. 1717448075)
        # Нам треба перетворити його у зручний рядок "DD.MM.YYYY HH:MM", як у нашому app.py
        tx_time = datetime.fromtimestamp(tx['time']).strftime("%d.%m.%Y %H:%M")

        # Записуємо в базу
        cursor.execute(
            'INSERT INTO transactions (description, amount, timestamp) VALUES (%s, %s, %s)',
            (description, amount, tx_time)
        )
        added_count += 1

    # Зберігаємо зміни та закриваємо з'єднання
    conn.commit()
    conn.close()

    print(f"🎉 Успішно збережено {added_count} транзакцій в SQLite!")