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
