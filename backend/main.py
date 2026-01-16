import os
import sqlite3
from typing import Optional

import finnhub
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from database import create_database

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "finnhub_data.db"))

API_KEY = os.environ.get("FINNHUB_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FINNHUB_API_KEY (set it in env or .env)")

client = finnhub.Client(api_key=API_KEY)

app = FastAPI(title="Finnhub -> SQLite API")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@app.on_event("startup")
def startup():
    create_database(DB_PATH)


@app.get("/health")
def health():
    return {"ok": True, "db": DB_PATH}


@app.post("/ingest/{symbol}")
def ingest_symbol(symbol: str):
    symbol = symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Empty symbol")

    # Fetch from Finnhub
    try:
        profile = client.company_profile2(symbol=symbol) or {}
        quote = client.quote(symbol) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Finnhub error: {repr(e)}")

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
        raise HTTPException(status_code=502, detail="Quote missing 't' (timestamp)")

    # Upsert into SQLite
    conn = get_conn()
    try:
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

        conn.commit()
    finally:
        conn.close()

    return {"ok": True, "symbol": symbol, "quote_ts": quote_ts}


@app.get("/stocks")
def list_stocks(limit: int = 100, offset: int = 0):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT symbol, name, currency, exchange, industry, updated_at FROM stocks ORDER BY symbol LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/stocks/{symbol}")
def get_stock(symbol: str):
    symbol = symbol.strip().upper()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT symbol, name, currency, exchange, industry, updated_at FROM stocks WHERE symbol = ?",
            (symbol,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Symbol not found in DB. Call POST /ingest/{symbol} first.")
        return dict(row)
    finally:
        conn.close()


@app.get("/quotes/latest/{symbol}")
def get_quote_latest(symbol: str):
    symbol = symbol.strip().upper()
    conn = get_conn()
    try:
        row = conn.execute(
            """
            SELECT symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts, updated_at
            FROM quotes_latest
            WHERE symbol = ?
            """,
            (symbol,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No quote in DB. Call POST /ingest/{symbol} first.")
        return dict(row)
    finally:
        conn.close()