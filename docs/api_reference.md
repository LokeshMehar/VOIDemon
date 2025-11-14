# API & Communications Reference

VOIDemon relies on a mix of REST APIs for control and configuration, peer-to-peer HTTP for gossip synchronization, and WebSockets for live telemetry streaming.

This document details the communication boundaries between the various components.

---

## 1. API Gateway (Node.js/Express)

The API Gateway runs on **Port 5000** and serves as the primary bridge between the React frontend and the Python backend simulation.

### `GET /api/config`
Retrieves the current simulation parameters by parsing `experiments/config.ini`.
- **Response:** `200 OK` (JSON representation of the INI structure)

### `POST /api/config`
Accepts a JSON payload, serializes it back to INI format, and overwrites `config.ini`.
- **Body:** `{ "VOIDemonParam": { "node_range": "[10]" ... } }`
- **Response:** `200 OK`

### `POST /api/start`
Proxies the start signal from the dashboard to the Python Orchestrator.
- **Response:** `200 OK` (Returns the orchestrator's boot confirmation)

### `POST /api/kill-node/:ip/:port`
The **Chaos Engine** endpoint. Sends a hard termination signal to a specific docker container to simulate hardware failure.
- **Parameters:** `ip` (string), `port` (string)
- **Response:** `200 OK` (Or `500 Server Error` if the node is already dead or unreachable)

```mermaid
sequenceDiagram
    participant UI as Dashboard (User)
    participant GW as API Gateway (:5000)
    participant N as Node Flask Server (Target)
    participant O as Orchestrator (:4000)
    
    UI->>GW: POST /api/kill-node/:ip/:port
    GW->>N: POST /terminate
    N-->>GW: 200 OK
    Note over N: sys.exit(0) triggered<br/>Container dies
    GW->>O: POST /notify_node_killed
    O-->>GW: 200 OK
```

### WebSockets (`Socket.IO`)
The Gateway exposes a Socket.IO server on the same port.
- **Event `run_started`**: Emitted when the orchestrator boots the cluster. Contains the initial topology list (IPs, Ports, Node IDs).
- **Event `new_metric`**: Emitted multiple times per second as nodes gossip. Contains the updated state, round number, and VoI efficiency metrics for a specific node.

---

## 2. Python Orchestrator (Flask)

The Orchestrator runs on **Port 4000**. It controls the Docker daemon and receives data from the nodes.

### `POST /start`
Reads `config.ini`, wipes the `voidemon.db` tables, spawns the Docker containers, and kicks off the simulation run.

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant D as Docker Daemon
    participant N as Gossip Nodes
    
    O->>O: Parse config.ini
    O->>O: Clean voidemon.db
    O->>D: Create 'test' bridge network
    O->>D: Spawn N containers (voidemon-node)
    D-->>O: Return container IPs/Ports
    O->>N: Inject complete topology list
    Note over N: Nodes begin independent<br/>Gossip loops
```

### `POST /receive_node_data`
*Internal endpoint used by the Gossip Nodes.*
As nodes execute gossip rounds, they push their current worldview to this endpoint. The orchestrator batches these and writes them to the SQLite database.
- **Query Params:** `?ip=...&port=...&round=...`
- **Body:** The complete JSON state of the node.

### `POST /notify_node_killed`
*Internal endpoint used by the API Gateway Chaos Engine.*
Tells the orchestrator that a node was intentionally killed, allowing the orchestrator to adjust its expected convergence target size so the simulation doesn't hang waiting for a dead node.

---

## 3. P2P Gossip Node (Flask inside Docker)

Each node runs its own Flask server mapped dynamically from an internal container Port 5000 to an available host port (e.g., 60592).

### `POST /gossip`
The core peer-to-peer synchronization endpoint.
1. The initiating node sends a metadata vector (Counters + SHA256 Digests).
2. The receiving node calculates the delta.
3. The receiving node returns a JSON payload containing the full state for objects the initiator was missing, and requests full state for objects the receiver is missing.

### `POST /terminate`
When hit, the Flask server calls `sys.exit(0)`. This violently kills the python process, shutting down the container. Used by the Chaos Engine to test the Leaderless Quorum Consensus failure detection.
