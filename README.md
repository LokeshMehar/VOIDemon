├── LICENSE                            # MIT License
├── CONTRIBUTING.md                    # Contribution guidelines
├── CODE_OF_CONDUCT.md                 # Contributor Covenant
└── .gitignore                         # Ignores DBs, caches, node_modules, etc.
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS | Real-time dashboard with live force-graph topology |
| **API Gateway** | Node.js, Express, Socket.IO | Bridges frontend ↔ orchestrator; live WebSocket push |
| **Orchestrator** | Python 3.9+, Flask | Manages experiment lifecycle, Docker cluster, data ingest |
| **Node Cluster** | Python, Docker, SQLite WAL | Gossip engine, VoI filtering, metric propagation |
| **Analytics** | Pandas, Matplotlib | Post-run bandwidth/battery/convergence visualizations |

---

## 🚀 Quick Start
