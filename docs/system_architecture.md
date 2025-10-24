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
