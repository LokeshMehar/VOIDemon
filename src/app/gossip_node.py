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
