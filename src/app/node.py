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
