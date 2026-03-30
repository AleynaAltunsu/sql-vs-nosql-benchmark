"""
benchmark_runner.py
────────────────────
Runs timed benchmarks across PostgreSQL and MongoDB for 8 operation types.
Outputs results to JSON files and prints a summary table.

Usage:
    python benchmarks/benchmark_runner.py
    python benchmarks/benchmark_runner.py --runs 10
"""

import argparse
import json
import os
import statistics
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras
from bson import ObjectId
from pymongo import MongoClient

import sys
sys.path.insert(0, os.path.dirname(__file__))
from config import (
    PG_CONFIG, MONGO_CONFIG, MONGO_DB_NAME,
    BENCHMARK_WARM_RUNS, BENCHMARK_RESULT_DIR
)

# ─────────────────────────────────────────────
# Timing utility
# ─────────────────────────────────────────────
def timed(fn, runs: int = 5):
    """Run fn `runs` times and return (median_ms, min_ms, max_ms, all_times)."""
    timings = []
    for _ in range(runs):
        t0 = time.perf_counter()
        fn()
        timings.append((time.perf_counter() - t0) * 1000)
    return {
        "median_ms": round(statistics.median(timings), 3),
        "min_ms":    round(min(timings), 3),
        "max_ms":    round(max(timings), 3),
        "runs":      runs,
        "all_ms":    [round(t, 3) for t in timings],
    }


# ═════════════════════════════════════════════════════════════
# POSTGRESQL BENCHMARKS
# ═════════════════════════════════════════════════════════════
class PostgresBenchmark:
    def __init__(self, runs: int):
        self.runs = runs
        self.conn = psycopg2.connect(**PG_CONFIG)
        self.conn.autocommit = True
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self._prepare()

    def _prepare(self):
        """Fetch sample IDs for use in benchmarks."""
        self.cur.execute("SELECT user_id FROM users LIMIT 100")
        self.user_ids = [r["user_id"] for r in self.cur.fetchall()]

        self.cur.execute("SELECT product_id FROM products LIMIT 100")
        self.product_ids = [r["product_id"] for r in self.cur.fetchall()]

        self.cur.execute("SELECT order_id FROM orders LIMIT 100")
        self.order_ids = [r["order_id"] for r in self.cur.fetchall()]

    def run_all(self) -> dict:
        import random
        results = {}

        # 1. INSERT 1000 records
        def bench_insert():
            rows = [(str(uuid.uuid4()), f"bench_{uuid.uuid4().hex[:8]}@test.com",
                     f"user_{uuid.uuid4().hex[:6]}") for _ in range(1000)]
            psycopg2.extras.execute_values(
                self.cur,
                "INSERT INTO users (user_id, email, username) VALUES %s ON CONFLICT DO NOTHING",
                rows
            )
        results["insert_1000"] = timed(bench_insert, self.runs)

        # 2. Point lookup by ID
        def bench_point_lookup():
            uid = random.choice(self.user_ids)
            self.cur.execute("SELECT * FROM users WHERE user_id = %s", (uid,))
            self.cur.fetchone()
        results["point_lookup"] = timed(bench_point_lookup, self.runs)

        # 3. Multi-condition filtered search
        def bench_filtered_search():
            self.cur.execute(
                """SELECT product_id, name, price FROM products
                   WHERE price BETWEEN %s AND %s AND stock > 0 AND is_active = TRUE
                   ORDER BY price LIMIT 20""",
                (50.0, 500.0)
            )
            self.cur.fetchall()
        results["filtered_search"] = timed(bench_filtered_search, self.runs)

        # 4. Aggregation (revenue by category)
        def bench_aggregation():
            self.cur.execute(
                """SELECT c.name, SUM(oi.quantity * oi.unit_price) AS revenue
                   FROM order_items oi
                   JOIN orders o ON o.order_id = oi.order_id
                   JOIN products p ON p.product_id = oi.product_id
                   JOIN categories c ON c.category_id = p.category_id
                   WHERE o.status NOT IN ('cancelled','refunded')
                   GROUP BY c.name ORDER BY revenue DESC"""
            )
            self.cur.fetchall()
        results["aggregation"] = timed(bench_aggregation, self.runs)

        # 5. 3-table JOIN (order + product + user)
        def bench_join():
            oid = random.choice(self.order_ids)
            self.cur.execute(
                """SELECT o.order_id, u.username, u.email, p.name, oi.quantity, oi.unit_price
                   FROM orders o
                   JOIN users u ON u.user_id = o.user_id
                   JOIN order_items oi ON oi.order_id = o.order_id
                   JOIN products p ON p.product_id = oi.product_id
                   WHERE o.order_id = %s""",
                (oid,)
            )
            self.cur.fetchall()
        results["multi_join"] = timed(bench_join, self.runs)

        # 6. Full-text search
        def bench_fts():
            self.cur.execute(
                """SELECT product_id, name FROM products
                   WHERE fts_vector @@ to_tsquery('english', 'wireless & bluetooth')
                   ORDER BY ts_rank(fts_vector, to_tsquery('english', 'wireless & bluetooth')) DESC
                   LIMIT 10"""
            )
            self.cur.fetchall()
        results["fulltext_search"] = timed(bench_fts, self.runs)

        # 7. Conditional update
        def bench_update():
            oid = random.choice(self.order_ids)
            self.cur.execute(
                "UPDATE orders SET status = 'confirmed' WHERE order_id = %s AND status = 'pending'",
                (oid,)
            )
        results["conditional_update"] = timed(bench_update, self.runs)

        # 8. Bulk delete (cancelled orders, limited)
        def bench_delete():
            self.cur.execute(
                """DELETE FROM orders WHERE order_id IN (
                       SELECT order_id FROM orders WHERE status = 'cancelled' LIMIT 10
                   )"""
            )
        results["bulk_delete"] = timed(bench_delete, self.runs)

        self.conn.close()
        return results


# ═════════════════════════════════════════════════════════════
# MONGODB BENCHMARKS
# ═════════════════════════════════════════════════════════════
class MongoBenchmark:
    def __init__(self, runs: int):
        self.runs = runs
        client = MongoClient(**MONGO_CONFIG)
        self.db = client[MONGO_DB_NAME]
        self._prepare()

    def _prepare(self):
        self.user_ids = [
            d["_id"] for d in self.db.users.find({}, {"_id": 1}).limit(100)
        ]
        self.product_ids = [
            d["_id"] for d in self.db.products.find({}, {"_id": 1}).limit(100)
        ]
        self.order_ids = [
            d["_id"] for d in self.db.orders.find({}, {"_id": 1}).limit(100)
        ]

    def run_all(self) -> dict:
        import random
        results = {}

        # 1. INSERT 1000 records
        def bench_insert():
            docs = [
                {"email": f"bench_{ObjectId()}@test.com",
                 "username": f"user_{ObjectId()}",
                 "isActive": True,
                 "createdAt": datetime.now(timezone.utc),
                 "updatedAt": datetime.now(timezone.utc),
                 "addresses": []}
                for _ in range(1000)
            ]
            self.db.users.insert_many(docs, ordered=False)
        results["insert_1000"] = timed(bench_insert, self.runs)

        # 2. Point lookup by ID
        def bench_point_lookup():
            uid = random.choice(self.user_ids)
            self.db.users.find_one({"_id": uid})
        results["point_lookup"] = timed(bench_point_lookup, self.runs)

        # 3. Multi-condition filtered search
        def bench_filtered_search():
            list(self.db.products.find(
                {"price": {"$gte": 50, "$lte": 500}, "stock": {"$gt": 0}, "isActive": True},
                {"name": 1, "price": 1}
            ).sort("price", 1).limit(20))
        results["filtered_search"] = timed(bench_filtered_search, self.runs)

        # 4. Aggregation pipeline (revenue by category)
        def bench_aggregation():
            list(self.db.orders.aggregate([
                {"$match": {"status": {"$nin": ["cancelled", "refunded"]}}},
                {"$unwind": "$items"},
                {"$lookup": {"from": "products", "localField": "items.productId",
                             "foreignField": "_id", "as": "product"}},
                {"$unwind": "$product"},
                {"$lookup": {"from": "categories", "localField": "product.categoryId",
                             "foreignField": "_id", "as": "category"}},
                {"$unwind": "$category"},
                {"$group": {"_id": "$category.name",
                            "revenue": {"$sum": {"$multiply": ["$items.quantity", "$items.unitPrice"]}}}},
                {"$sort": {"revenue": -1}}
            ]))
        results["aggregation"] = timed(bench_aggregation, self.runs)

        # 5. $lookup join equivalent
        def bench_lookup():
            oid = random.choice(self.order_ids)
            list(self.db.orders.aggregate([
                {"$match": {"_id": oid}},
                {"$lookup": {"from": "users", "localField": "userId",
                             "foreignField": "_id", "as": "user"}},
            ]))
        results["multi_join"] = timed(bench_lookup, self.runs)

        # 6. Full-text search
        def bench_fts():
            list(self.db.products.find(
                {"$text": {"$search": "wireless bluetooth"}},
                {"score": {"$meta": "textScore"}, "name": 1}
            ).sort([("score", {"$meta": "textScore"})]).limit(10))
        results["fulltext_search"] = timed(bench_fts, self.runs)

        # 7. Conditional update
        def bench_update():
            oid = random.choice(self.order_ids)
            self.db.orders.update_one(
                {"_id": oid, "status": "pending"},
                {"$set": {"status": "confirmed", "updatedAt": datetime.now(timezone.utc)}}
            )
        results["conditional_update"] = timed(bench_update, self.runs)

        # 8. Bulk delete
        def bench_delete():
            ids = [
                d["_id"] for d in self.db.orders.find(
                    {"status": "cancelled"}, {"_id": 1}
                ).limit(10)
            ]
            if ids:
                self.db.orders.delete_many({"_id": {"$in": ids}})
        results["bulk_delete"] = timed(bench_delete, self.runs)

        return results


# ═════════════════════════════════════════════════════════════
# REPORT
# ═════════════════════════════════════════════════════════════
OPERATION_LABELS = {
    "insert_1000":        "Insert 1000 records",
    "point_lookup":       "Point lookup by ID",
    "filtered_search":    "Multi-condition search",
    "aggregation":        "Aggregation (revenue)",
    "multi_join":         "Multi-table JOIN / $lookup",
    "fulltext_search":    "Full-text search",
    "conditional_update": "Conditional update",
    "bulk_delete":        "Bulk delete (10 rows)",
}

def print_table(pg_results: dict, mg_results: dict):
    header = f"{'Operation':<30} {'PostgreSQL (ms)':>16} {'MongoDB (ms)':>14} {'Winner':>8}"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))
    for key, label in OPERATION_LABELS.items():
        pg = pg_results.get(key, {}).get("median_ms", "N/A")
        mg = mg_results.get(key, {}).get("median_ms", "N/A")
        if isinstance(pg, float) and isinstance(mg, float):
            winner = "🐘 PG" if pg < mg else "🍃 Mongo"
        else:
            winner = "—"
        print(f"{label:<30} {pg:>16} {mg:>14} {winner:>8}")
    print("=" * len(header))


def save_results(pg_results, mg_results, runs):
    Path(BENCHMARK_RESULT_DIR).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = {
        "timestamp": ts,
        "runs_per_operation": runs,
        "postgresql": pg_results,
        "mongodb": mg_results,
    }
    path = f"{BENCHMARK_RESULT_DIR}/benchmark_{ts}.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to {path}")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=BENCHMARK_WARM_RUNS,
                        help="Number of timed runs per operation (default: 5)")
    args = parser.parse_args()

    print(f"\n🚀 Starting benchmarks ({args.runs} runs per operation)...\n")

    print("📊 Running PostgreSQL benchmarks...")
    pg_results = PostgresBenchmark(args.runs).run_all()

    print("📊 Running MongoDB benchmarks...")
    mg_results = MongoBenchmark(args.runs).run_all()

    print_table(pg_results, mg_results)
    save_results(pg_results, mg_results, args.runs)
