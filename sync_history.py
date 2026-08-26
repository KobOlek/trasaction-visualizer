import sqlite3
from datetime import datetime
from mono import get_jar, get_jar_history

DB_NAME = "monobank.db"


def sync_history():
    print("⏳ Отримуємо інформацію про банку...")
    jar = get_jar()

    if not jar:
        print("❌ Помилка: Банку не знайдено.")
        return

    jar_id = jar['id']
    print(f"✅ Знайдено банку: '{jar['title']}'. Завантажуємо історію за останні 31 день...")

    # Викликаємо вашу функцію з mono.py
    history = get_jar_history(jar_id)

    if not history:
        print("ℹ️ Історія порожня або виникла помилка (можливо, спрацював ліміт запитів 1 раз на хвилину).")
        return

    print(f"📥 Отримано {len(history)} транзакцій. Записуємо в базу даних...")

    # Підключаємось до нашої існуючої бази
    conn = sqlite3.connect(DB_NAME)
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
            'INSERT INTO transactions (description, amount, timestamp) VALUES (?, ?, ?)',
            (description, amount, tx_time)
        )
        added_count += 1

    # Зберігаємо зміни та закриваємо з'єднання
    conn.commit()
    conn.close()

    print(f"🎉 Успішно збережено {added_count} транзакцій в SQLite!")