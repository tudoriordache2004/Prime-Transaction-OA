import os
import sqlite3
from typing import Optional

import finnhub
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import create_database

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "finnhub_data.db"))

def parse_symbols(value: Optional[str]) -> list[str]:
    if not value:
        return []
    raw = value.replace(",", " ").split()
    return sorted({s.strip().upper() for s in raw if s.strip()})

WATCHLIST_SYMBOLS = parse_symbols(os.environ.get("SYMBOLS"))
WATCHLIST_MAX = int(os.environ.get("WATCHLIST_MAX", "100"))


API_KEY = os.environ.get("FINNHUB_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FINNHUB_API_KEY (set it in env or .env)")

client = finnhub.Client(api_key=API_KEY)

app = FastAPI(title="Finnhub -> SQLite API")

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get(
        "CORS_ORIGINS"
    ).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper()

def db_watchlist_symbols(conn: sqlite3.Connection) -> list[str]:
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


@app.on_event("startup")
def startup():
    create_database(DB_PATH)


@app.get("/health")
def health():
    return {"ok": True, "db": DB_PATH}

# Nu mai este nevoie de endpoint-ul ingest, am creat un script care sa apeleze automat inserarea datelor in db 

# @app.post("/ingest/{symbol}")
# def ingest_symbol(symbol: str):
#     symbol = symbol.strip().upper()
#     if not symbol:
#         raise HTTPException(status_code=400, detail="Empty symbol")

#     # Fetch from Finnhub
#     try:
#         profile = client.company_profile2(symbol=symbol) or {}
#         quote = client.quote(symbol) or {}
#     except Exception as e:
#         raise HTTPException(status_code=502, detail=f"Finnhub error: {repr(e)}")

#     name = profile.get("name")
#     currency = profile.get("currency")
#     exchange = profile.get("exchange")
#     industry = profile.get("finnhubIndustry")

#     current_price = quote.get("c")
#     high_price = quote.get("h")
#     low_price = quote.get("l")
#     open_price = quote.get("o")
#     previous_close = quote.get("pc")
#     quote_ts = quote.get("t")

#     if quote_ts is None:
#         raise HTTPException(status_code=502, detail="Quote missing 't' (timestamp)")

#     # Upsert into SQLite
#     conn = get_conn()
#     try:
#         cur = conn.cursor()

#         cur.execute(
#             """
#             INSERT INTO stocks(symbol, name, currency, exchange, industry, updated_at)
#             VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
#             ON CONFLICT(symbol) DO UPDATE SET
#               name=excluded.name,
#               currency=excluded.currency,
#               exchange=excluded.exchange,
#               industry=excluded.industry,
#               updated_at=CURRENT_TIMESTAMP;
#             """,
#             (symbol, name, currency, exchange, industry),
#         )

#         cur.execute(
#             """
#             INSERT INTO quotes_latest(
#               symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts, updated_at
#             )
#             VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
#             ON CONFLICT(symbol) DO UPDATE SET
#               current_price=excluded.current_price,
#               high_price=excluded.high_price,
#               low_price=excluded.low_price,
#               open_price=excluded.open_price,
#               previous_close=excluded.previous_close,
#               quote_ts=excluded.quote_ts,
#               updated_at=CURRENT_TIMESTAMP;
#             """,
#             (symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts),
#         )

#         conn.commit()
#     finally:
#         conn.close()

#     return {"ok": True, "symbol": symbol, "quote_ts": quote_ts}


# ---------------------------------------------------------
# Backend endpoints for stocks

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
            raise HTTPException(status_code=404, detail="Symbol not found in DB.")
        return dict(row)
    finally:
        conn.close()

# ---------------------------------------------------------
# Backend endpoints for quotes

@app.get("/quotes/latest")
def quotes_latest(limit: int = 1000, offset: int = 0):
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts, updated_at
            FROM quotes_latest
            ORDER BY symbol
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [dict(r) for r in rows]
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

@app.get("/quotes/history/{symbol}")
def quote_history(symbol: str, limit: int = 200):
    symbol = symbol.strip().upper()
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT collected_ts, current_price
            FROM quotes_history
            WHERE symbol = ?
            ORDER BY quote_ts DESC
            LIMIT ?
            """,
            (symbol, limit),
        ).fetchall()

        out = [dict(r) for r in rows][::-1]
        return out
    finally:
        conn.close()

# ---------------------------------------------------------
# Backend endpoints for watchlist
@app.get("/watchlist")
def watchlist():
    conn = get_conn()
    try:
        symbols = db_watchlist_symbols(conn)
        return {"symbols": symbols, "source": "db:watchlist"}
    finally:
        conn.close()


@app.post("/watchlist/{symbol}")
def watchlist_add(symbol: str):
    symbol = normalize_symbol(symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="Empty symbol")

    conn = get_conn()
    try:
        # Ensure stock exists (FK requires it). If not, insert a minimal row.
        conn.execute(
            """
            INSERT OR IGNORE INTO stocks(symbol, name, currency, exchange, industry, updated_at)
            VALUES (?, NULL, NULL, NULL, NULL, CURRENT_TIMESTAMP)
            """,
            (symbol,),
        )

        conn.execute(
            """
            INSERT OR IGNORE INTO watchlist(symbol, created_at)
            VALUES (?, CURRENT_TIMESTAMP)
            """,
            (symbol,),
        )
        conn.commit()
        return {"ok": True, "symbol": symbol}
    finally:
        conn.close()

@app.post("/watchlist/{symbol}/refresh")
def refresh_symbol(symbol: str):
    symbol = normalize_symbol(symbol)
    if not symbol:
        raise HTTPException(status_code=400, detail="Empty symbol")

    try:
        profile = client.company_profile2(symbol=symbol) or {}
        quote = client.quote(symbol) or {}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Finnhub error: {repr(e)}")

    quote_ts = quote.get("t")
    if quote_ts is None:
        raise HTTPException(status_code=502, detail="Quote missing 't'")

    name = profile.get("name")
    currency = profile.get("currency")
    exchange = profile.get("exchange")
    industry = profile.get("finnhubIndustry")

    current_price = quote.get("c")
    high_price = quote.get("h")
    low_price = quote.get("l")
    open_price = quote.get("o")
    previous_close = quote.get("pc")

    conn = get_conn()
    try:
        conn.execute(
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

        conn.execute(
            """
            INSERT INTO quotes_latest(symbol, current_price, high_price, low_price, open_price, previous_close, quote_ts, updated_at)
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
        return {"ok": True, "symbol": symbol, "quote_ts": quote_ts}
    finally:
        conn.close()

@app.delete("/watchlist/{symbol}/purge")
def watchlist_purge(symbol: str):
    symbol = normalize_symbol(symbol)
    conn = get_conn()
    try:
        conn.execute("BEGIN;")

        h = conn.execute("DELETE FROM quotes_history WHERE symbol = ?", (symbol,)).rowcount
        q = conn.execute("DELETE FROM quotes_latest WHERE symbol = ?", (symbol,)).rowcount
        w = conn.execute("DELETE FROM watchlist WHERE symbol = ?", (symbol,)).rowcount
        s = conn.execute("DELETE FROM stocks WHERE symbol = ?", (symbol,)).rowcount

        conn.commit()
        return {
            "ok": True,
            "symbol": symbol,
            "deleted": {"quotes_history": h, "quotes_latest": q, "watchlist": w, "stocks": s},
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

@app.get("/watchlist/stocks")
def watchlist_stocks():
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT s.symbol, s.name, s.currency, s.exchange, s.industry, s.updated_at
            FROM watchlist w
            JOIN stocks s ON s.symbol = w.symbol
            ORDER BY
              CASE WHEN w.position IS NULL THEN 1 ELSE 0 END,
              w.position,
              w.created_at
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

@app.get("/search")
def search(query: str):
    q = (query or "").strip()
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Query too short (min 2 chars).")

    try:
        return client.symbol_lookup(q)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Finnhub error: {repr(e)}")


