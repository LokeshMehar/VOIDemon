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

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting a pull request.

---

## 📄 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.<div align="center">

# VOIDemon
### Value-of-Information (VoI) Optimized Distributed Edge Monitoring

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![Node.js](https://img.shields.io/badge/Node.js-Express-339933?style=flat-square&logo=nodedotjs&logoColor=white)](https://nodejs.org)
[![SQLite](https://img.shields.io/badge/SQLite-WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat-square)](LICENSE)

**VOIDemon** is a decentralized, self-adaptive, and resource-aware monitoring framework designed for volatile edge computing environments. By integrating a stochastic gossip protocol with a novel priority-based metric filtering mechanism, VOIDemon drastically reduces network bandwidth consumption and extends IoT device battery life by over 50%, completely eliminating the need for centralized monitoring bottlenecks.

[Explore the Documentation](docs/) · [Report Bug](https://github.com/LokeshMehar/VOIDemon/issues) · [Request Feature](https://github.com/LokeshMehar/VOIDemon/issues)

</div>

---

## 📖 The Problem with Centralized Monitoring

The proliferation of the Internet of Things (IoT) has driven the adoption of edge computing to process data near its source. However, traditional monitoring systems (like Prometheus or Datadog) rely on a **centralized architecture**. In the resource-constrained context of the edge—characterized by network volatility, high latency, and limited battery life—these centralized servers create severe performance bottlenecks and single points of failure.

Decentralized peer-to-peer (P2P) systems like Epidemic/Gossip protocols solve the single-point-of-failure problem, but they are notoriously resource-intensive, continuously blasting full state payloads across the network and draining mobile batteries.

## 🚀 The VOIDemon Solution

**VOIDemon** bridges this gap by introducing **Value of Information (VoI)** into the decentralized fabric. 

Instead of broadcasting every metric on every tick, VOIDemon assigns priority tiers (HIGH, MEDIUM, LOW) to system metrics. The engine evaluates the mathematical *value* of the data: Has it changed significantly? Is it critical for real-time operations? Redundant, static information (like storage capacity) is heavily suppressed, while vital performance data (like CPU spikes) bypasses the filters.

### 🌟 Key Performance Outcomes
- **~60% Reduction in Network Overhead:** Bandwidth is conserved by intelligently suppressing up to 82% of static metric transmissions.
- **+52.5% Extended Battery Life:** By eliminating wireless radio transmissions for redundant data, projected device operational lifetime jumps significantly.
- **100% Resilience:** Leaderless Quorum Consensus (LQC) ensures rapid failure detection without a central coordinator.

---

## 🏗️ System Architecture

<p align="center">
  <img src="docs/architecture.svg" alt="VOIDemon System Architecture" width="100%"/>
</p>

---

## 📚 Comprehensive Documentation

To understand the deep technical implementation and theoretical models backing VOIDemon, please explore our comprehensive documentation directory:

| Topic | Description |
|---|---|
| [**Theory & Concepts**](docs/theory_and_concepts.md) | Deep dive into the Stochastic Gossip push-pull protocol, the VoI filtering algorithm, math models, and Leaderless Quorum Consensus. |
| [**System Architecture**](docs/system_architecture.md) | A complete breakdown of the 4-layer stack: Node Cluster, Python Orchestrator, Node.js API Gateway, and React Dashboard. |
| [**Engineering Paradigms**](docs/codingParadigm.md) | Detailed Q&A covering the massive architectural trade-offs, implementation choices, and system-level preferences (Docker, SQLite WAL, React RAF, etc.). |
| [**API Reference**](docs/api_reference.md) | Detailed documentation on the REST endpoints and WebSocket (Socket.IO) event streams. |
| [**Getting Started**](docs/getting_started.md) | Step-by-step instructions for installing dependencies, configuring simulations, and booting the Dockerized network. |

---

## 📂 Project Structure

