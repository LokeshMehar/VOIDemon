"""
quorum_query.py — Leaderless Quorum Consensus Query

Implements the read-path of the VOIDemon gossip system.
To ensure consistent results without a dedicated leader, a random quorum of
`quorum_size` peers is sampled, their metadata (counter + digest) is compared,
and only when all agree on the same counter AND digest is the actual data
fetched from one peer.

Retries up to MAX_QUERY_RETRIES times with a small backoff between attempts.
"""

import random
import time
import requests

# Maximum number of quorum attempts before giving up
MAX_QUERY_RETRIES = 30


def query(node_list, quorum_size, target_node_ip, target_node_port, docker_ip):
    """
    Execute a consistent quorum read for the given target node's state.

    Args:
        node_list:       Full list of peer node dicts (with 'ip' and 'port').
        quorum_size:     Number of peers that must agree for a valid read.
        target_node_ip:  IP of the node whose state we want to read.
        target_node_port:Port of the target node.
        docker_ip:       Host-visible IP to use when building URLs (overrides container IPs).

    Returns:
        Tuple of (total_messages_sent, query_result_dict).

    Raises:
        RuntimeError: If quorum consensus is never reached within MAX_QUERY_RETRIES.
    """
    def build_url(node, path):
        host = docker_ip if docker_ip else node["ip"]
        return f"http://{host}:{node['port']}{path}"

    target_key = f"{target_node_ip}:{target_node_port}"

    for attempt in range(MAX_QUERY_RETRIES):
        # 1. Sample a random quorum of peers
        random_nodes = random.sample(node_list, quorum_size)

        metadatas = {}
        total_messages = 0

        # 2. Gather metadata (counter + digest) from each quorum member
        for node in random_nodes:
            total_messages += 1
            try:
                resp = requests.get(build_url(node, "/metadata"), timeout=5)
                resp.raise_for_status()
                data = resp.json()[target_key]
                metadatas[f"{node['ip']}:{node['port']}"] = data
            except Exception as e:
                print(f"[QuorumQuery] Node {node['ip']}:{node['port']} not responding: {e}")

        # 3. Full quorum must have replied
        if len(metadatas) == quorum_size:
            # Counter consensus
            counters = [d["counter"] for d in metadatas.values()]
            if len(set(counters)) == 1:
                # Digest consensus — guarantees identical data
                digests = [d["digest"] for d in metadatas.values()]
                if len(set(digests)) == 1:
                    # 4. Fetch actual node data from the first quorum member
                    first_node = random_nodes[0]
                    data_resp = requests.get(
                        build_url(first_node, "/get_recent_data_from_node"),
                        timeout=5
                    )
                    data_resp.raise_for_status()
                    result = data_resp.json()[target_key]
                    print(f"[QuorumQuery] Consensus reached on attempt {attempt + 1}: {result}")
                    return total_messages, result

        # Small backoff before the next attempt
        time.sleep(0.5)

    raise RuntimeError(
        f"[QuorumQuery] Failed: could not reach quorum consensus after {MAX_QUERY_RETRIES} attempts"
    )
