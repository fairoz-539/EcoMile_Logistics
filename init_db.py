import sqlite3

def init_db_with_user():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Create tables (same as in app.py)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS routes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        addresses TEXT NOT NULL,
        geometry TEXT NOT NULL,
        total_distance REAL,
        total_co2 REAL,
        analytics TEXT,
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS collaboration_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        competitor_id TEXT,
        goods TEXT,
        services TEXT,
        routes TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    # Insert default user
    c.execute('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', ('user1', 'password1'))
    conn.commit()
    conn.close()
    print("Database initialized with default user: user1 / password1")

if __name__ == '__main__':
    init_db_with_user()