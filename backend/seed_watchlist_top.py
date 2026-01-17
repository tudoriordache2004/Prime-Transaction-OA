import os
import sqlite3
from dotenv import load_dotenv

from database import create_database

# Statically populates the db with 50 values from the API to avoid API timeout from fetching too much data

DEFAULT = [
    "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","BRK.B","JPM","V",
    "UNH","XOM","AVGO","LLY","MA","COST","HD","PG","KO","PEP",
    "ABBV","WMT","ORCL","CRM","BAC","NFLX","ADBE","CSCO","TM","NKE",
    "ASML","INTC","AMD","QCOM","TMO","MCD","ABT","MRK","CVX","DIS",
    "GE","IBM","INTU","AMAT","TXN","CAT","PM","LIN","NOW","SPY",
]

def main():
    load_dotenv()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.environ.get("DB_PATH") or os.path.join(base_dir, "finnhub_data.db")

    create_database(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("BEGIN;")
        conn.execute("DELETE FROM watchlist;")

        for i, sym in enumerate(DEFAULT, start=1):
            sym = sym.strip().upper()

            # asigură stock (FK)
            conn.execute(
                """
                INSERT OR IGNORE INTO stocks(symbol, name, currency, exchange, industry, updated_at)
                VALUES (?, NULL, NULL, NULL, NULL, CURRENT_TIMESTAMP)
                """,
                (sym,),
            )

            conn.execute(
                """
                INSERT OR IGNORE INTO watchlist(symbol, position, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (sym, i),
            )

        conn.commit()
    finally:
        conn.close()

    print({"ok": True, "seeded": len(DEFAULT)})

if __name__ == "__main__":
    main()