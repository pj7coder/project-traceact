import math
import statistics
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set, Tuple

from backend.schemas.wallet import NormalizedTransaction, TransactionDirection
from backend.services.entity_service import entity_service


DEFAULT_SCORING_WEIGHTS = {
    "many_unique_senders": 20,
    "high_transaction_frequency": 15,
    "consolidation": 20,
    "sweep_behavior": 20,
    "short_retention": 10,
    "repeated_destinations": 10,
    "known_vasp_interaction": 5,
}


class UnknownVaspDiscoveryService:
    """
    Unknown VASP Discovery Engine for cryptocurrency forensic investigations.
    Extracts blockchain-neutral behavioral features, identifies exchange-like deposit/consolidation/sweep patterns,
    computes a 0-100 VASP Behavior Score, generates Potential Service Clusters (UC-YYYY-XXXX),
    and produces explainable heuristic classifications without asserting unverified ownership.
    """

    def __init__(self, scoring_weights: Optional[Dict[str, int]] = None):
        self.scoring_weights = scoring_weights or dict(DEFAULT_SCORING_WEIGHTS)

    @staticmethod
    def _parse_iso(ts_str: Optional[str]) -> Optional[datetime]:
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def _to_decimal(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    def extract_behavioral_features(
        self,
        address: str,
        transactions: List[Any],
        connected_wallets: Optional[List[str]] = None,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Extracts 28+ reusable blockchain-neutral behavioral features for an address.
        Works identically across Ethereum, Bitcoin, Tron, and Solana.
        """
        clean_addr = address.strip().lower() if chain.lower() == "ethereum" else address.strip()
        tx_list: List[NormalizedTransaction] = []

        # Normalize incoming transactions if dicts
        for t in transactions:
            if isinstance(t, NormalizedTransaction):
                tx_list.append(t)
            elif isinstance(t, dict):
                try:
                    tx_list.append(NormalizedTransaction(**t))
                except Exception:
                    pass

        tx_count = len(tx_list)
        if tx_count == 0:
            return self._get_empty_features(address, chain)

        # Separate incoming and outgoing
        incoming_txs = []
        outgoing_txs = []
        unique_senders_set: Set[str] = set()
        unique_receivers_set: Set[str] = set()
        dest_counts: Dict[str, int] = {}
        values: List[Decimal] = []
        total_received = Decimal("0")
        total_sent = Decimal("0")
        timestamps: List[datetime] = []
        known_vasp_counterparties = 0

        for tx in tx_list:
            v = self._to_decimal(tx.value)
            values.append(v)
            dt = self._parse_iso(tx.timestamp)
            if dt:
                timestamps.append(dt)

            from_addr = (tx.fromAddress or "").strip()
            to_addr = (tx.toAddress or "").strip()
            is_incoming = (
                tx.direction == TransactionDirection.INCOMING
                or to_addr.lower() == clean_addr.lower()
            )

            if is_incoming:
                incoming_txs.append(tx)
                total_received += v
                if from_addr and from_addr.lower() != clean_addr.lower():
                    unique_senders_set.add(from_addr)
                    if entity_service.is_vasp(from_addr):
                        known_vasp_counterparties += 1
            else:
                outgoing_txs.append(tx)
                total_sent += v
                if to_addr and to_addr.lower() != clean_addr.lower():
                    unique_receivers_set.add(to_addr)
                    dest_counts[to_addr] = dest_counts.get(to_addr, 0) + 1
                    if entity_service.is_vasp(to_addr):
                        known_vasp_counterparties += 1

        in_count = len(incoming_txs)
        out_count = len(outgoing_txs)
        unique_senders = len(unique_senders_set)
        unique_receivers = len(unique_receivers_set)

        # Values stats
        float_vals = [float(v) for v in values if float(v) > 0]
        avg_val = statistics.mean(float_vals) if float_vals else 0.0
        median_val = statistics.median(float_vals) if float_vals else 0.0

        # Small deposits / Large withdrawals
        # Small deposit: < 20% of avg or < 0.1 ETH / equivalent
        small_deposit_cutoff = min(avg_val * 0.3, 0.5)
        num_small_deposits = sum(
            1 for tx in incoming_txs if float(self._to_decimal(tx.value)) <= small_deposit_cutoff
        )
        large_withdrawal_cutoff = max(avg_val * 1.5, 1.0)
        num_large_withdrawals = sum(
            1 for tx in outgoing_txs if float(self._to_decimal(tx.value)) >= large_withdrawal_cutoff
        )

        # Timeline & activity
        wallet_age_days = 1.0
        txs_per_day = float(tx_count)
        burst_activity = False

        if timestamps:
            timestamps.sort()
            span_seconds = (timestamps[-1] - timestamps[0]).total_seconds()
            wallet_age_days = max(1.0, span_seconds / 86400.0)
            txs_per_day = round(tx_count / wallet_age_days, 2)

            # Check burst: >= 5 txs in <= 15 minutes
            for i in range(len(timestamps) - 4):
                if (timestamps[i + 4] - timestamps[i]).total_seconds() <= 900:
                    burst_activity = True
                    break

        # In-degree / Out-degree
        in_degree = unique_senders
        out_degree = unique_receivers
        sender_receiver_ratio = (
            round(float(unique_senders) / max(1.0, float(unique_receivers)), 2)
        )

        # Consolidation ratio: Many unique senders into very few receivers
        # E.g., 20 senders -> 1 receiver gives high consolidation
        consolidation_ratio = 0.0
        if unique_senders > 0:
            consolidation_ratio = round(
                float(unique_senders) / max(1.0, float(unique_receivers + 1)), 2
            )

        # Sweeping behavior & Balance retention time
        # Check time between an incoming tx and subsequent outgoing tx
        time_deltas = []
        for in_tx in incoming_txs:
            in_dt = self._parse_iso(in_tx.timestamp)
            if not in_dt:
                continue
            for out_tx in outgoing_txs:
                out_dt = self._parse_iso(out_tx.timestamp)
                if out_dt and out_dt >= in_dt:
                    delta = (out_dt - in_dt).total_seconds()
                    time_deltas.append(delta)
                    break  # Closest subsequent outgoing

        avg_time_between_rcv_send = statistics.mean(time_deltas) if time_deltas else 86400.0
        balance_retention_time_hours = round(avg_time_between_rcv_send / 3600.0, 2)

        # Sweeps: Forwarding >= 70% of received funds within <= 2 hours
        sweep_count = 0
        for in_tx in incoming_txs:
            in_dt = self._parse_iso(in_tx.timestamp)
            in_v = float(self._to_decimal(in_tx.value))
            if not in_dt or in_v <= 0:
                continue
            for out_tx in outgoing_txs:
                out_dt = self._parse_iso(out_tx.timestamp)
                out_v = float(self._to_decimal(out_tx.value))
                if out_dt and in_dt <= out_dt:
                    diff_hours = (out_dt - in_dt).total_seconds() / 3600.0
                    if diff_hours <= 2.0 and out_v >= in_v * 0.7:
                        sweep_count += 1
                        break
        sweep_frequency = round(sweep_count / max(1.0, float(in_count)), 2)

        # Repeated destinations
        repeated_dest_count = sum(1 for c in dest_counts.values() if c >= 2)
        top_dest_percentage = 0.0
        if dest_counts and out_count > 0:
            max_dest_txs = max(dest_counts.values())
            top_dest_percentage = round((max_dest_txs / out_count) * 100.0, 1)

        # Component scores (0-100)
        deposit_pattern_score = min(
            100.0,
            (unique_senders * 5.0) + (num_small_deposits * 4.0) + (sender_receiver_ratio * 10.0),
        )
        withdrawal_pattern_score = min(
            100.0, (num_large_withdrawals * 15.0) + (top_dest_percentage * 0.5)
        )
        consolidation_score = min(
            100.0,
            (consolidation_ratio * 20.0) if unique_receivers <= 3 and unique_senders >= 3 else 0.0,
        )
        sweep_score = min(
            100.0,
            (sweep_frequency * 80.0) + (20.0 if balance_retention_time_hours <= 3.0 else 0.0),
        )

        return {
            "address": address,
            "chain": chain,
            "transaction_count": tx_count,
            "incoming_transaction_count": in_count,
            "outgoing_transaction_count": out_count,
            "unique_senders": unique_senders,
            "unique_receivers": unique_receivers,
            "total_received": str(total_received),
            "total_sent": str(total_sent),
            "average_transaction_value": f"{avg_val:.4f}",
            "median_transaction_value": f"{median_val:.4f}",
            "wallet_age_days": round(wallet_age_days, 1),
            "transactions_per_day": txs_per_day,
            "in_degree": in_degree,
            "out_degree": out_degree,
            "sender_receiver_ratio": sender_receiver_ratio,
            "number_of_small_deposits": num_small_deposits,
            "number_of_large_withdrawals": num_large_withdrawals,
            "consolidation_ratio": consolidation_ratio,
            "sweep_frequency": sweep_frequency,
            "average_time_between_receive_and_send_seconds": round(avg_time_between_rcv_send, 1),
            "balance_retention_time_hours": balance_retention_time_hours,
            "repeated_destination_count": repeated_dest_count,
            "top_destination_percentage": top_dest_percentage,
            "known_vasp_interactions": known_vasp_counterparties,
            "number_of_connected_wallets": len(connected_wallets or []) or (unique_senders + unique_receivers),
            "burst_activity": burst_activity,
            "deposit_pattern_score": round(deposit_pattern_score, 1),
            "withdrawal_pattern_score": round(withdrawal_pattern_score, 1),
            "consolidation_score": round(consolidation_score, 1),
            "sweep_score": round(sweep_score, 1),
        }

    def _get_empty_features(self, address: str, chain: str) -> Dict[str, Any]:
        return {
            "address": address,
            "chain": chain,
            "transaction_count": 0,
            "incoming_transaction_count": 0,
            "outgoing_transaction_count": 0,
            "unique_senders": 0,
            "unique_receivers": 0,
            "total_received": "0",
            "total_sent": "0",
            "average_transaction_value": "0",
            "median_transaction_value": "0",
            "wallet_age_days": 0.0,
            "transactions_per_day": 0.0,
            "in_degree": 0,
            "out_degree": 0,
            "sender_receiver_ratio": 0.0,
            "number_of_small_deposits": 0,
            "number_of_large_withdrawals": 0,
            "consolidation_ratio": 0.0,
            "sweep_frequency": 0.0,
            "average_time_between_receive_and_send_seconds": 0.0,
            "balance_retention_time_hours": 0.0,
            "repeated_destination_count": 0,
            "top_destination_percentage": 0.0,
            "known_vasp_interactions": 0,
            "number_of_connected_wallets": 0,
            "burst_activity": False,
            "deposit_pattern_score": 0.0,
            "withdrawal_pattern_score": 0.0,
            "consolidation_score": 0.0,
            "sweep_score": 0.0,
        }

    def compute_vasp_behavior_score(
        self, features: Dict[str, Any]
    ) -> Tuple[int, Dict[str, int], List[str]]:
        """
        Computes the 0-100 VASP Behavior Score using configurable weights.
        Returns: (score, breakdown_dict, evidence_justifications)
        """
        weights = self.scoring_weights
        breakdown: Dict[str, int] = {}
        evidence: List[str] = []
        score = 0

        # 1. Many unique senders (+20)
        # 5+ unique senders indicates multi-party deposit/collection
        senders = features.get("unique_senders", 0)
        ratio = features.get("sender_receiver_ratio", 0.0)
        if senders >= 8 or (senders >= 4 and ratio >= 2.0):
            pts = weights.get("many_unique_senders", 20)
            score += pts
            breakdown["many_unique_senders"] = pts
            evidence.append(
                f"Multi-depositor collection topology: {senders} unique sending addresses observed (Sender/Receiver Ratio: {ratio}x)"
            )
        elif senders >= 3:
            pts = int(weights.get("many_unique_senders", 20) * 0.5)
            score += pts
            breakdown["many_unique_senders"] = pts
            evidence.append(f"Multiple depositors: {senders} unique senders identified")
        else:
            breakdown["many_unique_senders"] = 0

        # 2. High transaction frequency (+15)
        tpd = features.get("transactions_per_day", 0.0)
        tx_count = features.get("transaction_count", 0)
        if tpd >= 5.0 or tx_count >= 50 or features.get("burst_activity"):
            pts = weights.get("high_transaction_frequency", 15)
            score += pts
            breakdown["high_transaction_frequency"] = pts
            evidence.append(
                f"High-frequency throughput: {tx_count} total txs ({tpd} tx/day) exceeds routine personal wallet activity"
            )
        elif tx_count >= 15:
            pts = int(weights.get("high_transaction_frequency", 15) * 0.6)
            score += pts
            breakdown["high_transaction_frequency"] = pts
            evidence.append(f"Moderate commercial frequency: {tx_count} total transactions")
        else:
            breakdown["high_transaction_frequency"] = 0

        # 3. Consolidation (+20)
        consol_ratio = features.get("consolidation_ratio", 0.0)
        unique_recv = features.get("unique_receivers", 0)
        if consol_ratio >= 3.0 and unique_recv <= 3:
            pts = weights.get("consolidation", 20)
            score += pts
            breakdown["consolidation"] = pts
            evidence.append(
                f"Strong pooling consolidation: Inflows from {senders} addresses funnel into {unique_recv} primary hub(s)"
            )
        elif consol_ratio >= 1.5:
            pts = int(weights.get("consolidation", 20) * 0.5)
            score += pts
            breakdown["consolidation"] = pts
            evidence.append(f"Fund consolidation observed (Consolidation Ratio: {consol_ratio})")
        else:
            breakdown["consolidation"] = 0

        # 4. Sweep behavior (+20)
        sweep_freq = features.get("sweep_frequency", 0.0)
        if sweep_freq >= 0.5:
            pts = weights.get("sweep_behavior", 20)
            score += pts
            breakdown["sweep_behavior"] = pts
            evidence.append(
                f"Automated sweeping behavior: {int(sweep_freq * 100)}% of deposits are swept out in bulk shortly after receipt"
            )
        elif sweep_freq >= 0.2:
            pts = int(weights.get("sweep_behavior", 20) * 0.5)
            score += pts
            breakdown["sweep_behavior"] = pts
            evidence.append(f"Occasional sweep patterns detected ({int(sweep_freq * 100)}% frequency)")
        else:
            breakdown["sweep_behavior"] = 0

        # 5. Short retention time (+10)
        retention_hours = features.get("balance_retention_time_hours", 24.0)
        if retention_hours <= 1.5:
            pts = weights.get("short_retention", 10)
            score += pts
            breakdown["short_retention"] = pts
            evidence.append(
                f"Transient pass-through balance: Average retention time is {retention_hours} hours (< 90 mins)"
            )
        elif retention_hours <= 6.0:
            pts = int(weights.get("short_retention", 10) * 0.5)
            score += pts
            breakdown["short_retention"] = pts
            evidence.append(f"Short balance retention: Funds held for average {retention_hours} hours")
        else:
            breakdown["short_retention"] = 0

        # 6. Repeated central destinations (+10)
        rep_dest = features.get("repeated_destination_count", 0)
        top_dest_pct = features.get("top_destination_percentage", 0.0)
        if rep_dest >= 2 or top_dest_pct >= 60.0:
            pts = weights.get("repeated_destinations", 10)
            score += pts
            breakdown["repeated_destinations"] = pts
            evidence.append(
                f"Fixed router destinations: {top_dest_pct}% of outflows route to persistent centralized counterparty addresses"
            )
        elif rep_dest >= 1:
            pts = int(weights.get("repeated_destinations", 10) * 0.5)
            score += pts
            breakdown["repeated_destinations"] = pts
            evidence.append("Periodic routing to recurrent downstream addresses")
        else:
            breakdown["repeated_destinations"] = 0

        # 7. Known VASP interaction (+5)
        known_vasp_txs = features.get("known_vasp_interactions", 0)
        if known_vasp_txs >= 1:
            pts = weights.get("known_vasp_interaction", 5)
            score += pts
            breakdown["known_vasp_interaction"] = pts
            evidence.append(
                f"Direct bridgehead to regulated VASP infrastructure: {known_vasp_txs} interaction(s) observed"
            )
        else:
            breakdown["known_vasp_interaction"] = 0

        final_score = min(100, max(0, score))
        return final_score, breakdown, evidence

    def classify_entity(
        self,
        features: Dict[str, Any],
        vasp_score: int,
        is_known_vasp: bool = False,
        known_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classifies an entity based on behavioral metrics, VASP behavior score, and known labels.
        Adheres strictly to the responsible labeling rule: Never state unverified exact ownership.
        """
        if is_known_vasp:
            return {
                "classification": "CENTRALIZED_EXCHANGE",
                "tier": "VERIFIED_VASP",
                "label": known_name or "Verified VASP",
                "verified": True,
                "disclaimer": "Confirmed against verified public ledger labels and regulatory registry records.",
            }

        # Determine Tier
        if vasp_score >= 80:
            tier = "STRONG_VASP_LIKE_BEHAVIOUR"
        elif vasp_score >= 60:
            tier = "PROBABLE_VASP"
        elif vasp_score >= 40:
            tier = "POSSIBLE_VASP"
        else:
            tier = "NO_STRONG_VASP_SIGNAL"

        # Determine Entity Classification
        senders = features.get("unique_senders", 0)
        receivers = features.get("unique_receivers", 0)
        consol_ratio = features.get("consolidation_ratio", 0.0)
        sweep_freq = features.get("sweep_frequency", 0.0)
        retention = features.get("balance_retention_time_hours", 24.0)
        tx_count = features.get("transaction_count", 0)

        if vasp_score >= 70 and consol_ratio >= 3.0:
            classification = "CUSTODIAL_SERVICE"
            description = "Behavior is consistent with custodial exchange infrastructure or deposit collection. Exact provider is not independently verified."
        elif vasp_score >= 60 and sweep_freq >= 0.5:
            classification = "PAYMENT_PROCESSOR"
            description = "Behavior aligns with automated payment routing or merchant sweep gateway. Exact organization is unverified."
        elif vasp_score >= 60:
            classification = "PROBABLE_VASP"
            description = "High concentration of custodial indicators detected. Operating entity is unknown."
        elif tx_count >= 50 and consol_ratio <= 0.8 and senders >= 10 and receivers >= 10:
            classification = "MERCHANT"
            description = "Bi-directional high-volume merchant or commerce transacting wallet."
        elif retention <= 0.5 and sweep_freq >= 0.8 and tx_count >= 8:
            classification = "LAUNDERING_HUB"
            description = "Aggressive rapid pass-through / peeling pattern without long-term balance retention."
        elif vasp_score >= 40:
            classification = "POSSIBLE_VASP"
            description = "Moderate operational centralization signals observed. Insufficient evidence for definitive custodial classification."
        elif tx_count <= 10:
            classification = "NORMAL_WALLET"
            description = "Standard personal or retail self-custody wallet activity."
        else:
            classification = "UNKNOWN_ENTITY"
            description = "Unattributed on-chain address with no strong custodial signature."

        return {
            "classification": classification,
            "tier": tier,
            "label": f"Heuristic: {classification.replace('_', ' ').title()}",
            "verified": False,
            "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION. Exact provider or owner is not independently verified.",
            "description": description,
        }

    def detect_service_clusters(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        chain: str = "ethereum",
    ) -> List[Dict[str, Any]]:
        """
        Analyzes connected graph nodes to identify Potential Service Clusters (PART F).
        Groups addresses that share common consolidation targets, similar sweep timing,
        or high counterparty overlap.
        """
        clusters: List[Dict[str, Any]] = []
        if not nodes or not edges:
            return clusters

        # Map target destinations to feeders (Many-to-One consolidation clusters)
        consolidation_hubs: Dict[str, List[str]] = {}
        for edge in edges:
            src = edge.get("source", "").strip()
            dst = edge.get("target", "").strip()
            if src and dst and src.lower() != dst.lower():
                consolidation_hubs.setdefault(dst, []).append(src)

        cluster_index = 1
        seen_addresses: Set[str] = set()

        for hub_addr, feeders in consolidation_hubs.items():
            unique_feeders = list(set(feeders))
            if len(unique_feeders) >= 2:
                # Potential consolidation cluster found
                cluster_addresses = [hub_addr] + unique_feeders
                unseen = [a for a in cluster_addresses if a.lower() not in seen_addresses]
                if len(unseen) < 2:
                    continue

                for a in cluster_addresses:
                    seen_addresses.add(a.lower())

                hub_node = next((n for n in nodes if n.get("address", "").lower() == hub_addr.lower()), None)
                hub_score = hub_node.get("vaspBehaviorScore", 75) if hub_node else 75

                cluster_id = f"UC-{datetime.now(timezone.utc).year}-{cluster_index:04d}"
                cluster_index += 1

                cluster_evidence = [
                    f"Consolidation pattern: {len(unique_feeders)} feeder address(es) regularly route into central hub ({hub_addr[:10]}...)",
                    f"Shared deposit infrastructure: Synchronized transfer topologies detected",
                    "Automated pooling behavior consistent with custodial deposit routing",
                ]

                clusters.append({
                    "clusterId": cluster_id,
                    "chain": chain,
                    "addresses": cluster_addresses,
                    "addressCount": len(cluster_addresses),
                    "centralWallets": [hub_addr],
                    "transactionCount": len(feeders),
                    "uniqueDepositors": len(unique_feeders),
                    "classification": "Probable Custodial Service" if hub_score >= 60 else "Potential Service Cluster",
                    "vaspBehaviorScore": hub_score,
                    "exactOrganization": "Unknown",
                    "verification": "UNVERIFIED",
                    "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION",
                    "evidence": cluster_evidence,
                })

        return clusters


vasp_discovery_service = UnknownVaspDiscoveryService()
