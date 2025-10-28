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
