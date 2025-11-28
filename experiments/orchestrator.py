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
        self.monitoring_address_ip = monitoring_address_ip
        self.voidemon_db = db.VoidemonDB()
        self.query_queue = queue.Queue()
        self.query_thread = None
        self.is_send_data_back = is_send_data_back
        self.push_mode = push_mode
        self.node_db = db.NodeDB()

    def set_db_id(self, param):
        self.db_id = param


MAX_SPAWN_RETRIES = 5


def spawn_node(index, node_list, client, custom_network_name, retries=0):
    """Spawn a single Docker container for a gossip node, with retry logic."""
    if retries >= MAX_SPAWN_RETRIES:
        print("Failed to spawn node {} after {} retries, giving up".format(index, MAX_SPAWN_RETRIES))
        return
    try:
        new_node = docker_client.containers.run(
            "voidemon-node", auto_remove=True, detach=True,
            network_mode=custom_network_name,
            ports={'5000': node_list[index]["port"]}
        )
    except Exception as e:
        print("Node not spawned: {}".format(e))
        print("trace: {}".format(traceback.format_exc()))
        node_list[index]["port"] = get_free_port()
        spawn_node(index, node_list, client, custom_network_name, retries + 1)
    else:
        node_details = client.containers.get(new_node.id)
        node_list[index] = {
            "id": node_details.id,
            "ip": node_details.attrs['NetworkSettings']['Networks']['test']['IPAddress'],
            "port": node_details.attrs['NetworkSettings']['Ports']['5000/tcp'][0]['HostPort']
        }


def spawn_multiple_nodes(run):
    """Spawn all node containers for this run in parallel."""
    network_name = "test"
    from_index = 0
    if run.node_list is None:
        run.node_list = [None] * run.node_count
    elif len(run.node_list) == run.node_count:
        return  # Nodes already spawned
    else:
        from_index = len(run.node_list)
        run.node_list = run.node_list + [None] * (run.node_count - len(run.node_list))
    client = docker.DockerClient()
    for i in range(from_index, run.node_count):
        run.node_list[i] = {}
        run.node_list[i]["port"] = get_free_port()
    Parallel(n_jobs=-1, prefer="threads")(
        delayed(spawn_node)(i, run.node_list, client, network_name) for i in range(from_index, run.node_count)
    )


def nodes_are_ready(run):
    for i in range(0, run.node_count):
        if docker_client.containers.get(run.node_list[i]['id']).status != "running":
            return False
        run.node_list[i]["is_alive"] = True
    return True


def restart_node(docker_id):
    try:
        docker_client.containers.get(docker_id).restart()
    except Exception as e:
        print("Error restarting container: {}".format(e))


def reset_node(ip, port, docker_id):
    try:
        time.sleep(random.uniform(0.01, 0.05))
        session.get("http://{}:{}/reset_node".format(ip, port), timeout=30)
    except Exception as e:
        print("Error resetting node: {}".format(e))
        restart_node(docker_id)


@orchestrator.route('/delete_nodes', methods=['GET'])
def delete_all_nodes():
    """Force-remove all running voidemon-node containers."""
    to_remove = docker_client.containers.list(filters={"ancestor": "voidemon-node"})
    for node in to_remove:
        node.remove(force=True)
    return "OK"


def restart_all_nodes(run):
    """Restart all node containers in parallel."""
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=run.node_count) as executor:
        for i in range(0, run.node_count):
            executor.submit(restart_node, run.node_list[i]["id"])
    print("Restart time: {}".format(time.time() - start), flush=True)


def start_node(index, run, database_address, monitoring_address, ip, retries=0):
    """Send the /start_node POST to initialise a node container's gossip loop."""
    if retries > 5:
        print(f"Giving up starting node {index} after 5 retries.")
        return
    to_send = {
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import concurrent.futures
import configparser
import json
import random
import sqlite3
import time
import docker
import socket
import requests
import traceback
import queue
import threading
from flask import Flask, request
from joblib import Parallel, delayed
import database as db
from sqlite3 import Connection
        "node_list": run.node_list,
        "target_count": run.target_count,
        "gossip_rate": run.gossip_rate,
        "database_address": database_address,
        "monitoring_address": monitoring_address,
        "node_ip": run.node_list[index]["ip"],
        "is_send_data_back": experiment.is_send_data_back,
        "push_mode": experiment.push_mode,
        "client_port": parser.get('VOIDemonParam', 'client_port')
    }
    try:
        time.sleep(0.01)
        session.post("http://{}:{}/start_node".format(ip, run.node_list[index]["port"]), json=to_send)
    except Exception as e:
        print(f"Node {index} not started: {e}. Retrying...")
        time.sleep(0.5)
        start_node(index, run, database_address, monitoring_address, ip, retries + 1)


def start_run(run, monitoring_address):
    database_address = parser.get('database', 'db_file')
    ip = parser.get('system_setting', 'docker_ip')
    run.start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=run.node_count) as executor:
        for i in range(0, run.node_count):
            executor.submit(start_node, i, run, database_address, monitoring_address, ip)


def reset_run_sync(run):
    ip = parser.get('system_setting', 'docker_ip')
    print("Resetting nodes", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=run.node_count) as executor:
        for i in range(0, run.node_count):
            executor.submit(reset_node, ip, run.node_list[i]["port"], run.node_list[i]["id"])


def prepare_run(run):
    spawn_multiple_nodes(run)
    while not nodes_are_ready(run):
        time.sleep(1)
    save_run_to_database(run)
    print("Run {} started".format(run.db_id), flush=True)

    # Notify the dashboard of the new run and its initial node list
    def _notify_run_start():
        try:
            nodes = [
                {"ip": node['ip'], "port": node['port']}
                for node in run.node_list
                if node and 'ip' in node and 'port' in node
            ]
            payload = {
                "node_count": run.node_count,
                "active_target": run.node_count,
                "nodes": nodes,
                "timestamp": time.time()
            }
            requests.post("http://localhost:5000/api/live-run-start", json=payload, timeout=2)
        except Exception:
            pass

    threading.Thread(target=_notify_run_start, daemon=True).start()
    time.sleep(10)


def check_if_all_nodes_are_reset(run):
    return all(not node["is_alive"] for node in run.node_list)


def stop_node_percentage(run, percent):
    print("Stopping {}% of nodes".format(percent * 100))
    if percent == 0:
        return
    nodes_to_stop_count = int(len(run.node_list) * percent)
    indices = list(range(len(run.node_list)))
    random_indices_to_stop = random.sample(indices, nodes_to_stop_count)
    for i in random_indices_to_stop:
        try:
            container_to_stop = docker_client.containers.get(run.node_list[i]["id"])
            container_to_stop.stop()
            run.node_list[i]["is_alive"] = False
            run.stopped_nodes[i] = run.node_list[i]
        except Exception as e:
            print("Error stopping container: {}".format(e))
    print("{}% of nodes (n={}) are stopped".format(percent * 100, nodes_to_stop_count))


def run_converged(run):
    if run.is_converged:
        return
    run.convergence_message_count = run.message_count
    if run.start_time is not None:
        run.convergence_time = time.time() - run.start_time
    else:
        run.convergence_time = 0.0
    print("Convergence time: {}".format(run.convergence_time))
    print("Convergence message count: {}".format(run.convergence_message_count))
    run.is_converged = True


def check_convergence(run, data_stored_in_node):
    """
    Declare convergence when every alive peer in the gossip snapshot holds
    a valid counter entry.

    Key insight for chaos testing: when a node is killed, the survivors stop
    hearing from it and eventually delete it from their node_list via the
    3-strike failure detector. We honour run.manually_killed_count so the
    target is immediately lowered when the dashboard kills a node — before the
    3-strike eviction propagates through the cluster.
    """
    if run.is_converged:
        return True

    alive_peers = {
        peer for peer, d in data_stored_in_node.items()
        if d.get("hbState", {}).get("nodeAlive", True)
    }

    expected_count = run.node_count - run.manually_killed_count
    if expected_count <= 0:
        return False

    if len(alive_peers) < expected_count:
        return False

    for peer in alive_peers:
        peer_data = data_stored_in_node.get(peer, {})
        if "counter" not in peer_data:
            return False

    run_converged(run)
    return True


def save_query_in_database(run, i, failure_percent, target_key, time_to_query, total_messages_for_query, success):
    experiment.voidemon_db.save_query_in_database(
        run.db_id, run.node_count, i, failure_percent, time_to_query, total_messages_for_query, success
    )


def run_queries(run, query_count, failure_percent):
    docker_ip = parser.get('system_setting', 'docker_ip')
    quorum_size = 3
    for i in range(0, query_count):
        alive_nodes = [item for item in run.node_list if item.get("is_alive", False)]
        if not alive_nodes:
            print("No alive nodes available for querying")
            continue
        target_node = random.choice(alive_nodes)
        try:
            start_time = time.time()
            total_messages_for_query, query_result = query_client.query(
                alive_nodes, quorum_size, target_node["ip"], target_node["port"], docker_ip
            )
            time_to_query = time.time() - start_time
            success = True
        except Exception as e:
            print(f"Query failed: {e}")
            time_to_query = time.time() - start_time
            total_messages_for_query = 0
            success = False
        save_query_in_database(run, i, failure_percent, target_node["ip"] + ":" + target_node["port"],
                               time_to_query, total_messages_for_query, success)


def update_during_run(run):
    while not run.is_converged:
        time.sleep(0.1)
    print(parser.get('VOIDemonParam', 'continue_after_convergence'))
    if parser.get('VOIDemonParam', 'continue_after_convergence') == "1":
        print("Convergence reached, continuing run")
        while not run.max_round_is_reached:
            time.sleep(0.1)
        print("Max round reached: stopping now")
    print("Starting query phase")
    if parser.get('system_setting', 'query_logic') == "1":
        failure_ratio = float(parser.get('system_setting', 'failure_rate'))
        stop_node_percentage(run, failure_ratio)
        time.sleep(20)
        run_queries(run, query_count=100, failure_percent=failure_ratio)


# ── In-memory push-data store (NodeStorage) ──────────────────────────────────
connection_pool = sqlite3.connect("node_storage.db", check_same_thread=False, isolation_level=None)
with connection_pool:
    connection_pool.execute(
        "CREATE TABLE IF NOT EXISTS unique_entries "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT)"
    )
    connection_pool.execute(
        "CREATE TABLE IF NOT EXISTS data_entries "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, node TEXT, round INTEGER, key TEXT, unique_entry_id INTEGER)"
    )

database_lock = threading.Lock()


