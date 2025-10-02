          onClick={onClose}
          className="mt-0.5 w-8 h-8 rounded-xl flex items-center justify-center text-slate-600 hover:text-white hover:bg-white/8 transition-all border border-transparent hover:border-white/10 active:scale-90"
          aria-label="Close node inspector"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* ── Body ──────────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-5 space-y-6">

        {/* Resources */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-[9px] font-black text-slate-500 uppercase tracking-[0.25em]">System Resources</h4>
            {anyFiltered && (
              <span className="text-[9px] text-amber-500/80 font-bold flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-amber-500 animate-pulse" />
                VoI Active
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <ResourceCard label="CPU"      value={cpu}     unit="%" isFiltered={isCpuFiltered}     icon={mkIcon(icons.cpu)}  />
            <ResourceCard label="Memory"   value={memory}  unit="%" isFiltered={isMemoryFiltered}  icon={mkIcon(icons.mem)}  />
            <ResourceCard label="Network"  value={network} unit="Mbps" isFiltered={isNetworkFiltered} icon={mkIcon(icons.net)}  />
            <ResourceCard label="Storage"  value={storage} unit="%" isFiltered={isStorageFiltered} icon={mkIcon(icons.disk)} />
          </div>
        </section>

        {/* Convergence */}
        <section className="bg-slate-900/50 rounded-2xl p-4 border border-white/5 space-y-4">
          <h4 className="text-[9px] font-black text-indigo-400 uppercase tracking-[0.25em]">Gossip Convergence</h4>

          {/* Progress */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-[10px] text-slate-500">Progress</span>
              <span className="text-[10px] font-mono font-bold text-white">{Math.min(node.ic ?? 0, activeNodeCount)} / {activeNodeCount}</span>
            </div>
            <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full bar-animate transition-all duration-500 ${isConverged ? "bg-emerald-500" : "bg-indigo-500"}`}
                style={{ width: `${convergePct}%` }}
              />
            </div>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: "Round",     value: node.round ?? 0 },
              { label: "Peers",     value: node.nd ?? 0    },
              { label: "Messages",  value: nodeTotal         },
              { label: "Filtered",  value: nodeFiltered      },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-800/40 rounded-xl p-3 border border-white/[0.04]">
                <p className="text-[9px] font-bold text-slate-600 uppercase tracking-wider mb-1">{label}</p>
                <p className="text-sm font-mono font-black text-white">{value.toLocaleString()}</p>
              </div>
            ))}
          </div>
        </section>

      </div>

      {/* ── Footer ────────────────────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-t border-white/5 bg-black/20">
        <div className="flex items-center justify-between">
          <span className="text-[9px] font-mono text-slate-700">PORT: {nodeId.split(":").pop()}</span>
          <div className="flex items-center gap-1.5">
            <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[9px] font-mono text-emerald-700 font-bold">LIVE</span>
          </div>
        </div>
      </div>
import React from "react";
import { ResourceCard } from "./ResourceCard";

/**
 * NodeInspector — slide-in right-panel showing real-time diagnostics
 * for the selected node.
 *
 * Props:
 *   nodeId            — "ip:port" string
 *   nodesInfo         — Object map of nodeId → node data (from graphData.nodes_info)
 *   onClose           — callback to deselect
 *   killedNodes       — Set<string> of manually/auto-killed node IDs
 */
export function NodeInspector({ nodeId, nodesInfo, onClose, killedNodes }) {
  const node = nodesInfo[nodeId];
  if (!node) return null;

  const appState = node.appState || {};
  const isKilled = node.isDead || killedNodes.has(nodeId);

  const cpu     = appState.cpu     ?? "—";
  const memory  = appState.memory  ?? "—";
  const network = appState.network ?? "—";
  const storage = appState.storage ?? "—";

  const isCpuFiltered     = appState._isCpuFiltered;
    </div>
  );
}
