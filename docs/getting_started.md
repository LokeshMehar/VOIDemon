# Getting Started Guide

This guide will walk you through setting up, configuring, and running the VOIDemon decentralized monitoring cluster on your local machine.

## Prerequisites

Because the system simulates a real edge environment, you need the following dependencies installed on your host machine:

- **Docker** and **Docker Compose** (Required to spin up the isolated gossip nodes)
- **Python 3.9+** (Required for the Orchestrator and Analytics scripts)
- **Node.js 18+** & **npm** (Required for the API Gateway and React Dashboard)

---

## 1. Installation

Clone the repository and install the dependencies for all three layers.

```bash
git clone https://github.com/LokeshMehar/VOIDemon.git
cd VOIDemon

# 1. Install Orchestrator Python Dependencies
pip install -r requirements.txt

# 2. Install API Gateway Node Dependencies
cd dashboard/api
npm install
cd ../..

# 3. Install React Client Dependencies
cd dashboard/client
npm install
cd ../..
```

---

## 2. Configuration (`experiments/config.ini`)

Before running a simulation, you can tweak the environment parameters. The main configurations are found in `experiments/config.ini`:

```ini
[VOIDemonParam]
node_range       = "[10]"    ; The number of Docker nodes to spawn. E.g., "[10, 20]" to run sequential tests.
gossip_rate      = 3         ; Fan-out factor: How many random peers a node contacts per round.
runs             = 1         ; How many times to repeat the experiment for statistical accuracy.

[MetricPriority]
cpu              = 1         ; HIGH Priority (Always sent)
network          = 3         ; MEDIUM Priority
memory           = 5         ; LOW Priority (Heavily filtered)
storage          = 10        ; LOWEST Priority (Almost never sent unless significantly changed)
```

*(Note: Higher priority numbers mean the metric is transmitted less frequently, optimizing bandwidth based on the Value of Information).*

---

## 3. Running the System

You must start the components in this specific order.

### Step 3.1: Build the Docker Base Image
The nodes run inside a custom Docker image. Build it first:
```bash
docker-compose up --build -d
```
*This command parses `docker-compose.yml`, builds the `voidemon-node` image, and creates an internal bridge network named `test`.*

### Step 3.2: Start the Python Orchestrator
Open a new terminal at the project root:
```bash
python experiments/orchestrator.py
```
*The orchestrator will boot up on port 4000 and wait for the start signal.*

### Step 3.3: Start the API Gateway
