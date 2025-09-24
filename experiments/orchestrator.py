                    unique_entry_id = existing_entry[0]
                else:
                    cursor.execute('INSERT INTO unique_entries (key, value) VALUES (?, ?)', (k, v))
                    unique_entry_id = cursor.lastrowid
                cursor.execute(
                    'INSERT INTO data_entries (node, round, key, unique_entry_id) VALUES (?, ?, ?, ?)',
                    (node_key, client_round, k, unique_entry_id)
                )
        connection_pool.commit()
    return "OK"


@orchestrator.route('/notify_node_killed', methods=['POST'])
def notify_node_killed():
    """
    Chaos Engine notification — called by the dashboard after a soft-kill succeeds.

    Immediately lowers the convergence target so the surviving nodes can declare
    convergence without waiting for the 3-strike timeout to propagate.
    """
    data = request.get_json(silent=True) or {}
    killed_ip = data.get("ip", "")
    with run_lock:
        if experiment and experiment.runs:
            run = experiment.runs[-1]
            run.manually_killed_count += 1
            killed_key = data.get("ip", "") + ":" + str(data.get("port", ""))
            run.killed_node_keys.add(killed_key)
            run.data_entries_per_ip.pop(killed_key, None)
            print("[Chaos] Node {} manually killed. New target: {}/{}".format(
                killed_ip, run.node_count - run.manually_killed_count, run.node_count))
    return "OK"


@orchestrator.route('/receive_ic', methods=['GET'])
def update_ic():
    client_ip = request.args['ip']
    client_port = request.args['port']
    with run_lock:
        experiment.runs[-1].ip_per_ic[client_ip + ":" + client_port] = True
        if len(experiment.runs[-1].ip_per_ic) == experiment.runs[-1].node_count:
            run_converged(experiment.runs[-1])
    return "OK"


@orchestrator.route('/receive_node_data', methods=['POST'])
def update_data_entries_per_ip():
    """Receive per-round metric and flow data from a gossip node."""
    if not experiment:
        print("No experiment running, but a gossip node sent data")
        return "NOK"
    client_ip = request.args['ip']
    client_port = request.args['port']
    round_num = request.args['round']
    inc = request.get_json()
    data_stored_in_node = inc["data"]
    data_flow_per_round = inc["data_flow_per_round"]

    nd = data_flow_per_round.setdefault('nd', 0)
    fd = data_flow_per_round.setdefault('fd', 0)
    rm = data_flow_per_round.setdefault('rm', 0)

    ic = len(data_stored_in_node)
    bytes_of_data = len(json.dumps(data_stored_in_node).encode('utf-8'))

    with run_lock:
        experiment.runs[-1].convergence_round = max(experiment.runs[-1].convergence_round, int(round_num))
        experiment.runs[-1].message_count += 1
        experiment.runs[-1].data_entries_per_ip[client_ip + ":" + client_port] = data_stored_in_node
        check_convergence(experiment.runs[-1], data_stored_in_node)
        if int(round_num) >= 80:
            run_converged(experiment.runs[-1])
