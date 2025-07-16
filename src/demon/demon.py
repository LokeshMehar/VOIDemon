
from flask import Flask
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
gossip = Flask(__name__)



@gossip.route('/metadata', methods=['GET'])
def get_metadata():
    if not Node.instance().is_alive:
        # reset_node()
        return "Dead Node", 500
    node = Node.instance()
    latest_entry = max(node.data.keys(), key=int)
    metadata = {}
    for key in node.data[latest_entry]:
        if 'counter' in node.data[latest_entry][key]:
            metadata[key] = {'counter': node.data[latest_entry][key]['counter'],
                             'digest': node.data[latest_entry][key]['digest']}
    return json.dumps(metadata)


def compare_node_data_with_metadata(data):
    # metadata form: {ip1: counter1, ip2: counter2, .....}
    # to_send = {'metadata': metadata, key:own_recent_data}
    node = Node.instance()
    metadata = data['metadata']
    sender_key = next(key for key in data if key != 'metadata')
    sender_data = data[sender_key]
    if len(node.data) == 0:
        # node doesnt store any data yet
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

    # lists of ips who reclaim that this node is dead
    ips_to_update = []
    data_to_send = {}
    for key in all_keys:
        # both nodes store the data if IP
        if key in node.data[latest_entry] and key in metadata:
            # node doesnt store the key or counter of metadata > counter of noda.data
            if ('counter' not in node.data[latest_entry][key]) or (
                    float(metadata[key]) > float(node.data[latest_entry][key]['counter'])):
                ips_to_update.append(key)
            else:
                data_to_send[key] = node.data[latest_entry][key]
        # metadata doesnt store the data of IP
        elif key in node.data[latest_entry] and key not in metadata:
            data_to_send[key] = node.data[latest_entry][key]
        # node doesnt store the data of IP
        else:
            ips_to_update.append(key)
    requests_updates = {'requested_keys': ips_to_update, 'updates': data_to_send}
    return requests_updates


def compare_and_update_node_data(inc_data):
    node = Node.instance()
    new_time_key = node.gossip_counter
    latest_entry = max(node.data.keys(), key=int) if len(node.data) > 0 else new_time_key
    new_data = inc_data
    # new_data = inc_data['data']
    # new_node_list = inc_data['node_list']
    all_keys = set().union(node.data[latest_entry].keys(), new_data.keys())
    inc_round = int(request.args.get('inc_round'))
    # received messages ['rm'] per round
    node.data_flow_per_round.setdefault(node.cycle, {}).setdefault('rm', 0)
    node.data_flow_per_round[node.cycle]['rm'] += 1

    # lists of ips who reclaim that this node is dead
    list1 = []
    list2 = []
    for key in all_keys:
        # both nodes store the data if IP
        if key in node.data[latest_entry] and key in new_data:

            # Handle partial metric updates - preserve existing metrics if not in incoming data
            if 'appSate' in new_data[key] and 'appSate' in node.data[latest_entry][key]:
                # Get lists of metrics
                existing_metrics = set(node.data[latest_entry][key]['appSate'].keys())
                incoming_metrics = set(new_data[key]['appSate'].keys())
                
                # For any metric in existing but not in incoming, copy from existing
                for metric in existing_metrics - incoming_metrics:
                    new_data[key]['appSate'][metric] = node.data[latest_entry][key]['appSate'][metric]
            
            if 'metric_sent_flags' in new_data[key]:
                sent_count = sum(1 for v in new_data[key]['metric_sent_flags'].values() if v)
                filtered_count = sum(1 for v in new_data[key]['metric_sent_flags'].values() if not v)
        
                # Add to round statistics
                node.data_flow_per_round[node.cycle].setdefault('metrics_sent', 0)
                node.data_flow_per_round[node.cycle].setdefault('metrics_filtered', 0)
                node.data_flow_per_round[node.cycle]['metrics_sent'] += sent_count
                node.data_flow_per_round[node.cycle]['metrics_filtered'] += filtered_count
                
            list1 = node.data[latest_entry][key]["hbState"]["failureList"]
            list2 = new_data[key]["hbState"]["failureList"]
            if ('counter' in new_data[key] and 'counter' in node.data[latest_entry][key] \
                and float(new_data[key]['counter']) > float(node.data[latest_entry][key]['counter'])) or \
                    ('counter' in new_data[key] and 'counter' not in node.data[latest_entry][key]):
                node.data.setdefault(new_time_key, {})[key] = new_data[key]

                # fresh data per round ['fd'] per round, fresh data describes data that is updated or added in this node
                node.data_flow_per_round[node.cycle].setdefault('fd', 0)
                node.data_flow_per_round[node.cycle]['fd'] += 1
            else:
                node.data.setdefault(new_time_key, {})[key] = node.data[latest_entry][key]
        # inc data doesnt store the data of IP
        elif key in node.data[latest_entry] and key not in new_data:
            node.data.setdefault(new_time_key, {})[key] = node.data[latest_entry][key]
        # node doesnt store the data of IP
        else:
            node.data.setdefault(new_time_key, {})[key] = new_data[key]
            # node.data[key] = new_data[key]
            # new data per round ['nd'] per round (nd is data from an unknown node -> fd = nd)
            node.data_flow_per_round[node.cycle].setdefault('nd', 0)
            node.data_flow_per_round[node.cycle].setdefault('fd', 0)
            node.data_flow_per_round[node.cycle]['nd'] += 1
            node.data_flow_per_round[node.cycle]['fd'] += 1
        # only for deleted nodes
        if key in node.data[latest_entry] and key in new_data:
            merged_failure_list = list(set(list1).union(set(list2)))
            node.data[new_time_key][key]["hbState"]["failureList"] = merged_failure_list
    # TODO update Database
    # send both data and data_flow_per_round to monitor
    # TODO: Save latest data snapshot with key = self.gossip_counter in data
    if new_time_key not in node.data:
        print("No new data to send", flush=True)
        data_to_send_to_monitor = node.data[latest_entry]
    else:
        data_to_send_to_monitor = node.data[new_time_key]
    to_send = {'data': data_to_send_to_monitor, 'data_flow_per_round': node.data_flow_per_round[node.cycle]}
    # TODO: Session here
    if node.is_send_data_back == "1":
        node.session_to_monitoring.post(
            'http://{}:{}/receive_node_data?ip={}&port={}&round={}'.format(node.monitoring_address,node.client_port, node.ip,
                                                                             node.port,
                                                                             inc_round), json=to_send)


@gossip.route('/receive_message', methods=['GET'])
def receive_message():
    if not Node.instance().is_alive:
        # reset_node()
        return "Dead Node", 500
    compare_and_update_node_data(request.get_json())
    return "OK"

@gossip.route('/VOIDemon', methods=['GET'])
def get_hello_from_node():
    return "Hello from VOIDemon😈"

if __name__ == "__main__":
    # get port from container
    gossip.run(host='0.0.0.0', debug=True, threaded=True)
