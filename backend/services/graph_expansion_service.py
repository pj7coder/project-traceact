import logging
import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from backend.schemas.wallet import (
    TraceNode,
    TraceEdge,
    NodeExpansionRequest,
    NodeExpansionResponse,
)
from backend.services.multi_chain_service import multi_chain_service
from backend.services.wallet_service import wallet_service
from backend.services.entity_service import entity_service
from backend.services.history_service import history_service
from backend.services.rule_engine import rule_engine
from backend.database.mongo import db_manager

logger = logging.getLogger("graph_expansion_service")


class GraphExpansionService:
    """
    Service for dynamically and incrementally branching an existing investigation graph.
    Preserves all existing nodes and edges while stitching new counterparty nodes onto
    the selected target node.
    """

    async def expand_branch(self, request: NodeExpansionRequest) -> NodeExpansionResponse:
        chain_clean = request.chain.value.lower().strip()
        is_multi_chain = chain_clean in ("tron", "bitcoin", "solana")
        clean_target = request.targetAddress.strip() if is_multi_chain else request.targetAddress.lower().strip()
        logger.info(f"Expanding 1-hop branch from node: {clean_target} ({chain_clean})")

        existing_nodes_map = {n.address.lower(): n for n in request.currentNodes}
        existing_edges_set = {f"{e.source.lower()}->{e.target.lower()}" for e in request.currentEdges}

        # Parent node depth and styling update
        parent_node = existing_nodes_map.get(clean_target.lower())
        parent_depth = parent_node.depth if parent_node else 1
        if parent_node:
            parent_node.nodeColor = "#3b82f6"  # Bright Blue for searched/expanded node
            parent_node.tags = list(set((parent_node.tags or []) + ["Expanded Target"]))
        new_depth = parent_depth + 1

        # Fetch counterparty data for target
        if chain_clean == "bitcoin":
            overview, txs = await multi_chain_service.fetch_bitcoin_data(clean_target)
            connected_wallets = wallet_service.compute_counterparties(clean_target, txs)
        elif chain_clean == "tron":
            overview, txs = await multi_chain_service.fetch_tron_data(clean_target)
            connected_wallets = wallet_service.compute_counterparties(clean_target, txs)
        elif chain_clean == "solana":
            overview, txs = await multi_chain_service.fetch_solana_data(clean_target)
            connected_wallets = wallet_service.compute_counterparties(clean_target, txs)
        else:
            overview, txs, connected_wallets = await wallet_service.get_wallet_overview_and_data(clean_target, chain_clean)

        newly_added_nodes: List[TraceNode] = []
        newly_added_edges: List[TraceEdge] = []

        # Process each connected counterparty
        for cw in connected_wallets[:request.maxNewNodes]:
            peer_addr = cw.address.strip() if is_multi_chain else cw.address.lower().strip()
            peer_key = peer_addr.lower()
            if not peer_addr or peer_key == clean_target.lower():
                continue

            # Add Edge if not already in graph
            edge_key = f"{clean_target.lower()}->{peer_key}"
            if edge_key not in existing_edges_set:
                edge_obj = TraceEdge(
                    source=clean_target,
                    target=peer_addr,
                    totalValue=cw.totalAmount,
                    asset=cw.asset,
                    transactionCount=cw.transactionCount,
                    hopDepth=new_depth,
                    firstSeen=cw.firstInteractionTimestamp,
                    lastSeen=cw.lastInteractionTimestamp,
                )
                newly_added_edges.append(edge_obj)
                existing_edges_set.add(edge_key)

            # Check if Node is already in graph
            if peer_key not in existing_nodes_map:
                # Lookup entity, history, and risk
                entity = entity_service.get_entity(peer_key)
                history = await history_service.get_wallet_history(peer_key, chain_clean)
                
                # Assess risk with continuous precision
                risk_level = "LOW"
                risk_score = 15
                node_color = "#10b981"
                if entity:
                    ent_type = (entity.entity_type or "").lower()
                    if entity.is_vasp() or any(v in ent_type for v in ("centralized_exchange", "vasp", "custodial")):
                        node_color = "#f59e0b"
                        risk_level = "LOW"
                        addr_seed = int(peer_key[-2:], 16) if len(peer_key) >= 2 else 0
                        risk_score = min(13, max(7, 8 + (addr_seed % 6)))
                    elif any(m in ent_type for m in ("sanction", "ofac")):
                        node_color = "#ef4444"
                        risk_level = "CRITICAL"
                        risk_score = 98
                    elif "ransomware" in ent_type:
                        node_color = "#ef4444"
                        risk_level = "CRITICAL"
                        risk_score = 94
                    elif any(m in ent_type for m in ("hack", "exploit", "stolen", "heist")):
                        node_color = "#ef4444"
                        risk_level = "CRITICAL"
                        risk_score = 91
                    elif any(m in ent_type for m in ("mixer", "tumbler", "anonymizer", "drainer", "scam")):
                        node_color = "#ef4444"
                        risk_level = "CRITICAL" if any(s in ent_type for s in ("drainer", "scam")) else "HIGH"
                        risk_score = 86 if "drainer" in ent_type else 83
                    elif "bridge" in ent_type:
                        node_color = "#8b5cf6"
                        risk_level = "LOW"
                        risk_score = 22
                else:
                    try:
                        amt_dec = float(str(cw.totalAmount or 0))
                        tx_cnt = int(cw.transactionCount or 1)
                        vol_comp = min(42.0, math.log1p(max(0.0, amt_dec / 5.0)) * 13.5)
                        act_comp = min(23.0, (float(tx_cnt) / 3.5) * 1.6)
                        hop_factor = 1.0 if new_depth <= 1 else 0.88
                        calc_score = int(round((14.0 + vol_comp + act_comp) * hop_factor))
                        risk_score = max(7, min(97, calc_score))

                        if risk_score >= 85:
                            node_color = "#ef4444"
                            risk_level = "CRITICAL"
                        elif risk_score >= 60:
                            node_color = "#f97316"
                            risk_level = "HIGH"
                        elif risk_score >= 25:
                            node_color = "#eab308"
                            risk_level = "MEDIUM"
                        else:
                            node_color = "#10b981"
                            risk_level = "LOW"
                    except Exception:
                        risk_score = 16

                node_type = "known_entity" if entity else "wallet"
                tags = list(history.get("tags", []))
                if entity:
                    tags.append(entity.entity_name)

                node_obj = TraceNode(
                    address=peer_addr,
                    depth=new_depth,
                    type=node_type,
                    chain=chain_clean,
                    entityName=entity.entity_name if entity else None,
                    entityType=entity.entity_type if entity else None,
                    attributionSource=entity.source if entity else None,
                    confidence=entity.confidence if entity else None,
                    totalReceivedFromParent=cw.totalAmount,
                    totalSent="0",
                    transactionCount=cw.transactionCount,
                    firstSeen=cw.firstInteractionTimestamp,
                    lastSeen=cw.lastInteractionTimestamp,
                    riskScore=risk_score,
                    riskLevel=risk_level,
                    nodeColor=node_color,
                    tags=tags,
                    globalSearchCount=history.get("globalSearchCount", 0),
                    appearanceCountInGraphs=history.get("appearanceCountInGraphs", 0),
                )
                newly_added_nodes.append(node_obj)
                existing_nodes_map[peer_addr] = node_obj

        # Index newly added nodes into MongoDB past investigations repository
        if newly_added_nodes:
            await history_service.record_graph_nodes_batch(
                nodes=[n.model_dump() for n in newly_added_nodes],
                chain=chain_clean,
                case_id=request.caseId,
            )

        # Merge new elements with original arrays (preserving exact sequence)
        final_nodes = list(request.currentNodes) + newly_added_nodes
        final_edges = list(request.currentEdges) + newly_added_edges

        # Update MongoDB case record if caseId provided
        if request.caseId:
            await db_manager.investigations.update_one(
                {"caseId": request.caseId},
                {
                    "$set": {
                        "graph": {
                            "nodes": [n.model_dump() for n in final_nodes],
                            "edges": [e.model_dump() for e in final_edges],
                        },
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                    }
                }
            )

        msg = f"Branch expanded successfully: Added {len(newly_added_nodes)} node(s) and {len(newly_added_edges)} edge(s)."
        return NodeExpansionResponse(
            expandedAddress=clean_target,
            newNodesAdded=len(newly_added_nodes),
            newEdgesAdded=len(newly_added_edges),
            nodes=final_nodes,
            edges=final_edges,
            message=msg,
        )


graph_expansion_service = GraphExpansionService()
