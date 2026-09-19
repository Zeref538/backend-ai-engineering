"""Fill report.db with ~200 fake orders. Run it twice and you still get 200."""
import random
import sqlite3
from contextlib import closing
from datetime import date, timedelta

DB = "report.db"
PRODUCTS = ["Espresso Machine", "Grinder", "Kettle", "Mug Set", "Bean Sampler", "Filter Papers"]
NAMES = ["Ada", "Ben", "Cleo", "Dara", "Eli", "Fay", "Gus", "Hana", "Ivan", "Jo"]


def seed(n=200, seed_value=7):
    random.seed(seed_value)  # same data every run, so the PDF is comparable
    with closing(sqlite3.connect(DB)) as con, con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS orders ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  customer TEXT NOT NULL,"
            "  product TEXT NOT NULL,"
            "  amount REAL NOT NULL,"
            "  created_at DATE NOT NULL)"
        )
        # Wipe first. Without this, running seed twice leaves 400 orders and
        # every total in the report silently doubles.
        con.execute("DELETE FROM orders")
        today = date.today()
        rows = [
            (random.choice(NAMES), random.choice(PRODUCTS),
             round(random.uniform(5, 200), 2),
             (today - timedelta(days=random.randint(0, 29))).isoformat())
            for _ in range(n)
        ]
        con.executemany(
            "INSERT INTO orders (customer, product, amount, created_at) VALUES (?, ?, ?, ?)", rows)
    return n


if __name__ == "__main__":
    print(f"seeded {seed()} orders")
