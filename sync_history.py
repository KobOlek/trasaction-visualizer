import os

os.environ["LC_ALL"] = "en_US.UTF-8"

import psycopg
from mono import get_jar, get_jar_history
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

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

    print(f"{len(history)} transactions received. Saving to database...")

    added_count = 0

    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cursor:

            for tx in reversed(history):
                # amount вже поділено на 100 у mono.py
                amount = tx['amount']
                description = tx.get('description', 'Поповнення банки')

                balance = tx.get('balance', 0) / 100

                tx_time_unix = tx['time']
                utc_time = datetime.fromtimestamp(tx_time_unix, tz=timezone.utc)
                kyiv_time = utc_time + timedelta(hours=3)
                tx_time = kyiv_time.replace(tzinfo=None)

                cursor.execute(
                    'INSERT INTO transactions (description, amount, timestamp, balance) VALUES (%s, %s, %s, %s)',
                    (description, amount, tx_time, balance)
                )
                added_count += 1

            cursor.execute('''
                           SELECT setval(
                                          pg_get_serial_sequence('transactions', 'id'),
                                          COALESCE(MAX(id), 1)
                                  )
                           FROM transactions;
                           ''')

    print(f"{added_count} transactions successfully saved.")


if __name__ == "__main__":
    sync_history()