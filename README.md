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

Want to see it in action immediately? You need Docker, Python 3.9+, and Node 18+ installed on your host machine.

```bash
# 1. Clone the repository
git clone https://github.com/LokeshMehar/VOIDemon.git
cd VOIDemon

# 2. Build the Docker Image for the edge nodes
docker-compose up --build -d

# 3. Install backend dependencies and boot Orchestrator
pip install -r requirements.txt
python experiments/orchestrator.py
```

Open two more terminals for the Dashboard:
```bash
# Terminal A (API Gateway)
cd dashboard/api && npm install && npm start

