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
