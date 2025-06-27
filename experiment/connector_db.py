import sqlite3
import configparser


parser = configparser.ConfigParser()
parser.read('demonMonitoring.ini')


def get_connection():
    return sqlite3.connect('demonDB.db', check_same_thread=False)




def insert_into_round_of_node(run_id, ip, port, this_round, nd, fd, rm, ic, bytes_of_data, connection):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM round_of_node WHERE run_id = ? AND ip = ? AND port = ? AND round = ?",
                       (run_id, ip, port, this_round))
        cursor.execute("INSERT INTO round_of_node ("
                       "run_id,"
                       "ip,"
                       "port,"
                       "round,"
                       "nd,"
                       "fd,"
                       "rm,"
                       "ic,"
                       "bytes_of_data) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (run_id,
                        ip,
                        port,
                        this_round,
                        nd,
                        fd,
                        rm,
                        ic,
                        bytes_of_data))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print("Error db: {}".format(e))
        return False


def insert_into_round_of_node_max_round(run_id, ip, port, this_round, nd, fd, rm, ic, bytes_of_data, connection):
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM round_of_node_max_round WHERE run_id = ? AND ip = ? AND port = ? AND round = ?",
                       (run_id, ip, port, this_round))
        cursor.execute("INSERT INTO round_of_node_max_round ("
                       "run_id,"
                       "ip,"
                       "port,"
                       "round,"
                       "nd,"
                       "fd,"
                       "rm,"
                       "ic,"
                       "bytes_of_data) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (run_id,
                        ip,
                        port,
                        this_round,
                        nd,
                        fd,
                        rm,
                        ic,
                        bytes_of_data))
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print("Error db: {}".format(e))
        return False

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

    def insert_into_experiment(self, timestamp):
        try:
            self.connection = sqlite3.connect('demonDB.db', check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.cursor.execute("INSERT INTO experiment (timestamp) VALUES (?)", (timestamp,))
            to_return = self.cursor.lastrowid
            self.connection.commit()
            self.connection.close()
            return to_return
        except Exception as e:
            print("Error DB Insert: {}".format(e))
            return -1

    def insert_into_run(self, experiment_id, run_count, node_count, gossip_rate, target_count):
        try:
            self.connection = sqlite3.connect('demonDB.db', check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.cursor.execute("INSERT INTO run ("
                                "experiment_id,"
                                "run_count, "
                                "node_count, "
                                "gossip_rate, "
                                "target_count) "
                                "VALUES (?, ?, ?, ?, ?)",
                                (experiment_id,
                                 run_count,
                                 node_count,
                                 gossip_rate,
                                 target_count
                                 ))
            to_return = self.cursor.lastrowid
            self.connection.commit()
            self.connection.close()
            return to_return
        except Exception as e:
            print("Error DB Insert run: {}".format(e))
            return -1

    def save_query_in_database(self, run_id, node_count, i, failure_percent, time_to_query, total_messages_for_query,
                               success):
        try:
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO query ("
                "run_id,"
                "node_count, "
                "query_num,"
                "failure_percent, "
                "time_to_query, "
                "total_messages_for_query, "
                "success)"
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id,
                 node_count,
                 i,
                 failure_percent,
                 time_to_query,
                 total_messages_for_query,
                 success
                 ))
            connection.commit()
            connection.close()
            return True
        except Exception as e:
            print("Exception in save_query_in_database: {}".format(e))

    def insert_into_converged_run(self, run_id, convergence_round, convergence_message_count, convergence_time):
        try:
            self.connection = sqlite3.connect('demonDB.db', check_same_thread=False)
            self.cursor = self.connection.cursor()
            self.cursor.execute("UPDATE run SET "
                                "convergence_round = ?, "
                                "convergence_message_count = ?, "
                                "convergence_time = ? "
                                "WHERE id = ?",
                                (convergence_round,
                                 convergence_message_count,
                                 convergence_time,
                                 run_id
                                 ))
            to_return = self.cursor.lastrowid
            self.connection.commit()
            self.connection.close()
            return to_return
        except Exception as e:
            print("Error DB Update run: {}".format(e))
            return -1
