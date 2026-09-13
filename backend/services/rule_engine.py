import logging
import math
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from backend.schemas.wallet import NormalizedTransaction, WalletOverview, ConnectedWallet
from backend.services.entity_service import entity_service

logger = logging.getLogger("rule_engine")


class ForensicRuleEngine:
    """
    Prioritized Law Enforcement Forensic Rule Engine.
    Evaluates wallet transaction history, counterparty clusters, and entity linkages
    to compute a deterministic 0-100 Suspicion Score with prioritized severity tiers.
    Supports investigator-customizable system logic filters and multi-chain calibration.
    """

    @staticmethod
    def _parse_dec(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    def evaluate_wallet(
        self,
        wallet: WalletOverview,
        transactions: List[NormalizedTransaction],
        connected_wallets: Optional[List[ConnectedWallet]] = None,
        multihop_nodes: Optional[List[Dict[str, Any]]] = None,
        system_logic: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes prioritized forensic rules, calculates the composite suspicion score,
        assigns risk classification, and outputs the forensic justification bundle.
        Applies investigator-tuned system logic profile and parameter overrides if provided.
        """
        # Parse Investigator System Logic
        if system_logic is not None:
            cfg = system_logic.model_dump() if hasattr(system_logic, "model_dump") else (
                system_logic.dict() if hasattr(system_logic, "dict") else (
                    dict(system_logic) if isinstance(system_logic, dict) else {}
                )
            )
        else:
            cfg = {}

        profile = cfg.get("profile") or "balanced"
        sensitivity_mult = Decimal(str(cfg.get("sensitivityMultiplier") or 1.0))
        custom_large_val = cfg.get("largeTransferThreshold")
        custom_velocity = cfg.get("burstVelocityThreshold")
        custom_rapid_ratio = Decimal(str(cfg.get("rapidMovementRetentionRatio") or 0.5))
        enable_mixer_booster = cfg.get("enableMixerBooster", True)
        enable_vasp_dampener = cfg.get("enableVaspDampener", True)
        disabled_rules = set(cfg.get("disabledRuleIds") or [])
        custom_weights = cfg.get("customRuleWeights") or {}

        # Profile-based modifier overrides
        if profile == "strict":
            if cfg.get("sensitivityMultiplier") is None:
                sensitivity_mult = Decimal("1.25")
            enable_vasp_dampener = False
            custom_velocity = custom_velocity or 5
        elif profile == "fraud_syndicate":
            if "P6_RAPID_MOVEMENT" not in custom_weights:
                custom_weights["P6_RAPID_MOVEMENT"] = 90
            if "P8_CLUSTER_CIRCULAR" not in custom_weights:
                custom_weights["P8_CLUSTER_CIRCULAR"] = 75
            if "P13_NO_VASP_ACCOUNT" not in custom_weights:
                custom_weights["P13_NO_VASP_ACCOUNT"] = 45
        elif profile == "relaxed":
            if cfg.get("sensitivityMultiplier") is None:
                sensitivity_mult = Decimal("0.75")

        triggered_rules: List[Dict[str, Any]] = []
        clean_addr = wallet.address.lower().strip()
        balance_num = self._parse_dec(wallet.balance)
        tx_count = len(transactions)

        # Helper to apply rule overrides, support legacy aliases, and skip disabled rules
        def add_rule(
            rule_id: str,
            priority: int,
            title: str,
            severity: str,
            default_weight: int,
            desc: str,
            evidence: List[str],
            aliases: Optional[List[str]] = None,
        ):
            all_keys = [rule_id] + (aliases or [])
            if any(k in disabled_rules for k in all_keys):
                return
            weight = default_weight
            for k in all_keys:
                if k in custom_weights:
                    weight = custom_weights[k]
                    break
            triggered_rules.append({
                "ruleId": rule_id,
                "priority": priority,
                "title": title,
                "severity": severity,
                "weight": weight,
                "description": desc,
                "evidence": evidence,
            })

        # Pre-compute counterparty address sets and entity lookups
        counterparty_addrs = set()
        incoming_txs = []
        outgoing_txs = []
        total_volume = Decimal("0")

        has_coinjoin_tx = False
        has_peeling_tx = False

        for tx in transactions:
            from_a = (tx.fromAddress or "").lower().strip()
            to_a = (tx.toAddress or "").lower().strip()
            if from_a == clean_addr and to_a:
                counterparty_addrs.add(to_a)
                outgoing_txs.append(tx)
            elif to_a == clean_addr:
                counterparty_addrs.add(from_a)
                incoming_txs.append(tx)
            total_volume += self._parse_dec(tx.value)

            tt = getattr(tx, "txType", "")
            if tt == "coinjoin_mixing":
                has_coinjoin_tx = True
            elif tt == "peeling_chain":
                has_peeling_tx = True

        # Check multi-hop node tags for CoinJoin or Peeling
        if multihop_nodes:
            for mn in multihop_nodes:
                tags = mn.get("tags") or []
                if "CoinJoin Mixer" in tags:
                    has_coinjoin_tx = True
                if "Peeling Chain" in tags:
                    has_peeling_tx = True

        # Multi-Chain Asset Calibration
        chain_clean = (wallet.chain or "ethereum").lower().strip()
        asset_symbol = (wallet.asset or ("BTC" if chain_clean == "bitcoin" else ("TRX" if chain_clean == "tron" else ("SOL" if chain_clean == "solana" else "ETH")))).upper()

        if chain_clean in ("bitcoin", "btc"):
            large_tx_threshold = Decimal(str(custom_large_val if custom_large_val is not None else (0.25 if profile == "strict" else 0.5)))
            high_volume_threshold = Decimal("2.5") if profile != "strict" else Decimal("1.0")
            rapid_min_in = Decimal("0.02")
            high_holding_threshold = Decimal("3.0")
        elif chain_clean == "tron" or asset_symbol in ("TRX", "USDT", "USDC"):
            large_tx_threshold = Decimal(str(custom_large_val if custom_large_val is not None else (2500.0 if profile == "strict" else 5000.0)))
            high_volume_threshold = Decimal("25000.0") if profile != "strict" else Decimal("10000.0")
            rapid_min_in = Decimal("200.0")
            high_holding_threshold = Decimal("20000.0")
        elif chain_clean == "solana" or asset_symbol == "SOL":
            large_tx_threshold = Decimal(str(custom_large_val if custom_large_val is not None else (10.0 if profile == "strict" else 25.0)))
            high_volume_threshold = Decimal("100.0") if profile != "strict" else Decimal("50.0")
            rapid_min_in = Decimal("2.0")
            high_holding_threshold = Decimal("100.0")
        else:  # Ethereum / EVM
            large_tx_threshold = Decimal(str(custom_large_val if custom_large_val is not None else (2.5 if profile == "strict" else 5.0)))
            high_volume_threshold = Decimal("30.0") if profile != "strict" else Decimal("15.0")
            rapid_min_in = Decimal("0.2")
            high_holding_threshold = Decimal("15.0")

        # =============================================================
        # PRIORITIZED FORENSIC RULES HIERARCHY (1 to 16)
        # =============================================================

        # -------------------------------------------------------------
        # Priority 1: Connection to Sanctioned Addresses (Weight 100, CRITICAL)
        # -------------------------------------------------------------
        has_sanction = False
        matched_sanctions = []
        for cp in counterparty_addrs:
            ent = entity_service.get_entity(cp)
            if ent and ent.entity_type in ("sanctioned", "OFAC_sanctioned", "sanctioned_entity"):
                has_sanction = True
                matched_sanctions.append(f"{ent.entity_name} ({cp[:8]}...)")

        if has_sanction:
            p1_weight = 98 if len(matched_sanctions) == 1 else 99
            add_rule(
                "P1_SANCTIONED_ADDRESSES", 1, "Connection to Sanctioned Addresses", "CRITICAL", p1_weight,
                f"Direct transaction detected with OFAC/UN sanctioned entity: {', '.join(matched_sanctions)}",
                matched_sanctions,
                aliases=["P1_SANCTION_MATCH"],
            )

        # -------------------------------------------------------------
        # Priority 2: Interaction with Known Ransomware (Weight ~94-96, CRITICAL)
        # -------------------------------------------------------------
        has_ransom = False
        matched_ransom = []
        for cp in counterparty_addrs:
            ent = entity_service.get_entity(cp)
            if ent and "ransomware" in ent.entity_type.lower():
                has_ransom = True
                matched_ransom.append(f"{ent.entity_name} ({cp[:8]}...)")

        if has_ransom:
            p2_weight = 94 if len(matched_ransom) == 1 else 96
            add_rule(
                "P2_RANSOMWARE_INTERACTION", 2, "Interaction with Known Ransomware", "CRITICAL", p2_weight,
                f"Counterparty identified as ransomware extortion infrastructure: {', '.join(matched_ransom)}",
                matched_ransom,
                aliases=["P2_RANSOMWARE_LINK"],
            )

        # -------------------------------------------------------------
        # Priority 3: Receiving Stolen Funds & Connection to Known Hacks (Weight ~91-93, CRITICAL)
        # -------------------------------------------------------------
        has_stolen = False
        matched_hacks = []
        for cp in counterparty_addrs:
            ent = entity_service.get_entity(cp)
            if ent and any(term in ent.entity_type.lower() for term in ("hack", "exploit", "stolen", "heist")):
                has_stolen = True
                matched_hacks.append(f"{ent.entity_name} ({cp[:8]}...)")

        if has_stolen:
            p3_weight = 91 if len(matched_hacks) == 1 else 93
            add_rule(
                "P3_RECEIVING_STOLEN_FUNDS_HACKS", 3, "Receiving Stolen Funds & Connection to Known Hacks", "CRITICAL", p3_weight,
                f"Wallet exchanged assets with known illicit exploit address or stolen funds pool: {', '.join(matched_hacks)}",
                matched_hacks,
                aliases=["P3_STOLEN_FUNDS"],
            )

        # -------------------------------------------------------------
        # Priority 4: Connection to Scams & Interaction with Malicious Contracts (Weight ~87-89, CRITICAL)
        # -------------------------------------------------------------
        has_malicious = False
        matched_mal = []
        for cp in counterparty_addrs:
            ent = entity_service.get_entity(cp)
            if ent and any(term in ent.entity_type.lower() for term in ("drainer", "phishing", "scam", "malicious", "ponzi")):
                has_malicious = True
                matched_mal.append(f"{ent.entity_name} ({cp[:8]}...)")

        if has_malicious:
            p4_weight = 87 if len(matched_mal) == 1 else 89
            add_rule(
                "P4_SCAMS_MALICIOUS_CONTRACTS", 4, "Connection to Scams & Malicious Contract Interaction", "CRITICAL", p4_weight,
                f"Address executed transactions with known phishing drainers, fraudulent tokens, or scam contracts: {', '.join(matched_mal)}",
                matched_mal,
                aliases=["P4_MALICIOUS_CONTRACT"],
            )

        # -------------------------------------------------------------
        # Priority 5: Connection to Illicit Services & Anonymizing Mixers (Weight ~82-84, HIGH)
        # -------------------------------------------------------------
        has_mixer = False
        matched_mixers = []
        for cp in counterparty_addrs:
            ent = entity_service.get_entity(cp)
            if ent and ent.entity_type in ("mixer", "tumbler", "anonymizer", "darknet"):
                has_mixer = True
                matched_mixers.append(f"{ent.entity_name} ({cp[:8]}...)")

        if has_coinjoin_tx:
            has_mixer = True
            matched_mixers.append("CoinJoin mixing pool signature (equal-output multi-party mixing)")

        if has_mixer:
            p5_weight = 82 if not has_coinjoin_tx else 84
            add_rule(
                "P5_ILLICIT_SERVICES_MIXERS", 5, "Connection to Illicit Services & Anonymizing Mixers", "HIGH", p5_weight,
                f"Assets routed through obfuscation service, darknet market, or anonymity mixer: {', '.join(matched_mixers)}",
                matched_mixers,
                aliases=["P5_MIXER_INTERACTION"],
            )

        # -------------------------------------------------------------
        # Priority 6: Rapid Movement of Funds (Peeling Chains & Pass-Through) (Weight ~74-77, HIGH)
        # -------------------------------------------------------------
        has_rapid_passthrough = False
        rapid_details = []

        if has_peeling_tx:
            has_rapid_passthrough = True
            rapid_details.append("Peeling Chain pattern: sequential automated peel from unspent reservoir")

        if incoming_txs and outgoing_txs:
            for in_tx in incoming_txs:
                v_in = self._parse_dec(in_tx.value)
                if v_in < rapid_min_in:
                    continue
                for out_tx in outgoing_txs:
                    v_out = self._parse_dec(out_tx.value)
                    if v_out >= (v_in * custom_rapid_ratio):
                        has_rapid_passthrough = True
                        rapid_details.append(f"Received {v_in:.4f} {in_tx.asset} and rapidly forwarded {v_out:.4f} {out_tx.asset}")
                        break
                if has_rapid_passthrough:
                    break
        elif len(transactions) >= 2:
            sorted_txs = sorted(transactions, key=lambda t: t.timestamp or "")
            for i in range(len(sorted_txs) - 1):
                t1 = sorted_txs[i]
                t2 = sorted_txs[i+1]
                if t1.direction == "incoming" and t2.direction == "outgoing":
                    v1 = self._parse_dec(t1.value)
                    v2 = self._parse_dec(t2.value)
                    if v1 >= rapid_min_in and v2 >= (v1 * custom_rapid_ratio):
                        has_rapid_passthrough = True
                        rapid_details.append(f"Received {v1:.4f} {t1.asset} and forwarded {v2:.4f} {t2.asset}")
                        break

        if has_rapid_passthrough:
            p6_weight = 74 + (3 if has_peeling_tx else (2 if len(rapid_details) >= 2 else 0))
            add_rule(
                "P6_RAPID_MOVEMENT_OF_FUNDS", 6, "Rapid Movement of Funds (Peeling Chains & Pass-Through)", "HIGH", p6_weight,
                "Suspect pass-through behavior: Large funds transferred out shortly after receipt without substantial retention.",
                rapid_details[:2],
                aliases=["P6_RAPID_MOVEMENT", "RULE_P5_RAPID_MOVEMENT"],
            )

        # -------------------------------------------------------------
        # Priority 7: Multiple Wallets as One Cluster (Syndicate Looping) (Weight ~69-72, HIGH)
        # -------------------------------------------------------------
        circular_detected = False
        for cp in counterparty_addrs:
            sent_to = any(tx.toAddress and tx.toAddress.lower() == cp for tx in outgoing_txs)
            rcvd_from = any(tx.fromAddress and tx.fromAddress.lower() == cp for tx in incoming_txs)
            if sent_to and rcvd_from:
                circular_detected = True
                break

        if circular_detected:
            p7_weight = 69 + min(3, len(counterparty_addrs) // 6)
            add_rule(
                "P7_MULTIPLE_WALLETS_AS_ONE_CLUSTER", 7, "Multiple Wallets as One Cluster (Syndicate Looping)", "HIGH", p7_weight,
                "Bi-directional fund looping and co-spending observed between target and peer wallets, characteristic of syndicate clustering.",
                ["Bidirectional transfer loop detected across counterparties"],
                aliases=["P8_CLUSTER_CIRCULAR"],
            )

        # -------------------------------------------------------------
        # Priority 8: Suspicious Transaction Pattern (High Velocity Burst) (Weight ~63-71, HIGH)
        # -------------------------------------------------------------
        velocity_threshold = custom_velocity if custom_velocity is not None else 10
        if tx_count >= velocity_threshold:
            burst_intensity = min(8, int((tx_count - velocity_threshold) / 4)) if tx_count > velocity_threshold else 0
            p8_weight = 63 + burst_intensity
            add_rule(
                "P8_SUSPICIOUS_TRANSACTION_PATTERN", 8, "Suspicious Transaction Pattern (High Velocity Burst)", "HIGH", p8_weight,
                f"Concentrated burst of {tx_count} automated transfers in target timeline.",
                [f"{tx_count} transactions recorded across {len(counterparty_addrs)} counterparty endpoints"],
                aliases=["P7_HIGH_VELOCITY"],
            )

        # -------------------------------------------------------------
        # Priority 9: Receiving/Sending Large Amounts (Weight ~49-58, MEDIUM)
        # -------------------------------------------------------------
        large_txs = [tx for tx in transactions if self._parse_dec(tx.value) >= large_tx_threshold]
        if large_txs or total_volume >= high_volume_threshold:
            vol_float = float(total_volume)
            p9_weight = min(58, 49 + int(min(5, len(large_txs)) + min(4.0, math.log1p(max(0.0, vol_float / 10.0)) * 1.5)))
            add_rule(
                "P9_RECEIVING_SENDING_LARGE_AMOUNTS", 9, "Receiving/Sending Large Amounts (High-Value Exposure)", "MEDIUM", p9_weight,
                f"High value transfer volume detected: Cumulative {total_volume:.2f} {asset_symbol}.",
                [f"{len(large_txs)} transactions exceeding {large_tx_threshold} {asset_symbol}"],
                aliases=["P9_LARGE_AMOUNT"],
            )

        # -------------------------------------------------------------
        # Priority 10: Making Large Number of Transactions (Weight ~42-48, MEDIUM)
        # -------------------------------------------------------------
        if wallet.transactionCount >= 100 or tx_count >= 50:
            tx_total = wallet.transactionCount or tx_count
            p10_weight = min(48, 42 + int(min(6, tx_total // 40)))
            add_rule(
                "P10_MAKING_LARGE_NUMBER_OF_TRANSACTIONS", 10, "Making Large Number of Transactions (High Frequency)", "MEDIUM", p10_weight,
                f"Wallet exhibits heavy activity with {tx_total} logged operations.",
                [f"Total transaction count: {tx_total}"],
                aliases=["P10_HIGH_TX_COUNT"],
            )

        # -------------------------------------------------------------
        # Priority 11: Indirect Exposure to Suspicious Wallets (Weight ~33-39, MEDIUM)
        # -------------------------------------------------------------
        if multihop_nodes:
            indirect_suspicious = []
            min_hop_depth = 99
            for node in multihop_nodes:
                d = node.get("depth", 0)
                if d >= 2:
                    ent_n = node.get("entityName")
                    ent_t = (node.get("entityType") or "").lower()
                    tags = node.get("tags") or []
                    if (ent_n and ent_t in ("mixer", "sanctioned", "hack", "scam")) or "CoinJoin Mixer" in tags:
                        label = ent_n or "Mixer Pool"
                        indirect_suspicious.append(f"{label} at Hop {d}")
                        if d < min_hop_depth:
                            min_hop_depth = d
            if indirect_suspicious:
                p11_weight = 37 if min_hop_depth <= 2 else max(31, 37 - (min_hop_depth - 2) * 3)
                add_rule(
                    "P11_INDIRECT_EXPOSURE_SUSPICIOUS_WALLETS", 11, "Indirect Exposure to Suspicious Wallets (2+ Hops)", "MEDIUM", p11_weight,
                    f"Multi-hop graph reveals downstream ties to flagged endpoints: {', '.join(indirect_suspicious[:2])}",
                    indirect_suspicious,
                    aliases=["P12_INDIRECT_EXPOSURE"],
                )

        # -------------------------------------------------------------
        # Priority 12: Creating a New Wallet with Sudden High Activity (Weight ~32-37, MEDIUM)
        # -------------------------------------------------------------
        if wallet.transactionCount <= 5 and total_volume >= (large_tx_threshold * Decimal("0.8")):
            vol_ratio = float(total_volume / large_tx_threshold) if large_tx_threshold > 0 else 1.0
            p12_weight = min(37, 32 + int(min(5.0, vol_ratio)))
            add_rule(
                "P12_CREATING_A_NEW_WALLET", 12, "Creating a New Wallet with Sudden Volume Surge", "MEDIUM", p12_weight,
                "Wallet was recently generated but immediately transferred significant digital asset volume.",
                [f"Low lifetime tx count ({wallet.transactionCount}) vs High volume ({total_volume:.2f} {asset_symbol})"],
                aliases=["P11_NEW_WALLET_SURGE"],
            )

        # -------------------------------------------------------------
        # Priority 13: No VASP Account (Pure Unhosted Hopping) (Weight ~23-28, LOW_MEDIUM)
        # -------------------------------------------------------------
        has_vasp_counterparty = any(entity_service.is_vasp(cp) for cp in counterparty_addrs)
        if not has_vasp_counterparty and tx_count > 0:
            p13_weight = min(28, 23 + int(min(5, tx_count // 4)))
            add_rule(
                "P13_NO_VASP_ACCOUNT", 13, "No VASP Account (Pure Unhosted Hopping)", "LOW_MEDIUM", p13_weight,
                "All counterparties are unhosted self-custody addresses with zero direct registered VASP links.",
                ["Zero 1-hop centralized exchange deposit/withdrawal events"],
                aliases=["P13_NO_VASP_ACCOUNT"],
            )

        # -------------------------------------------------------------
        # Priority 14: Holding a Lot of ETH (High Custodial Balance) (Weight ~12-18, INFORMATIONAL)
        # -------------------------------------------------------------
        if balance_num >= high_holding_threshold:
            bal_float = float(balance_num)
            p14_weight = min(18, 12 + int(min(6.0, math.log1p(bal_float) * 0.7)))
            add_rule(
                "P14_HOLDING_A_LOT_OF_ETH", 14, "Holding a Lot of ETH (High Custodial Balance)", "INFORMATIONAL", p14_weight,
                f"Wallet currently holds {balance_num:.4f} {asset_symbol} in liquid custody.",
                [f"On-chain balance: {balance_num:.4f} {asset_symbol}"],
                aliases=["P14_HIGH_HOLDING"],
            )

        # -------------------------------------------------------------
        # Priority 15: Sending ETH Directly to Another Person (Direct P2P) (Weight ~9-13, INFORMATIONAL)
        # -------------------------------------------------------------
        direct_p2p_txs = [
            tx for tx in outgoing_txs
            if tx.toAddress and not entity_service.is_vasp(tx.toAddress)
        ]
        if direct_p2p_txs:
            p15_weight = min(13, 9 + int(min(4, len(direct_p2p_txs) // 2)))
            add_rule(
                "P15_SENDING_ETH_DIRECTLY_TO_PERSON", 15, "Sending ETH Directly to Another Person (Direct P2P)", "INFORMATIONAL", p15_weight,
                f"Direct unhosted peer-to-peer asset transfers observed outside smart contracts or custodial rails ({len(direct_p2p_txs)} P2P transfers).",
                [f"Direct transfer to {direct_p2p_txs[0].toAddress[:8]}... ({direct_p2p_txs[0].value} {asset_symbol})"],
                aliases=["P15_DIRECT_P2P"],
            )

        # -------------------------------------------------------------
        # Priority 16: Using Ethereum for Day-to-Day Purposes (Weight ~-17 to -23, CLEAN DAMPENER)
        # -------------------------------------------------------------
        has_critical = has_sanction or has_ransom or has_stolen or has_malicious
        if enable_vasp_dampener and has_vasp_counterparty and not has_critical and not has_mixer:
            p16_weight = -17 - min(6, len(counterparty_addrs) // 3)
            add_rule(
                "P16_DAY_TO_DAY_PURPOSES", 16, "Using Ethereum for Day-to-Day Purposes (Routine Retail Baseline)", "CLEAN_BASELINE", p16_weight,
                "Normal personal/commercial utility with verified regulated exchange counterparties without illicit nexus.",
                ["Verified interactions with regulated custodial exchanges"],
                aliases=["P15_RETAIL_CLEAN", "P16_RETAIL_CLEAN"],
            )

        # -------------------------------------------------------------
        # Calculate Final Suspicion Score (0 to 100) - Continuous & Precise
        # -------------------------------------------------------------
        pos_rules = [r for r in triggered_rules if r.get("weight", 0) > 0]
        damp_rules = [r for r in triggered_rules if r.get("weight", 0) < 0]

        if not pos_rules:
            damp_sum = sum(r.get("weight", 0) for r in damp_rules)
            base_score = max(4.0, 14.0 + float(damp_sum) * 0.35)
        else:
            sorted_weights = sorted([float(r.get("weight", 0)) for r in pos_rules], reverse=True)
            anchor = sorted_weights[0]

            # Diminishing non-linear addition for secondary independent indicators
            secondary_acc = 0.0
            for idx, w in enumerate(sorted_weights[1:]):
                rank_decay = 1.0 / (1.7 + 0.35 * idx)
                secondary_acc += (w * 0.16) * rank_decay

            # Volume intensity scaling
            vol_float = float(total_volume)
            vol_shift = min(3.5, max(-2.0, math.log1p(max(0.0, vol_float)) * 0.55 - 1.2))

            # Dampener impact
            damp_sum = sum(float(r.get("weight", 0)) for r in damp_rules)
            damp_offset = damp_sum * 0.40

            raw_score = anchor * 0.86 + secondary_acc + vol_shift + damp_offset
            base_score = min(98.4, max(4.0, raw_score))

        # Scale by Investigator Sensitivity Multiplier
        scaled_score = Decimal(str(round(base_score, 2))) * sensitivity_mult
        suspicion_score = max(1, min(99, int(round(float(scaled_score)))))
        precise_score = round(float(min(Decimal("99.9"), max(Decimal("1.0"), scaled_score))), 1)

        # Risk Classification & Color Code
        if suspicion_score >= 85:
            risk_level = "CRITICAL"
            node_color = "#ef4444"  # Red
            tag_label = "Critical Threat"
        elif suspicion_score >= 60:
            risk_level = "HIGH"
            node_color = "#f97316"  # Orange
            tag_label = "High Risk"
        elif suspicion_score >= 25:
            risk_level = "MEDIUM"
            node_color = "#eab308"  # Yellow
            tag_label = "Medium Suspicion"
        else:
            risk_level = "LOW"
            node_color = "#10b981"  # Emerald Green
            tag_label = "Low Risk / Clean"

        # Check if target itself is a known VASP
        if entity_service.is_vasp(clean_addr):
            node_color = "#f59e0b"  # Gold for Regulated VASP
            tag_label = "Regulated VASP"

        return {
            "address": clean_addr,
            "suspicionScore": suspicion_score,
            "preciseScore": precise_score,
            "riskLevel": risk_level,
            "riskClassification": risk_level,
            "nodeColor": node_color,
            "tagLabel": tag_label,
            "triggeredRulesCount": len(triggered_rules),
            "triggeredRules": triggered_rules,
            "heuristicsBreakdown": {
                "baseScore": round(float(base_score), 1),
                "normalizedScore": suspicion_score,
                "preciseScore": precise_score,
                "sensitivityMultiplier": float(sensitivity_mult),
                "mixerBooster": bool((has_mixer or has_coinjoin_tx) and enable_mixer_booster),
                "vaspDampener": bool(enable_vasp_dampener and has_vasp_counterparty),
                "hasCriticalTrigger": bool(has_critical),
            },
            "recommendation": (
                "IMMEDIATE STATUTORY FREEZE: High-priority nexus to illicit laundering infrastructure."
                if suspicion_score >= 75
                else "CONTINUED MONITORING: Transaction patterns exhibit notable velocity or unhosted clustering."
                if suspicion_score >= 35
                else "STANDARD BASELINE: No critical anomaly identified in current transaction window."
            ),
            "evaluatedAt": datetime.now(timezone.utc).isoformat(),
            "systemLogicApplied": {
                "profile": profile,
                "sensitivityMultiplier": float(sensitivity_mult),
                "largeTransferThreshold": float(large_tx_threshold),
                "burstVelocityThreshold": int(velocity_threshold),
                "enableMixerBooster": enable_mixer_booster,
                "enableVaspDampener": enable_vasp_dampener,
                "disabledRulesCount": len(disabled_rules),
            },
            "availableProfiles": [
                {"id": "balanced", "name": "Standard LEA SOP (Balanced)", "description": "Standard regulatory baseline with balanced thresholds."},
                {"id": "strict", "name": "Terror & Ransomware (Strict Zero-Tolerance)", "description": "1.25x multiplier, lowered burst thresholds, disables VASP dampener."},
                {"id": "fraud_syndicate", "name": "Cyber Syndicate & Peeling Chains", "description": "Prioritizes rapid pass-through, mule clusters, and unhosted hops."},
                {"id": "relaxed", "name": "Commercial / OTC Trader (Relaxed)", "description": "0.75x multiplier for high-net-worth commercial entities."},
                {"id": "custom", "name": "Custom Investigator Logic", "description": "User-tuned thresholds, rule toggles, and weight overrides."},
            ]
        }


rule_engine = ForensicRuleEngine()
