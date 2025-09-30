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
