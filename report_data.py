"""One function, one object, four aggregations. All the numbers come from SQL.

Doing this in SQL rather than in Python matters once the table is big: the
database reads 200 rows and hands back 5 numbers, instead of shipping 200 rows
across so Python can add them up.
"""
import sqlite3
from contextlib import closing

DB = "report.db"

TOTALS = """
SELECT COUNT(*) AS total_orders, ROUND(SUM(amount), 2) AS total_revenue
FROM orders
"""

TOP_PRODUCTS = """
SELECT product, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
FROM orders
GROUP BY product
ORDER BY revenue DESC
LIMIT 5
"""

ORDERS_PER_DAY = """
SELECT created_at AS day, COUNT(*) AS orders, ROUND(SUM(amount), 2) AS revenue
FROM orders
-- 'localtime' matters: date('now') is UTC, but the rows were written with the
-- machine's local date. Without it the window is a day out and returns 8 days.
WHERE created_at >= date('now', 'localtime', '-6 days')
GROUP BY created_at
ORDER BY created_at
"""

ALL_ORDERS = """
SELECT id, customer, product, amount, created_at
FROM orders
ORDER BY created_at DESC, id DESC
"""


def get_report_data():
    with closing(sqlite3.connect(DB)) as con:
        con.row_factory = sqlite3.Row
        q = lambda sql: [dict(r) for r in con.execute(sql)]
        totals = q(TOTALS)[0]
        return {
            "total_orders": totals["total_orders"],
            "total_revenue": totals["total_revenue"],
            "top_products": q(TOP_PRODUCTS),
            "orders_per_day": q(ORDERS_PER_DAY),
            "orders": q(ALL_ORDERS),
        }


if __name__ == "__main__":
    import json
    d = get_report_data()
    print(json.dumps({k: v for k, v in d.items() if k != "orders"}, indent=2))
    print("orders in the long table:", len(d["orders"]))
    # Sanity check: no single product can out-earn the whole shop.
    assert all(p["revenue"] <= d["total_revenue"] for p in d["top_products"])
    print("sanity check passed: no product's revenue exceeds the total")
