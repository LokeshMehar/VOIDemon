    AF[Browser Animation Frame<br/>60 FPS] -- Reads --> R
    AF -- Calls --> ST(React setState)
    ST -- Renders --> DOM[Force-Directed Graph DOM]
```

### 17. Why use JSON over REST instead of Protocol Buffers (gRPC)?
**Decision:** REST / JSON.
**Trade-off:** gRPC and Protobufs are vastly superior for inter-service communication because they send compressed binary data instead of heavy strings. However, this requires compiling `.proto` files, managing schemas, and configuring HTTP/2 support in the Python servers, significantly increasing the barrier to entry for students and researchers. JSON is human-readable, natively supported by Flask and Express, and easily visible in the Chrome Network tab. We explicitly chose developer experience (DX) and debuggability over maximum binary efficiency.

### 18. Why use HTTP POST for Chaos Engine termination instead of `docker kill`?
**Decision:** Soft-kill via Flask `/terminate`.
**Trade-off:** The Orchestrator could easily use the Docker API to run `docker stop <container>`. However, communicating with the Docker daemon takes time (sometimes 1-2 seconds), which skews the microsecond-level timing of the simulation. By exposing a `/terminate` endpoint on the Node itself that immediately triggers a `sys.exit(0)`, the node dies instantly. This accurately simulates a hard hardware crash (like a power cut) without the overhead of the Docker daemon intervening.

### 19. Why does the API Gateway proxy the React config updates to a physical `.ini` file?
**Decision:** Configuration File Persistence.
**Trade-off:** We could store the configuration purely in a database or in memory. However, researchers running this system on headless servers often prefer modifying a physical `config.ini` file via SSH and `vim`. By building a two-way sync where the React UI modifies the `.ini` file via the API Gateway, we cater to both visual users and terminal-power-users simultaneously, while keeping the configuration physically portable across environments.

### 20. Summary: The Ultimate Trade-off
Ultimately, **VOIDemon** is engineered under the philosophy that **Eventual Consistency and Developer Ergonomics are more important than Absolute Precision and Maximum Performance.** 

We trade deep JSON equality for fast Hashes. We trade synchronous DB safety for fast WAL queues. We trade absolute metric accuracy for massive battery savings via VoI. Every decision is specifically calibrated to simulate a volatile, resource-constrained edge environment as accurately and safely as possible on standard developer hardware.
# Engineering Paradigms & Implementation Trade-offs

This document serves as an exhaustive deep dive into the engineering decisions, architectural patterns, and unavoidable trade-offs made during the implementation of **VOIDemon**. 

It is structured as a Q&A designed for technical interviewers, engineering managers, and systems architects who understand distributed systems theory but need to evaluate the practical, code-level implementation choices.

---

## Part 1: Core Architecture & Frameworks

### 1. Why use Docker containers to simulate the nodes instead of just running multiple Python threads/processes on the host?
**Decision:** Full containerization via Docker.
**Trade-off:** Running lightweight Python threads or `multiprocessing` processes would consume significantly less CPU overhead and memory than booting $N$ Docker containers. However, threads share the same network interface, file system, and OS environment. By using Docker, we achieve **true network isolation**. Each node gets its own distinct IP address on the Docker bridge network. This allows the simulation to accurately replicate a physical edge deployment where network latency, dropped packets, and isolated failures occur. Docker also ensures the environment is reproducible across any developer's machine without dependency hell.

```mermaid
graph TD
    subgraph Traditional Threading Model
        P[Python Process]
        P --> T1[Thread 1]
        P --> T2[Thread 2]
        T1 -.-|Shared Memory & IP| T2
    end
    
    subgraph VOIDemon Docker Model
        D[Docker Engine]
        D --> C1[Container Node 1<br/>IP: 172.18.0.2]
        D --> C2[Container Node 2<br/>IP: 172.18.0.3]
        C1 -.-|Isolated TCP/IP Network| C2
    end
