"""
generate_data.py
────────────────
Generates synthetic e-commerce data using Faker and seeds both
PostgreSQL and MongoDB databases.

Usage:
    python scripts/generate_data.py --records 50000
    python scripts/generate_data.py --records 10000 --db both
    python scripts/generate_data.py --records 5000 --db sql
"""

import argparse
import random
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras
from bson import ObjectId
from faker import Faker
from pymongo import MongoClient, InsertOne

from config import PG_CONFIG, MONGO_CONFIG

fake = Faker("tr_TR")  # Turkish locale for realistic names/addresses
Faker.seed(42)
random.seed(42)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
CATEGORIES = [
    {"name": "Electronics", "slug": "electronics", "parent": None},
    {"name": "Headphones", "slug": "headphones", "parent": "Electronics"},
    {"name": "Smartphones", "slug": "smartphones", "parent": "Electronics"},
    {"name": "Laptops", "slug": "laptops", "parent": "Electronics"},
    {"name": "Clothing", "slug": "clothing", "parent": None},
    {"name": "Men's Clothing", "slug": "mens-clothing", "parent": "Clothing"},
    {"name": "Women's Clothing", "slug": "womens-clothing", "parent": "Clothing"},
    {"name": "Books", "slug": "books", "parent": None},
    {"name": "Sports", "slug": "sports", "parent": None},
    {"name": "Home & Kitchen", "slug": "home-kitchen", "parent": None},
]

ORDER_STATUSES = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
STATUS_WEIGHTS = [5, 10, 15, 20, 40, 10]  # % probability


def random_past_date(days_back: int = 365) -> datetime:
    delta = timedelta(seconds=random.randint(0, days_back * 86400))
    return datetime.now(timezone.utc) - delta


# ═════════════════════════════════════════════════════════════
# POSTGRESQL SEEDER
# ═════════════════════════════════════════════════════════════
class PostgresSeeder:
    def __init__(self, n_users: int, n_products: int, n_orders: int):
        self.n_users = n_users
        self.n_products = n_products
        self.n_orders = n_orders
        self.conn = psycopg2.connect(**PG_CONFIG)
        self.cur = self.conn.cursor()
        self.user_ids = []
        self.product_ids = []
        self.address_ids = []
        self.category_ids = {}

    def run(self):
        print("[PostgreSQL] Seeding started...")
        self._seed_categories()
        self._seed_users()
        self._seed_products()
        self._seed_orders()
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        print("[PostgreSQL] ✅ Seeding complete.")

    def _seed_categories(self):
        name_to_id = {}
        for cat in CATEGORIES:
            parent_id = name_to_id.get(cat["parent"])
            self.cur.execute(
                """
                INSERT INTO categories (name, slug, parent_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                RETURNING category_id
                """,
                (cat["name"], cat["slug"], parent_id),
            )
            cat_id = self.cur.fetchone()[0]
            name_to_id[cat["name"]] = cat_id
            self.category_ids[cat["name"]] = cat_id
        print(f"  [categories] {len(CATEGORIES)} records inserted.")

    def _seed_users(self):
        batch = []
        for _ in range(self.n_users):
            uid = str(uuid.uuid4())
            self.user_ids.append(uid)
            batch.append((
                uid,
                fake.unique.email(),
                fake.user_name(),
                fake.name(),
                fake.phone_number()[:20],
                random_past_date(730),
            ))
        psycopg2.extras.execute_values(
            self.cur,
            "INSERT INTO users (user_id, email, username, full_name, phone, created_at) VALUES %s",
            batch,
        )

        # Seed addresses
        addr_batch = []
        for uid in self.user_ids:
            n_addr = random.randint(1, 3)
            for i in range(n_addr):
                aid = str(uuid.uuid4())
                self.address_ids.append((uid, aid))
                addr_batch.append((
                    aid, uid,
                    random.choice(["home", "work", "other"]),
                    fake.street_address(),
                    fake.city(),
                    "Turkey",
                    fake.postcode(),
                    i == 0,  # first address is default
                ))
        psycopg2.extras.execute_values(
            self.cur,
            "INSERT INTO addresses (address_id, user_id, label, street, city, country, postal_code, is_default) VALUES %s",
            addr_batch,
        )
        print(f"  [users] {self.n_users} users + {len(addr_batch)} addresses inserted.")

    def _seed_products(self):
        leaf_categories = [
            "Headphones", "Smartphones", "Laptops",
            "Men's Clothing", "Women's Clothing",
            "Books", "Sports", "Home & Kitchen",
        ]
        batch = []
        for _ in range(self.n_products):
            pid = str(uuid.uuid4())
            self.product_ids.append(pid)
            cat_name = random.choice(leaf_categories)
            cat_id = self.category_ids[cat_name]
            price = round(random.uniform(9.99, 2999.99), 2)
            batch.append((
                pid, cat_id,
                fake.catch_phrase()[:150],
                fake.text(max_nb_chars=300),
                f"SKU-{fake.unique.bothify('????-####').upper()}",
                price,
                random.randint(0, 500),
                fake.company()[:100],
            ))
        psycopg2.extras.execute_values(
            self.cur,
            """INSERT INTO products
               (product_id, category_id, name, description, sku, price, stock, brand)
               VALUES %s""",
            batch,
        )
        print(f"  [products] {self.n_products} records inserted.")

    def _seed_orders(self):
        order_batch = []
        item_batch = []
        for _ in range(self.n_orders):
            oid = str(uuid.uuid4())
            uid = random.choice(self.user_ids)
            # find user's address
            user_addrs = [a[1] for a in self.address_ids if a[0] == uid]
            addr_id = random.choice(user_addrs) if user_addrs else None
            status = random.choices(ORDER_STATUSES, STATUS_WEIGHTS)[0]
            created = random_past_date(365)
            n_items = random.randint(1, 5)
            items = random.sample(self.product_ids, min(n_items, len(self.product_ids)))
            total = 0
            for pid in items:
                qty = random.randint(1, 3)
                price = round(random.uniform(9.99, 999.99), 2)
                item_batch.append((oid, pid, qty, price, round(random.uniform(0, 20), 2)))
                total += qty * price
            order_batch.append((
                oid, uid, addr_id, status,
                round(total, 2), 0, round(random.uniform(0, 30), 2),
                random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
                created,
            ))

        psycopg2.extras.execute_values(
            self.cur,
            """INSERT INTO orders
               (order_id, user_id, address_id, status, total_amount, discount_amount, shipping_fee, payment_method, created_at)
               VALUES %s""",
            order_batch,
        )
        psycopg2.extras.execute_values(
            self.cur,
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_pct) VALUES %s",
            item_batch,
        )
        print(f"  [orders] {self.n_orders} orders + {len(item_batch)} items inserted.")


# ═════════════════════════════════════════════════════════════
# MONGODB SEEDER
# ═════════════════════════════════════════════════════════════
class MongoSeeder:
    def __init__(self, n_users: int, n_products: int, n_orders: int):
        self.n_users = n_users
        self.n_products = n_products
        self.n_orders = n_orders
        client = MongoClient(**MONGO_CONFIG)
        self.db = client["ecommerce_nosql"]
        self.user_ids = []
        self.product_ids = []
        self.category_ids = {}

    def run(self):
        print("[MongoDB] Seeding started...")
        self._seed_categories()
        self._seed_users()
        self._seed_products()
        self._seed_orders()
        print("[MongoDB] ✅ Seeding complete.")

    def _seed_categories(self):
        name_to_id = {}
        for cat in CATEGORIES:
            oid = ObjectId()
            name_to_id[cat["name"]] = oid
            self.category_ids[cat["name"]] = oid
        docs = []
        for cat in CATEGORIES:
            docs.append({
                "_id": self.category_ids[cat["name"]],
                "name": cat["name"],
                "slug": cat["slug"],
                "parentId": self.category_ids.get(cat["parent"]),
                "description": fake.sentence()
            })
        self.db.categories.drop()
        self.db.categories.insert_many(docs)
        print(f"  [categories] {len(docs)} records inserted.")

    def _seed_users(self):
        docs = []
        for _ in range(self.n_users):
            uid = ObjectId()
            self.user_ids.append(uid)
            n_addr = random.randint(1, 3)
            addresses = []
            for i in range(n_addr):
                addresses.append({
                    "label": random.choice(["home", "work", "other"]),
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "country": "Turkey",
                    "postalCode": fake.postcode(),
                    "isDefault": i == 0
                })
            docs.append({
                "_id": uid,
                "email": fake.unique.email(),
                "username": fake.user_name(),
                "fullName": fake.name(),
                "phone": fake.phone_number()[:20],
                "isActive": True,
                "createdAt": random_past_date(730),
                "updatedAt": datetime.now(timezone.utc),
                "addresses": addresses
            })
        self.db.users.drop()
        self.db.users.insert_many(docs)
        print(f"  [users] {self.n_users} records inserted.")

    def _seed_products(self):
        leaf_categories = [
            "Headphones", "Smartphones", "Laptops",
            "Men's Clothing", "Women's Clothing",
            "Books", "Sports", "Home & Kitchen",
        ]
        docs = []
        for _ in range(self.n_products):
            pid = ObjectId()
            self.product_ids.append(pid)
            cat_name = random.choice(leaf_categories)
            docs.append({
                "_id": pid,
                "name": fake.catch_phrase()[:150],
                "description": fake.text(max_nb_chars=300),
                "sku": f"SKU-{fake.unique.bothify('????-####').upper()}",
                "price": round(random.uniform(9.99, 2999.99), 2),
                "stock": random.randint(0, 500),
                "brand": fake.company()[:100],
                "categoryId": self.category_ids[cat_name],
                "isActive": True,
                "createdAt": random_past_date(730),
                "updatedAt": datetime.now(timezone.utc),
                "attributes": {
                    "color": random.choice(["Black", "White", "Silver", "Blue", "Red"]),
                    "weight": f"{round(random.uniform(0.1, 5.0), 1)}kg",
                },
                "ratingSummary": {"avgRating": 0.0, "reviewCount": 0}
            })
        self.db.products.drop()
        # Bulk insert in chunks for memory efficiency
        chunk = 1000
        for i in range(0, len(docs), chunk):
            self.db.products.insert_many(docs[i:i+chunk])
        print(f"  [products] {self.n_products} records inserted.")

    def _seed_orders(self):
        docs = []
        for _ in range(self.n_orders):
            uid = random.choice(self.user_ids)
            status = random.choices(ORDER_STATUSES, STATUS_WEIGHTS)[0]
            n_items = random.randint(1, 5)
            items = random.sample(self.product_ids, min(n_items, len(self.product_ids)))
            embedded_items = []
            total = 0
            for pid in items:
                qty = random.randint(1, 3)
                price = round(random.uniform(9.99, 999.99), 2)
                embedded_items.append({
                    "productId": pid,
                    "productName": fake.catch_phrase()[:100],  # snapshot
                    "sku": f"SKU-{fake.bothify('????-####').upper()}",
                    "quantity": qty,
                    "unitPrice": price,
                    "discountPct": round(random.uniform(0, 20), 2)
                })
                total += qty * price
            docs.append({
                "userId": uid,
                "status": status,
                "totalAmount": round(total, 2),
                "discountAmount": 0,
                "shippingFee": round(random.uniform(0, 30), 2),
                "paymentMethod": random.choice(["credit_card", "debit_card", "paypal"]),
                "createdAt": random_past_date(365),
                "updatedAt": datetime.now(timezone.utc),
                "shippingAddress": {
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "country": "Turkey",
                    "postalCode": fake.postcode()
                },
                "items": embedded_items
            })
        self.db.orders.drop()
        chunk = 1000
        for i in range(0, len(docs), chunk):
            self.db.orders.insert_many(docs[i:i+chunk])
        print(f"  [orders] {self.n_orders} records inserted.")


# ═════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and seed benchmark data")
    parser.add_argument("--records", type=int, default=10000, help="Total number of user records")
    parser.add_argument("--db", choices=["sql", "nosql", "both"], default="both")
    args = parser.parse_args()

    n_users = args.records
    n_products = max(1000, n_users // 5)
    n_orders = n_users * 3

    print(f"Generating: {n_users} users | {n_products} products | {n_orders} orders")

    if args.db in ("sql", "both"):
        PostgresSeeder(n_users, n_products, n_orders).run()

    if args.db in ("nosql", "both"):
        MongoSeeder(n_users, n_products, n_orders).run()
