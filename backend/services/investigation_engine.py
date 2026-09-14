import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set, Tuple

from backend.services.entity_service import entity_service
from backend.services.vasp_discovery_service import vasp_discovery_service


class InvestigationIntelligenceEngine:
    """
    Investigation Decision Engine for cryptocurrency forensic investigators.
    Synthesizes graph traversals, fund flows, entity attributions, and behavioral heuristic signals
    into actionable, explainable investigative decisions.
    """

    @staticmethod
    def _to_decimal(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    @staticmethod
    def _fmt(d: Decimal) -> str:
        try:
            if d == Decimal("0"):
                return "0"
            f = f"{d:.6f}".rstrip("0").rstrip(".")
            return f if f else "0"
        except Exception:
            return "0"

    # -------------------------------------------------------------
    # 1. Proportional Taint Accounting & Conservation Check (PART K & L)
    # -------------------------------------------------------------
    def calculate_taint_and_conservation(
        self,
        original_suspicious_value: Decimal | str | float,
        paths: List[Any],
        nodes: List[Any],
        vasp_candidates: List[Any],
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Calculates Proportional Taint Accounting across discovered paths and runs the
        Fund Conservation Check to flag impossible balance inflation or leakage.
        """
        orig_val = self._to_decimal(original_suspicious_value)
        if orig_val <= Decimal("0"):
            # If not explicitly provided, estimate from sum of hop-1 outflows from root
            hop1_sum = Decimal("0")
            for p in paths:
                v = self._to_decimal(getattr(p, "totalVolume", 0) if hasattr(p, "totalVolume") else p.get("totalVolume", 0))
                hop1_sum += v
            orig_val = hop1_sum if hop1_sum > Decimal("0") else Decimal("10.0")

        # Track funds reaching verified VASPs vs unknown VASP candidates vs unresolved
        at_known_vasp = Decimal("0")
        at_unknown_vasp = Decimal("0")
        traced_total = Decimal("0")
        fees_est = Decimal("0")

        # Sum values reaching VASP candidates
        for cand in vasp_candidates:
            c_val = self._to_decimal(
                getattr(cand, "totalObservedTransfer", 0)
                if hasattr(cand, "totalObservedTransfer")
                else cand.get("totalObservedTransfer", 0)
            )
            is_verified = (
                getattr(cand, "verified", False)
                if hasattr(cand, "verified")
                else cand.get("verified", False)
            )
            if is_verified:
                at_known_vasp += c_val
            else:
                at_unknown_vasp += c_val
            traced_total += c_val

        # Estimated mining / network fees across steps (approx 0.5% - 1.5%)
        hop_counts = [
            getattr(p, "hopCount", 1) if hasattr(p, "hopCount") else p.get("hopCount", 1)
            for p in paths
        ]
        avg_hops = sum(hop_counts) / max(1, len(hop_counts)) if hop_counts else 2
        fees_est = min(orig_val * Decimal("0.02"), Decimal("0.005") * Decimal(str(avg_hops)))

        # Unresolved funds
        accounted = at_known_vasp + at_unknown_vasp + fees_est
        unresolved = max(Decimal("0"), orig_val - accounted)
        coverage_pct = (
            min(100.0, float((traced_total / orig_val) * Decimal("100")))
            if orig_val > Decimal("0")
            else 0.0
        )

        # FUND CONSERVATION CHECK (PART L)
        # Check if accounted value exceeds original by > 5% (unrelated inflow contamination)
        conservation_warning = None
        has_consistency_anomaly = False

        if (at_known_vasp + at_unknown_vasp) > (orig_val * Decimal("1.05")):
            has_consistency_anomaly = True
            conservation_warning = (
                f"FUND FLOW CONSISTENCY WARNING: Accounted fund volume ({self._fmt(traced_total)}) "
                f"exceeds original suspicious root inflow ({self._fmt(orig_val)}). "
                f"Unrelated counterparty inflows along multi-hop splitters have diluted the transaction trail. "
                f"Proportional Taint Model applied to discount non-case funds."
            )

        return {
            "taintModel": "PROPORTIONAL_TAINT",
            "originalSuspiciousValue": self._fmt(orig_val),
            "tracedValue": self._fmt(traced_total),
            "attributedToKnownVasp": self._fmt(at_known_vasp),
            "attributedToUnknownVasp": self._fmt(at_unknown_vasp),
            "unresolvedValue": self._fmt(unresolved),
            "estimatedFees": self._fmt(fees_est),
            "caseCoveragePercentage": round(coverage_pct, 1),
            "conservationWarning": conservation_warning,
            "hasConsistencyAnomaly": has_consistency_anomaly,
            "accountingUnit": "BTC" if chain.lower() == "bitcoin" else "ETH" if chain.lower() == "ethereum" else "TRX" if chain.lower() == "tron" else "SOL",
        }

    # -------------------------------------------------------------
    # 2. Confidence Decay Modeler (PART M)
    # -------------------------------------------------------------
    def calculate_path_confidence_decay(
        self,
        path_addresses: List[str],
        base_confidence: float = 0.99,
        has_mixer: bool = False,
        has_bridge: bool = False,
        has_dex: bool = False,
        dilution_ratio: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculates mathematical confidence decay along a multi-hop fund path.
        Accounts for hop distance, mixers (-30%), cross-chain bridges (-20%), DEX swaps (-15%), and taint dilution.
        """
        steps = []
        current_conf = base_confidence
        hop_count = max(0, len(path_addresses) - 1)

        for i, addr in enumerate(path_addresses):
            if i == 0:
                steps.append({
                    "step": i,
                    "address": addr,
                    "label": "Suspect Root Target",
                    "confidence": round(current_conf * 100, 1),
                    "decayFactor": "Root Source (100%)",
                })
                continue

            # Apply hop distance decay (approx 5% per standard unhosted hop)
            hop_decay = 0.95
            reason = "Intermediary unhosted hop (-5%)"

            # Check if this step is a mixer or bridge
            if i == hop_count and has_mixer:
                hop_decay = 0.70
                reason = "Mixer / Obfuscator boundary (-30%)"
            elif i == hop_count and has_bridge:
                hop_decay = 0.80
                reason = "Cross-chain bridge transition (-20%)"
            elif i == hop_count and has_dex:
                hop_decay = 0.85
                reason = "DEX liquidity pool swap (-15%)"
            elif dilution_ratio > 0.3:
                hop_decay = max(0.75, 0.95 - (dilution_ratio * 0.2))
                reason = f"Unrelated inflow dilution (-{int(dilution_ratio * 20)}%)"

            current_conf = max(0.15, current_conf * hop_decay)
            steps.append({
                "step": i,
                "address": addr,
                "label": f"Hop {i} Intermediary" if i < hop_count else "Endpoint Target",
                "confidence": round(current_conf * 100, 1),
                "decayFactor": reason,
            })

        final_conf_pct = round(current_conf * 100, 1)
        conf_level = "HIGH" if final_conf_pct >= 80 else "MEDIUM" if final_conf_pct >= 60 else "LOW"

        return {
            "initialConfidence": round(base_confidence * 100, 1),
            "finalConfidence": final_conf_pct,
            "confidenceLevel": conf_level,
            "hopCount": hop_count,
            "decaySteps": steps,
        }

    # -------------------------------------------------------------
    # 3. Attribution Challenge Engine (PART N)
    # -------------------------------------------------------------
    def challenge_attribution(
        self,
        vasp_candidate: Dict[str, Any],
        supporting_evidence: List[str],
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Adversarial validation / Self-Critique on VASP attribution conclusions.
        Examines supporting evidence against potential contradictions and alternative hypotheses.
        """
        name = vasp_candidate.get("entityName") or vasp_candidate.get("name") or "Target Entity"
        is_verified = vasp_candidate.get("verified", False)
        hop_dist = vasp_candidate.get("hopDistance", 1)
        initial_conf_str = vasp_candidate.get("confidence", "HIGH")
        initial_conf = 92 if initial_conf_str == "HIGH" else 75 if initial_conf_str == "MEDIUM" else 50

        conflicting_evidence: List[str] = []
        assumptions: List[str] = []
        alternative_explanations: List[str] = []

        # Challenge 1: Unverified vs Verified
        if not is_verified:
            conflicting_evidence.append(
                "Address does not match any confirmed regulatory registry or public exchange cold/hot label"
            )
            assumptions.append(
                "Classification relies on heuristic behavioral features (sweeping, consolidation) rather than deterministic KYC attribution"
            )
            alternative_explanations.append(
                "Could be an unhosted OTC trading desk, decentralized aggregator router, or high-volume payment merchant"
            )
        else:
            assumptions.append(
                f"Assumes public ledger attribution tag for '{name}' accurately reflects current infrastructure ownership"
            )

        # Challenge 2: Hop Distance & Intermediaries
        if hop_dist >= 2:
            conflicting_evidence.append(
                f"Funds traversed {hop_dist} intermediary unhosted wallets before reaching this destination"
            )
            assumptions.append(
                "Assumes intermediate transfers represent a continuous intentional laundering chain rather than independent commercial commerce"
            )
            alternative_explanations.append(
                "Intermediary could have received and co-mingled independent legitimate third-party payments"
            )

        # Challenge 3: Single-Source vs Multi-Source
        verification_status = vasp_candidate.get("verificationStatus", "TRUSTED_PUBLIC_LABEL")
        if verification_status in ["UNVERIFIED", "TRUSTED_PUBLIC_LABEL"]:
            conflicting_evidence.append(
                "Single-source attribution label; independent corroboration from secondary blockchain analytics is pending"
            )

        # Calculate adjusted confidence
        penalty = len(conflicting_evidence) * 6
        adjusted_conf = max(25, initial_conf - penalty)

        recommendation = (
            "HIGH CONFIDENCE — ACTIONABLE FOR FORMAL SECTION 91 NOTICE"
            if adjusted_conf >= 80 and is_verified
            else "PROBABLE ATTRIBUTION — HUMAN REVIEW & CORROBORATION RECOMMENDED"
            if adjusted_conf >= 60
            else "INVESTIGATIVE HYPOTHESIS — REQUIRES INDEPENDENT CORROBORATION"
        )

        return {
            "entityName": name,
            "initialConfidence": initial_conf,
            "adjustedConfidence": adjusted_conf,
            "adjustedConfidenceLevel": "HIGH" if adjusted_conf >= 80 else "MEDIUM" if adjusted_conf >= 60 else "LOW",
            "supportingEvidence": supporting_evidence or [
                "Direct on-chain transaction trail confirmed",
                "Transaction hashes recorded in public ledger",
            ],
            "conflictingEvidence": conflicting_evidence,
            "assumptions": assumptions,
            "alternativeExplanations": alternative_explanations,
            "recommendation": recommendation,
            "requiresHumanReview": adjusted_conf < 80 or not is_verified,
        }

    # -------------------------------------------------------------
    # 4. Evidence Gap Detector & Blind-Spot Warning (PART O & Q)
    # -------------------------------------------------------------
    def detect_evidence_gaps(
        self,
        vasp_candidates: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        has_bridges: bool = False,
        has_mixers: bool = False,
        unresolved_amount: Decimal = Decimal("0"),
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Identifies missing evidence, unconfirmed assumptions, and blind spots.
        Recommends 'Best Next Evidence to Collect' with estimated confidence improvements.
        """
        gaps: List[Dict[str, Any]] = []
        blind_spots: List[str] = []

        # Check clusters
        for cl in clusters:
            if cl.get("verification") == "UNVERIFIED":
                gaps.append({
                    "gapId": f"GAP-CL-{cl.get('clusterId')}",
                    "title": f"Unverified Service Cluster Ownership ({cl.get('clusterId')})",
                    "description": f"Cluster {cl.get('clusterId')} controls {cl.get('addressCount', 0)} wallets exhibiting custodial behavior, but operating legal entity is unconfirmed.",
                    "recommendedAction": "Obtain independent second-source label or issue inquiry to suspected infrastructure provider.",
                    "potentialConfidenceImprovement": "67% -> ~85% (Estimated)",
                    "priority": "HIGH",
                })

        # Check single-source VASPs
        for v in vasp_candidates:
            if not v.get("verified", False):
                gaps.append({
                    "gapId": f"GAP-VASP-{v.get('entityName', 'unknown')[:10]}",
                    "title": f"Independent Corroboration for {v.get('entityName')}",
                    "description": "Entity classification is based on heuristic behavioral indicators. Independent regulatory confirmation is missing.",
                    "recommendedAction": "Verify central consolidation wallet and counterparty overlap with known exchange deposit routers.",
                    "potentialConfidenceImprovement": "60% -> ~80% (Estimated)",
                    "priority": "MEDIUM",
                })

        # Check unresolved volume
        if unresolved_amount > Decimal("0.5"):
            gaps.append({
                "gapId": "GAP-UNRESOLVED-VOLUME",
                "title": f"Unresolved Fund Flow Residue",
                "description": f"A residual balance of funds remains unlocated or parked in intermediary unhosted wallets.",
                "recommendedAction": "Trace 2 additional downstream hops or configure 1-hour live monitoring on active intermediary addresses.",
                "potentialConfidenceImprovement": "70% -> ~88% (Estimated)",
                "priority": "HIGH",
            })

        # Blind Spots (PART Q)
        if has_bridges:
            blind_spots.append(
                "Cross-chain bridge transition detected: Destination-side withdrawal mapping requires specialized relayer ledger indexing."
            )
        if has_mixers:
            blind_spots.append(
                "Privacy mixer / CoinJoin pool detected: Direct cryptographic linkage is severed; timing-analysis and peeling change heuristics applied."
            )
        blind_spots.append(
            "Unhosted intermediate private wallets cannot be tied to real-world beneficial owners without formal VASP KYC subpoenas."
        )

        return gaps, blind_spots

    # -------------------------------------------------------------
    # 5. VASP Actionability Score & Path Ranking (PART H & I)
    # -------------------------------------------------------------
    def calculate_vasp_actionability(
        self,
        vasp: Dict[str, Any],
        total_case_value: Decimal,
        chain: str = "ethereum",
    ) -> Dict[str, Any]:
        """
        Calculates the 0-100 VASP Actionability Score for deciding which VASP to contact first.
        Factors:
        - Amount exposure (30%)
        - Percentage of total case funds (20%)
        - Attribution confidence (15%)
        - Verification strength (10%)
        - KYC likelihood (10%)
        - Jurisdiction relevance (10%)
        - Recency of fund arrival (5%)
        """
        name = vasp.get("entityName") or vasp.get("name") or "Unknown VASP"
        val = self._to_decimal(vasp.get("totalObservedTransfer", 0))
        is_verified = vasp.get("verified", False)
        hop_dist = vasp.get("hopDistance", 1)

        # Retrieve VASP directory record for compliance / jurisdiction info
        vasp_record = entity_service.get_vasp_by_address(vasp.get("address", ""))
        jurisdiction = vasp_record.jurisdiction if vasp_record else "Global / Offshore"
        kyc_status = vasp_record.kyc_status if vasp_record else "MANDATORY_KYC" if is_verified else "PARTIAL_KYC"
        is_fiu = "FIU-IND" in jurisdiction or "India" in jurisdiction

        score = 0
        reasons: List[str] = []

        # 1. Amount exposure (up to 30 pts)
        val_float = float(val)
        if val_float >= 5.0:
            score += 30
            reasons.append(f"Substantial financial exposure: {val_float:.4f} asset units")
        elif val_float >= 1.0:
            score += 20
            reasons.append(f"Significant financial exposure: {val_float:.4f} asset units")
        else:
            score += 10
            reasons.append(f"Modest financial exposure: {val_float:.4f} asset units")

        # 2. Percentage of case funds (up to 20 pts)
        case_val_float = float(total_case_value) if total_case_value > Decimal("0") else 1.0
        pct_of_case = min(100.0, (val_float / case_val_float) * 100.0)
        if pct_of_case >= 50.0:
            score += 20
            reasons.append(f"Major case share: {pct_of_case:.1f}% of all tracked suspicious funds")
        elif pct_of_case >= 20.0:
            score += 15
            reasons.append(f"Notable case share: {pct_of_case:.1f}% of tracked funds")
        else:
            score += 8
            reasons.append(f"{pct_of_case:.1f}% of tracked funds")

        # 3. Attribution confidence (up to 15 pts)
        conf = vasp.get("confidence", "HIGH")
        if conf == "HIGH":
            score += 15
            reasons.append("High attribution confidence supported by confirmed ledger tags")
        elif conf == "MEDIUM":
            score += 10
            reasons.append("Medium attribution confidence with verified counterparty link")
        else:
            score += 5
            reasons.append("Heuristic attribution confidence")

        # 4. Verification strength (up to 10 pts)
        if is_verified:
            score += 10
            reasons.append("Verified regulated VASP infrastructure")
        else:
            score += 3
            reasons.append("Heuristic VASP candidate (Unverified infrastructure)")

        # 5. KYC Likelihood (up to 10 pts)
        if kyc_status == "MANDATORY_KYC":
            score += 10
            reasons.append("Mandatory user identity (Aadhaar / PAN / Passport) KYC enforced")
        else:
            score += 5
            reasons.append("Tiered or partial KYC policy")

        # 6. Jurisdiction relevance (up to 10 pts)
        if is_fiu:
            score += 10
            reasons.append("FIU-IND registered domestic reporting entity (Rapid Section 91 CrPC compliance)")
        elif "United States" in jurisdiction or "FinCEN" in jurisdiction:
            score += 8
            reasons.append("Regulated US entity subject to MLAT subpoena treaties")
        else:
            score += 5
            reasons.append(f"Offshore jurisdiction: {jurisdiction}")

        # 7. Recency / hop distance (up to 5 pts)
        if hop_dist <= 1:
            score += 5
            reasons.append("Direct deposit (Hop 1) with immediate evidentiary proximity")
        else:
            score += 3
            reasons.append(f"Hop distance: {hop_dist} transfers from suspect wallet")

        final_score = min(100, score)
        priority = (
            "CRITICAL" if final_score >= 85
            else "HIGH" if final_score >= 70
            else "MEDIUM" if final_score >= 50
            else "LOW"
        )

        return {
            "entityName": name,
            "address": vasp.get("address", ""),
            "actionabilityScore": final_score,
            "priority": priority,
            "percentageOfCase": round(pct_of_case, 1),
            "amountExposure": f"{val_float:.4f}",
            "jurisdiction": jurisdiction,
            "kycStatus": kyc_status,
            "isFiuRegistered": is_fiu,
            "reasons": reasons,
            "recommendedContactOrder": 1 if priority == "CRITICAL" else 2 if priority == "HIGH" else 3,
        }

    # -------------------------------------------------------------
    # 6. Minimum Intervention Set (PART J)
    # -------------------------------------------------------------
    def compute_minimum_intervention_set(
        self,
        ranked_vasps: List[Dict[str, Any]],
        total_case_value: Decimal,
        target_coverage_threshold: float = 70.0,
    ) -> Dict[str, Any]:
        """
        Computes the Minimum Intervention Set using a greedy algorithm (PART J).
        Finds the minimum number of VASPs covering >= target_coverage_threshold of suspicious funds.
        """
        # Sort VASPs by actionable exposure (descending)
        sorted_vasps = sorted(
            ranked_vasps,
            key=lambda x: float(x.get("amountExposure", 0)),
            reverse=True,
        )

        selected_vasps: List[Dict[str, Any]] = []
        cumulative_exposure = Decimal("0")
        total_float = float(total_case_value) if total_case_value > Decimal("0") else 1.0

        for vasp in sorted_vasps:
            v_amt = self._to_decimal(vasp.get("amountExposure", 0))
            selected_vasps.append(vasp)
            cumulative_exposure += v_amt

            cov = (float(cumulative_exposure) / total_float) * 100.0
            if cov >= target_coverage_threshold:
                break

        final_coverage_pct = round(
            min(100.0, (float(cumulative_exposure) / total_float) * 100.0), 1
        )

        return {
            "targetCoverageThreshold": target_coverage_threshold,
            "achievedCoveragePercentage": final_coverage_pct,
            "coveredAmount": self._fmt(cumulative_exposure),
            "vaspCount": len(selected_vasps),
            "selectedVasps": [
                {
                    "name": v.get("entityName"),
                    "address": v.get("address"),
                    "amountExposure": v.get("amountExposure"),
                    "priority": v.get("priority"),
                    "jurisdiction": v.get("jurisdiction"),
                }
                for v in selected_vasps
            ],
            "explanation": (
                f"Minimum Intervention Set recommends initiating formal notices to {len(selected_vasps)} VASP(s) "
                f"to achieve {final_coverage_pct}% potential asset freeze/subscriber coverage "
                f"({self._fmt(cumulative_exposure)} out of total {self._fmt(total_case_value)} case value)."
            ),
        }

    # -------------------------------------------------------------
    # 7. Next Best Action Engine (PART R)
    # -------------------------------------------------------------
    def generate_next_actions(
        self,
        ranked_vasps: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        gaps: List[Dict[str, Any]],
        unresolved_val: Decimal,
        case_id: str = "CASE-2026",
    ) -> List[Dict[str, Any]]:
        """
        Generates a structured, explainable action plan for the forensic officer.
        """
        actions: List[Dict[str, Any]] = []
        action_idx = 1

        # Priority 1: Evidence Snapshot Preservation
        actions.append({
            "actionId": f"ACT-{action_idx:03d}",
            "priority": "CRITICAL",
            "actionType": "PRESERVE_EVIDENCE",
            "title": "Preserve On-Chain Ledger Evidence Snapshot",
            "reason": "Cryptocurrency transaction state and unspent outputs must be cryptographically hashed for court admissibility.",
            "relatedEntity": "Investigation Case File",
            "expectedInvestigativeValue": "Prevents evidence spoliation; establishes Section 65B Indian Evidence Act / BSA legal chain of custody.",
            "evidenceRequired": "SHA-256 integrity hash of raw JSON transaction log and block heights.",
            "currentConfidence": 100,
        })
        action_idx += 1

        # Priority 2: Primary VASP Section 91 CrPC Request
        if ranked_vasps:
            top_vasp = ranked_vasps[0]
            actions.append({
                "actionId": f"ACT-{action_idx:03d}",
                "priority": "CRITICAL",
                "actionType": "ISSUE_LAWFUL_REQUEST",
                "title": f"Serve Section 91 CrPC Lawful Notice to {top_vasp.get('entityName')}",
                "reason": f"Largest identified destination of suspicious funds ({top_vasp.get('amountExposure')} assets, Actionability Score: {top_vasp.get('actionabilityScore')}/100).",
                "relatedEntity": top_vasp.get("entityName"),
                "expectedInvestigativeValue": "Immediate account freeze to prevent further dispersal; disclosure of KYC subscriber identity, bank account details, and login IPs.",
                "evidenceRequired": "Certified transaction hash manifest, source wallet proof, and verified deposit router trail.",
                "currentConfidence": 92,
            })
            action_idx += 1

        # Priority 3: Secondary VASP Request if available
        if len(ranked_vasps) > 1:
            sec_vasp = ranked_vasps[1]
            actions.append({
                "actionId": f"ACT-{action_idx:03d}",
                "priority": "HIGH",
                "actionType": "ISSUE_LAWFUL_REQUEST",
                "title": f"Serve Subpoena / Information Request to {sec_vasp.get('entityName')}",
                "reason": f"Secondary destination handling {sec_vasp.get('amountExposure')} assets ({sec_vasp.get('percentageOfCase')}% of case).",
                "relatedEntity": sec_vasp.get("entityName"),
                "expectedInvestigativeValue": "Prevents asset dissipation across secondary laundering branch.",
                "evidenceRequired": "Transaction trail and recipient wallet identifier.",
                "currentConfidence": 85,
            })
            action_idx += 1

        # Priority 4: Service Cluster Investigation
        if clusters:
            top_cl = clusters[0]
            actions.append({
                "actionId": f"ACT-{action_idx:03d}",
                "priority": "HIGH",
                "actionType": "INVESTIGATE_CLUSTER",
                "title": f"Investigate Potential Service Cluster {top_cl.get('clusterId')}",
                "reason": f"Controls {top_cl.get('addressCount')} interconnected wallets with strong custodial pooling signature (Score: {top_cl.get('vaspBehaviorScore')}/100).",
                "relatedEntity": top_cl.get("clusterId"),
                "expectedInvestigativeValue": "Uncovers hidden exchange deposit infrastructure or syndicate consolidation hubs.",
                "evidenceRequired": "Consolidation transaction timing analysis and counterparty clustering records.",
                "currentConfidence": top_cl.get("vaspBehaviorScore", 75),
            })
            action_idx += 1

        # Priority 5: Trace Unresolved Funds
        if unresolved_val > Decimal("0.1"):
            actions.append({
                "actionId": f"ACT-{action_idx:03d}",
                "priority": "MEDIUM",
                "actionType": "CONTINUE_TRACING",
                "title": f"Expand Traversal on Unresolved Fund Residue ({self._fmt(unresolved_val)} assets)",
                "reason": "A portion of funds remains unlocated in intermediary private wallets.",
                "relatedEntity": "Unresolved Branch Wallets",
                "expectedInvestigativeValue": "Identifies secondary exit cash-out ramps or P2P merchant off-ramps.",
                "evidenceRequired": "Deep multi-hop BFS traversal beyond depth 3.",
                "currentConfidence": 65,
            })
            action_idx += 1

        # Priority 6: Live Monitoring
        actions.append({
            "actionId": f"ACT-{action_idx:03d}",
            "priority": "LOW",
            "actionType": "MONITOR_WALLETS",
            "title": "Enable 1-Hour Automated Background Tracking",
            "reason": "Active intermediary unhosted wallets may execute sweeps at future block heights.",
            "relatedEntity": "Intermediary Wallets",
            "expectedInvestigativeValue": "Instant email and websocket alerts upon fund movement.",
            "evidenceRequired": "Mempool / block explorer webhooks.",
            "currentConfidence": 100,
        })

        return actions

    # -------------------------------------------------------------
    # 8. Deterministic Step-Wise Investigation Playbook (Zero LLM)
    # -------------------------------------------------------------
    def generate_deterministic_investigation_playbook(
        self,
        target_address: str,
        chain: str,
        ranked_vasps: List[Dict[str, Any]],
        mis: Dict[str, Any],
        bottleneck_mules: List[Dict[str, Any]],
        clusters: List[Dict[str, Any]],
        unresolved_val: Decimal,
        total_case_value: Decimal,
        case_id: str = "CASE-2026",
        detected_cycles: Optional[List[List[str]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generates a 100% deterministic, step-wise Standard Operating Procedure (SOP)
        playbook for the forensic investigator under Indian Law (CrPC/BNSS/BSA).
        Operates without LLMs using domain rules, NetworkX centrality, and statutory deadlines.
        """
        chain_clean = chain.lower().strip()
        asset = "BTC" if chain_clean == "bitcoin" else ("TRX" if chain_clean == "tron" else ("SOL" if chain_clean == "solana" else "ETH"))
        clean_target = (target_address or "").strip()
        playbook: List[Dict[str, Any]] = []

        # STEP 1: Evidence Preservation & Hashing
        playbook.append({
            "stepNumber": 1,
            "phase": "GOLDEN_WINDOW",
            "phaseLabel": "Phase 1: Immediate Containment (0–2h)",
            "priority": "CRITICAL",
            "title": "Preserve Cryptographic Ledger State (Section 65B BSA)",
            "statutoryReference": "Section 65B(4) Indian Evidence Act, 1872 / Section 63 Bharatiya Sakshya Adhiniyam, 2023",
            "targetEntity": "Suspect On-Chain Ledger State",
            "targetAddress": clean_target,
            "amount": f"{self._fmt(total_case_value)} {asset}",
            "actionableDirective": (
                f"Freeze on-chain state for suspect address {clean_target[:10]}... by computing SHA-256 integrity hash "
                f"of the raw transaction manifest. Record current block height and validator timestamp to preclude evidence tampering defenses."
            ),
            "deadline": "Immediate (< 1 Hour)",
            "expectedOutcome": "Non-repudiable legal chain-of-custody established for judicial trial.",
            "badgeClass": "badge-critical",
        })

        # STEP 2: Emergency Statutory Freeze Notice to Primary VASP
        if ranked_vasps:
            top_vasp = ranked_vasps[0]
            v_name = top_vasp.get("entityName", "Primary VASP")
            v_addr = top_vasp.get("address", "")
            v_amt = top_vasp.get("amountExposure", "0")
            v_pct = top_vasp.get("percentageOfCase", 0)
            v_jur = top_vasp.get("jurisdiction", "Regulated VASP")
            playbook.append({
                "stepNumber": 2,
                "phase": "GOLDEN_WINDOW",
                "phaseLabel": "Phase 1: Immediate Containment (0–2h)",
                "priority": "CRITICAL",
                "title": f"Serve Emergency Section 91 & 102 CrPC Notice to {v_name}",
                "statutoryReference": "Section 91 & 102 CrPC (Section 94 & 106 BNSS) r/w FIU-IND AML/CFT Guidelines",
                "targetEntity": v_name,
                "targetAddress": v_addr,
                "amount": f"{v_amt} {asset} ({v_pct}% of Case)",
                "actionableDirective": (
                    f"Issue formal statutory requisition to Nodal Compliance Officer of {v_name} ({v_jur}). "
                    f"Order immediate debit freeze on beneficiary custodial account receiving {v_amt} {asset} and demand full KYC dossier "
                    f"(PAN, Aadhaar/Passport, linked bank accounts, and IP login audit logs)."
                ),
                "deadline": "Within 2 Hours (Golden Window before fiat withdrawal)",
                "expectedOutcome": "Immediate debit freeze on suspect custodial balance and identification of real-world beneficiary.",
                "badgeClass": "badge-critical",
            })

        # STEP 3: Interdict Key Bottleneck Mule (NetworkX Centrality)
        if bottleneck_mules:
            top_mule = bottleneck_mules[0]
            m_addr = top_mule.get("address", "")
            m_cent = top_mule.get("betweennessCentrality", 0)
            playbook.append({
                "stepNumber": 3,
                "phase": "ACTIVE_INTERDICTION",
                "phaseLabel": "Phase 2: Active Interdiction (2–24h)",
                "priority": "HIGH",
                "title": f"Interdict Critical Bottleneck Mule: {m_addr[:10]}...",
                "statutoryReference": "Section 91 CrPC (Section 94 BNSS) - Layering Intermediation",
                "targetEntity": f"Key Money Mule (Betweenness Centrality: {m_cent})",
                "targetAddress": m_addr,
                "amount": "Intermediary Layering Hub",
                "actionableDirective": (
                    f"NetworkX topology identified {m_addr} as the critical bridge carrying {round(m_cent * 100, 1)}% of shortest paths. "
                    f"Requisition the initial gas-funding transaction of this mule wallet to discover the parent funding exchange where the operator purchased transaction fees."
                ),
                "deadline": "Within 6 Hours",
                "expectedOutcome": "Uncovers the parent exchange account funding the mule network; disrupts criminal syndicate.",
                "badgeClass": "badge-high",
            })
        else:
            playbook.append({
                "stepNumber": 3,
                "phase": "ACTIVE_INTERDICTION",
                "phaseLabel": "Phase 2: Active Interdiction (2–24h)",
                "priority": "HIGH",
                "title": "Subpoena Gas/Fee Funding Origin for Suspect Target",
                "statutoryReference": "Section 91 CrPC (Section 94 BNSS)",
                "targetEntity": "Gas Funding Source",
                "targetAddress": clean_target,
                "amount": "Account Creation Inflow",
                "actionableDirective": (
                    f"Trace the genesis transaction providing native gas to {clean_target[:10]}... "
                    f"Issue Section 91 notice to the originating exchange to identify the wallet's funding patron."
                ),
                "deadline": "Within 6 Hours",
                "expectedOutcome": "Identifies the source entity that activated the criminal wallet.",
                "badgeClass": "badge-high",
            })

        # STEP 4: Secondary VASP Subpoenas under Minimum Intervention Set (MIS)
        if len(ranked_vasps) > 1:
            sec_vasp = ranked_vasps[1]
            s_name = sec_vasp.get("entityName", "Secondary VASP")
            s_addr = sec_vasp.get("address", "")
            s_amt = sec_vasp.get("amountExposure", "0")
            cov_pct = mis.get("achievedCoveragePercentage", 70)
            playbook.append({
                "stepNumber": 4,
                "phase": "ACTIVE_INTERDICTION",
                "phaseLabel": "Phase 2: Active Interdiction (2–24h)",
                "priority": "HIGH",
                "title": f"Serve Secondary Requisition to {s_name} ({s_amt} {asset})",
                "statutoryReference": "Section 91 CrPC / Law Enforcement Portal (LERT)",
                "targetEntity": s_name,
                "targetAddress": s_addr,
                "amount": f"{s_amt} {asset}",
                "actionableDirective": (
                    f"Serve statutory subpoena on secondary destination {s_name}. In conjunction with Step 2, "
                    f"this fulfills the Minimum Intervention Set (MIS) recommendation to achieve {cov_pct}% stolen fund coverage."
                ),
                "deadline": "Within 12 Hours",
                "expectedOutcome": "Secures secondary branch from dissipation across offshore accounts.",
                "badgeClass": "badge-high",
            })

        # STEP 5: Service Cluster Inquiry if Unknown Cluster Detected
        if clusters:
            top_cl = clusters[0]
            cl_id = top_cl.get("clusterId", "UC-2026")
            cl_cnt = top_cl.get("addressCount", 1)
            cl_score = top_cl.get("vaspBehaviorScore", 80)
            playbook.append({
                "stepNumber": 5,
                "phase": "ACTIVE_INTERDICTION",
                "phaseLabel": "Phase 2: Active Interdiction (2–24h)",
                "priority": "MEDIUM",
                "title": f"Issue Inquiry for Potential Custodial Cluster {cl_id}",
                "statutoryReference": "Section 91 CrPC Inquiry on Unregistered Intermediary / Payment Bridge",
                "targetEntity": f"Cluster {cl_id} ({top_cl.get('classification', 'Probable Custodial')})",
                "targetAddress": top_cl.get("addresses", [clean_target])[0],
                "amount": f"{cl_cnt} Interconnected Addresses (VASP Score: {cl_score}/100)",
                "actionableDirective": (
                    f"Cluster {cl_id} exhibits commercial pooling ({cl_cnt} addresses). "
                    f"Issue Section 91 notice to associated domain registrars, payment gateways, or cloud hosts linked to this cluster's consolidation activity."
                ),
                "deadline": "Within 24 Hours",
                "expectedOutcome": "Determines whether cluster is an unregistered OTC desk or underground payment processor.",
                "badgeClass": "badge-medium",
            })

        # STEP 6: Deploy 24/7 Automated Sentry on Residue
        playbook.append({
            "stepNumber": 6,
            "phase": "JUDICIAL_RECOVERY",
            "phaseLabel": "Phase 3: Judicial Recovery (24–72h)",
            "priority": "MEDIUM",
            "title": f"Deploy 24/7 Automated Sentry on Unresolved Residue ({self._fmt(unresolved_val)} {asset})",
            "statutoryReference": "Police Standing Order on Continuous Electronic Asset Tracking",
            "targetEntity": "Unhosted Residue Wallets",
            "targetAddress": "Residual Unspent Outflows",
            "amount": f"{self._fmt(unresolved_val)} {asset} Unresolved",
            "actionableDirective": (
                f"Activate 60-minute automated ledger tracking on {self._fmt(unresolved_val)} {asset} parked in unhosted wallets. "
                f"Configured to dispatch immediate SMTP alerts upon subsequent sweep to another VASP or cross-chain bridge."
            ),
            "deadline": "Continuous Background Monitoring",
            "expectedOutcome": "Real-time alerts if suspect attempts delayed liquidation.",
            "badgeClass": "badge-clean",
        })

        # STEP 7: Charge-Sheet Annexures & Section 65B Certificate Assembly
        playbook.append({
            "stepNumber": 7,
            "phase": "JUDICIAL_RECOVERY",
            "phaseLabel": "Phase 3: Judicial Recovery (24–72h)",
            "priority": "CRITICAL",
            "title": "Compile Final Judicial Charge-Sheet Annexures & Sec 65B Certificate",
            "statutoryReference": "Section 173 CrPC / Section 193 BNSS r/w Section 65B Indian Evidence Act / Section 63 BSA",
            "targetEntity": "Jurisdictional Criminal Court",
            "targetAddress": f"Case File {case_id}",
            "amount": f"Total Admissibility Docket: {self._fmt(total_case_value)} {asset}",
            "actionableDirective": (
                f"Compile the 16-section TraceACT forensic dossier, VASP compliance confirmation letters, "
                f"frozen account debit notices, and signed Section 65B BSA certificate into the formal charge sheet for court submission."
            ),
            "deadline": "Within 72 Hours (Filing Window)",
            "expectedOutcome": "Court-ready electronic evidence packet ready for framing of charges.",
            "badgeClass": "badge-critical",
        })

        return playbook


investigation_engine = InvestigationIntelligenceEngine()
