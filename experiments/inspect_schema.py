"""
inspect_schema.py — Database Schema Inspector (Debug Utility)

Prints all table CREATE statements from the VOIDemon SQLite database.
Run this after an experiment to verify the schema is as expected.

Usage:
    python experiments/inspect_schema.py
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'voidemon.db')

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
schemas = cursor.fetchall()

print("=== VOIDemon Database Schema ===")
for schema in schemas:
    if schema[0]:
        print(schema[0])
        print()

conn.close()
