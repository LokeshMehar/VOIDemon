            "(run_id, ip, port, round, nd, fd, rm, ic, bytes_of_data) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, ip, port, this_round, nd, fd, rm, ic, bytes_of_data)
        )
        connection.commit()
        connection.close()
        return True
    except Exception as e:
        print("Error DB insert round_of_node_max_round: {}".format(e))
        return False


class NodeDB:
    """Manages the node state snapshot store (unique_entries + data_entries tables)."""

    def _connect(self):
        conn = sqlite3.connect(
