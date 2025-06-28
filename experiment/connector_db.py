import sqlite3
import configparser


parser = configparser.ConfigParser()
parser.read('demonMonitoring.ini')


def get_connection():
    return sqlite3.connect('demonDB.db', check_same_thread=False)

class NodeDB:
    def __init__(self):
        self.connection = sqlite3.connect('NodeStorage.db', check_same_thread=False)
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
        return sqlite3.connect('NodeStorage.db', check_same_thread=False)


class DemonDB:
    def __init__(self):
        self.connection = sqlite3.connect('demonDB.db', check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS experiment ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")

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
            "bytes_of_data INTEGER)")
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
            "bytes_of_data INTEGER)")
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS query ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id BIGINT references run(id), "
            "node_count INTEGER, "
            "query_num INTEGER,"
            "failure_percent INTEGER, "
            "time_to_query TEXT, "
            "total_messages_for_query INTEGER, "
            "success TEXT)"
        )
        self.connection.commit()
        self.connection.close()
