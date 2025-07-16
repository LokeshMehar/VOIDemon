
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
