import time
import psutil
import requests
from singleton import Singleton
import logging
import secrets
from digest import mk_digest

logger = logging.getLogger("voidemon.node")

# Priority levels
PRIORITY_HIGH = 1     # Update every round
PRIORITY_MEDIUM = 5   # Update every 5 rounds
PRIORITY_LOW = 10     # Update every 10 rounds

# Configure priorities for different metrics
        "nfState": {},
        "metric_sent_flags": metric_flags,
    }

    digest = mk_digest(data)
    data["digest"] = digest

    return data


def should_send_metric(node, metric, value):
    """Evaluate VoI priority + delta rule for a single metric.
    
    Uses per-node instance state (node.last_metric_values, node.last_metric_sent_round)
    so that state is properly reset when the node is re-initialised.
    """
    if metric not in node.last_metric_values:
        node.last_metric_values[metric] = value
        node.last_metric_sent_round[metric] = 0
        return True  # Always send the first reading

    priority = METRIC_PRIORITIES.get(metric, PRIORITY_HIGH)
    rounds_since_sent = node.cycle - node.last_metric_sent_round.get(metric, 0)

    # Delta calculation
    prev = node.last_metric_values[metric]
    if isinstance(value, (int, float)) and isinstance(prev, (int, float)):
        if metric in ("network", "storage"):
            denom = max(abs(value), abs(prev))
            delta_percent = 0.0 if denom == 0 else (abs(value - prev) / denom) * 100
        else:
            delta_percent = abs(value - prev)
METRIC_PRIORITIES = {
    "cpu": PRIORITY_HIGH,      # CPU is critical - update every round
    "memory": PRIORITY_MEDIUM, # Memory - update every 5 rounds
    "network": PRIORITY_MEDIUM, # Network - update every 5 rounds
    "storage": PRIORITY_LOW    # Storage changes slowly - update every 10 rounds
}

# Delta thresholds for each metric (minimum change to trigger update)
METRIC_DELTAS = {
    "cpu": 5.0,      # 5% change in CPU
    "memory": 7.0,   # 7% change in memory
    "network": 15.0, # 15% change in network
    "storage": 10.0  # 10% change in storage
}


    else:
        delta_percent = float('inf')

    should_send = False

    if priority == PRIORITY_HIGH:
        should_send = True
    elif rounds_since_sent >= priority:
        should_send = True
    elif delta_percent >= METRIC_DELTAS.get(metric, 0):
        should_send = True

    if should_send:
        node.last_metric_sent_round[metric] = node.cycle

    node.last_metric_values[metric] = value

    logger.debug(
        "METRIC_PRIORITY: metric=%s, value=%.2f, priority=%d, "
        "delta=%.2f%%, rounds_since_sent=%d, decision=%s",
        metric, value, priority, delta_percent,
        rounds_since_sent, 'SEND' if should_send else 'SKIP',
    )

    return should_send


@Singleton
class Node:
    """
    Singleton gossip node — holds all per-node runtime state.

    All metric-tracking fields are instance attributes so they reset cleanly
    when set_params() is called for a new experiment run. This prevents stale
    metric baselines (last_network_bytes, last_metric_sent_round, etc.) from
    leaking across successive VOIDemon experiment runs.
    """

    def __init__(self):
        self.ip = None
        self.port = None
        self.cycle = None
        self.node_list = None
        self.data = None
        self.data_flow_per_round = None
        self.is_alive = None
        self.gossip_counter = None
        self.failure_counter = None
        self.failure_list = []
        self.monitoring_address = None
        self.database_address = None
        self.client_thread = None
        self.counter_thread = None
        self.push_mode = None
        self.is_send_data_back = None
        self.metric_last_sent = {}
        
        # Sessions — instance scope for experiment isolation
        self.session_to_monitoring = requests.Session()
        self.gossip_session = requests.Session()

        # VoI metric tracking — stored as instance attrs so they reset on re-init
        self.last_metric_values = {}
        self.last_metric_sent_round = {}
        self.last_network_bytes = 0
        self.last_network_time = time.time()
        self.node_process = psutil.Process()

        # Quiesce event — set by the gossip loop when it exits, used by /terminate
        self.quiesced_event = None

    def set_params(self, ip, port, cycle, node_list, data, is_alive, gossip_counter,
                   failure_counter, monitoring_address, database_address,
                   is_send_data_back, client_thread, counter_thread,
                   data_flow_per_round, push_mode, client_port):
        """(Re-)initialise node state for a new experiment run.
        
        Resets all per-lifecycle fields including metric tracking state so that
        VoI filtering behaves correctly from round 0 of each new run.
        """
        self.ip = ip
        self.port = port
        self.monitoring_address = monitoring_address
        self.database_address = database_address
        self.cycle = cycle
        self.node_list = node_list
        self.data = data
        self.is_alive = is_alive
        self.gossip_counter = gossip_counter
        self.failure_counter = failure_counter
        self.client_thread = client_thread
        self.counter_thread = counter_thread
        self.data_flow_per_round = data_flow_per_round
        self.is_send_data_back = is_send_data_back
        self.push_mode = push_mode
        self.client_port = client_port

        # Reset metric tracking state — prevents stale baselines leaking across runs
        self.last_metric_values = {}
        self.last_metric_sent_round = {}
        self.last_network_bytes = 0
        self.last_network_time = time.time()
        self.node_process = psutil.Process()

        # Fresh quiesce signal for this run
        import threading
        self.quiesced_event = threading.Event()

    def close_sessions(self):
        """Explicitly close connection pools for this node."""
        try:
            if hasattr(self, 'session_to_monitoring'):
                self.session_to_monitoring.close()
            if hasattr(self, 'gossip_session'):
                self.gossip_session.close()
        except Exception as e:
            logger.error(f"[Session] Error closing node sessions: {e}")

    def get_random_nodes(self, node_list, target_count):
        """Return a random sample of peers, excluding self."""
        filtered_nodes = [node for node in node_list if node['ip'] != self.ip]
        if not filtered_nodes:
            return []
        sample_size = min(target_count, len(filtered_nodes))
        return secrets.SystemRandom().sample(filtered_nodes, sample_size)

    def start_gossip_counter(self):
        """OBSOLETE: Gossip counter is now driven by transmit()."""
        pass

    def start_gossiping(self, target_count, gossip_rate):
        """Main gossip loop — runs until is_alive is set False."""
        print("Starting gossiping with target count: {} and gossip rate: {} and length of node list: {}".format(
            target_count, gossip_rate, len(self.node_list)),
            flush=True)
        try:
            while self.is_alive:
                if self.push_mode == "1":
                    print("Pushing data", flush=True)
                    if self.cycle % 10 == 0 and self.cycle != 0:
                        self.push_latest_data_and_delete_after_push()
                self.cycle += 1
                self.transmit(target_count)
                time.sleep(gossip_rate)

def get_new_data():
    node = Node.instance()
    
    # Calculate Bandwidth (Mbps)
    current_network_bytes = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
    current_time = time.time()
    
    if node.last_network_bytes == 0:
        # First call, initialize values and return 0
        node.last_network_bytes = current_network_bytes
        node.last_network_time = current_time
        bandwidth_mbps = 0.0
    else:
        delta_bytes = current_network_bytes - node.last_network_bytes
        delta_time = current_time - node.last_network_time
        finally:
            # Signal /terminate that the gossip loop has quiesced
            if self.quiesced_event is not None:
                self.quiesced_event.set()

    def transmit(self, target_count):
        """Build and send current state to target_count randomly selected peers."""
        # Increment round ID (gossip counter) for every round to ensure freshness
        self.gossip_counter += 1
        new_time_key = self.gossip_counter

        if self.data:
            latest_entry = max(self.data.keys(), key=int)
            latest_data = self.data[latest_entry].copy()
        else:
            latest_data = {}

        latest_data[f"{self.ip}:{self.port}"] = get_new_data()
        self.data[new_time_key] = latest_data

        random_nodes = self.get_random_nodes(self.node_list, target_count)

        for node in random_nodes:
            self.send_to_node(node, new_time_key)

    def prepare_metadata_and_own_fresh_data(self, time_key):
        """Package this node's own fresh data + peer counters for metadata exchange."""
        own_key = f"{self.ip}:{self.port}"
        time_data = self.data[time_key]
        own_recent_data = time_data[own_key]

        # Use the already-decided own_recent_data from get_new_data directly
        # to avoid double-filtering that undoes VoI/delta logic.
        metadata = {
            key: node_data['counter']
            for key, node_data in time_data.items()
            if key != own_key and 'counter' in node_data
        }

        return {'metadata': metadata, own_key: own_recent_data}

    def prepare_requested_data(self, time_key, requested_keys):
        """Return the subset of stored data requested by a peer."""
        requested_data = {}
        for key in requested_keys:
            requested_data[key] = self.data[time_key][key]
        return requested_data

    def update_own_data(self, updates, new_time_key):
        """Merge incoming peer updates into local data store."""
        for u_key in updates:
            self.data_flow_per_round.setdefault(self.cycle, {})
            if u_key in self.data[new_time_key]:
                self.data_flow_per_round[self.cycle].setdefault('fd', 0)
                self.data_flow_per_round[self.cycle]['fd'] += 1
            else:
                self.data_flow_per_round[self.cycle].setdefault('nd', 0)
                self.data_flow_per_round[self.cycle].setdefault('fd', 0)
                self.data_flow_per_round[self.cycle]['nd'] += 1
                self.data_flow_per_round[self.cycle]['fd'] += 1
            self.data[new_time_key][u_key] = updates[u_key]

    def get_filtered_data_by_priority(self, full_data):
        """Apply VoI priority filtering to outgoing gossip data."""
        
        # Avoid division by zero
        if delta_time > 0:
            bandwidth_mbps = (delta_bytes * 8) / (delta_time * 1024 * 1024)
        else:
            bandwidth_mbps = 0.0
            
        node.last_network_bytes = current_network_bytes
        node.last_network_time = current_time
    
    # Calculate Storage (Usage %)
    storage_percent = psutil.disk_usage('/').percent
    
    # Get current node-specific resource usage
    # (Using non-blocking cpu_percent() to avoid hanging the gossip thread)
    cpu_usage = node.node_process.cpu_percent(interval=None)
        filtered_data = full_data.copy()
        # First cycle — always send everything to bootstrap the network
        if self.cycle <= 1:
            for metric in METRIC_PRIORITIES:
                self.metric_last_sent[metric] = self.cycle
            return filtered_data

        if "appState" in filtered_data:
            app_state = filtered_data["appState"].copy()
            for metric, priority in METRIC_PRIORITIES.items():
                last_sent = self.metric_last_sent.get(metric, 0)
                if (self.cycle - last_sent) < priority:
                    if metric in app_state:
                        app_state[metric] = "not_updated"
                else:
                    self.metric_last_sent[metric] = self.cycle
