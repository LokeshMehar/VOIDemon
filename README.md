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

# Terminal B (React Client)
cd dashboard/client && npm install && npm run dev
```

Finally, open your browser to [**http://localhost:5173**](http://localhost:5173) and click **"BOOT DISTRIBUTED NETWORK"** to watch the real-time simulation begin!

---

## 📈 Analytics Generation

Once a simulation run concludes (the Orchestrator logs will report `OK - Experiment finished`), you can generate beautiful Matplotlib visualizations detailing the VoI efficiency and convergence times:

```bash
python experiments/analytics.py
```

This will parse the SQLite WAL database and output high-res `.png` charts into the `experiments/` directory.

---

## 🤝 Contributing
