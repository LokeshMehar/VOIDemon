
    if (body !== "TERMINATED" && !response.ok) {
      throw new Error(`Node returned unexpected status ${response.status}: ${body}`);
    }

    // Notify the Python orchestrator to immediately lower the convergence target
    try {
      await fetch("http://localhost:4000/notify_node_killed", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ip: targetIp, port: targetPort }),
        signal: AbortSignal.timeout(2000)
      });
    } catch (_) { /* orchestrator notification is best-effort */ }

    console.log(`[Chaos Engine] Node ${targetIp}:${targetPort} terminated successfully.`);
    res.json({ success: true, ip: targetIp, port: targetPort });
  } catch (err) {
    console.error(`[Chaos Engine] Soft-kill failed for ${targetIp}:${targetPort}:`, err.message);
    res.status(500).json({ error: `Chaos Engine Error: Could not reach node at ${targetIp}:${targetPort}. Is the experiment running?`, details: err.message });
  }
});



// ---------------------------------------------------------------------------
// Start server (use server.listen, NOT app.listen, so socket.io binds too)
// ---------------------------------------------------------------------------
server.listen(PORT, () => {
  console.log(`VOIDemon Control Center API running on http://localhost:${PORT}`);
  console.log(`Socket.io attached and listening for connections`);
  console.log(`Config path: ${CONFIG_PATH}`);
});
const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const ini = require("ini");
const http = require("http");
const { Server } = require("socket.io");
const { exec } = require("child_process");

const app = express();
const PORT = 5000;

// Create HTTP server and attach Socket.io
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"],
  },
});

// Path to config.ini relative to this file (dashboard/api/ -> experiments/)
const CONFIG_PATH = path.resolve(__dirname, "../../experiments/config.ini");

app.use(cors());
app.use(express.json());

// ---------------------------------------------------------------------------
// Socket.io connection handling
// ---------------------------------------------------------------------------
io.on("connection", (socket) => {
  console.log(`[Socket.io] Client connected: ${socket.id}`);
  socket.on("disconnect", () => {
    console.log(`[Socket.io] Client disconnected: ${socket.id}`);
  });
});

// ---------------------------------------------------------------------------
