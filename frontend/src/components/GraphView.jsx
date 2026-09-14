import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  useReactFlow,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Maximize2,
  Minimize2,
  ZoomIn,
  ZoomOut,
  Compass,
  GitFork,
  Orbit,
  LayoutGrid,
  Workflow,
  Map as MapIcon,
} from 'lucide-react';
import { RectangularNode } from './RectangularNode';
import { NodeDetailModal } from './NodeDetailModal';

const nodeTypes = {
  customWalletNode: RectangularNode,
  investigatedWalletNode: RectangularNode,
  connectedWalletNode: RectangularNode,
  suspect: RectangularNode,
  wallet: RectangularNode,
  known_entity: RectangularNode,
};

const CARD_W = 210;
const CARD_H = 74;
const MIN_V_GAP = 145; // 145px center-to-center leaves > 70px clear vertical space between cards

/**
 * Common Helper: Deduplicate raw nodes and identify the root target.
 */
function prepareNodesAndAdjacency(rawNodes, rawEdges, rootAddress) {
  const nodeMap = new Map();
  (rawNodes || []).forEach((node) => {
    const rawId = node.id || node.address || (node.data && (node.data.fullAddress || node.data.address)) || '';
    const key = rawId.toLowerCase();
    if (key && !nodeMap.has(key)) {
      nodeMap.set(key, { ...node, id: key });
    }
  });

  const cleanRoot = (rootAddress || '').toLowerCase();
  let rootNode = null;

  for (const [key, node] of nodeMap.entries()) {
    const addr = (node.data?.fullAddress || node.address || node.id || '').toLowerCase();
    const isRoot =
      (cleanRoot && addr === cleanRoot) ||
      node.data?.nodeType === 'investigated' ||
      node.data?.depth === 0 ||
      node.data?.role === 'investigated' ||
      node.type === 'investigatedWalletNode' ||
      node.isTarget;
    if (isRoot && !rootNode) {
      rootNode = { ...node, isTarget: true, id: key };
      break;
    }
  }

  if (!rootNode && nodeMap.size > 0) {
    const firstKey = nodeMap.keys().next().value;
    rootNode = { ...nodeMap.get(firstKey), isTarget: true, id: firstKey };
  }

  const rootId = rootNode ? rootNode.id : '';

  const outEdges = new Map();
  const inEdges = new Map();

  (rawEdges || []).forEach((e) => {
    const s = (e.source || '').toLowerCase();
    const t = (e.target || '').toLowerCase();
    if (!outEdges.has(s)) outEdges.set(s, []);
    outEdges.get(s).push({ target: t, edge: e });
    if (!inEdges.has(t)) inEdges.set(t, []);
    inEdges.get(t).push({ source: s, edge: e });
  });

  return { nodeMap, rootNode, rootId, outEdges, inEdges };
}

/**
 * Common Helper: Resolve bounding-box collisions to mathematically guarantee zero overlap.
 */
function resolveCollisions(nodesList) {
  for (let pass = 0; pass < 8; pass++) {
    for (let i = 0; i < nodesList.length; i++) {
      for (let j = i + 1; j < nodesList.length; j++) {
        const A = nodesList[i];
        const B = nodesList[j];
        const dx = Math.abs(A.position.x - B.position.x);
        const dy = Math.abs(A.position.y - B.position.y);

        if (dx < CARD_W + 45 && dy < CARD_H + 40) {
          const overlapY = CARD_H + 40 - dy;
          if (A.position.y <= B.position.y) {
            A.position.y -= overlapY / 2;
            B.position.y += overlapY / 2;
          } else {
            A.position.y += overlapY / 2;
            B.position.y -= overlapY / 2;
          }
        }
      }
    }
  }
}

/**
 * Layout 1: Bilateral Forensic Flow (Horizontal).
 * - Target at center (0, 0).
 * - Incoming senders on Left (Hop 1 at -380px, Hop 2 at -760px).
 * - Outgoing recipients on Right (Hop 1 at +380px, Hop 2 at +760px).
 * - Strict 90-degree orthogonal step edges, aligned sibling branches.
 */
function computeBilateralLayout(rawNodes, rawEdges, rootAddress, targetAsset) {
  const { nodeMap, rootNode, rootId, outEdges, inEdges } = prepareNodesAndAdjacency(rawNodes, rawEdges, rootAddress);
  if (!rootNode) return [];

  const H_STEP = 380;
  const assigned = new Set([rootId]);
  const outgoingByDepth = new Map();
  const parentOf = new Map();

  let currentHop = 1;
  let currentSources = [rootId];

  while (currentSources.length > 0 && currentHop <= 6) {
    const nextTargets = [];
    const hopNodes = [];
    for (const src of currentSources) {
      const edges = outEdges.get(src) || [];
      for (const { target } of edges) {
        if (!assigned.has(target) && nodeMap.has(target)) {
          assigned.add(target);
          nextTargets.push(target);
          parentOf.set(target, src);
          hopNodes.push(nodeMap.get(target));
        }
      }
    }
    if (hopNodes.length > 0) {
      outgoingByDepth.set(currentHop, hopNodes);
      currentSources = nextTargets;
      currentHop++;
    } else {
      break;
    }
  }

  const incomingByDepth = new Map();
  const childOf = new Map();

  currentHop = 1;
  let currentTargets = [rootId];

  while (currentTargets.length > 0 && currentHop <= 6) {
    const nextSources = [];
    const hopNodes = [];
    for (const tgt of currentTargets) {
      const edges = inEdges.get(tgt) || [];
      for (const { source } of edges) {
        if (!assigned.has(source) && nodeMap.has(source)) {
          assigned.add(source);
          nextSources.push(source);
          childOf.set(source, tgt);
          hopNodes.push(nodeMap.get(source));
        }
      }
    }
    if (hopNodes.length > 0) {
      incomingByDepth.set(currentHop, hopNodes);
      currentTargets = nextSources;
      currentHop++;
    } else {
      break;
    }
  }

  for (const [key, node] of nodeMap.entries()) {
    if (!assigned.has(key)) {
      assigned.add(key);
      const role = node.data?.role || node.role;
      if (role === 'incoming') {
        const list = incomingByDepth.get(1) || [];
        list.push(node);
        incomingByDepth.set(1, list);
      } else {
        const list = outgoingByDepth.get(1) || [];
        list.push(node);
        outgoingByDepth.set(1, list);
      }
    }
  }

  const resultNodes = [
    {
      ...rootNode,
      id: rootId,
      position: { x: 0, y: 0 },
      data: {
        ...(rootNode.data || rootNode),
        isTarget: true,
        nodeType: 'investigated',
        depth: 0,
        asset: targetAsset,
      },
    },
  ];

  const layoutSide = (depthMap, isLeft) => {
    const depths = Array.from(depthMap.keys()).sort((a, b) => a - b);
    if (depths.length === 0) return;

    const hop1Nodes = depthMap.get(1) || [];
    const hop2Nodes = depthMap.get(2) || [];
    const hop1Children = new Map();
    hop1Nodes.forEach((n) => hop1Children.set(n.id, []));

    hop2Nodes.forEach((n2) => {
      const p = isLeft ? childOf.get(n2.id) : parentOf.get(n2.id);
      if (p && hop1Children.has(p)) {
        hop1Children.get(p).push(n2);
      } else if (hop1Nodes.length > 0) {
        hop1Children.get(hop1Nodes[0].id).push(n2);
      }
    });

    let totalSlots = 0;
    const branchSlots = [];
    hop1Nodes.forEach((h1) => {
      const children = hop1Children.get(h1.id) || [];
      const slots = Math.max(1, children.length);
      branchSlots.push({ node: h1, children, slots });
      totalSlots += slots;
    });

    let currentSlot = 0;
    const startY = -((totalSlots - 1) * MIN_V_GAP) / 2;

    branchSlots.forEach(({ node: h1, children, slots }) => {
      const branchCenterY = startY + (currentSlot + (slots - 1) / 2) * MIN_V_GAP;
      const col1X = isLeft ? -H_STEP : H_STEP;

      resultNodes.push({
        ...h1,
        id: h1.id,
        position: { x: col1X, y: branchCenterY },
        data: {
          ...(h1.data || h1),
          depth: 1,
          asset: targetAsset,
          role: isLeft ? 'incoming' : 'outgoing',
        },
      });

      const col2X = isLeft ? -2 * H_STEP : 2 * H_STEP;

      if (children.length === 1) {
        resultNodes.push({
          ...children[0],
          id: children[0].id,
          position: { x: col2X, y: branchCenterY },
          data: {
            ...(children[0].data || children[0]),
            depth: 2,
            asset: targetAsset,
            role: isLeft ? 'incoming' : 'outgoing',
          },
        });
      } else if (children.length > 1) {
        children.forEach((c, cIdx) => {
          const childY = startY + (currentSlot + cIdx) * MIN_V_GAP;
          resultNodes.push({
            ...c,
            id: c.id,
            position: { x: col2X, y: childY },
            data: {
              ...(c.data || c),
              depth: 2,
              asset: targetAsset,
              role: isLeft ? 'incoming' : 'outgoing',
            },
          });
        });
      }

      currentSlot += slots;
    });

    depths
      .filter((d) => d > 2)
      .forEach((d) => {
        const list = depthMap.get(d) || [];
        const colX = isLeft ? -d * H_STEP : d * H_STEP;
        const count = list.length;
        list.forEach((node, idx) => {
          const y = (idx - (count - 1) / 2) * MIN_V_GAP;
          resultNodes.push({
            ...node,
            id: node.id,
            position: { x: colX, y },
            data: {
              ...(node.data || node),
              depth: d,
              asset: targetAsset,
              role: isLeft ? 'incoming' : 'outgoing',
            },
          });
        });
      });
  };

  layoutSide(outgoingByDepth, false);
  layoutSide(incomingByDepth, true);
  resolveCollisions(resultNodes);

  return resultNodes;
}

/**
 * Layout 2: Vertical Waterfall / Top-to-Bottom Cascade.
 * - Inflow Senders at Top (Hop 2: -640px, Hop 1: -320px).
 * - Target Root at Center (0, 0).
 * - Outflow Destinations cascading Downwards (Hop 1: +320px, Hop 2: +640px).
 * - Unmatched visual comfort for sequential financial cascades.
 */
function computeWaterfallLayout(rawNodes, rawEdges, rootAddress, targetAsset) {
  const { nodeMap, rootNode, rootId, outEdges, inEdges } = prepareNodesAndAdjacency(rawNodes, rawEdges, rootAddress);
  if (!rootNode) return [];

  const V_STEP = 320;
  const MIN_H_GAP = 250;

  const assigned = new Set([rootId]);
  const outgoingByDepth = new Map();
  const parentOf = new Map();

  let currentHop = 1;
  let currentSources = [rootId];

  while (currentSources.length > 0 && currentHop <= 6) {
    const nextTargets = [];
    const hopNodes = [];
    for (const src of currentSources) {
      const edges = outEdges.get(src) || [];
      for (const { target } of edges) {
        if (!assigned.has(target) && nodeMap.has(target)) {
          assigned.add(target);
          nextTargets.push(target);
          parentOf.set(target, src);
          hopNodes.push(nodeMap.get(target));
        }
      }
    }
    if (hopNodes.length > 0) {
      outgoingByDepth.set(currentHop, hopNodes);
      currentSources = nextTargets;
      currentHop++;
    } else {
      break;
    }
  }

  const incomingByDepth = new Map();
  const childOf = new Map();

  currentHop = 1;
  let currentTargets = [rootId];

  while (currentTargets.length > 0 && currentHop <= 6) {
    const nextSources = [];
    const hopNodes = [];
    for (const tgt of currentTargets) {
      const edges = inEdges.get(tgt) || [];
      for (const { source } of edges) {
        if (!assigned.has(source) && nodeMap.has(source)) {
          assigned.add(source);
          nextSources.push(source);
          childOf.set(source, tgt);
          hopNodes.push(nodeMap.get(source));
        }
      }
    }
    if (hopNodes.length > 0) {
      incomingByDepth.set(currentHop, hopNodes);
      currentTargets = nextSources;
      currentHop++;
    } else {
      break;
    }
  }

  for (const [key, node] of nodeMap.entries()) {
    if (!assigned.has(key)) {
      assigned.add(key);
      const list = outgoingByDepth.get(1) || [];
      list.push(node);
      outgoingByDepth.set(1, list);
    }
  }

  const resultNodes = [
    {
      ...rootNode,
      id: rootId,
      position: { x: 0, y: 0 },
      data: {
        ...(rootNode.data || rootNode),
        isTarget: true,
        nodeType: 'investigated',
        depth: 0,
        asset: targetAsset,
      },
    },
  ];

  const layoutVerticalSide = (depthMap, isTop) => {
    const depths = Array.from(depthMap.keys()).sort((a, b) => a - b);
    if (depths.length === 0) return;

    const hop1Nodes = depthMap.get(1) || [];
    const hop2Nodes = depthMap.get(2) || [];
    const hop1Children = new Map();
    hop1Nodes.forEach((n) => hop1Children.set(n.id, []));

    hop2Nodes.forEach((n2) => {
      const p = isTop ? childOf.get(n2.id) : parentOf.get(n2.id);
      if (p && hop1Children.has(p)) {
        hop1Children.get(p).push(n2);
      } else if (hop1Nodes.length > 0) {
        hop1Children.get(hop1Nodes[0].id).push(n2);
      }
    });

    let totalSlots = 0;
    const branchSlots = [];
    hop1Nodes.forEach((h1) => {
      const children = hop1Children.get(h1.id) || [];
      const slots = Math.max(1, children.length);
      branchSlots.push({ node: h1, children, slots });
      totalSlots += slots;
    });

    let currentSlot = 0;
    const startX = -((totalSlots - 1) * MIN_H_GAP) / 2;

    branchSlots.forEach(({ node: h1, children, slots }) => {
      const branchCenterX = startX + (currentSlot + (slots - 1) / 2) * MIN_H_GAP;
      const row1Y = isTop ? -V_STEP : V_STEP;

      resultNodes.push({
        ...h1,
        id: h1.id,
        position: { x: branchCenterX, y: row1Y },
        data: {
          ...(h1.data || h1),
          depth: 1,
          asset: targetAsset,
          role: isTop ? 'incoming' : 'outgoing',
        },
      });

      const row2Y = isTop ? -2 * V_STEP : 2 * V_STEP;

      if (children.length === 1) {
        resultNodes.push({
          ...children[0],
          id: children[0].id,
          position: { x: branchCenterX, y: row2Y },
          data: {
            ...(children[0].data || children[0]),
            depth: 2,
            asset: targetAsset,
            role: isTop ? 'incoming' : 'outgoing',
          },
        });
      } else if (children.length > 1) {
        children.forEach((c, cIdx) => {
          const childX = startX + (currentSlot + cIdx) * MIN_H_GAP;
          resultNodes.push({
            ...c,
            id: c.id,
            position: { x: childX, y: row2Y },
            data: {
              ...(c.data || c),
              depth: 2,
              asset: targetAsset,
              role: isTop ? 'incoming' : 'outgoing',
            },
          });
        });
      }

      currentSlot += slots;
    });
  };

  layoutVerticalSide(outgoingByDepth, false); // Bottom
  layoutVerticalSide(incomingByDepth, true);  // Top
  resolveCollisions(resultNodes);

  return resultNodes;
}

/**
 * Layout 3: Radial Orbit (Concentric Rings).
 * - Target at center (0, 0).
 * - Hop 1 counterparties arranged on inner orbit (Radius R1 = 360px).
 * - Hop 2 counterparties arranged on outer orbit (Radius R2 = 660px).
 * - Angular sectors align Hop 2 children with their Hop 1 parent angle.
 */
function computeRadialLayout(rawNodes, rawEdges, rootAddress, targetAsset) {
  const { nodeMap, rootNode, rootId, outEdges, inEdges } = prepareNodesAndAdjacency(rawNodes, rawEdges, rootAddress);
  if (!rootNode) return [];

  const R1 = 360;
  const R2 = 660;

  const assigned = new Set([rootId]);
  const hop1Nodes = [];
  const hop2Nodes = [];
  const parentOf = new Map();

  const directNeighbors = new Set();
  (outEdges.get(rootId) || []).forEach((e) => directNeighbors.add(e.target));
  (inEdges.get(rootId) || []).forEach((e) => directNeighbors.add(e.source));

  directNeighbors.forEach((tgt) => {
    if (nodeMap.has(tgt) && !assigned.has(tgt)) {
      assigned.add(tgt);
      hop1Nodes.push(nodeMap.get(tgt));
      parentOf.set(tgt, rootId);
    }
  });

  hop1Nodes.forEach((h1) => {
    const neighbors = [];
    (outEdges.get(h1.id) || []).forEach((e) => neighbors.push(e.target));
    (inEdges.get(h1.id) || []).forEach((e) => neighbors.push(e.source));

    neighbors.forEach((tgt) => {
      if (nodeMap.has(tgt) && !assigned.has(tgt)) {
        assigned.add(tgt);
        hop2Nodes.push(nodeMap.get(tgt));
        parentOf.set(tgt, h1.id);
      }
    });
  });

  for (const [key, node] of nodeMap.entries()) {
    if (!assigned.has(key)) {
      assigned.add(key);
      hop1Nodes.push(node);
    }
  }

  const resultNodes = [
    {
      ...rootNode,
      id: rootId,
      position: { x: 0, y: 0 },
      data: {
        ...(rootNode.data || rootNode),
        isTarget: true,
        nodeType: 'investigated',
        depth: 0,
        asset: targetAsset,
      },
    },
  ];

  const N1 = Math.max(1, hop1Nodes.length);
  const hop1Children = new Map();
  hop1Nodes.forEach((n) => hop1Children.set(n.id, []));

  hop2Nodes.forEach((n2) => {
    const p = parentOf.get(n2.id);
    if (p && hop1Children.has(p)) {
      hop1Children.get(p).push(n2);
    } else if (hop1Nodes.length > 0) {
      hop1Children.get(hop1Nodes[0].id).push(n2);
    }
  });

  hop1Nodes.forEach((h1, idx) => {
    const theta = (2 * Math.PI * idx) / N1 - Math.PI / 2;
    const x1 = Math.round(R1 * Math.cos(theta));
    const y1 = Math.round(R1 * Math.sin(theta));

    resultNodes.push({
      ...h1,
      id: h1.id,
      position: { x: x1, y: y1 },
      data: {
        ...(h1.data || h1),
        depth: 1,
        asset: targetAsset,
      },
    });

    const children = hop1Children.get(h1.id) || [];
    if (children.length === 1) {
      const x2 = Math.round(R2 * Math.cos(theta));
      const y2 = Math.round(R2 * Math.sin(theta));
      resultNodes.push({
        ...children[0],
        id: children[0].id,
        position: { x: x2, y: y2 },
        data: {
          ...(children[0].data || children[0]),
          depth: 2,
          asset: targetAsset,
        },
      });
    } else if (children.length > 1) {
      const fanAngle = Math.min(0.35, (2 * Math.PI) / (N1 * 2));
      children.forEach((c, cIdx) => {
        const phi = theta + (cIdx - (children.length - 1) / 2) * fanAngle;
        const x2 = Math.round(R2 * Math.cos(phi));
        const y2 = Math.round(R2 * Math.sin(phi));
        resultNodes.push({
          ...c,
          id: c.id,
          position: { x: x2, y: y2 },
          data: {
            ...(c.data || c),
            depth: 2,
            asset: targetAsset,
          },
        });
      });
    }
  });

  resolveCollisions(resultNodes);
  return resultNodes;
}

/**
 * Layout 4: Entity Matrix / Forensic Categorical Lanes.
 * - Lane 1 (Left: -420px): Intermediaries, Splitters, Feeders, and Unverified Clusters.
 * - Lane 2 (Center: 0px): Investigated Target Address (Suspect Root).
 * - Lane 3 (Right: +420px): Verified Regulated VASPs & Exchanges (CoinDCX, Binance, etc.).
 * - Lane 4 (Far Right: +840px): External / Low-Risk Counterparties.
 */
function computeEntityLanesLayout(rawNodes, rawEdges, rootAddress, targetAsset) {
  const { nodeMap, rootNode, rootId } = prepareNodesAndAdjacency(rawNodes, rawEdges, rootAddress);
  if (!rootNode) return [];

  const laneIntermediaries = [];
  const laneVasps = [];
  const lanePeers = [];

  for (const [key, node] of nodeMap.entries()) {
    if (key === rootId) continue;

    const data = node.data || node;
    const isVasp = Boolean(
      node.type === 'known_entity' ||
      data.nodeType === 'known_entity' ||
      data.isVasp ||
      (data.entityType && /exchange|vasp|custodial/i.test(data.entityType)) ||
      (data.tags && data.tags.some((t) => /vasp|exchange|coindcx|binance|wazirx|kraken|coinbase/i.test(t))) ||
      (data.entityName && /exchange|vasp|coindcx|binance|wazirx|kraken|coinbase/i.test(data.entityName))
    );

    const riskScore = data.riskScore || 0;
    const isIntermediary =
      !isVasp &&
      (riskScore >= 50 ||
        (data.tags && data.tags.some((t) => /peel|feeder|cluster|split|mixer/i.test(t))) ||
        (data.entityName && /splitter|feeder|cluster/i.test(data.entityName)));

    if (isVasp) {
      laneVasps.push(node);
    } else if (isIntermediary) {
      laneIntermediaries.push(node);
    } else {
      lanePeers.push(node);
    }
  }

  const resultNodes = [
    {
      ...rootNode,
      id: rootId,
      position: { x: 0, y: 0 },
      data: {
        ...(rootNode.data || rootNode),
        isTarget: true,
        nodeType: 'investigated',
        depth: 0,
        asset: targetAsset,
      },
    },
  ];

  const placeLaneColumn = (list, colX) => {
    const count = list.length;
    list.forEach((node, idx) => {
      const y = (idx - (count - 1) / 2) * MIN_V_GAP;
      resultNodes.push({
        ...node,
        id: node.id,
        position: { x: colX, y },
        data: {
          ...(node.data || node),
          asset: targetAsset,
        },
      });
    });
  };

  placeLaneColumn(laneIntermediaries, -420);
  placeLaneColumn(laneVasps, 420);
  placeLaneColumn(lanePeers, 840);

  resolveCollisions(resultNodes);
  return resultNodes;
}

const GraphInner = ({
  initialNodes = [],
  initialEdges = [],
  rootAddress = '',
  targetAsset = 'ETH',
  onTrackNode,
  onInvestigateAddress,
}) => {
  const [layoutMode, setLayoutMode] = useState('bilateral'); // 'bilateral' | 'waterfall' | 'radial' | 'matrix'
  const [showMinimap, setShowMinimap] = useState(false);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [inspectNode, setInspectNode] = useState(null);
  const containerRef = useRef(null);
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  const handleOpenNode = useCallback((nodeData) => {
    setInspectNode(nodeData);
  }, []);

  const handleTrackNode = useCallback(
    (nodeData, onDone) => {
      if (onTrackNode) {
        onTrackNode(nodeData, onDone);
      }
    },
    [onTrackNode]
  );

  const currMeta = useMemo(() => {
    const a = (targetAsset || 'ETH').toUpperCase();
    if (a === 'BTC') return { symbol: 'BTC', name: 'Bitcoin', color: '#f7931a' };
    if (a === 'TRX') return { symbol: 'TRX', name: 'TRON', color: '#eb0029' };
    if (a === 'SOL') return { symbol: 'SOL', name: 'Solana', color: '#14f195' };
    return { symbol: 'ETH', name: 'Ethereum', color: '#0071e3' };
  }, [targetAsset]);

  const totalTracedVolume = useMemo(() => {
    let sum = 0;
    (initialEdges || []).forEach((e) => {
      const val = parseFloat(String(e.data?.totalTransferred || e.totalValue || '0'));
      if (!isNaN(val) && val > 0) sum += val;
    });
    return sum;
  }, [initialEdges]);

  const formattedTotalVolume = useMemo(() => {
    const a = (targetAsset || 'ETH').toUpperCase();
    if (a === 'BTC') return `${totalTracedVolume.toFixed(totalTracedVolume < 0.1 ? 4 : 3)} BTC`;
    if (a === 'TRX') return `${totalTracedVolume.toLocaleString(undefined, { maximumFractionDigits: 1 })} TRX`;
    return `${totalTracedVolume.toFixed(2)} ${a}`;
  }, [totalTracedVolume, targetAsset]);

  // 1. Calculate layout based on chosen pattern mode
  const layoutedNodes = useMemo(() => {
    if (layoutMode === 'waterfall') {
      return computeWaterfallLayout(initialNodes, initialEdges, rootAddress, targetAsset);
    }
    if (layoutMode === 'radial') {
      return computeRadialLayout(initialNodes, initialEdges, rootAddress, targetAsset);
    }
    if (layoutMode === 'matrix') {
      return computeEntityLanesLayout(initialNodes, initialEdges, rootAddress, targetAsset);
    }
    return computeBilateralLayout(initialNodes, initialEdges, rootAddress, targetAsset);
  }, [initialNodes, initialEdges, rootAddress, targetAsset, layoutMode]);

  const nodePosMap = useMemo(() => {
    return new Map(layoutedNodes.map((n) => [n.id.toLowerCase(), n.position]));
  }, [layoutedNodes]);

  // 2. Build base edge definitions with clean 90-degree orthogonal handles
  const baseEdges = useMemo(() => {
    const rawEdges = initialEdges || [];
    return rawEdges.map((e, idx) => {
      const srcId = (e.source || '').toLowerCase();
      const tgtId = (e.target || '').toLowerCase();
      const pSrc = nodePosMap.get(srcId) || { x: 0, y: 0 };
      const pTgt = nodePosMap.get(tgtId) || { x: 0, y: 0 };

      let sourceHandle = 'right';
      let targetHandle = 'left';

      if (layoutMode === 'waterfall') {
        // Vertical Waterfall: Top-to-Bottom
        if (pSrc.y <= pTgt.y) {
          sourceHandle = 'bottom-src';
          targetHandle = 'top';
        } else {
          sourceHandle = 'top-src';
          targetHandle = 'bottom';
        }
      } else if (layoutMode === 'radial') {
        // Radial Orbit: Direction-based
        const dx = pTgt.x - pSrc.x;
        const dy = pTgt.y - pSrc.y;
        if (Math.abs(dx) >= Math.abs(dy)) {
          if (dx >= 0) {
            sourceHandle = 'right';
            targetHandle = 'left';
          } else {
            sourceHandle = 'left-src';
            targetHandle = 'right-tgt';
          }
        } else {
          if (dy >= 0) {
            sourceHandle = 'bottom-src';
            targetHandle = 'top';
          } else {
            sourceHandle = 'top-src';
            targetHandle = 'bottom';
          }
        }
      } else {
        // Bilateral & Matrix 90-degree handle geometry
        if (pSrc.x <= pTgt.x) {
          if (pTgt.y < pSrc.y - 30) {
            sourceHandle = 'right-top';
            targetHandle = 'left-bottom';
          } else if (pTgt.y > pSrc.y + 30) {
            sourceHandle = 'right-bottom';
            targetHandle = 'left-top';
          } else {
            sourceHandle = 'right';
            targetHandle = 'left';
          }
        } else {
          if (pTgt.y < pSrc.y - 30) {
            sourceHandle = 'left-top-src';
            targetHandle = 'right-bottom-tgt';
          } else if (pTgt.y > pSrc.y + 30) {
            sourceHandle = 'left-bottom-src';
            targetHandle = 'right-top-tgt';
          } else {
            sourceHandle = 'left-src';
            targetHandle = 'right-tgt';
          }
        }
      }

      const edgeAsset = (e.asset || e.data?.asset || targetAsset || 'ETH').toUpperCase();
      let rawVal = parseFloat(String(e.data?.totalTransferred || e.totalValue || e.data?.totalValue || e.amount || e.data?.amount || '0'));
      if (isNaN(rawVal)) rawVal = 0;
      let formattedVal = '';
      if (!isNaN(rawVal) && rawVal > 0) {
        if (edgeAsset === 'BTC') {
          if (rawVal < 0.0001) formattedVal = `${Math.round(rawVal * 1e8).toLocaleString()} sat`;
          else formattedVal = `${rawVal.toFixed(rawVal < 0.05 ? 5 : 3)} BTC`;
        } else if (edgeAsset === 'TRX') {
          formattedVal = `${rawVal.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} TRX`;
        } else if (edgeAsset === 'SOL') {
          formattedVal = `${rawVal.toFixed(2)} SOL`;
        } else {
          formattedVal = `${rawVal.toFixed(rawVal < 0.01 ? 4 : 2)} ${edgeAsset}`;
        }
      }

      const cornerOffset = 25 + (idx % 3) * 20;

      return {
        ...e,
        id: e.id || `e-${srcId}-${tgtId}-${idx}`,
        source: srcId,
        target: tgtId,
        sourceHandle,
        targetHandle,
        type: 'smoothstep', // STRICT 90-DEGREE BENDS
        pathOptions: {
          borderRadius: layoutMode === 'radial' ? 12 : 10,
          offset: cornerOffset,
        },
        rawVal,
        formattedVal,
        edgeAsset,
      };
    });
  }, [initialEdges, nodePosMap, targetAsset, layoutMode]);

  // 3. Update ReactFlow nodes when layout or selection changes
  useEffect(() => {
    if (layoutedNodes.length === 0) {
      setNodes([]);
      return;
    }

    const enhancedNodes = layoutedNodes.map((n) => {
      const isNodeSelected = selectedNodeId && n.id.toLowerCase() === selectedNodeId;
      return {
        ...n,
        type: n.type || 'customWalletNode',
        selected: Boolean(isNodeSelected),
        data: {
          ...(n.data || n),
          asset: targetAsset,
          onOpen: handleOpenNode,
          onTrack: handleTrackNode,
        },
      };
    });

    setNodes(enhancedNodes);
  }, [layoutedNodes, selectedNodeId, targetAsset, handleOpenNode, handleTrackNode, setNodes]);

  // 4. Dynamically style edges: Green for Inflow, Red for Outflow relative to selected node
  useEffect(() => {
    if (baseEdges.length === 0) {
      setEdges([]);
      return;
    }

    const styledEdges = baseEdges.map((e) => {
      const srcId = e.source.toLowerCase();
      const tgtId = e.target.toLowerCase();

      const isIncomingToSelected = selectedNodeId && tgtId === selectedNodeId;
      const isOutgoingFromSelected = selectedNodeId && srcId === selectedNodeId;
      const isConnectedToSelected = isIncomingToSelected || isOutgoingFromSelected;
      const isDimmed = selectedNodeId && !isConnectedToSelected;

      let edgeColor = 'rgba(140, 140, 145, 0.45)';
      let edgeWidth = 1.4;
      let markerColor = 'rgba(140, 140, 145, 0.55)';
      let edgeZIndex = 2;
      let labelFill = 'var(--text-secondary)';
      let labelWeight = 500;
      let labelBorder = 'transparent';

      if (isIncomingToSelected) {
        edgeColor = '#34c759'; // VIBRANT GREEN FOR INFLOW
        markerColor = '#34c759';
        edgeWidth = 2.8;
        edgeZIndex = 50;
        labelFill = '#34c759';
        labelWeight = 700;
        labelBorder = 'rgba(52, 199, 89, 0.4)';
      } else if (isOutgoingFromSelected) {
        edgeColor = '#ff453a'; // VIBRANT RED FOR OUTFLOW
        markerColor = '#ff453a';
        edgeWidth = 2.8;
        edgeZIndex = 50;
        labelFill = '#ff453a';
        labelWeight = 700;
        labelBorder = 'rgba(255, 69, 58, 0.4)';
      } else if (isDimmed) {
        edgeColor = 'rgba(140, 140, 145, 0.15)';
        markerColor = 'rgba(140, 140, 145, 0.2)';
        edgeWidth = 1;
        edgeZIndex = 1;
        labelFill = 'rgba(140, 140, 145, 0.3)';
        labelWeight = 400;
      }

      return {
        ...e,
        animated: false,
        zIndex: edgeZIndex,
        label: e.formattedVal || '',
        labelStyle: {
          fontSize: isConnectedToSelected ? 9.5 : 8.5,
          fontFamily: 'ui-monospace, monospace',
          fill: labelFill,
          fontWeight: labelWeight,
        },
        labelBgStyle: {
          fill: 'var(--bg-card)',
          fillOpacity: 0.94,
          rx: 3,
          ry: 3,
          stroke: labelBorder,
          strokeWidth: isConnectedToSelected ? 1 : 0,
        },
        labelBgPadding: [4, 2],
        style: {
          stroke: edgeColor,
          strokeWidth: edgeWidth,
          transition: 'stroke 0.2s ease, stroke-width 0.2s ease',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: isConnectedToSelected ? 10 : 8,
          height: isConnectedToSelected ? 10 : 8,
          color: markerColor,
        },
      };
    });

    setEdges(styledEdges);
  }, [baseEdges, selectedNodeId, setEdges]);

  // 5. Fit view when layout pattern changes or new nodes arrive
  useEffect(() => {
    if (layoutedNodes.length > 0) {
      const timer = setTimeout(() => {
        fitView({ padding: 0.18, duration: 400 });
      }, 90);
      return () => clearTimeout(timer);
    }
  }, [layoutedNodes.length, layoutMode, fitView]);

  // Handle single-click to select node
  const handleNodeClick = useCallback((event, node) => {
    setSelectedNodeId((prev) => {
      const clickedId = node.id.toLowerCase();
      return prev === clickedId ? null : clickedId;
    });
  }, []);

  const handlePaneClick = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (isFullscreen) setIsFullscreen(false);
        if (selectedNodeId) setSelectedNodeId(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen, selectedNodeId]);

  const selectedNodeLabel = useMemo(() => {
    if (!selectedNodeId) return '';
    const n = nodes.find((node) => node.id.toLowerCase() === selectedNodeId);
    if (!n) return selectedNodeId;
    const name = n.data?.entityName || n.data?.name || n.data?.label || selectedNodeId;
    return name.length > 18 ? `${name.slice(0, 8)}...${name.slice(-4)}` : name;
  }, [selectedNodeId, nodes]);

  return (
    <div
      ref={containerRef}
      className={`react-flow-container ${isFullscreen ? 'fullscreen' : ''}`}
      style={{ height: isFullscreen ? '100vh' : 490 }}
    >
      {/* Top Left: 4 Graph Visual Layout Pattern Switcher */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          left: 12,
          zIndex: 10,
        }}
      >
        <div className="graph-layout-picker">
          <button
            type="button"
            className={`layout-pill-btn ${layoutMode === 'bilateral' ? 'active' : ''}`}
            onClick={() => setLayoutMode('bilateral')}
            title="Bilateral Flow: Left (Inflow) · Center (Target) · Right (Outflow) with 90° orthogonal edges"
          >
            <GitFork size={11} />
            <span>Bilateral Flow</span>
          </button>

          <button
            type="button"
            className={`layout-pill-btn ${layoutMode === 'waterfall' ? 'active' : ''}`}
            onClick={() => setLayoutMode('waterfall')}
            title="Vertical Cascade: Top (Inflow) · Center (Target) · Bottom (Outflow) waterfall cascade"
          >
            <Workflow size={11} />
            <span>Vertical Cascade</span>
          </button>

          <button
            type="button"
            className={`layout-pill-btn ${layoutMode === 'radial' ? 'active' : ''}`}
            onClick={() => setLayoutMode('radial')}
            title="Radial Orbit: Concentric Hop 1 and Hop 2 rings radiating from Target Root"
          >
            <Orbit size={11} />
            <span>Radial Orbit</span>
          </button>

          <button
            type="button"
            className={`layout-pill-btn ${layoutMode === 'matrix' ? 'active' : ''}`}
            onClick={() => setLayoutMode('matrix')}
            title="Entity Lanes: Categorical lanes separating Intermediaries, Target, and Verified VASPs"
          >
            <LayoutGrid size={11} />
            <span>Entity Lanes</span>
          </button>
        </div>
      </div>

      {/* Top Right: Status Legend & View Controls */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          right: 12,
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          background: 'var(--bg-glass)',
          backdropFilter: 'var(--blur-standard)',
          WebkitBackdropFilter: 'var(--blur-standard)',
          padding: '4px 10px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-sm)',
        }}
      >
        {/* Active Network & Volume Chip */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 5,
            padding: '2px 8px',
            borderRadius: 'var(--radius-pill)',
            background: `${currMeta.color}15`,
            border: `1px solid ${currMeta.color}35`,
            color: currMeta.color,
            fontWeight: 700,
            fontSize: 10,
            letterSpacing: '0.02em',
          }}
          title={`Active Tracing Network: ${currMeta.name}`}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: currMeta.color }} />
          <span>{currMeta.symbol}</span>
          {totalTracedVolume > 0 && (
            <span style={{ color: 'var(--text-secondary)', fontWeight: 600, fontSize: 9.5 }}>
              ({formattedTotalVolume})
            </span>
          )}
        </div>

        <div style={{ width: 1, height: 14, background: 'var(--border-subtle)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text-secondary)', fontWeight: 500, paddingRight: 4 }}>
          {selectedNodeId ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: '#34c759', fontWeight: 600 }}>● Inflow (Green)</span>
              <span style={{ color: '#ff453a', fontWeight: 600 }}>● Outflow (Red)</span>
              <span style={{ color: 'var(--text-secondary)', fontSize: 9.5, fontFamily: 'ui-monospace, monospace', opacity: 0.85 }}>
                Ref: {selectedNodeLabel}
              </span>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedNodeId(null);
                }}
                style={{
                  background: 'var(--bg-tag)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 4,
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  fontSize: 9.5,
                  padding: '1px 6px',
                  marginLeft: 2,
                }}
              >
                Reset
              </button>
            </span>
          ) : (
            <>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#0071e3' }} />
                Target
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, marginLeft: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#eab308' }} />
                VASP
              </span>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, marginLeft: 4 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34c759' }} />
                Peers
              </span>
            </>
          )}
          <span style={{ marginLeft: 6, color: 'var(--text-tertiary)', borderLeft: '1px solid var(--border-subtle)', paddingLeft: 6 }}>
            {nodes.length} nodes
          </span>
        </div>

        <div style={{ width: 1, height: 14, background: 'var(--border-subtle)' }} />

        <button
          type="button"
          className="apple-icon-btn"
          onClick={() => zoomIn({ duration: 250 })}
          title="Zoom In"
          style={{ width: 24, height: 24 }}
        >
          <ZoomIn size={12} />
        </button>

        <button
          type="button"
          className="apple-icon-btn"
          onClick={() => zoomOut({ duration: 250 })}
          title="Zoom Out"
          style={{ width: 24, height: 24 }}
        >
          <ZoomOut size={12} />
        </button>

        <button
          type="button"
          className="apple-icon-btn"
          onClick={() => fitView({ padding: 0.18, duration: 350 })}
          title="Fit to Center"
          style={{ width: 24, height: 24 }}
        >
          <Compass size={12} />
        </button>

        {/* MiniMap Enable/Disable Toggle (Directly Left to Fullscreen Button) */}
        <button
          type="button"
          className="apple-icon-btn"
          onClick={() => setShowMinimap((prev) => !prev)}
          title={showMinimap ? 'Hide MiniMap' : 'Show MiniMap'}
          style={{
            width: 24,
            height: 24,
            background: showMinimap ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
            color: showMinimap ? '#ffffff' : 'var(--text-secondary)',
            borderColor: showMinimap ? 'var(--accent-primary)' : 'var(--border-subtle)',
          }}
        >
          <MapIcon size={12} />
        </button>

        {/* Fullscreen Button */}
        <button
          type="button"
          className="apple-icon-btn"
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit Fullscreen (Esc)' : 'Fullscreen'}
          style={{ width: 24, height: 24 }}
        >
          {isFullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
        </button>
      </div>

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.08}
        maxZoom={2.5}
        attributionPosition="bottom-left"
      >
        <Background gap={18} size={1} color="rgba(140, 140, 145, 0.12)" />

        {/* Real Working MiniMap */}
        {showMinimap && (
          <MiniMap
            nodeColor={(node) => {
              if (node.data?.isTarget || node.data?.nodeType === 'investigated') return '#0071e3';
              if (node.data?.isVasp || node.data?.nodeType === 'known_entity') return '#eab308';
              const risk = node.data?.riskScore || 0;
              if (risk >= 75) return '#af52de';
              if (risk >= 50) return '#ff453a';
              if (risk >= 20) return '#ff9f0a';
              return '#34c759';
            }}
            nodeStrokeWidth={2}
            nodeBorderRadius={4}
            maskColor="rgba(0, 0, 0, 0.22)"
            style={{
              position: 'absolute',
              right: 12,
              bottom: 12,
              width: 140,
              height: 95,
              borderRadius: 8,
              background: 'var(--bg-glass)',
              backdropFilter: 'var(--blur-standard)',
              WebkitBackdropFilter: 'var(--blur-standard)',
              border: '1px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-md)',
            }}
          />
        )}
      </ReactFlow>

      {/* Node Detail Sheet / Modal (Opened via Info button or Double-Click) */}
      {inspectNode && (
        <NodeDetailModal
          nodeData={inspectNode}
          onClose={() => setInspectNode(null)}
          onTrack={handleTrackNode}
          onInvestigate={onInvestigateAddress}
        />
      )}
    </div>
  );
};

export const GraphView = (props) => {
  return (
    <ReactFlowProvider>
      <GraphInner {...props} />
    </ReactFlowProvider>
  );
};
