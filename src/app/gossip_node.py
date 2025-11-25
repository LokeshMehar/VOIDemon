    node.is_alive = False
    return "TERMINATED"


def compare_and_update_node_data(incoming_data):
    """Merge incoming gossip push data into the local data store."""
    node = Node.instance()
    new_time_key = node.gossip_counter
    latest_entry = max(node.data.keys(), key=int) if len(node.data) > 0 else new_time_key
    new_data = incoming_data
    all_keys = set().union(node.data[latest_entry].keys(), new_data.keys())
    inc_round = int(request.args.get('inc_round'))

    # Track received messages per round
    node.data_flow_per_round.setdefault(node.cycle, {}).setdefault('rm', 0)
    node.data_flow_per_round[node.cycle]['rm'] += 1

    list1 = []
    list2 = []
    for key in all_keys:
        if key in node.data[latest_entry] and key in new_data:

            # Preserve existing metrics that are absent from the partial incoming update
            if 'appState' in new_data[key] and 'appState' in node.data[latest_entry][key]:
                existing_metrics = set(node.data[latest_entry][key]['appState'].keys())
                incoming_metrics = set(new_data[key]['appState'].keys())
                for metric in existing_metrics - incoming_metrics:
                    new_data[key]['appState'][metric] = node.data[latest_entry][key]['appState'][metric]

            if 'metric_sent_flags' in new_data[key]:
                sent_count = sum(1 for v in new_data[key]['metric_sent_flags'].values() if v)
                filtered_count = sum(1 for v in new_data[key]['metric_sent_flags'].values() if not v)
                node.data_flow_per_round[node.cycle].setdefault('metrics_sent', 0)
                node.data_flow_per_round[node.cycle].setdefault('metrics_filtered', 0)
                node.data_flow_per_round[node.cycle]['metrics_sent'] += sent_count
                node.data_flow_per_round[node.cycle]['metrics_filtered'] += filtered_count

            list1 = node.data[latest_entry][key]["hbState"]["failureList"]
            list2 = new_data[key]["hbState"]["failureList"]
            if ('counter' in new_data[key] and 'counter' in node.data[latest_entry][key]
                and float(new_data[key]['counter']) > float(node.data[latest_entry][key]['counter'])) or \
                    ('counter' in new_data[key] and 'counter' not in node.data[latest_entry][key]):
                node.data.setdefault(new_time_key, {})[key] = new_data[key]
                node.data_flow_per_round[node.cycle].setdefault('fd', 0)
                node.data_flow_per_round[node.cycle]['fd'] += 1
            else:
                node.data.setdefault(new_time_key, {})[key] = node.data[latest_entry][key]
        elif key in node.data[latest_entry] and key not in new_data:
            node.data.setdefault(new_time_key, {})[key] = node.data[latest_entry][key]
        else:
            node.data.setdefault(new_time_key, {})[key] = new_data[key]
            node.data_flow_per_round[node.cycle].setdefault('nd', 0)
            node.data_flow_per_round[node.cycle].setdefault('fd', 0)
            node.data_flow_per_round[node.cycle]['nd'] += 1
            node.data_flow_per_round[node.cycle]['fd'] += 1

        # Merge failure lists for peers that appear in both datasets
        if key in node.data[latest_entry] and key in new_data:
            merged_failure_list = list(set(list1).union(set(list2)))
            node.data[new_time_key][key]["hbState"]["failureList"] = merged_failure_list

    if new_time_key not in node.data:
        data_to_send_to_monitor = node.data[latest_entry]
    else:
        data_to_send_to_monitor = node.data[new_time_key]

    to_send = {'data': data_to_send_to_monitor, 'data_flow_per_round': node.data_flow_per_round[node.cycle]}
    if node.is_send_data_back == "1":
        node.session_to_monitoring.post(
            'http://{}:{}/receive_node_data?ip={}&port={}&round={}'.format(
                node.monitoring_address, node.client_port, node.ip, node.port, inc_round
            ),
            json=to_send
        )

"""
gossip_node.py — VOIDemon Gossip Node Entrypoint

Each Docker container runs this Flask server. It exposes the gossip protocol
HTTP endpoints (push/pull metadata exchange), the VoI-filtered metric API,
the Chaos Engine /terminate soft-kill route, and lifecycle management routes
called by the orchestrator at experiment start/reset time.
"""

import time

from flask import Flask, request
from node import Node, METRIC_PRIORITIES, METRIC_DELTAS
import threading
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
gossip_app = Flask(__name__)


@gossip_app.route('/receive_message', methods=['GET'])
def receive_message():
    if not Node.instance().is_alive:
        return "Dead Node", 500

@gossip_app.route('/start_node', methods=['POST'])
def start_node():
    """Initialize and start the gossip loop for this node container."""
    init_data = request.get_json()
    monitoring_address = init_data["monitoring_address"]
    client_port = init_data["client_port"]
    database_address = init_data["database_address"]
    node_list = init_data["node_list"]
    target_count = init_data["target_count"]
    gossip_rate = init_data["gossip_rate"]
    node_ip = init_data["node_ip"]
    is_send_data_back = init_data["is_send_data_back"]
    push_mode = init_data["push_mode"]
    node = Node.instance()
    time.sleep(10)
    client_thread = threading.Thread(target=node.start_gossiping, args=(target_count, gossip_rate))
    counter_thread = threading.Thread(target=node.start_gossip_counter)
    node.set_params(node_ip,
                    request.headers.get('Host').split(':')[1], 0,
                    node_list, {}, True, 0, 0, monitoring_address, database_address,
                    is_send_data_back=is_send_data_back,
                    client_thread=client_thread, counter_thread=counter_thread, data_flow_per_round={},
                    push_mode=push_mode, client_port=client_port)
    client_thread.start()
    compare_and_update_node_data(request.get_json())
    return "OK"


@gossip_app.route('/metadata', methods=['GET'])
def get_metadata():
    if not Node.instance().is_alive:
        return "Dead Node", 500
    node = Node.instance()
    if not node.data:
        return json.dumps({})
    latest_entry = max(node.data.keys(), key=int)
    metadata = {}
    for key in node.data[latest_entry]:
        if 'counter' in node.data[latest_entry][key]:
            metadata[key] = {'counter': node.data[latest_entry][key]['counter'],
                             'digest': node.data[latest_entry][key]['digest']}
    return json.dumps(metadata)


def compare_node_data_with_metadata(data):
    """Compare incoming metadata with local state; return keys to request and data to push back."""
    node = Node.instance()
    metadata = data['metadata']
    sender_key = next(key for key in data if key != 'metadata')
    counter_thread.start()

    # Apply VoI priority/delta configuration sent by the orchestrator
    if 'metric_priorities' in init_data:
        METRIC_PRIORITIES.update(init_data['metric_priorities'])
    if 'metric_deltas' in init_data:
        METRIC_DELTAS.update(init_data['metric_deltas'])

    return "OK"


@gossip_app.route('/register_new_node', methods=['POST'])
def register_new_node():
    """Register a newly joined peer in this node's peer list."""
    Node.instance().node_list.append(request.get_json())
    return "OK"


@gossip_app.route('/get_data_from_node', methods=['GET'])
def get_data_from_node():
    """Return full historical gossip data stored by this node."""
    return Node.instance().data


@gossip_app.route('/get_recent_data_from_node', methods=['GET'])
def get_recent_data_from_node():
    """Return only the most recent gossip snapshot from this node."""
    data = Node.instance().data
    latest_entry = max(data.keys(), key=int)
    return data[latest_entry]


@gossip_app.route('/get_nodelist_from_node', methods=['GET'])
def get_nodelist_from_node():
    """Return this node's current peer list."""
    return json.dumps(Node.instance().node_list)


@gossip_app.route('/hello_world', methods=['GET'])
def health_check():
    """Health-check endpoint — confirms the node is responding."""
    return "VOIDemon node alive."


@gossip_app.route('/metrics_priority_stats', methods=['GET'])
def get_metrics_priority_stats():
    """Return statistics about VoI priority-based metric filtering for this node."""
    node = Node.instance()

    if len(node.data) == 0:
        return json.dumps({"error": "No data available"})

    metrics_sent = node.metrics_sent_count if hasattr(node, 'metrics_sent_count') else 0
    metrics_filtered = node.metrics_filtered_count if hasattr(node, 'metrics_filtered_count') else 0

    per_round_stats = {}
    for round_num, stats in node.data_flow_per_round.items():
        per_round_stats[round_num] = {
            'metrics_sent': stats.get('metrics_sent', 0),
            'metrics_filtered': stats.get('metrics_filtered', 0)
        }

    return json.dumps({
        'total_metrics_sent': metrics_sent,
        'total_metrics_filtered': metrics_filtered,
        'bandwidth_savings_percent': round(
            100 * metrics_filtered / (metrics_sent + metrics_filtered)
            if (metrics_sent + metrics_filtered) > 0 else 0, 2
        ),
        'per_round_stats': per_round_stats,
        'priorities': {k: v for k, v in METRIC_PRIORITIES.items()},
        'deltas': {k: v for k, v in METRIC_DELTAS.items()}
    })


if __name__ == "__main__":
    gossip_app.run(host='0.0.0.0', debug=True, threaded=True)
    sender_data = data[sender_key]
    if len(node.data) == 0:
        # Node doesn't store any data yet — request everything
        return metadata.keys()
    latest_entry = max(node.data.keys(), key=int)
    all_keys = set().union(node.data[latest_entry].keys(), metadata.keys())
    all_keys.discard(sender_key)
    node.data_flow_per_round.setdefault(node.cycle, {})
    if sender_key in node.data[latest_entry]:
        node.data_flow_per_round[node.cycle].setdefault('fd', 0)
        node.data_flow_per_round[node.cycle]['fd'] += 1
    else:
        node.data_flow_per_round[node.cycle].setdefault('nd', 0)
        node.data_flow_per_round[node.cycle].setdefault('fd', 0)
        node.data_flow_per_round[node.cycle]['nd'] += 1
        node.data_flow_per_round[node.cycle]['fd'] += 1

    node.data[latest_entry][sender_key] = sender_data

    ips_to_update = []
    data_to_send = {}
    for key in all_keys:
        if key in node.data[latest_entry] and key in metadata:
            if ('counter' not in node.data[latest_entry][key]) or (
                    float(metadata[key]) > float(node.data[latest_entry][key]['counter'])):
                ips_to_update.append(key)
            else:
                data_to_send[key] = node.data[latest_entry][key]
        elif key in node.data[latest_entry] and key not in metadata:
            data_to_send[key] = node.data[latest_entry][key]
        else:
            ips_to_update.append(key)
    return {'requested_keys': ips_to_update, 'updates': data_to_send}


@gossip_app.route('/receive_metadata', methods=['POST'])
def receive_metadata():
    if not Node.instance().is_alive:
        return "Dead Node", 500
    data = compare_node_data_with_metadata(request.get_json())
    return data


@gossip_app.route('/reset_node')
def reset_node():
    node = Node.instance()
    node.is_alive = False
    node.client_thread.join()
    node.counter_thread.join()
    node.set_params(None, None, 0, None, {}, False, 0, 0, None, None,
                    is_send_data_back=None, client_thread=None,
                    counter_thread=None, data_flow_per_round={},
                    push_mode=0, client_port=None)
    return "OK"


@gossip_app.route('/stop_node')
def stop_node():
    node = Node.instance()
    node.is_alive = False
    node.client_thread.join()
    node.counter_thread.join()
    return "OK"


@gossip_app.route('/terminate', methods=['POST', 'GET'])
def terminate_node():
    """
    Chaos Engine soft-kill endpoint called by the dashboard.

    Instantly sets is_alive=False so this node stops gossiping and returns
    HTTP 500 to all peers on their next gossip request, triggering the
    3-strike leaderless quorum failure detector — no Docker stop required.
    """
    node = Node.instance()
