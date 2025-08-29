# Demon

Demon is the core component of this repository, responsible for implementing a self-adaptive and robust monitoring system designed for volatile edge infrastructure. It utilizes a push/pull gossip algorithm for communication and coordination.

## Disclaimer

**Demon is a proof of concept application and should not be used in a production environment**. It is intended for experimental purposes and as a demonstration of the monitoring system's capabilities.

## Running Demon

Demon can be run in experimental environments by using for example containers or Raspberry Pi's.

### Docker Container

To run Demon in a Docker container, follow these steps:

1. Install Docker if not already installed on your system.
2. Build the Docker image using the provided [`Dockerfile`](./demon/Dockerfile).
3. Run a Docker container based on the built image.
4. Start a Demon node as described in [Starting a Demon Node](#starting-a-demon-node).

## Demon Endpoints

Demon exposes several HTTP endpoints through its Flask server for interaction. The most important endpoints are listed below:

- `/hello_world`: A simple endpoint to check if the server is running.
- `/start_node`: Start Demon on the given node.
- `/stop_node`: Halts the operation of a node or component.
- `/reset_node`: Resets the state of a node, clearing any accumulated data.

(The implementation of each endpoint can be found in the [`demon.py`](./demon/demon.py))

#### Starting a Demon Node
To initiate a new node or component in the monitoring system, you should make a POST request to the `/start_node` endpoint. The payload for this request should be in JSON format and include the necessary configuration parameters. Here's an example JSON payload:

```json
{
  "node_list": [],
  "target_count": 3,
  "gossip_rate": 1,
  "database_address": "db_address",
  "monitoring_address": "monitoring_address",
  "client_port": "4000",
  "node_ip": "ip_of_host",
  "is_send_data_back": 0,
  "push_mode": 0
}
```
Where the parameters are defined as follows: 
- `node_list`: A list of nodes to initially connect to, where each entry has the form: 
    ```json
    {
      "id": "node_id",
      "ip": "ip_of_node",
      "port": "port_of_node"
    }
    ```
- `target_count`: The number of nodes to connect to each gossip round.
- `gossip_rate`: The number of seconds (interval) between each gossip round.
- `database_address`: This parameter is deprecated and should be set to an empty string.
- `monitoring_address`: The address of the server which benchmarks  or pushed monitoring data will be sent to.
- `client_port`: The port on which benchmarks or pushed monitoring data will be sent to.
- `node_ip`: The IP address of the Demon node.
- `is_send_data_back`: When set to 1 (true), the node will send monitoring data back to the monitoring server.
- `push_mode`: When set to 1 (true), the node will push monitoring data to the monitoring server.


#### Other Endpoints
- The endpoints `/stop_node` and `/reset_node` can be used to stop or reset a node via a GET-Request.
- The endpoint `/get_recent_data_from_node` can be used to retrieve the most recent monitoring data from a node via a GET-Request.
- In order to retrieve the complete in memory data from a node `/get_data_from_node` can be used via a GET-Request.


# Query Client
Provides an importable method to query the demon system for trustable data.
