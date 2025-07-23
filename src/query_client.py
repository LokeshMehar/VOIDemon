import requests

def query(node_list, target_node_ip, target_node_port):
    # Basic query implementation - just query first node
    node = node_list[0]
    try:
        r = requests.get("http://" + node["ip"] + ":" + node["port"] + "/metadata")
        metadata = r.json()[target_node_ip + ":" + target_node_port]
        print("Metadata found: {}".format(metadata))
        
        # Get actual data
        response = requests.get("http://{}:{}/get_recent_data_from_node".format(node["ip"], node["port"]))
        result = response.json()[target_node_ip + ":" + target_node_port]
        print("Query result: {}".format(result))
        return result
    except Exception as e:
        print("Error querying node: {}".format(e))
        return None
