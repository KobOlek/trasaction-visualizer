import os

from flask import Flask, request, jsonify, render_template, redirect
from datetime import datetime
import psycopg
from psycopg.rows import dict_row  # Added to make rows act like dictionaries
from dotenv import load_dotenv

load_dotenv()


from mono import *

app = Flask(__name__)
TITLE = "Общак Центурії"

DB_URL = os.getenv("DATABASE_URL")

def init_db():
    # Тепер підключаємося через рядок DB_URL
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS transactions
                           (
                               id SERIAL PRIMARY KEY,
                               description TEXT,
                               amount NUMERIC,
                               timestamp TIMESTAMP,
                               balance NUMERIC
                           )
                           ''')

init_db()
@app.route("/")
def show_statement():
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute('SELECT description, amount, timestamp, balance FROM transactions WHERE amount >= 1 ORDER BY id DESC')
            rows = cursor.fetchall()

    if rows and rows[0]['balance'] is not None:
        current_balance = float(rows[0]['balance'])
    else:
        current_balance = 0.0

    transactions = []
    for row in rows:
        transactions.append({
            "description": row["description"],
            "amount": float(row["amount"]) if row["amount"] else 0.0,
            "time": row["timestamp"].strftime("%d.%m.%Y %H:%M") if isinstance(row["timestamp"], datetime) else row[
                "timestamp"],
            "balance": float(row["balance"]) if row["balance"] else 0.0
        })

    return render_template(
        "index.html",
        jar_name=TITLE,
        balance=round(current_balance, 2),
        transactions=transactions
    )


@app.route("/mono-webhook", methods=["POST"])
def mono_webhook():
    req_data = request.json

    if req_data and req_data.get('type') == 'StatementItem':

        # Безпечно дістаємо account
        account_id = req_data.get('data', {}).get('account')
        TARGET_JAR_ID = 'nwxAv5X9hnzaHWK6y7P86axFL9FG91g'

        if account_id != TARGET_JAR_ID:
            print(f"⏭️ Пропущено транзакцію з іншої картки/рахунку")
            return jsonify({"status": "ignored"}), 200

        tx_data = req_data.get('data', {}).get('statementItem', {})

        if not tx_data:
            return jsonify({"status": "error"}), 400

        amount = tx_data.get('amount', 0) / 100
        description = tx_data.get('description', 'Поповнення банки')

        # Використовуємо реальний час транзакції від Монобанку!
        tx_time_unix = tx_data.get('time', datetime.now().timestamp())
        current_time = datetime.fromtimestamp(tx_time_unix)

        balance = tx_data.get('balance', 0) / 100

        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    'INSERT INTO transactions (description, amount, timestamp, balance) VALUES (%s, %s, %s, %s)',
                    (description, amount, current_time, balance)
                )

        print(f"💾 Транзакцію збережено: {amount} UAH")

    return jsonify({"status": "success"}), 200


@app.route("/activate")
def setup_webhook():
    activate_webhook()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)