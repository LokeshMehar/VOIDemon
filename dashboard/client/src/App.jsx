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
                <div className="absolute inset-0 bg-indigo-500/40 rounded-2xl blur-md" />
                <div className="relative w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center shadow-xl">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-black tracking-tight text-white leading-none">
                  VOID<span className="gradient-text-indigo">DEMON</span>
                </h1>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.25em] mt-0.5">Control Center</p>
              </div>
            </div>
            <p className="text-slate-500 text-sm leading-relaxed max-w-sm">
              Distributed monitoring via VoI-prioritized gossip protocol with real-time fault detection.
            </p>
          </div>

          {/* Status pill + efficiency badge */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <GlobalEfficiencyBadge savingsPercent={globalSavingsPercent} />
            <div className="glass px-4 py-2 rounded-xl flex items-center gap-2.5">
              <div className="relative">
                <div className="absolute inset-0 bg-emerald-500 rounded-full animate-ping-slow opacity-60" />
                <div className="relative w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Stream <span className="text-slate-100">Live</span>
              </span>
            </div>
          </div>
        </header>

        {/* ── Stats Bar ────────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Active Nodes"
            value={activeNodeCount}
            sub={killedNodes.size > 0 ? `${killedNodes.size} terminated` : "All healthy"}
            accentClass="bg-indigo-500/10 text-indigo-400"
            iconPath="M5 12h14M12 5l7 7-7 7"
/** Extract the IP portion from an "ip:port" string. */
function ipOnly(nodeId) {
  return nodeId ? nodeId.split(":")[0] : nodeId;
}

/** Format bytes to a human-readable string. */
function formatBytes(bytes) {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

// ── Stat Card component ────────────────────────────────────────────────────────
function StatCard({ label, value, sub, accentClass, iconPath, delay = 0 }) {
  return (
    <div
      className={`fade-in glass rounded-2xl p-5 flex items-start gap-4 border hover:border-white/10 transition-all duration-300 group`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${accentClass} transition-transform duration-300 group-hover:scale-110`}>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d={iconPath} />
        </svg>
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-1">{label}</p>
        <p className="text-xl font-mono font-black text-white truncate stat-value">{value}</p>
        {sub && <p className="text-[10px] text-slate-600 font-medium mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function App() {
  // ── Hooks ───────────────────────────────────────────────────────────────────
  const {
    graphData,
    killedNodes,
    globalTotalMessages,
    globalFilteredMessages,
    killNode: gossipKillNode,
  } = useGossipSocket();

  const {
    config,
    loading,
    fetchError,
    saving,
    fetchConfig,
    handleChange,
    handleSave,
  } = useConfig();

  // ── Local UI state ───────────────────────────────────────────────────────────
  const [booting, setBooting] = useState(false);
  const [toast, setToast] = useState(null);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [pendingKills, setPendingKills] = useState(new Set());

  // Fetch config on mount
  useEffect(() => { fetchConfig(); }, [fetchConfig]);

