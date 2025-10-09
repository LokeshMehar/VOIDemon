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

  }, []);

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#020617] text-slate-100 selection:bg-violet-500/30 overflow-x-hidden">

      {/* ── Ambient background glows ─────────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 right-0 w-[700px] h-[700px] bg-indigo-600/10 rounded-full blur-[140px] -translate-y-1/3 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-emerald-600/8 rounded-full blur-[140px] translate-y-1/3 -translate-x-1/3" />
        <div className="absolute top-1/2 left-1/2 w-[400px] h-[400px] bg-violet-600/5 rounded-full blur-[100px] -translate-x-1/2 -translate-y-1/2" />
      </div>

      <div className="relative max-w-6xl mx-auto px-6 lg:px-8 py-10 flex flex-col gap-10">

        {/* ── Header ───────────────────────────────────────────────────────────── */}
        <header className="fade-in flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div>
            {/* Logo + Name */}
            <div className="flex items-center gap-3 mb-3">
              <div className="relative">
