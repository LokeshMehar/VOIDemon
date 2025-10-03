# API & Communications Reference

VOIDemon relies on a mix of REST APIs for control and configuration, peer-to-peer HTTP for gossip synchronization, and WebSockets for live telemetry streaming.

This document details the communication boundaries between the various components.

---

## 1. API Gateway (Node.js/Express)

The API Gateway runs on **Port 5000** and serves as the primary bridge between the React frontend and the Python backend simulation.

### `GET /api/config`
Retrieves the current simulation parameters by parsing `experiments/config.ini`.
- **Response:** `200 OK` (JSON representation of the INI structure)

### `POST /api/config`
Accepts a JSON payload, serializes it back to INI format, and overwrites `config.ini`.
- **Body:** `{ "VOIDemonParam": { "node_range": "[10]" ... } }`
- **Response:** `200 OK`

### `POST /api/start`
