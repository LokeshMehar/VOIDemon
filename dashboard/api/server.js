
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
