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

