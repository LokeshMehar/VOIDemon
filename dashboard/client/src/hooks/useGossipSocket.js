      node.appState = {
        ...(node.appState || {}),
        ...fieldStats,
        cpu:     p.cpu     === "not_updated" ? (node.appState?.cpu     ?? "not_updated") : p.cpu,
        memory:  p.memory  === "not_updated" ? (node.appState?.memory  ?? "not_updated") : p.memory,
        network: p.network === "not_updated" ? (node.appState?.network ?? "not_updated") : p.network,
        storage: p.storage === "not_updated" ? (node.appState?.storage ?? "not_updated") : p.storage,
        _isCpuFiltered:     p.cpu     === "not_updated",
        _isMemoryFiltered:  p.memory  === "not_updated",
        _isNetworkFiltered: p.network === "not_updated",
        _isStorageFiltered: p.storage === "not_updated",
      };

      // ── Process peer topology ─────────────────────────────────────────────
      const peers      = p.data_stored_in_node || [];
      const peerStatus = p.peer_status || {};

      peers.forEach(peerKey => {
        if (typeof peerKey !== "string" || peerKey === senderKey) return;

        let targetDead = false;
        if (peerStatus[peerKey]) {
          const stats = peerStatus[peerKey];
          if (stats.failCount > 0) {
            const curStrikes = strikesMapRef.current.get(peerKey) || 0;
            strikesMapRef.current.set(peerKey, Math.max(curStrikes, stats.failCount));
          }
          if (stats.isAlive === false || stats.failCount >= 3) {
            targetDead = true;
          }
        }

        if (!nodesMap.has(peerKey)) {
          nodesMap.set(peerKey, {
            id: peerKey, label: peerKey, ic: 0, node_count: p.node_count || 1,
            round: 0, nd: 0, rm: 0, bytes_of_data: 0, lastSeen: now,
            x: (Math.random() - 0.5) * 100, y: (Math.random() - 0.5) * 100,
            appState: {}, isDead: false, totalMessages: 0, filteredMessages: 0,
            strikes: 0,
          });
        }

        const edgeA = `${senderKey}->${peerKey}`;
        const edgeB = `${peerKey}->${senderKey}`;

        if (targetDead) {
          linksSet.delete(edgeA);
          linksSet.delete(edgeB);
        } else {
          if (!linksSet.has(edgeA) && !linksSet.has(edgeB)) linksSet.add(edgeA);
        }
      });

      // ── Propagate strike counts; mark nodes dead ──────────────────────────
      let newKillsDetected = false;
      nodesMap.forEach(n => {
        const strikes = strikesMapRef.current.get(n.id) || 0;
        n.strikes = strikes;
        if (strikes >= 3 && !killedSet.has(n.id)) {
          killedSet.add(n.id);
          n.isDead = true;
          newKillsDetected = true;
        }
      });

      if (newKillsDetected) {
        // Update React state for killedNodes (triggers re-render for badges etc.)
        const nextSet = new Set(killedSet);
        killedNodesRef.current = nextSet;
        setKilledNodes(nextSet);
      }

      // Schedule a batched flush instead of setState on every message
      scheduleFlush();
    });

    return () => {
      socket.disconnect();
      if (rafHandleRef.current) cancelAnimationFrame(rafHandleRef.current);
    };
