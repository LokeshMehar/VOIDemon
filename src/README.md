# VOIDemon — Source (Gossip Engine)

This directory contains the core implementation of the VOIDemon gossip node and the quorum query bridge.

## 📁 Contents

### `app/`
The individual gossip node logic.

| File | Purpose |
|---|---|
| `gossip_node.py` | Flask entrypoint for each node container — handles gossip HTTP routes, VoI filtering, and Chaos Engine `/terminate` |
| `node.py` | Node state machine — gossip transmission loop, peer tracking, 3-strike failure detection |
| `quorum_query.py` | Leaderless quorum consensus read implementation |
| `digest.py` | SHA-256 digest helper used to detect data staleness during gossip exchange |
| `singleton.py` | Decorator-based process-safe singleton pattern |
| `Dockerfile` | Container definition for a single gossip node (`voidemon-node` image) |

### `query_client.py`
Re-exports `query()` from `quorum_query.py` so the orchestrator can import it cleanly via `from src import query_client`.

## 🧠 Key Logic: VoI Priority Filtering

VOIDemon nodes don't send every metric every round. Before each transmission, the `Node` evaluates each metric:

1. **Staleness** — Has it been too long since we last sent this? (based on `MetricPriority`)
2. **Drift** — Has the value changed significantly since the last update? (based on `MetricDelta`)
3. **Forced Send** — New nodes and critical updates bypass the filters entirely

This logic produces drastic bandwidth reductions (up to 100×) without sacrificing monitoring accuracy.
