"""
reset_db.py
───────────
Drops and recreates all tables/collections, then re-seeds.
USE WITH CAUTION — deletes all data.

Usage:
    python scripts/reset_db.py
    python scripts/reset_db.py --records 10000
"""

import argparse
import subprocess
import sys

import psycopg2
from pymongo import MongoClient

import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "benchmarks"))
from config import PG_CONFIG, MONGO_CONFIG, MONGO_DB_NAME


def reset_postgres():
    print("[PostgreSQL] Dropping and recreating schema...")
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        DROP TABLE IF EXISTS
            reviews, order_items, orders, product_attributes,
            products, addresses, users, categories
        CASCADE;
        DROP TYPE IF EXISTS order_status;
    """)

    with open("sql/schema/create_tables.sql") as f:
        cur.execute(f.read())

    conn.close()
    print("[PostgreSQL] ✅ Schema recreated.")


def reset_mongo():
    print("[MongoDB] Dropping all collections...")
    client = MongoClient(**MONGO_CONFIG)
    db = client[MONGO_DB_NAME]
    for col in ["users", "products", "orders", "reviews", "categories"]:
        db[col].drop()
    client.close()
    print("[MongoDB] ✅ Collections dropped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=10000)
    args = parser.parse_args()

    reset_postgres()
    reset_mongo()

    print("\nRe-seeding databases...")
    subprocess.run([
        sys.executable,
        "scripts/generate_data.py",
        "--records", str(args.records)
    ], check=True)
