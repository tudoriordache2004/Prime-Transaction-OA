import sqlite3

def create_database(db_name="finnhub_data.db"):
    # Conectarea la baza de date (se va crea automat dacă nu există)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # 1. Tabel pentru Profilul Companiei
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

    # 2. Tabel pentru Prețuri (Quotes)
    # Folosim o cheie străină (Foreign Key) către tabelul stocks
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

    conn.commit()
    conn.close()
    print(f"Baza de date '{db_name}' a fost creată cu succes!")

if __name__ == "__main__":
    create_database()