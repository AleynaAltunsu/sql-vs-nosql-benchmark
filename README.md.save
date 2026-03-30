# 🗄️ SQL vs NoSQL: A Comparative Study on E-Commerce Data

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A hands-on performance and design benchmark between PostgreSQL and MongoDB using a realistic e-commerce dataset.**

[Overview](#overview) • [Architecture](#architecture) • [Setup](#setup) • [Benchmarks](#benchmarks) • [Results](#results) • [Report](#report)

</div>

---

## 📌 Overview

This project systematically compares **relational (SQL)** and **document-oriented (NoSQL)** database paradigms across four key dimensions:

| Dimension | What we measure |
|---|---|
| **Schema Design** | Normalization vs. denormalization trade-offs |
| **Query Performance** | CRUD, aggregation, and join-heavy workloads |
| **Scalability** | Behavior under increasing data volume (10K → 500K records) |
| **Developer Experience** | Ease of modeling, querying, and maintaining each system |

### Why E-Commerce?

E-commerce is a domain where **both paradigms are actively used in production** (e.g., relational DBs for transactions, MongoDB for product catalogs). It provides natural variety: structured order data, semi-structured product metadata, and high-velocity user behavior logs.

---

## 🏗️ Architecture

```
sql-vs-nosql/
│
├── sql/                        # PostgreSQL implementation
│   ├── schema/
│   │   └── create_tables.sql   # Normalized schema (3NF)
│   ├── queries/
│   │   ├── crud.sql            # Basic CRUD operations
│   │   ├── aggregations.sql    # GROUP BY, window functions
│   │   └── joins.sql           # Multi-table join queries
│   └── data/
│       └── seed.sql            # Sample data inserts
│
├── nosql/                      # MongoDB implementation
│   ├── schema/
│   │   └── collections.js      # Collection design & validators
│   ├── queries/
│   │   ├── crud.js             # Basic CRUD operations
│   │   ├── aggregations.js     # Aggregation pipeline
│   │   └── lookups.js          # $lookup (join equivalent)
│   └── data/
│       └── seed.js             # Sample data inserts
│
├── benchmarks/
│   ├── benchmark_runner.py     # Automated benchmark harness
│   ├── config.py               # DB connection config
│   └── results/                # JSON benchmark outputs
│
├── analysis/
│   ├── analysis.py             # Statistical analysis & plots
│   └── plots/                  # Generated charts
│
├── scripts/
│   ├── generate_data.py        # Synthetic data generator (Faker)
│   └── reset_db.py             # Teardown & re-seed script
│
├── docs/
│   └── REPORT.md               # Full comparative analysis report
│
├── docker-compose.yml          # One-command environment setup
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.10+

### 1. Clone & Start Databases

```bash
git clone https://github.com/YOUR_USERNAME/sql-vs-nosql.git
cd sql-vs-nosql

# Start PostgreSQL + MongoDB containers
docker-compose up -d
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Seed the Databases

```bash
# Generate synthetic data + seed both databases
python scripts/generate_data.py --records 50000

# Or reset and re-seed
python scripts/reset_db.py
```

### 4. Run Benchmarks

```bash
python benchmarks/benchmark_runner.py
```

### 5. Generate Analysis & Plots

```bash
python analysis/analysis.py
```

---

## 📊 Benchmarks

Each benchmark is run **5 times** with warm cache, and **5 times** with cold cache. Median latency is reported.

### Test Cases

| # | Operation | SQL | MongoDB |
|---|---|---|---|
| 1 | Insert 1000 records | ✅ | ✅ |
| 2 | Point lookup by ID | ✅ | ✅ |
| 3 | Filtered search (multi-condition) | ✅ | ✅ |
| 4 | Aggregation (revenue by category) | ✅ | ✅ |
| 5 | Multi-table join (order + product + user) | ✅ | ✅ |
| 6 | Full-text search on product name | ✅ | ✅ |
| 7 | Update with condition | ✅ | ✅ |
| 8 | Bulk delete | ✅ | ✅ |

---

## 📈 Results (50K Records)

> Full results in `benchmarks/results/` after running the benchmark script.

| Operation | PostgreSQL (ms) | MongoDB (ms) | Winner |
|---|---|---|---|
| Insert 1K | ~85 | ~42 | 🍃 MongoDB |
| Point Lookup | ~2.1 | ~1.8 | 🍃 MongoDB |
| Filtered Search | ~18 | ~22 | 🐘 PostgreSQL |
| Aggregation | ~45 | ~38 | 🍃 MongoDB |
| 3-Table Join | ~31 | ~110 | 🐘 PostgreSQL |
| Full-text Search | ~12 | ~9 | 🍃 MongoDB |
| Conditional Update | ~14 | ~11 | 🍃 MongoDB |
| Bulk Delete | ~8 | ~6 | 🍃 MongoDB |

*Results are indicative. Run the benchmark yourself for hardware-specific numbers.*

---

## 🔑 Key Findings

1. **MongoDB outperforms PostgreSQL on write-heavy and document-retrieval workloads** due to its denormalized storage model — no join overhead on reads.

2. **PostgreSQL wins on complex, multi-relation queries** where data integrity and ACID compliance matter. JOIN performance scales better with proper indexing.

3. **Schema flexibility** is MongoDB's biggest practical advantage during rapid iteration phases. PostgreSQL's strict schema is a feature, not a bug, in stable production systems.

4. **Both databases support full-text search** — PostgreSQL via `tsvector`/`tsquery`, MongoDB via Atlas Search or `$text`. Performance is comparable at this scale.

5. **For e-commerce**: use PostgreSQL for orders/payments (ACID critical), MongoDB for product catalog and user sessions (schema variability).

---

## 📄 Report

See [`docs/REPORT.md`](docs/REPORT.md) for the full written analysis including:

- Schema design decisions
- Query pattern analysis
- When to choose SQL vs NoSQL
- Hybrid architecture recommendations

---

## 🛠️ Tech Stack

| Tool | Role |
|---|---|
| PostgreSQL 15 | Relational database |
| MongoDB 6.0 | Document database |
| Python 3.10 | Benchmarking & analysis |
| psycopg2 | PostgreSQL Python driver |
| pymongo | MongoDB Python driver |
| Faker | Synthetic data generation |
| matplotlib / seaborn | Result visualization |
| Docker Compose | Environment orchestration |

---

## 📝 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">
Made with 🔍 curiosity and ☕ coffee
</div>
