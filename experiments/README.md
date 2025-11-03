# VOIDemon — Experiments (Orchestrator & Analytics)

This directory contains the experiment orchestration logic, analytics, database layer, and configuration.

## 📁 Core Components

### `orchestrator.py`
The heart of the simulation — a Flask server that acts as both a control plane and metric aggregator.

- **Orchestration**: Dynamically spawns Docker containers (`voidemon-node`), configures their initial state, and triggers the gossip phase.
- **Monitoring**: Receives real-time data packets from nodes via `/receive_node_data` and tracks convergence.
- **Chaos Engine**: Accepts `/notify_node_killed` calls from the dashboard to immediately lower the convergence target.
- **Persistence**: Records every gossip round and metric transmission into `voidemon.db` (SQLite WAL mode).

### `analytics.py`
Post-run visualization suite using Matplotlib.

- **VoI Bandwidth Savings**: Pie charts and line graphs showing metrics filtered vs. transmitted.
- **Resilience**: Query success rates plotted against varying node failure percentages.
- **Metric Breakdown**: Per-metric type analysis (CPU / Memory / Network / Storage prioritization).

### `database.py`
The database abstraction layer.

- **SSD Safety**: WAL mode + `synchronous = NORMAL` to prevent excessive disk wear during high-throughput writes.
- **VoidemonDB**: Stores experiment runs, convergence data, per-round flow stats, and VoI efficiency metrics.
- **NodeDB**: Manages the node state snapshot store.

### `inspect_schema.py`
A debug utility that prints all table CREATE statements from the database. Useful for verifying the schema after a run.

## ⚙️ Configuration

All simulation parameters live in `config.ini`:

```ini
[VOIDemonParam]
node_range      = "[10]"   ; Node cluster size(s) to test
gossip_rate     = 3        ; Fan-out — number of peers contacted per round
runs            = 1        ; Number of experiment repetitions
```
