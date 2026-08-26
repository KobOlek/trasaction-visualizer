import sqlite3
from flask import Flask, request, jsonify, render_template
from datetime import datetime

from mono import *
from sync_history import sync_history

app = Flask(__name__)
DB_NAME = "monobank.db"
data = get_jar()

title = data['title']

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS transactions
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       description
                       TEXT,
                       amount
                       REAL,
                       timestamp
                       TEXT,
                       balance REAL
                   )
                   ''')
    conn.commit()
    conn.close()

init_db()
sync_history()

@app.route("/")
def show_statement():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Витягуємо всі поля, включаючи balance
    cursor.execute('SELECT description, amount, timestamp, balance FROM transactions ORDER BY id DESC')
    rows = cursor.fetchall()

    # ЛОГІКА ГОЛОВНОГО БАЛАНСУ:
    if rows and rows[0]['balance'] is not None:
        # Якщо в базі є транзакції, беремо баланс із найсвіжішої (останньої) події
        current_balance = rows[0]['balance']
    else:
        # Якщо база порожня (ще не було жодного вебхука), беремо реальний залишок з API Монобанку
        # float() потрібен, бо у вашому mono.py баланс повертається як рядок
        current_balance = float(data.get('balance', 0.0))

    conn.close()

    # Формуємо список транзакцій для HTML
    transactions = []
    for row in rows:
        transactions.append({
            "description": row["description"],
            "amount": row["amount"],
            "time": row["timestamp"],
            "balance": row["balance"]  # Додаємо залишок для кожної події
        })

    return render_template(
        "index.html",
        jar_name=title,
        balance=round(current_balance, 2),
        transactions=transactions
    )

@app.route("/mono-webhook", methods=["POST"])
def mono_webhook():
    data = request.json

    if 'type' in data and data['type'] == 'StatementItem':


        account_id = data['data']['account']
        TARGET_JAR_ID = 'nwxAv5X9hnzaHWK6y7P86axFL9FG91g'

        # 3. Фільтруємо: якщо це не наша банка, ігноруємо запит
        if account_id != TARGET_JAR_ID:
            print(f"⏭️ Пропущено транзакцію з іншої картки/рахунку ({account_id})")
            return jsonify({"status": "ignored"}), 200

        tx_data = data['data']['statementItem']

        print(tx_data)

        amount = tx_data['amount'] / 100
        description = tx_data.get('description', 'Поповнення банки')
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        balance = tx_data['balance'] / 100

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO transactions (description, amount, timestamp, balance) VALUES (?, ?, ?, ?)',
            (description, amount, current_time, balance)
        )
        conn.commit()
        conn.close()

        print(f"💾 Транзакцію успішно збережено в SQLite: {amount} UAH")

    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)