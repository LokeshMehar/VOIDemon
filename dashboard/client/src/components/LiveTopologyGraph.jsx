import React, { useRef, useEffect, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";

/**
 * LiveTopologyGraph — renders the force-directed network graph and the
 * Live Diagnostic Feed table below it.
 *
 * Props:
 *   graphData      — { nodes, links, nodes_info }
 *   onSelectNode   — callback(nodeId) to open the inspector panel
 *   killedNodes    — Set<string> of dead node IDs
 *   onKillNode     — callback(nodeId) to trigger Chaos Engine kill
 *   selectedNodeId — currently selected node ID or null
 */
export function LiveTopologyGraph({ graphData, onSelectNode, killedNodes, pendingKills, onKillNode, selectedNodeId }) {
  const graphRef = useRef();

  // Auto-fit the graph whenever the node count changes
  useEffect(() => {
    let timerId = null;
    if (graphRef.current && graphData.nodes.length > 0) {
      const fg = graphRef.current;
      const centerForce = fg.d3Force("center");
      if (centerForce) centerForce.x(0).y(0);

      timerId = setTimeout(() => {
        fg.zoomToFit(400, 100);
      }, 150);
    }
    return () => {
      if (timerId) clearTimeout(timerId);
    };
  }, [graphData.nodes.length]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const isKilled   = killedNodes.has(node.id);
    const isSelected = selectedNodeId === node.id;
    const isPending  = pendingKills?.has(node.id);
    const r          = isSelected ? 11 : 8;
    const { ic, node_count } = node;
    const activeNodeCount = node.active_target || Math.max((node_count || 1) - killedNodes.size, 1);

    let color = "#64748b";
    if (isKilled)       color = "#475569";
    else if (isPending) color = "#f59e0b";
    else if (ic > 0)    color = ic >= activeNodeCount ? "#10b981" : "#6366f1";

    // Outer glow ring (selected or converged)
    if (!isKilled) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, r + 6, 0, 2 * Math.PI);
      ctx.fillStyle = isSelected ? `${color}30` : `${color}15`;
      ctx.fill();
    }

    // Node disc
    ctx.beginPath();
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
    ctx.fillStyle = isKilled ? "transparent" : color;
    ctx.fill();

    // Border
    ctx.strokeStyle = isKilled ? "#ef444440" : isSelected ? "#fff" : `${color}80`;
    ctx.lineWidth   = isKilled ? 1.5 : isSelected ? 2.5 : 1.5;
    ctx.setLineDash(isKilled ? [3, 2] : []);
    ctx.stroke();
    ctx.setLineDash([]);

