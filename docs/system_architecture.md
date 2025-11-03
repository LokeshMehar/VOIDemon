# System Architecture & Component Breakdown

VOIDemon is engineered as a highly modular, multi-tier system. It separates the decentralized heavy-lifting of the gossip protocol from the centralized simulation management, analytics, and frontend visualization.

This separation of concerns ensures that the core gossip nodes run exactly as they would on real edge IoT devices, while the orchestrator acts solely as an external observer.

---

## High-Level Topology

The following SVG diagram provides a comprehensive, zoomed-out view of the entire VOIDemon system:

<p align="center">
  <img src="architecture.svg" alt="VOIDemon Full System Architecture" width="100%"/>
</p>

The interactive Mermaid version below captures the same topology in a text-renderable format:

```mermaid
graph TD
    subgraph Frontend & Control
        D[React Dashboard]
    end
    
    subgraph API Layer
        A[Express API Gateway]
    end
    
    subgraph Simulation Layer
        O[Python Orchestrator]
        DB[(SQLite WAL Database)]
    end
    
    subgraph Containerized Edge Network
        N1[Gossip Node 1]
        N2[Gossip Node 2]
        N3[Gossip Node 3]
        NX[Gossip Node N]
    end

    D <-->|Socket.IO (Live Metrics)| A
    D <-->|REST (Config)| A
    A <-->|HTTP POST /start| O
    A -.->|Chaos Engine /terminate| N1
    O -->|Spawns via Docker API| Containerized Edge Network
    O -->|Writes analytics| DB
    N1 <-->|P2P Gossip Exchange| N2
    N2 <-->|P2P Gossip Exchange| N3
    N3 <-->|P2P Gossip Exchange| NX
    Containerized Edge Network -->|Push State Updates| O
```

---

## 1. The Edge Cluster (`src/`)

The core of the system is the gossip node logic, designed to be deployed directly onto edge hardware or run in isolated Docker containers for simulation.

### 1.1 `gossip_node.py` (The Entrypoint)
Each node runs a lightweight Flask server. This server exposes the endpoints necessary for the push-pull gossip protocol.
- **`/gossip`**: The primary endpoint. Receives metadata vectors from peers, computes the difference against its local state, and returns the fresher state payloads.
- **`/terminate`**: The Chaos Engine endpoint. When hit, the node immediately shuts down to simulate a sudden hardware or network failure.

### 1.2 `node.py` (The State Machine)
The actual algorithmic engine. It runs a background thread that wakes up every gossip interval, selects $k$ random peers, and initiates the synchronization sequence. It encapsulates the Value of Information (VoI) filtering logic to strip out redundant metrics before transmission.

### 1.3 `quorum_query.py` & `digest.py`
Provides the Leaderless Quorum Consensus (LQC) read implementation and SHA-256 hashing to efficiently compare deeply nested JSON states without massive CPU overhead.

```mermaid
flowchart LR
    subgraph Container: voidemon-node
        direction TB
        F[Flask Server] -->|Incoming Gossip| S[(Singleton Node State)]
        D[Daemon Thread] -->|Read State| S
        D -->|Outgoing Gossip| P((Peer Nodes))
        P -->|Push/Pull| F
    end
```

---

## 2. The Orchestrator (`experiments/`)

The Python orchestrator manages the lifecycle of the simulation. **It does not participate in the gossip network.** It acts purely as a God-view observer.

### 2.1 Dynamic Bootstrapping (`orchestrator.py`)
Using the Docker SDK, the orchestrator reads the `config.ini` file, calculates the requested number of nodes, and dynamically spawns that many `voidemon-node` containers. It maps their internal ports (5000) to random available host ports and injects the topology list into each container so they know who to gossip with.

### 2.2 Data Aggregation & Persistence
As nodes gossip, they independently stream their updated state views to the orchestrator's `/receive_node_data` endpoint. The orchestrator batches these updates and writes them to the `voidemon.db` SQLite database.
- **WAL Mode:** To handle the massive concurrency of dozens of nodes hammering the database simultaneously, VOIDemon utilizes SQLite Write-Ahead Logging (WAL) mode, ensuring SSD safety and preventing lock contention.

### 2.3 `analytics.py`
A post-run script that parses the SQLite database using Pandas and Matplotlib to generate the bandwidth, battery, and convergence graphs based on the theoretical models.

---

## 3. The API Gateway (`dashboard/api/`)

A Node.js / Express server that bridges the Python backend and the React frontend.

- **Config Proxy:** Reads and writes the `config.ini` file, exposing it as a REST JSON endpoint (`GET/POST /api/config`).
- **Live Stream (Socket.IO):** The orchestrator pushes database batch updates to the Express server, which then broadcasts them via WebSockets to all connected React clients. This completely decouples the heavy SQLite write operations from the real-time UI.
- **Chaos Gateway:** Proxies the "Kill Node" command from the frontend directly to the specific Docker container's IP/Port.

```mermaid
sequenceDiagram
    participant DB as SQLite WAL
    participant Orch as Python Orchestrator
    participant API as Node.js Gateway
