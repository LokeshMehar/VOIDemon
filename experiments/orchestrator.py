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
