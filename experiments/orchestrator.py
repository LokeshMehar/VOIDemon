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
