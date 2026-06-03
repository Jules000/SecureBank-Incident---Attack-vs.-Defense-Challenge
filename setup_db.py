import os
import sqlite3
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "db.sqlite")


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


SEED_USERS = [
    ("alice", hash_password("rockyou"), "Alice Johnson", 5500.00),
    ("bob", hash_password("password123"), "Bob Smith", 12300.00),
    ("charlie", hash_password("iloveyou"), "Charlie Brown", 8700.00),
    ("diana", hash_password("letmein"), "Diana Prince", 22150.00),
    ("edward", hash_password("12345678"), "Edward Norton", 3120.00),
    ("frank", hash_password("admin123"), "Frank Castle", 9750.00),
    ("grace", hash_password("welcome"), "Grace Hopper", 6400.00),
]

TRANSACTIONS_BY_USER = {
    "alice": [
        ("Salary Deposit", "income", "2024-10-21", 12450.00, "credit"),
        ("Apple Store, Fifth Ave", "technology", "2024-10-24", 1299.00, "debit"),
        ("L'Artusi Ristorante", "dining", "2024-10-23", 245.50, "debit"),
        ("Amazon.com", "shopping", "2024-10-20", 189.99, "debit"),
        ("Uber Ride", "transport", "2024-10-19", 32.50, "debit"),
        ("Netflix Subscription", "entertainment", "2024-10-18", 15.99, "debit"),
    ],
    "bob": [
        ("Freelance Payment", "income", "2024-10-21", 3500.00, "credit"),
        ("Best Buy Electronics", "technology", "2024-10-22", 899.00, "debit"),
        ("Olive Garden", "dining", "2024-10-20", 78.50, "debit"),
        ("Walmart", "shopping", "2024-10-19", 156.20, "debit"),
        ("Shell Gas Station", "transport", "2024-10-18", 45.00, "debit"),
        ("Spotify Premium", "entertainment", "2024-10-17", 9.99, "debit"),
    ],
    "charlie": [
        ("Consulting Fee", "income", "2024-10-21", 5200.00, "credit"),
        ("Micro Center", "technology", "2024-10-23", 450.00, "debit"),
        ("Chipotle", "dining", "2024-10-22", 22.80, "debit"),
        ("Target", "shopping", "2024-10-20", 95.40, "debit"),
        ("Lyft Ride", "transport", "2024-10-19", 28.75, "debit"),
        ("HBO Max", "entertainment", "2024-10-18", 14.99, "debit"),
    ],
    "diana": [
        ("Bi-Weekly Paycheck", "income", "2024-10-21", 8900.00, "credit"),
        ("Verizon Bill", "utilities", "2024-10-24", 145.00, "debit"),
        ("Sushi Bar", "dining", "2024-10-23", 67.30, "debit"),
        ("Nordstrom", "shopping", "2024-10-22", 320.00, "debit"),
        ("Amtrak Ticket", "transport", "2024-10-20", 89.00, "debit"),
        ("Planet Fitness", "health", "2024-10-19", 49.99, "debit"),
    ],
    "edward": [
        ("Year-End Bonus", "income", "2024-10-21", 2000.00, "credit"),
        ("Dell Laptop", "technology", "2024-10-25", 1450.00, "debit"),
        ("McDonald's", "dining", "2024-10-23", 12.50, "debit"),
        ("Costco Wholesale", "shopping", "2024-10-22", 230.00, "debit"),
        ("BP Gas Station", "transport", "2024-10-20", 38.00, "debit"),
        ("Hulu Subscription", "entertainment", "2024-10-19", 7.99, "debit"),
    ],
    "frank": [
        ("Contract Payment", "income", "2024-10-21", 4200.00, "credit"),
        ("Geek Squad Services", "technology", "2024-10-24", 199.00, "debit"),
        ("Ruth's Chris Steakhouse", "dining", "2024-10-22", 185.00, "debit"),
        ("Macy's", "shopping", "2024-10-21", 275.00, "debit"),
        ("Parking Garage", "transport", "2024-10-20", 15.00, "debit"),
        ("Apple Music", "entertainment", "2024-10-19", 10.99, "debit"),
    ],
    "grace": [
        ("Monthly Salary", "income", "2024-10-21", 6750.00, "credit"),
        ("Adobe Creative Cloud", "technology", "2024-10-24", 52.99, "debit"),
        ("Panera Bread", "dining", "2024-10-23", 18.50, "debit"),
        ("IKEA", "shopping", "2024-10-22", 420.00, "debit"),
        ("MetroCard Refill", "transport", "2024-10-20", 127.00, "debit"),
        ("Disney+", "entertainment", "2024-10-19", 13.99, "debit"),
    ],
}


def setup_database():
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS transactions")
    cur.execute("DROP TABLE IF EXISTS users")

    cur.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            balance REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('credit', 'debit')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cur.executemany(
        "INSERT INTO users (username, password, name, balance) VALUES (?, ?, ?, ?)",
        SEED_USERS,
    )

    cur.execute("SELECT id, username FROM users")
    user_map = {row[1]: row[0] for row in cur.fetchall()}

    txn_data = []
    for username, txns in TRANSACTIONS_BY_USER.items():
        uid = user_map[username]
        for desc, cat, date, amt, typ in txns:
            txn_data.append((uid, desc, cat, date, amt, typ))

    cur.executemany(
        "INSERT INTO transactions (user_id, description, category, date, amount, type) VALUES (?, ?, ?, ?, ?, ?)",
        txn_data,
    )

    conn.commit()
    conn.close()
    print(f"Database created at: {DB_PATH}")
    print(f"Inserted {len(SEED_USERS)} users and {len(txn_data)} transactions.")


if __name__ == "__main__":
    setup_database()
