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
/**
 * App.jsx — VOIDemon Control Center
 *
 * All heavy lifting is delegated to:
 *   hooks/useGossipSocket  — WebSocket lifecycle, graph state
 *   hooks/useConfig        — config fetch / save
 *   components/*           — pure UI components
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";

import { useGossipSocket } from "./hooks/useGossipSocket";
import { useConfig } from "./hooks/useConfig";
import { Toast } from "./components/Toast";
import { Spinner, GlobalEfficiencyBadge } from "./components/Spinner";
import { SectionCard } from "./components/SectionCard";
import { NodeInspector } from "./components/NodeInspector";
import { LiveTopologyGraph } from "./components/LiveTopologyGraph";

const API_BASE = (import.meta.env.VITE_API_BASE || "") + "/api";

