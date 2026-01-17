import sqlite3

def create_database(db_name="finnhub_data.db"):
    # Connecting to the sqlite3 db
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Company profiles, shown in the /watchlist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        currency TEXT,
        exchange TEXT,
        industry TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Price fluctuation, shown in /quotes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes_latest (
        symbol TEXT PRIMARY KEY,
        current_price REAL,
        high_price REAL,
        low_price REAL,
        open_price REAL,
        previous_close REAL,
        quote_ts INTEGER,             
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            symbol TEXT PRIMARY KEY,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            position INTEGER,
            FOREIGN KEY (symbol) REFERENCES stocks (symbol)
        )
    ''')

    # 4. Quotes history for updating the charts
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes_history (
        symbol TEXT,
        collected_ts INTEGER,   -- int(time.time()) când ai rulat ingest
        quote_ts INTEGER,       -- Finnhub t (poate rămâne constant)
        current_price REAL,
        high_price REAL,
        low_price REAL,
        open_price REAL,
        previous_close REAL,
        PRIMARY KEY (symbol, collected_ts),
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
        )  
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_quotes_history_symbol_ts
        ON quotes_history(symbol, collected_ts)
    ''')

    conn.commit()
    conn.close()
    print(f"Baza de date '{db_name}' a fost creată cu succes!")

if __name__ == "__main__":
    create_database()