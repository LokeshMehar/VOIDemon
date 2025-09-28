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
