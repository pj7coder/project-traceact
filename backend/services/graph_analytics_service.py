import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from decimal import Decimal
import networkx as nx

logger = logging.getLogger("graph_analytics_service")


class GraphAnalyticsService:
    """
    Forensic Graph Analytics Engine powered by NetworkX.
    Extracts topological properties, betweenness centrality, PageRank, wash-trading cycles,
    and identifies critical money-mule bottlenecks to boost attribution confidence
    and drive deterministic step-wise investigative playbooks.
    """

    @staticmethod
    def _to_decimal(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    def build_networkx_graph(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> nx.DiGraph:
        """
        Constructs a directed NetworkX graph with node and edge attributes.
        """
        G = nx.DiGraph()

        for node in nodes:
            # Support both flat dicts and React Flow node format ({ id, data: {...} })
            addr = node.get("address") or node.get("id") or ""
            if not addr:
                continue
            data = node.get("data", {})
            if isinstance(data, dict):
                entity_name = node.get("entityName") or data.get("entityName") or ""
                entity_type = node.get("entityType") or data.get("entityType") or "wallet"
                risk_score = node.get("riskScore", data.get("riskScore", 0))
                depth = node.get("depth", data.get("depth", 0))
            else:
                entity_name = node.get("entityName", "")
                entity_type = node.get("entityType", "wallet")
                risk_score = node.get("riskScore", 0)
                depth = node.get("depth", 0)

            G.add_node(
                addr.lower().strip(),
                address=addr.strip(),
                entity_name=entity_name,
                entity_type=entity_type,
                risk_score=risk_score,
                depth=depth,
            )

        for edge in edges:
            src = (edge.get("source") or "").lower().strip()
            tgt = (edge.get("target") or "").lower().strip()
            if not src or not tgt:
                continue

            val_str = edge.get("totalValue") or edge.get("value") or "0"
            tx_count = edge.get("transactionCount", 1)
            hop_depth = edge.get("hopDepth", 1)
            tx_hashes = edge.get("transactionHashes", [])

            G.add_edge(
                src,
                tgt,
                weight=float(self._to_decimal(val_str)),
                total_value=str(val_str),
                tx_count=tx_count,
                hop_depth=hop_depth,
                tx_hashes=tx_hashes,
            )

        return G

    def analyze_network_topology(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        target_address: str,
        vasp_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Performs deep topological analysis on the transaction graph using NetworkX.
        Returns centrality metrics, money mule bottlenecks, wash-trading cycles,
        and confidence enhancement modifiers.
        """
        clean_target = (target_address or "").lower().strip()
        G = self.build_networkx_graph(nodes, edges)

        node_count = G.number_of_nodes()
        edge_count = G.number_of_edges()

        if node_count == 0:
            return self._empty_analytics_result(clean_target)

        # 1. Centrality Metrics
        try:
            betweenness = nx.betweenness_centrality(G, normalized=True, weight=None)
        except Exception as e:
            logger.warning(f"Error computing betweenness centrality: {e}")
            betweenness = {n: 0.0 for n in G.nodes()}

        try:
            pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
        except Exception:
            pagerank = {n: 1.0 / max(1, node_count) for n in G.nodes()}

        try:
            in_degree_cent = nx.in_degree_centrality(G)
            out_degree_cent = nx.out_degree_centrality(G)
        except Exception:
            in_degree_cent = {n: 0.0 for n in G.nodes()}
            out_degree_cent = {n: 0.0 for n in G.nodes()}

        # 2. Cycle Detection (Wash-trading / Circular fund loops)
        detected_cycles = []
        try:
            raw_cycles = list(nx.simple_cycles(G))
            for c in raw_cycles[:10]:  # Cap at 10 cycles for performance
                detected_cycles.append([G.nodes[n].get("address", n) for n in c])
        except Exception as e:
            logger.warning(f"Error checking simple cycles: {e}")
            detected_cycles = []

        # 3. Connected Components (Syndicate Cluster Groups)
        try:
            weak_components = list(nx.weakly_connected_components(G))
            syndicate_clusters = []
            for idx, comp in enumerate(weak_components):
                if len(comp) > 1:
                    syndicate_clusters.append({
                        "clusterId": f"NETX-CL-{idx+1:02d}",
                        "nodeCount": len(comp),
                        "addresses": [G.nodes[n].get("address", n) for n in comp],
                    })
        except Exception:
            syndicate_clusters = []

        # 4. Critical Money Mule / Bottleneck Identification
        # An intermediary node with high betweenness centrality (excluding root and known VASPs)
        bottleneck_mules = []
        for n, bc in betweenness.items():
            if n == clean_target:
                continue
            ent_type = G.nodes[n].get("entity_type", "wallet")
            if ent_type in ("centralized_exchange", "VASP"):
                continue

            # Flag nodes that bridge paths
            if bc >= 0.10 or (node_count > 3 and bc >= 0.05):
                bottleneck_mules.append({
                    "address": G.nodes[n].get("address", n),
                    "entityName": G.nodes[n].get("entity_name") or "Intermediary Layering Mule",
                    "betweennessCentrality": round(float(bc), 4),
                    "pageRank": round(float(pagerank.get(n, 0)), 4),
                    "inDegree": G.in_degree(n),
                    "outDegree": G.out_degree(n),
                    "classification": "CRITICAL_BOTTLENECK_MULE" if bc >= 0.25 else "INTERMEDIARY_BRIDGE",
                    "significance": (
                        f"Carries {round(bc * 100, 1)}% of all shortest transaction paths in case graph. "
                        f"Interdicting this wallet cuts off downstream cash-out routes."
                    ),
                })

        bottleneck_mules.sort(key=lambda x: x["betweennessCentrality"], reverse=True)

        # 5. Graph Structural Attributes
        is_dag = nx.is_directed_acyclic_graph(G)
        density = nx.density(G)

        # 6. Topological Confidence Calibration for Attribution
        confidence_adjustments = self._evaluate_topological_confidence(
            G=G,
            target_addr=clean_target,
            vasp_candidates=vasp_candidates or [],
            detected_cycles=detected_cycles,
            bottlenecks=bottleneck_mules,
            is_dag=is_dag,
        )

        return {
            "graphSummary": {
                "nodeCount": node_count,
                "edgeCount": edge_count,
                "isDirectedAcyclic": is_dag,
                "density": round(density, 4),
                "hasCycles": len(detected_cycles) > 0,
                "cycleCount": len(detected_cycles),
            },
            "bottleneckMules": bottleneck_mules,
            "detectedCycles": detected_cycles,
            "syndicateClusters": syndicate_clusters,
            "centralityMetrics": {
                n: {
                    "address": G.nodes[n].get("address", n),
                    "betweenness": round(betweenness.get(n, 0.0), 4),
                    "pageRank": round(pagerank.get(n, 0.0), 4),
                    "inDegree": G.in_degree(n),
                    "outDegree": G.out_degree(n),
                }
                for n in G.nodes()
            },
            "confidenceAdjustments": confidence_adjustments,
        }

    def _evaluate_topological_confidence(
        self,
        G: nx.DiGraph,
        target_addr: str,
        vasp_candidates: List[Dict[str, Any]],
        detected_cycles: List[List[str]],
        bottlenecks: List[Dict[str, Any]],
        is_dag: bool,
    ) -> List[Dict[str, Any]]:
        """
        Uses graph topology to deterministically enhance or penalize VASP attribution confidence.
        """
        adjustments = []

        for cand in vasp_candidates:
            v_addr = (cand.get("address") or "").lower().strip()
            v_name = cand.get("entityName") or "VASP"
            initial_conf = cand.get("confidence", "HIGH")
            base_score = 92 if initial_conf == "HIGH" else (75 if initial_conf == "MEDIUM" else 55)

            boost = 0
            reasons = []

            if v_addr in G:
                # Rule 1: Acyclic Directed Flow Confirmation (+6%)
                if is_dag and nx.has_path(G, target_addr, v_addr):
                    boost += 6
                    reasons.append("NetworkX verified acyclic shortest path: zero wash-trading or recursive dilution detected.")

                # Rule 2: Sink Terminal Status (+4%)
                out_deg = G.out_degree(v_addr)
                in_deg = G.in_degree(v_addr)
                if out_deg == 0 and in_deg >= 1:
                    boost += 4
                    reasons.append(f"NetworkX confirmed terminal absorption sink: {in_deg} inflow edge(s), zero observed outflows.")
                elif out_deg > 0:
                    boost -= 8
                    reasons.append(f"NetworkX outflow alert: entity forwarded {out_deg} transactions downstream (non-terminal).")

                # Rule 3: Bottleneck Mule Corroboration (+4%)
                if bottlenecks:
                    top_mule = bottlenecks[0]
                    mule_addr = top_mule["address"].lower()
                    # Check if path from suspect to VASP traverses this top mule
                    try:
                        shortest_path = nx.shortest_path(G, target_addr, v_addr)
                        if mule_addr in shortest_path:
                            boost += 4
                            reasons.append(f"Direct traversal confirmed through primary bottleneck mule {top_mule['address'][:10]}... (Betweenness: {top_mule['betweennessCentrality']}).")
                    except Exception:
                        pass

                # Rule 4: Circular Loop / Cycle Penalty (-12%)
                if detected_cycles:
                    for cyc in detected_cycles:
                        if v_addr in [c.lower() for c in cyc]:
                            boost -= 12
                            reasons.append("Circular cycle detected involving this address; potential wash-trading loop.")
                            break

            adjusted_score = max(35, min(99, base_score + boost))
            adjusted_level = "HIGH" if adjusted_score >= 82 else ("MEDIUM" if adjusted_score >= 60 else "LOW")

            adjustments.append({
                "entityName": v_name,
                "address": v_addr,
                "initialScore": base_score,
                "adjustedScore": adjusted_score,
                "adjustedLevel": adjusted_level,
                "netBoost": boost,
                "topologicalEvidence": reasons,
            })

        return adjustments

    def _empty_analytics_result(self, target_address: str) -> Dict[str, Any]:
        return {
            "graphSummary": {
                "nodeCount": 0,
                "edgeCount": 0,
                "isDirectedAcyclic": True,
                "density": 0.0,
                "hasCycles": False,
                "cycleCount": 0,
            },
            "bottleneckMules": [],
            "detectedCycles": [],
            "syndicateClusters": [],
            "centralityMetrics": {},
            "confidenceAdjustments": [],
        }


graph_analytics_service = GraphAnalyticsService()
