import requests

def query(node_list, target_node_ip, target_node_port):
    target_key = target_node_ip + ":" + target_node_port
    
    for i, node in enumerate(node_list):
        try:
            print(f"Querying node {i+1}/{len(node_list)}: {node['ip']}:{node['port']}")
            
            # Get metadata first
            metadata_url = f"http://{node['ip']}:{node['port']}/metadata"
            r = requests.get(metadata_url, timeout=5)
            
            if r.status_code != 200:
                print(f"Node {i+1} returned status {r.status_code}")
                continue
                
            metadata = r.json().get(target_key)
            if not metadata:
                print(f"Node {i+1} doesn't have metadata for target")
                continue
                
            print(f"Metadata found on node {i+1}: {metadata}")
            
            # Get actual data
            data_url = f"http://{node['ip']}:{node['port']}/get_recent_data_from_node"
            response = requests.get(data_url, timeout=5)
            
            if response.status_code != 200:
                print(f"Data request failed on node {i+1}")
                continue
                
            result = response.json().get(target_key)
            if result:
                print(f"Query successful on node {i+1}: {result}")
                return result
            else:
                print(f"Node {i+1} doesn't have data for target")
                
        except requests.exceptions.Timeout:
            print(f"Timeout querying node {i+1}")
        except requests.exceptions.ConnectionError:
            print(f"Connection error to node {i+1}")
        except Exception as e:
            print(f"Error querying node {i+1}: {e}")
    
    print("All nodes failed or don't have the requested data")
    return None
