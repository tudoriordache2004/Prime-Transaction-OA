import os
import json
import time
import argparse
import sqlite3
from datetime import datetime, timezone

import finnhub
from dotenv import load_dotenv

from database import create_database

# Script that fetches and parses information from the Finnhub API and sends it to the Sqlite db

def parse_symbols(value: str) -> list[str]:
    raw = value.replace(",", " ").split()
    return sorted({s.strip().upper() for s in raw if s.strip()})

# This function takes the parsed symbols with the information from the APIs and inserts tge data in the db

def upsert_learned_data(conn: sqlite3.Connection, symbol: str, profile: dict, quote: dict) -> None:
    name = profile.get("name")
    currency = profile.get("currency")
    exchange = profile.get("exchange")
    industry = profile.get("finnhubIndustry")

    current_price = quote.get("c")
    high_price = quote.get("h")
    low_price = quote.get("l")
    open_price = quote.get("o")
    previous_close = quote.get("pc")
    quote_ts = quote.get("t")

    if quote_ts is None:
        raise ValueError("Quote missing 't' (timestamp)")

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO stocks(symbol, name, currency, exchange, industry, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(symbol) DO UPDATE SET
          name=excluded.name,
          currency=excluded.currency,
          exchange=excluded.exchange,
          industry=excluded.industry,
          updated_at=CURRENT_TIMESTAMP;
        """,
        (symbol, name, currency, exchange, industry),
    )

    cur.execute(
        """
        INSERT INTO quotes_latest(
          symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(symbol) DO UPDATE SET
          current_price=excluded.current_price,
          high_price=excluded.high_price,
          low_price=excluded.low_price,
          open_price=excluded.open_price,
          previous_close=excluded.previous_close,
          quote_ts=excluded.quote_ts,
          updated_at=CURRENT_TIMESTAMP;
        """,
        (symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts),
    )
    collected_ts = int(time.time())

    cur.execute(
        """
        INSERT OR IGNORE INTO quotes_history(
        symbol, collected_ts, quote_ts, current_price, high_price, low_price, open_price, previous_close
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (symbol, collected_ts, quote_ts, current_price, high_price, low_price, open_price, previous_close),
    )


def fetch_with_retry(fn, *, retries: int, base_sleep_s: float):
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if attempt == retries:
                break
            time.sleep(base_sleep_s * (2 ** attempt))
    raise last_exc

# Reads from the db for /watchlist
def read_watchlist_symbols(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        rows = conn.execute(
            """
            SELECT symbol
            FROM watchlist
            ORDER BY
              CASE WHEN position IS NULL THEN 1 ELSE 0 END,
              position,
              created_at
            """
        ).fetchall()
        return [r["symbol"] for r in rows]
    finally:
        conn.close()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Ingest Finnhub -> SQLite (stocks + quotes_latest)")
    # change: symbols devine override, altfel citim din DB
    parser.add_argument("--symbols", default="", help="Optional override: Ex: AAPL,TSLA (altfel ia din DB watchlist)")
    parser.add_argument("--db-path", default=os.environ.get("DB_PATH"), help="Path către SQLite db")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--sleep", type=float, default=0.5, help="Sleep între simboluri (sec)")
    parser.add_argument("--interval", type=int, default=0, help="Dacă >0, rerulează ingest la fiecare N secunde")
    args = parser.parse_args()

    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        raise SystemExit("Missing FINNHUB_API_KEY")

    # change: calculezi db_path ÎNAINTE să citești watchlist
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = args.db_path or os.path.join(base_dir, "finnhub_data.db")

    # asigură schema (inclusiv watchlist)
    create_database(db_path)
    client = finnhub.Client(api_key=api_key)


    while True:
        # recitește watchlist-ul la fiecare rundă (dinamic)
        symbols = parse_symbols(args.symbols) if args.symbols else []
        if not symbols:
            symbols = read_watchlist_symbols(db_path)

        if not symbols:
            print("Watchlist is empty. Waiting...")
            if args.interval <= 0:
                break
            time.sleep(args.interval)
            continue

        summary = {
            "db_path": db_path,
            "symbols": symbols,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ok": [],
            "fail": [],
        }

        # deschide DB per rundă (safe pt long-running)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            for sym in symbols:
                try:
                    profile = fetch_with_retry(
                        lambda: client.company_profile2(symbol=sym) or {},
                        retries=args.retries,
                        base_sleep_s=1.0,
                    )
                    quote = fetch_with_retry(
                        lambda: client.quote(sym) or {},
                        retries=args.retries,
                        base_sleep_s=1.0,
                    )

                    conn.execute("BEGIN;")
                    upsert_learned_data(conn, sym, profile, quote)
                    conn.commit()

                    summary["ok"].append({"symbol": sym, "quote_ts": quote.get("t")})
                except Exception as e:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    summary["fail"].append({"symbol": sym, "error": repr(e)})

                time.sleep(args.sleep)
        finally:
            conn.close()

        summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        print(json.dumps(summary, ensure_ascii=False, indent=2))

        if args.interval <= 0:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()