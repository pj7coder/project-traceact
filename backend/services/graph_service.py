import math
import logging
from decimal import Decimal
from typing import List, Dict, Tuple, Any

from backend.schemas.wallet import (
    GraphData,
    GraphNode,
    GraphNodeData,
    GraphEdge,
    GraphEdgeData,
    ConnectedWallet,
    NormalizedTransaction,
    WalletOverview,
)
from backend.services.entity_service import entity_service

logger = logging.getLogger("graph_service")


class GraphService:
    """
    Generates structured 1-hop transaction graphs with radial coordinates,
    aggregated directed edges, volume metrics, and visual metadata for React Flow.
    """

    @staticmethod
    def _format_short_address(address: str) -> str:
        if not address:
            return ""
        if len(address) <= 12:
            return address
        return f"{address[:6]}...{address[-4:]}"

    @staticmethod
    def _wei_to_eth_str(wei_val: int | str | Decimal) -> str:
        try:
            val = Decimal(str(wei_val))
            eth = val / Decimal("1000000000000000000")
            formatted = f"{eth:.6f}".rstrip("0").rstrip(".")
            return formatted if formatted else "0"
        except Exception:
            return "0"

    def build_one_hop_graph(
        self,
        investigated_wallet: WalletOverview,
        connected_wallets: List[ConnectedWallet],
        transactions: List[NormalizedTransaction],
    ) -> GraphData:
        """
        Constructs a 1-hop graph with investigated node at center and connected nodes placed radially.
        Aggregates multiple transactions between pairs into unified directed edges.
        """
        center_addr = investigated_wallet.address.lower()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        # 1. Add Central Investigated Node
        center_color = "#06b6d4"  # Cyan for investigated root
        center_node = GraphNode(
            id=center_addr,
            type="investigatedWalletNode",
            data=GraphNodeData(
                label=self._format_short_address(center_addr),
                fullAddress=center_addr,
                nodeType="investigated",
                role="investigated",
                txCount=investigated_wallet.transactionCount,
                totalVolume=None,
                balance=investigated_wallet.balance,
                asset=investigated_wallet.asset,
                riskScore=investigated_wallet.riskScore or 0,
                riskLevel=investigated_wallet.riskLevel or "LOW",
                nodeColor=center_color,
                tags=investigated_wallet.tags or ["Target Wallet"],
                globalSearchCount=investigated_wallet.globalSearchCount or 1,
            ),
            position={"x": 400.0, "y": 300.0},
        )
        nodes.append(center_node)

        # 2. Place Connected Nodes in an Organic Transaction-Driven Flow Layout
        # Senders (incoming) flow in from the Left; Recipients (outgoing) branch out to the Right.
        # Radial distance is inversely modulated by transaction volume (higher volume = closer corridor).
        max_graph_nodes = 60
        display_wallets = connected_wallets[:max_graph_nodes]

        inflows = [w for w in display_wallets if getattr(w.direction, "value", str(w.direction)).lower() == "incoming"]
        outflows = [w for w in display_wallets if getattr(w.direction, "value", str(w.direction)).lower() == "outgoing"]
        mutuals = [w for w in display_wallets if w not in inflows and w not in outflows]

        positions_map: Dict[str, Tuple[float, float]] = {}

        # Place Upstream Inflow Senders on Left (X < 400)
        num_in = len(inflows)
        in_v_gap = max(90.0, min(150.0, 520.0 / max(num_in, 1)))
        for idx, wallet in enumerate(inflows):
            try:
                amt = float(str(wallet.totalAmount or 1.0))
            except Exception:
                amt = 1.0
            dist_x = max(260.0, min(380.0, 340.0 - math.log1p(amt) * 14.0))
            y_offset = (idx - (num_in - 1) / 2.0) * in_v_gap
            pos_x = 400.0 - dist_x
            pos_y = 300.0 + y_offset
            positions_map[wallet.address.lower()] = (pos_x, pos_y)

        # Place Downstream Outflow Recipients on Right (X > 400)
        num_out = len(outflows)
        out_v_gap = max(90.0, min(150.0, 520.0 / max(num_out, 1)))
        for idx, wallet in enumerate(outflows):
            try:
                amt = float(str(wallet.totalAmount or 1.0))
            except Exception:
                amt = 1.0
            dist_x = max(260.0, min(380.0, 340.0 - math.log1p(amt) * 14.0))
            y_offset = (idx - (num_out - 1) / 2.0) * out_v_gap
            pos_x = 400.0 + dist_x
            pos_y = 300.0 + y_offset
            positions_map[wallet.address.lower()] = (pos_x, pos_y)

        # Place Mutual / Bidirectional Counterparties in Top / Bottom Transition Zones
        num_mut = len(mutuals)
        for idx, wallet in enumerate(mutuals):
            is_top = (idx % 2 == 0)
            sign_y = -1.0 if is_top else 1.0
            h_offset = (idx // 2 - (num_mut // 2) / 2.0) * 160.0
            pos_x = 400.0 + h_offset
            pos_y = 300.0 + sign_y * 270.0
            positions_map[wallet.address.lower()] = (pos_x, pos_y)

        for wallet in display_wallets:
            w_key = wallet.address.lower()
            pos_x, pos_y = positions_map.get(w_key, (400.0 + 300.0, 300.0))

            # Node color & entity lookup
            ent = entity_service.get_entity(wallet.address)
            node_color = "#10b981"  # Emerald green default
            tags = list(wallet.tags or [])
            if ent:
                if ent.is_vasp():
                    node_color = "#f59e0b"  # Gold for VASP
                    tags.append(f"VASP: {ent.entity_name}")
                elif ent.entity_type in ("mixer", "sanctioned"):
                    node_color = "#ef4444"  # Red for high threat
                    tags.append("High Risk Entity")
                elif ent.entity_type == "bridge":
                    node_color = "#8b5cf6"  # Purple for bridge
                    tags.append("DeFi Bridge")

            node_id = wallet.address.lower() if wallet.address.startswith("0x") else wallet.address
            connected_node = GraphNode(
                id=node_id,
                type="connectedWalletNode",
                data=GraphNodeData(
                    label=self._format_short_address(wallet.address),
                    fullAddress=wallet.address,
                    nodeType="known_entity" if ent else "connected",
                    role=wallet.direction.value,
                    txCount=wallet.transactionCount,
                    totalVolume=wallet.totalAmount,
                    balance=getattr(wallet, "balance", None) or wallet.totalAmount,
                    asset=wallet.asset,
                    entityName=ent.entity_name if ent else None,
                    entityType=ent.entity_type if ent else None,
                    riskScore=wallet.riskScore or 0,
                    riskLevel=wallet.riskLevel or "LOW",
                    nodeColor=node_color,
                    tags=tags,
                ),
                position={"x": round(pos_x, 1), "y": round(pos_y, 1)},
            )
            nodes.append(connected_node)

        # 3. Aggregate Transactions into Directed Edges
        edge_aggregates: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for tx in transactions:
            from_addr = (tx.fromAddress or "").strip()
            to_addr = (tx.toAddress or "").strip()

            if not from_addr or not to_addr or from_addr.lower() == to_addr.lower():
                continue

            pair = (from_addr.lower(), to_addr.lower())
            if pair not in edge_aggregates:
                edge_aggregates[pair] = {
                    "source": from_addr,
                    "target": to_addr,
                    "count": 0,
                    "totalVal": Decimal("0"),
                    "totalWei": Decimal("0"),
                    "asset": tx.asset or investigated_wallet.asset or "ETH",
                }

            try:
                tx_val = Decimal(str(tx.value or "0"))
            except Exception:
                tx_val = Decimal("0")

            try:
                tx_wei = Decimal(str(tx.valueRaw or "0"))
            except Exception:
                tx_wei = Decimal("0")

            edge_aggregates[pair]["count"] += 1
            edge_aggregates[pair]["totalVal"] += tx_val
            edge_aggregates[pair]["totalWei"] += tx_wei

        # Build GraphEdge objects
        existing_node_ids = {n.id.lower() for n in nodes}
        for (src_k, tgt_k), data in edge_aggregates.items():
            if src_k not in existing_node_ids or tgt_k not in existing_node_ids:
                continue

            asset_sym = data.get("asset", "ETH")
            val_dec = data["totalVal"]
            total_str = f"{val_dec:.6f}".rstrip("0").rstrip(".") or "0"
            tx_count = data["count"]
            label = f"{tx_count} tx ({total_str} {asset_sym})" if total_str != "0" else f"{tx_count} tx"

            edge_id = f"e_{src_k[:8]}_{tgt_k[:8]}"
            edge_src = data["source"].lower() if data["source"].startswith("0x") else data["source"]
            edge_tgt = data["target"].lower() if data["target"].startswith("0x") else data["target"]

            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=edge_src,
                    target=edge_tgt,
                    label=label,
                    data=GraphEdgeData(
                        transactionCount=tx_count,
                        totalTransferred=total_str,
                        asset=asset_sym,
                    ),
                    animated=True,
                )
            )

        return GraphData(nodes=nodes, edges=edges)


graph_service = GraphService()
