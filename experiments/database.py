            "(run_id, ip, port, round, nd, fd, rm, ic, bytes_of_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, ip, port, this_round, nd, fd, rm, ic, bytes_of_data)
        )
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print("Error DB insert round_of_node_max_round: {}".format(e))
        return False


class NodeDB:
    """Manages the node state snapshot store (unique_entries + data_entries tables)."""

    def _connect(self):
        conn = sqlite3.connect(
            os.path.join(os.path.dirname(__file__), DB_FILE),
            check_same_thread=False
        )
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def __init__(self):
        self.connection = self._connect()
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unique_entries (
                id INTEGER PRIMARY KEY,
                key TEXT,
                value TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_entries (
                id INTEGER PRIMARY KEY,
                node TEXT,
                round INTEGER,
                key TEXT,
                unique_entry_id INTEGER,
                FOREIGN KEY (unique_entry_id) REFERENCES unique_entries(id)
            )
        ''')
        self.connection.commit()
        self.connection.close()

    def get_connection(self):
        return sqlite3.connect('node_storage.db', check_same_thread=False)


class VoidemonDB:
    """
    Primary experiment database for VOIDemon.

    Stores experiment metadata, per-run convergence results, per-round
    gossip flow statistics, VoI bandwidth savings, and quorum query results.
    """

    def __init__(self):
        self.connection = get_connection()
        self.cursor = self.connection.cursor()

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS experiment ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
"""
database.py — VOIDemon SQLite Database Layer

Provides two database classes:
  - VoidemonDB: Stores experiment run data, per-round flow metrics, VoI
    metric transmission statistics, and query results. Uses WAL mode for
    high-throughput concurrent writes from the gossip cluster.
  - NodeDB: Manages the node state snapshot store (unique_entries + data_entries).

All schema creation happens in __init__ so the database is self-bootstrapping.
"""

import os
import sqlite3
import configparser


        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS run ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "experiment_id INTEGER references experiment(id), "
            "run_count INTEGER, "
            "node_count INTEGER, "
            "gossip_rate INTEGER, "
            "target_count INTEGER, "
            "convergence_round TEXT, "
            "convergence_message_count TEXT, "
            "convergence_time TEXT)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS round_of_node ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "ip TEXT, "
            "port TEXT, "
            "round INTEGER, "
            "nd INTEGER, "
            "fd INTEGER, "
            "rm INTEGER, "
            "ic INTEGER, "
            "bytes_of_data INTEGER)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS round_of_node_max_round ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "ip TEXT, "
            "port TEXT, "
            "round INTEGER, "
            "nd INTEGER, "
            "fd INTEGER, "
            "rm INTEGER, "
            "ic INTEGER, "
            "bytes_of_data INTEGER)"
        )
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS query ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "node_count INTEGER, "
            "query_num INTEGER, "
            "failure_percent INTEGER, "
            "time_to_query TEXT, "
            "total_messages_for_query INTEGER, "
            "success TEXT)"
        )
        # VoI bandwidth savings tracking
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS round_metrics_stats ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "node_ip TEXT, "
            "node_port TEXT, "
            "round INTEGER, "
            "metrics_sent INTEGER, "
            "metrics_filtered INTEGER, "
            "timestamp REAL)"
        )
        # Per-metric transmission detail
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS metric_transmissions ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "node_ip TEXT, "
            "node_port TEXT, "
            "round INTEGER, "
            "metric_type TEXT, "
            "was_sent INTEGER, "
            "metric_value REAL, "
            "timestamp REAL)"
        )
        self.connection.commit()
        self.connection.close()

    def insert_into_experiment(self, timestamp):
        try:
            self.connection = get_connection()
            self.cursor = self.connection.cursor()
            self.cursor.execute("INSERT INTO experiment (timestamp) VALUES (?)", (timestamp,))
            to_return = self.cursor.lastrowid
            self.connection.commit()
            self.connection.close()
            return to_return
        except Exception as e:
            print("Error DB insert experiment: {}".format(e))
            return -1

    def insert_into_run(self, experiment_id, run_count, node_count, gossip_rate, target_count):
        try:
            self.connection = get_connection()
            self.cursor = self.connection.cursor()
            self.cursor.execute(
                "INSERT INTO run (experiment_id, run_count, node_count, gossip_rate, target_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (experiment_id, run_count, node_count, gossip_rate, target_count)
            )
            to_return = self.cursor.lastrowid
            self.connection.commit()
            self.connection.close()
            return to_return
        except Exception as e:
            print("Error DB insert run: {}".format(e))
            return -1

    def save_query_in_database(self, run_id, node_count, i, failure_percent,
                               time_to_query, total_messages_for_query, success):
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO query "
                "(run_id, node_count, query_num, failure_percent, time_to_query, total_messages_for_query, success) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, node_count, i, failure_percent, time_to_query, total_messages_for_query, success)
            )
            connection.commit()
