    }
  }, [gossipKillNode, pendingKills]);

  const onSave = useCallback(() => {
    handleSave(
      msg => setToast({ message: msg, type: "success" }),
      msg => setToast({ message: msg, type: "error" }),
    );
  }, [handleSave]);

  const handleStart = useCallback(async () => {
    setBooting(true);
    try {
      const res = await fetch(`${API_BASE}/start`, { method: "POST" });
      if (!res.ok) throw new Error("Orchestrator unreachable");
      setToast({ message: "🚀 Distributed experiment launched.", type: "success" });
    } catch (err) {
      setToast({ message: err.message, type: "error" });
    } finally {
      setBooting(false);
    }
