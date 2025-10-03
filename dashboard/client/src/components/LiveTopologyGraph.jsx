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

