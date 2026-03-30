"""
config.py — Database connection configuration
Read from environment variables with sensible defaults.
"""

import os

PG_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "user":     os.getenv("POSTGRES_USER", "benchuser"),
    "password": os.getenv("POSTGRES_PASSWORD", "benchpass"),
    "dbname":   os.getenv("POSTGRES_DB", "ecommerce_sql"),
}

MONGO_CONFIG = {
    "host":     os.getenv("MONGO_HOST", "localhost"),
    "port":     int(os.getenv("MONGO_PORT", 27017)),
    "username": os.getenv("MONGO_USER", "benchuser"),
    "password": os.getenv("MONGO_PASSWORD", "benchpass"),
    "authSource": "admin",
}

MONGO_DB_NAME = "ecommerce_nosql"

# Benchmark settings
BENCHMARK_WARM_RUNS = 5     # runs with warm cache (results averaged)
BENCHMARK_COLD_RUNS = 3     # runs after connection flush
BENCHMARK_RESULT_DIR = "benchmarks/results"
