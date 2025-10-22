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
