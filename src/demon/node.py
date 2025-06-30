import requests
import logging
import psutil
import time
import hashlib
import json

from singleton import Singleton
logger = logging.getLogger("demon.metrics")

# Define priority levels and update frequencies
PRIORITY_HIGH = 1     # Update every round
PRIORITY_MEDIUM = 5   # Update every 5 rounds
PRIORITY_LOW = 10     # Update every 10 rounds

# Configure priorities for different metrics
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

# Track last values to calculate deltas
last_metric_values = {}
# Track when each metric was last sent
last_metric_sent_round = {}

def mk_digest(to_digest):
    nested_dict_str = json.dumps(to_digest, sort_keys=True)
    hash_object = hashlib.sha256()
    hash_object.update(nested_dict_str.encode('utf-8'))
    digest = hash_object.hexdigest()
    return digest


def should_send_metric(node, metric, value):
    # Initialize tracking dictionaries if needed
    if metric not in last_metric_values:
        last_metric_values[metric] = value
        last_metric_sent_round[metric] = 0
        return True  # Always send first time
        
    # Get priority for this metric
    priority = METRIC_PRIORITIES.get(metric, PRIORITY_HIGH)
    
    # Calculate rounds since last sent
    rounds_since_sent = node.cycle - last_metric_sent_round[metric]
    
    # Calculate delta (percent change) for numeric metrics
    if isinstance(value, (int, float)) and isinstance(last_metric_values[metric], (int, float)) and last_metric_values[metric] != 0:
        if metric == "network" or metric == "storage":
            # For network and storage, calculate absolute change
            delta_percent = abs(value - last_metric_values[metric]) / max(value, last_metric_values[metric]) * 100
        else:
            # For CPU and memory, calculate percentage point change
            delta_percent = abs(value - last_metric_values[metric])
    else:
        delta_percent = float('inf')  # Always send non-numeric or zero-based values
        
    # Determine if we should send this metric
    should_send = False
    
    # Always send high priority metrics
    if priority == PRIORITY_HIGH:
        should_send = True
    # Send medium/low priority metrics based on schedule or significant change
    elif rounds_since_sent >= priority:
        should_send = True
    # Send if significant change detected
    elif delta_percent >= METRIC_DELTAS.get(metric, 0):
        should_send = True
        
    # Update last sent round if sending
    if should_send:
        last_metric_sent_round[metric] = node.cycle
    
    # Always update last value for future delta calculations
    last_metric_values[metric] = value
    
    # Log decision with structured information
    logger.debug(f"METRIC_PRIORITY: metric={metric}, value={value:.2f}, priority={priority}, " +
                f"delta={delta_percent:.2f}%, rounds_since_sent={rounds_since_sent}, decision={'SEND' if should_send else 'SKIP'}")
    
    return should_send

def get_new_data():
    node = Node.instance()
    network = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
    
    # Get current metric values
    current_metrics = {
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "network": network,
        "storage": psutil.disk_usage('/').free
    }
    
    # Determine which metrics to send based on priority and delta
    metrics_to_send = {}
    metrics_filtered = {}
    
    for metric, value in current_metrics.items():
        if should_send_metric(node, metric, value):
            metrics_to_send[metric] = value
        else:
            metrics_filtered[metric] = value
    
    # Create the data structure with only selected metrics
    app_state = {}
    for metric in metrics_to_send:
        app_state[metric] = str(metrics_to_send[metric])
    
    # Track metrics statistics for this round
    node.data_flow_per_round.setdefault(node.cycle, {})
    node.data_flow_per_round[node.cycle]['metrics_sent'] = len(metrics_to_send)
    node.data_flow_per_round[node.cycle]['metrics_filtered'] = len(metrics_filtered)
    
    # Store data about which metrics were sent this round
    metric_flags = {metric: (metric in metrics_to_send) for metric in current_metrics}
    
    data = {
        "counter": "{}".format(node.gossip_counter),
        "cycle": "{}".format(node.cycle),
        "digest": "",
        "nodeState": {
            "id": "",
            "ip": "{}".format(node.ip),
            "port": "{}".format(node.port)},
        "hbState": {
            "timestamp": "{}".format(time.time()),
            "failureCount": node.failure_counter,
            "failureList": node.failure_list,
            "nodeAlive": node.is_alive},
        "appSate": app_state,
        "nfState": {},
        "metric_sent_flags": metric_flags
    }
    
    digest = mk_digest(data)
    data["digest"] = digest
    
    return data

@Singleton
class Node:
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
        self.data_flow_per_round = None
        self.session_to_monitoring = requests.Session()
        self.push_mode = None
        self.is_send_data_back = None
        self.metric_last_sent = {}  # Track when each metric was last sent
        
        
    def start_gossip_counter(self):
        while self.is_alive:
            self.gossip_counter += 1
            time.sleep(1)

    def start_gossiping(self, target_count, gossip_rate):
        print("Starting gossiping with target count: {} and gossip rate: {} and length of node list: {}".format(
            target_count, gossip_rate, len(self.node_list)),
            flush=True)
        while self.is_alive:
            if self.push_mode == "1":
                print("Pushing data", flush=True)
                if self.cycle % 10 == 0 and self.cycle != 0:
                    self.push_latest_data_and_delete_after_push()
            self.cycle += 1
            self.transmit(target_count)
            time.sleep(gossip_rate)
            
    def prepare_metadata_and_own_fresh_data(self, time_key):
        metadata = {}
        own_key = self.ip + ':' + self.port
        own_recent_data = self.data[time_key][own_key]
        
        # Apply priority filtering to own data
        filtered_own_data = self.get_filtered_data_by_priority(own_recent_data)
        
        for key in self.data[time_key]:
            if 'counter' in self.data[time_key][key] and key is not own_key:
                metadata[key] = self.data[time_key][key]['counter']
        
        to_send = {'metadata': metadata, own_key: filtered_own_data}
        return to_send

    def transmit(self, target_count):
        new_time_key = self.gossip_counter
        if len(self.data) > 0:
            latest_entry = max(self.data.keys(), key=int)
            latest_data = self.data[latest_entry]
            self.data[new_time_key] = latest_data
        else:
            self.data[new_time_key] = {}
        self.data[new_time_key][self.ip + ':' + self.port] = get_new_data()
        random_nodes = self.get_random_nodes(self.node_list, target_count)

        for n in random_nodes:
            self.send_to_node(n, new_time_key)
            
            
    def update_failure_data(self, new_time_key, n):
        if self.ip + ':' + self.port not in self.data[new_time_key].get(n["ip"] + ':' + n["port"], {}).get("hbState",
                                                                                                           {}).get(
            "failureList", []):
            self.data[new_time_key][n["ip"] + ':' + n["port"]]["hbState"]["failureList"].append(
                self.ip + ':' + self.port)
            f_count = self.data[new_time_key].get(n["ip"] + ':' + n["port"], {}).get("hbState", {}).get("failureCount",
                                                                                                        0) + 1
            if f_count >= 3:
                self.delete_node_from_nodelist(n["ip"] + ':' + n["port"])
                self.data[new_time_key][n["ip"] + ':' + n["port"]]["hbState"]["nodeAlive"] = False
        pass
    
    
        
    def set_params(self, ip, port, cycle, node_list, data, is_alive, gossip_counter, failure_counter,
                   monitoring_address, database_address, is_send_data_back, client_thread, counter_thread, data_flow_per_round, push_mode, client_port):
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

    

    

    

