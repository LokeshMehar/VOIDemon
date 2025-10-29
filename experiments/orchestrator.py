                    unique_entry_id = existing_entry[0]
                else:
                    cursor.execute('INSERT INTO unique_entries (key, value) VALUES (?, ?)', (k, v))
                    unique_entry_id = cursor.lastrowid
                cursor.execute(
                    'INSERT INTO data_entries (node, round, key, unique_entry_id) VALUES (?, ?, ?, ?)',
                    (node_key, client_round, k, unique_entry_id)
                )
        connection_pool.commit()
    return "OK"


@orchestrator.route('/notify_node_killed', methods=['POST'])
def notify_node_killed():
    """
    Chaos Engine notification — called by the dashboard after a soft-kill succeeds.

    Immediately lowers the convergence target so the surviving nodes can declare
    convergence without waiting for the 3-strike timeout to propagate.
    """
    data = request.get_json(silent=True) or {}
    killed_ip = data.get("ip", "")
    with run_lock:
        if experiment and experiment.runs:
            run = experiment.runs[-1]
            run.manually_killed_count += 1
            killed_key = data.get("ip", "") + ":" + str(data.get("port", ""))
            run.killed_node_keys.add(killed_key)
            run.data_entries_per_ip.pop(killed_key, None)
            print("[Chaos] Node {} manually killed. New target: {}/{}".format(
                killed_ip, run.node_count - run.manually_killed_count, run.node_count))
    return "OK"


@orchestrator.route('/receive_ic', methods=['GET'])
def update_ic():
    client_ip = request.args['ip']
    client_port = request.args['port']
    with run_lock:
        experiment.runs[-1].ip_per_ic[client_ip + ":" + client_port] = True
        if len(experiment.runs[-1].ip_per_ic) == experiment.runs[-1].node_count:
            run_converged(experiment.runs[-1])
    return "OK"


@orchestrator.route('/receive_node_data', methods=['POST'])
def update_data_entries_per_ip():
    """Receive per-round metric and flow data from a gossip node."""
    if not experiment:
        print("No experiment running, but a gossip node sent data")
        return "NOK"
    client_ip = request.args['ip']
    client_port = request.args['port']
    round_num = request.args['round']
    inc = request.get_json()
    data_stored_in_node = inc["data"]
    data_flow_per_round = inc["data_flow_per_round"]

    nd = data_flow_per_round.setdefault('nd', 0)
    fd = data_flow_per_round.setdefault('fd', 0)
    rm = data_flow_per_round.setdefault('rm', 0)

    ic = len(data_stored_in_node)
    bytes_of_data = len(json.dumps(data_stored_in_node).encode('utf-8'))

    with run_lock:
        experiment.runs[-1].convergence_round = max(experiment.runs[-1].convergence_round, int(round_num))
        experiment.runs[-1].message_count += 1
        experiment.runs[-1].data_entries_per_ip[client_ip + ":" + client_port] = data_stored_in_node
        check_convergence(experiment.runs[-1], data_stored_in_node)
        if int(round_num) >= 80:
            run_converged(experiment.runs[-1])
from src import query_client

session = requests.Session()

orchestrator = Flask(__name__)
parser = configparser.ConfigParser()
parser.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
try:
    docker_client = docker.client.from_env()
except Exception as e:
    print("Error connecting to Docker: {}".format(e))
    print("trace: {}".format(traceback.format_exc()))
    exit(1)

experiment = None
# Protects concurrent reads/writes to run state from Flask threads
run_lock = threading.Lock()


def execute_queries_from_queue():
    """
    Dedicated SQLite writer thread — drains the query_queue in batches.

    Batching (commit every N items or when the queue drains temporarily) amortises
    the fsync cost of WAL-mode writes without losing data. On failure the
    transaction is rolled back, the cursor is recreated (a stale cursor after
    rollback can produce silent failures in SQLite's Python driver), and the
    failed batch is discarded — individual items are marked task_done so
    join() callers are never left hanging.
    """
    db_path = os.path.join(os.path.dirname(__file__), db.DB_FILE)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    batch_size = 50
    pending_items = []
            experiment.runs[-1].max_round_is_reached = True

    if not experiment.runs[-1].is_converged:
        current_node_count = int(experiment.runs[-1].node_count)
        if int(nd) > current_node_count:
            nd = current_node_count
        if int(fd) > current_node_count:
            fd = current_node_count
        delete_parameters = (experiment.runs[-1].db_id, client_ip, client_port, round_num)
        insert_parameters = (experiment.runs[-1].db_id, client_ip, client_port, round_num, nd, fd, rm, ic, bytes_of_data)
        experiment.query_queue.put(
            ("DELETE FROM round_of_node WHERE run_id = ? AND ip = ? AND port = ? AND round = ?", delete_parameters))
        experiment.query_queue.put((
            "INSERT INTO round_of_node (run_id, ip, port, round, nd, fd, rm, ic, bytes_of_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            insert_parameters
        ))

    # Store VoI metrics statistics
    metrics_sent = data_flow_per_round.get('metrics_sent', 0)
    metrics_filtered = data_flow_per_round.get('metrics_filtered', 0)
    if metrics_sent > 0 or metrics_filtered > 0:
        metrics_params = (experiment.runs[-1].db_id, client_ip, client_port, round_num,
                          metrics_sent, metrics_filtered, time.time())
        experiment.query_queue.put((
            "INSERT INTO round_metrics_stats (run_id, node_ip, node_port, round, metrics_sent, metrics_filtered, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            metrics_params
        ))

    # Store per-metric transmission detail
    if client_ip + ":" + client_port in data_stored_in_node:
        node_data = data_stored_in_node[client_ip + ":" + client_port]
        if 'metric_sent_flags' in node_data:
            timestamp = time.time()
            for metric_type, was_sent in node_data['metric_sent_flags'].items():
                metric_value = None
                if 'appState' in node_data and metric_type in node_data['appState']:
                    try:
                        metric_value = float(node_data['appState'][metric_type])
                    except (ValueError, TypeError):
                        pass
                metric_params = (experiment.runs[-1].db_id, client_ip, client_port, round_num,
                                 metric_type, 1 if was_sent else 0, metric_value, timestamp)
                experiment.query_queue.put((
                    "INSERT INTO metric_transmissions (run_id, node_ip, node_port, round, metric_type, was_sent, metric_value, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    metric_params
                ))

    current_run = experiment.runs[-1]

    # Forward live metrics to the Express dashboard API (non-blocking)
    def _forward_to_dashboard():
        try:
            peer_status = {}
            for peer, p_data in data_stored_in_node.items():
                if "hbState" in p_data:
                    peer_status[peer] = {
                        "isAlive": p_data["hbState"].get("nodeAlive", True),
                        "failCount": p_data["hbState"].get("failureCount", 0)
                    }
                else:
                    peer_status[peer] = {"isAlive": True, "failCount": 0}

            sender_key = client_ip + ":" + client_port
            sender_entry = data_stored_in_node.get(sender_key, {})
            app_state = sender_entry.get("appState", {})

            # Filter out manually killed nodes from the topology view
            filtered_data = {k: v for k, v in data_stored_in_node.items() if k not in current_run.killed_node_keys}
            active_ic = sum(1 for p, d in filtered_data.items() if d.get("hbState", {}).get("nodeAlive", True))

    while True:
        query_data = None
        try:
            query_data = experiment.query_queue.get()
            if query_data is None:
                # Poison pill — flush remaining batch and exit
                if pending_items:
                    conn.commit()
                    for _ in pending_items:
                        experiment.query_queue.task_done()
                    pending_items = []
                experiment.query_queue.task_done()
                break

            sql, parameters = query_data
            cursor.execute(sql, parameters)
            pending_items.append(query_data)
            filtered_nd = len(filtered_data)

            payload = {
                "ip": client_ip,
                "port": client_port,
                "round": round_num,
                "ic": active_ic,
                "nd": filtered_nd,
                "fd": fd,
                "rm": rm,
                "bytes_of_data": bytes_of_data,
                "node_count": current_run.node_count,
                "active_target": current_run.node_count - current_run.manually_killed_count,
                "message_count": current_run.message_count,
                "is_converged": current_run.is_converged,
                "data_stored_in_node": list(filtered_data.keys()),
                "peer_status": peer_status,
                "cpu":     app_state.get("cpu",     "not_updated"),
                "memory":  app_state.get("memory",  "not_updated"),
                "network": app_state.get("network", "not_updated"),
                "storage": app_state.get("storage", "not_updated"),
            }
            requests.post("http://localhost:5000/api/live-metrics", json=payload, timeout=2)
        except Exception:
            pass  # Dashboard may not be running; never block the experiment

    threading.Thread(target=_forward_to_dashboard, daemon=True).start()
    return "OK"


def generate_run(node_count, gossip_rate, target_count, run_count):
    if experiment.runs:
        return Run(node_count, gossip_rate, target_count, run_count, node_list=experiment.runs[-1].node_list)
    return Run(node_count, gossip_rate, target_count, run_count)



            # Commit when the batch is full or the queue is temporarily empty
            if len(pending_items) >= batch_size or experiment.query_queue.empty():
                conn.commit()
                for _ in pending_items:
                    experiment.query_queue.task_done()
                pending_items = []

        except sqlite3.Error as e:
            print("Error in DB batch write: {}".format(e))
            print("trace: {}".format(traceback.format_exc()))
            try:
                conn.rollback()
            except sqlite3.Error as rollback_err:
                print("Error during rollback: {}".format(rollback_err))

            # Recreate cursor — a cursor after rollback can be in an undefined
            # state in SQLite's Python driver.
def ensure_list(val):
    """Parse a config value that might be a JSON-encoded list or a plain value."""
    if isinstance(val, str):
        try:
            loaded = json.loads(val)
            if isinstance(loaded, str):
                return json.loads(loaded)
            return loaded
        except Exception:
            return [val]
    return val if isinstance(val, list) else [val]


def prepare_experiment(server_ip):
    global experiment

    # Reload config to pick up any dashboard-side changes
    parser.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

    def get_range(section, key):
        return ensure_list(parser.get(section, key))

    node_range = get_range('VOIDemonParam', 'node_range')
    gossip_rate_range = get_range('VOIDemonParam', 'gossip_rate_range')
    target_count_range = get_range('VOIDemonParam', 'target_count_range')
    runs = int(parser.get('VOIDemonParam', 'runs'))

    experiment = Experiment(
        node_range, gossip_rate_range, target_count_range, runs, server_ip,
        parser.get('system_setting', 'is_send_data_back'),
        parser.get('VOIDemonParam', 'push_mode')
    )
    experiment.set_db_id(experiment.voidemon_db.insert_into_experiment(time.time()))
    experiment.query_thread = threading.Thread(target=execute_queries_from_queue)
    experiment.query_thread.start()

            try:
                cursor = conn.cursor()
            except sqlite3.Error as cursor_err:
                print("Error recreating cursor: {}".format(cursor_err))

            for _ in pending_items:
                experiment.query_queue.task_done()
            pending_items = []

            if query_data is not None:
                experiment.query_queue.task_done()

            continue


def get_target_count(node_count, target_count_range):
    return [i for i in target_count_range if i <= node_count]


def print_experiment_summary():
    experiment.query_queue.put(None)
    experiment.query_thread.join()
    for run in experiment.runs:
        print("Run {}: converged after {} messages and {:.2f}s".format(
            run.node_count, run.convergence_message_count, run.convergence_time or 0
        ))


@orchestrator.route('/start', methods=['GET', 'POST'])
def start_voidemon():
    """Boot the full distributed gossip experiment."""
    server_ip = socket.gethostbyname(socket.gethostname())
    print("Orchestrator IP: {}".format(server_ip))
    prepare_experiment(server_ip)
    for node_count in experiment.node_count_range:
        new_target_count_range = get_target_count(node_count, experiment.target_count_range)
        for target_count in new_target_count_range:
            for gossip_rate in experiment.gossip_rate_range:
                for run_count in range(0, experiment.run_count):
                    print("Preparing run: {} nodes | gossip_rate={} | target_count={} | run={}".format(
                        node_count, gossip_rate, target_count, run_count))
                    run = generate_run(node_count, gossip_rate, target_count, run_count)
                    experiment.runs.append(run)
                    prepare_run(run)
                    print("Run {} prepared — {} nodes online".format(run.run, len(run.node_list)))
                    start_run(run, experiment.monitoring_address_ip)
                    update_during_run(run)
                    save_converged_run_to_database(run)
                    reset_run_sync(run)
    print_experiment_summary()
    delete_all_nodes()
    return "OK - Experiment finished"


if __name__ == "__main__":
    orchestrator.run(
        host='0.0.0.0',
        port=parser.getint('VOIDemonParam', 'client_port'),
        debug=False,
        threaded=True
    )

def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def make_saveable_dict_from_run(run):
    return {
        "node_count": run.node_count,
        "target_count": run.target_count,
        "gossip_rate": run.gossip_rate,
        "start_time": run.start_time,
        "convergence_time": run.convergence_time,
        "convergence_message_count": run.convergence_message_count,
        "convergence_round": run.convergence_round
    }


def save_run_to_database(run):
    run.db_id = experiment.voidemon_db.insert_into_run(
        experiment.db_id, run.run, run.node_count, run.gossip_rate, run.target_count
    )


def save_converged_run_to_database(run):
    experiment.voidemon_db.insert_into_converged_run(
        run.db_id, run.convergence_round, run.convergence_message_count, run.convergence_time
    )


class Run:
    """Represents a single experiment run (a specific node_count × gossip_rate combination)."""

    def __init__(self, node_count, gossip_rate, target_count, run, node_list=None, db_collection=None):
        self.db_id = -1
        self.data_entries_per_ip = {}
        self.node_list = node_list or []
        self.node_count = int(node_count)
        self.convergence_round = -1
        self.convergence_message_count = -1
        self.message_count = 0
        self.start_time = None
        self.convergence_time = None
        self.is_converged = False
        self.gossip_rate = float(gossip_rate)
        self.target_count = int(target_count)
        self.run = int(run)
        self.db_collection = db_collection
        self.max_round_is_reached = False
        self.ip_per_ic = {}
        self.stopped_nodes = {}
        self.manually_killed_count = 0  # Incremented when the dashboard kills a node via Chaos Engine
        self.killed_node_keys = set()   # Set of "ip:port" strings for manually killed nodes

    def set_db_id(self, param):
        self.db_id = param


class Experiment:
    """Holds configuration and state for the entire experiment (all runs)."""

    def __init__(self, node_count_range, gossip_rate_range, target_count_range, run_count,
                 monitoring_address_ip, is_send_data_back, push_mode):
        self.db_id = -1
        self.node_count_range = node_count_range
        self.gossip_rate_range = gossip_rate_range
        self.target_count_range = target_count_range
        self.run_count = run_count
        self.runs = []
"""
orchestrator.py — VOIDemon Experiment Orchestrator

The central Flask server that manages the full experiment lifecycle:
  - Spawns Docker node containers via the Docker SDK
  - Initialises and boots the gossip cluster
  - Receives live metric reports from every gossip node via /receive_node_data
  - Forwards real-time metrics to the Express dashboard backend via /api/live-metrics
  - Detects convergence and records results in the SQLite database
  - Provides the Chaos Engine kill notification endpoint /notify_node_killed

Run with:
    python experiments/orchestrator.py

The orchestrator listens on port 4000 by default (configurable in config.ini).
"""

import sys
