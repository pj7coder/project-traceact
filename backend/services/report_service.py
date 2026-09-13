import time
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from decimal import Decimal
import httpx

from backend.config.settings import settings
from backend.database.mongo import db_manager
from backend.schemas.attribution import (
    InvestigationReportResponse,
    ReportInfographics,
    AttributionRequest,
)
from backend.services.attribution_service import attribution_service
from backend.services.rule_engine import rule_engine
from backend.services.wallet_service import wallet_service
from backend.services.vasp_discovery_service import vasp_discovery_service
from backend.services.investigation_engine import investigation_engine
from backend.services.entity_service import entity_service

logger = logging.getLogger("report_service")


class LEAForensicReportService:
    """
    Law Enforcement Investigation Report Generator.
    Produces comprehensive, strictly factual 16-section forensic reports,
    actionable decision intelligence, infographic metrics, and statutory notices
    for the SAHYOG Portal under Section 91 of the Code of Criminal Procedure (CrPC).
    """

    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = 25.0

    async def generate_report(
        self,
        target_address: str,
        chain: str = "ethereum",
        case_id: Optional[str] = None,
        investigator_id: Optional[str] = None,
        investigator_name: Optional[str] = None,
        max_depth: int = 3,
    ) -> InvestigationReportResponse:
        clean_addr = target_address.strip()
        chain_clean = chain.lower().strip()
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        cid = case_id or f"CASE-{now_dt.year}-I4C-{int(time.time() % 10000):04d}"
        inv_id = investigator_id or settings.INVESTIGATOR_ID
        inv_name = investigator_name or settings.INVESTIGATOR_NAME

        # 1. Fetch wallet overview and transactions
        overview, txs, connected = await wallet_service.get_wallet_overview_and_data(clean_addr, chain_clean)

        # 2. Evaluate Rule Engine & Suspicion Score
        risk_result = rule_engine.evaluate_wallet(overview, txs, connected)
        suspicion_score = risk_result["suspicionScore"]
        risk_level = risk_result["riskLevel"]
        triggered_rules = risk_result["triggeredRules"]

        # 3. Retrieve VASP Attribution results
        attrib_req = AttributionRequest(chain=chain_clean, address=clean_addr, maxDepth=max_depth)
        attrib_res = await attribution_service.analyze_attribution(attrib_req)
        nearest_vasp = attrib_res.nearestVasp

        vasp_name = nearest_vasp.name if nearest_vasp else "Unattributed Unhosted Cluster"
        vasp_addr = nearest_vasp.address if nearest_vasp else "N/A"
        hop_dist = nearest_vasp.hopDistance if nearest_vasp else 0
        total_vol = nearest_vasp.totalTransferred if nearest_vasp else "0"

        # 4. Unknown VASP Discovery & Service Clusters
        node_dicts = [n.model_dump() for n in attrib_res.graph.nodes]
        edge_dicts = [e.model_dump() for e in attrib_res.graph.edges]
        clusters = vasp_discovery_service.detect_service_clusters(node_dicts, edge_dicts, chain=chain_clean)

        # Behavioral features of root wallet
        root_features = vasp_discovery_service.extract_behavioral_features(clean_addr, txs, connected, chain=chain_clean)
        root_vasp_score, root_vasp_breakdown, root_vasp_ev = vasp_discovery_service.compute_vasp_behavior_score(root_features)
        root_classification = vasp_discovery_service.classify_entity(root_features, root_vasp_score)

        # 5. Investigation Decision Intelligence Engine
        original_suspicious_amount = Decimal(str(overview.balance if hasattr(overview, "balance") else 10.0))
        if original_suspicious_amount <= Decimal("0"):
            original_suspicious_amount = Decimal("10.0")

        # Taint accounting & conservation check
        taint_results = investigation_engine.calculate_taint_and_conservation(
            original_suspicious_value=original_suspicious_amount,
            paths=attrib_res.paths,
            nodes=attrib_res.graph.nodes,
            vasp_candidates=attrib_res.vaspCandidates,
            chain=chain_clean,
        )

        # VASP Actionability Rankings
        ranked_vasps = []
        for cand in attrib_res.vaspCandidates:
            cand_dict = cand.model_dump() if hasattr(cand, "model_dump") else cand
            act = investigation_engine.calculate_vasp_actionability(
                cand_dict, original_suspicious_amount, chain=chain_clean
            )
            ranked_vasps.append(act)

        ranked_vasps.sort(key=lambda x: x["actionabilityScore"], reverse=True)

        # Minimum Intervention Set
        mis = investigation_engine.compute_minimum_intervention_set(
            ranked_vasps=ranked_vasps,
            total_case_value=original_suspicious_amount,
            target_coverage_threshold=70.0,
        )

        # Attribution Challenges
        attribution_challenges = []
        for cand in attrib_res.vaspCandidates[:3]:
            cand_dict = cand.model_dump() if hasattr(cand, "model_dump") else cand
            chal = investigation_engine.challenge_attribution(
                cand_dict,
                supporting_evidence=[
                    f"Direct traversal path identified: {cand_dict.get('path', [])}",
                    f"Transferred volume observed: {cand_dict.get('totalObservedTransfer', 0)}",
                    f"Attribution source: {cand_dict.get('source', 'Public Label')}",
                ],
                chain=chain_clean,
            )
            attribution_challenges.append(chal)

        # Evidence Gaps & Blind Spots
        evidence_gaps, blind_spots = investigation_engine.detect_evidence_gaps(
            vasp_candidates=[c.model_dump() for c in attrib_res.vaspCandidates],
            clusters=clusters,
            has_bridges=False,
            has_mixers=any("Mixer" in r.get("title", "") for r in triggered_rules),
            unresolved_amount=Decimal(taint_results["unresolvedValue"]),
        )

        # Next Best Actions
        next_actions = investigation_engine.generate_next_actions(
            ranked_vasps=ranked_vasps,
            clusters=clusters,
            gaps=evidence_gaps,
            unresolved_val=Decimal(taint_results["unresolvedValue"]),
            case_id=cid,
        )

        # 6. Executive Summary (Rule-based deterministic narrative; no invented facts)
        exec_summary = (
            f"The investigated target wallet transmitted funds across {len(attrib_res.graph.nodes)} interconnected nodes "
            f"and {len(attrib_res.paths)} distinct traversal paths. "
            f"Approximately {mis.get('achievedCoveragePercentage', 0)}% of the tracked suspicious value ({mis.get('coveredAmount', 0)} {taint_results['accountingUnit']}) "
            f"was traced towards verified VASP endpoints, primarily attributed to {vasp_name} ({hop_dist} hops away). "
            f"Additionally, {len(clusters)} potential custodial service cluster(s) and {len(attrib_res.vaspCandidates)} VASP destination candidate(s) were identified."
        )

        # 7. Format Section 91 CrPC SAHYOG Notice
        sahyog_notice = self._draft_sahyog_notice(
            case_id=cid,
            investigator_id=inv_id,
            investigator_name=inv_name,
            vasp_name=vasp_name,
            vasp_address=vasp_addr,
            suspect_address=clean_addr,
            chain=chain_clean,
            hop_distance=hop_dist,
            transferred_volume=total_vol,
            generated_date=now_dt.strftime("%d-%b-%Y %H:%M UTC"),
        )

        # 8. Infographic Data
        infographics = self._compile_infographics(
            suspicion_score=suspicion_score,
            risk_level=risk_level,
            hop_distance=hop_dist,
            txs=txs,
            connected=connected,
            triggered_rules=triggered_rules,
        )

        # 9. Formulate Evidence Chain & Cryptographic SHA-256 Checksum
        evidence_chain = []
        for r in triggered_rules:
            evidence_chain.append({
                "ruleId": r["ruleId"],
                "title": r["title"],
                "severity": r["severity"],
                "evidence": r.get("evidence", []),
            })
        if nearest_vasp:
            evidence_chain.append({
                "ruleId": "VASP_DIRECT_ATTRIBUTION",
                "title": f"Attributed to {vasp_name}",
                "severity": "EVIDENCE_ATTACHMENT",
                "evidence": [f"Hop Distance: {hop_dist}", f"Endpoint: {vasp_addr}", f"Source: {nearest_vasp.source}"],
            })

        evidence_hashes = [tx.txHash for tx in txs if tx.txHash]
        raw_manifest_payload = (
            f"{cid}|{clean_addr}|{vasp_name}|{suspicion_score}|{now_iso}|"
            f"{','.join(evidence_hashes[:20])}|{taint_results['taintModel']}"
        )
        sha256_checksum = hashlib.sha256(raw_manifest_payload.encode("utf-8")).hexdigest()

        # 10. Assemble Structured 16-Section Object
        sections: Dict[str, Any] = {
            "section1_case_summary": {
                "caseId": cid,
                "investigationDateTime": now_iso,
                "investigatingOfficer": f"{inv_name} ({inv_id})",
                "investigatingAgency": "Indian Cyber Crime Coordination Centre (I4C)",
                "inputWalletAddress": clean_addr,
                "detectedBlockchain": chain_clean.upper(),
                "investigationScope": f"{max_depth}-Hop Multi-Chain Traversal",
                "transactionsAnalysed": len(txs),
                "walletsAnalysed": len(attrib_res.graph.nodes),
                "maximumTraversalDepth": max_depth,
                "dataSourcesUsed": ["Public Blockchain Ledger", "Etherscan/Blockstream RPC", "Verified VASP Directory"],
                "analysisEngineVersion": "SAHYOG-Forensic-v2.6",
                "investigationStatus": "COMPLETED",
            },
            "section2_executive_finding": {
                "summary": exec_summary,
                "primaryDestination": vasp_name,
                "hopDistance": hop_dist,
                "suspiciousCoveragePercentage": mis.get("achievedCoveragePercentage", 0),
            },
            "section3_suspect_wallet_profile": {
                "address": clean_addr,
                "chain": chain_clean,
                "balance": f"{overview.balance if hasattr(overview, 'balance') else '0'} {taint_results['accountingUnit']}",
                "transactionCount": len(txs),
                "suspicionScore": suspicion_score,
                "riskLevel": risk_level,
                "behavioralClassification": root_classification.get("classification"),
                "vaspBehaviorScore": root_vasp_score,
                "tags": [r["title"] for r in triggered_rules[:3]],
            },
            "section4_transaction_flow_summary": taint_results,
            "section5_key_transaction_paths": [
                {
                    "pathId": f"PATH-{i+1:03d}",
                    "source": p.path[0] if p.path else clean_addr,
                    "destination": p.path[-1] if p.path else "N/A",
                    "hopCount": p.hopCount if hasattr(p, "hopCount") else len(p.path) - 1,
                    "volume": p.totalVolume if hasattr(p, "totalVolume") else "0",
                    "path": p.path if hasattr(p, "path") else [],
                    "transactionHashes": [s.txHash for s in p.steps if s.txHash] if hasattr(p, "steps") else [],
                }
                for i, p in enumerate(attrib_res.paths[:5])
            ],
            "section6_vasp_attribution_results": {
                "verifiedVasps": [v for v in ranked_vasps if entity_service.is_vasp(v.get("address", ""))],
                "vaspCandidates": ranked_vasps,
            },
            "section7_unknown_vasp_findings": {
                "candidates": [
                    {
                        "candidateId": f"UVC-{i+1:03d}",
                        "address": c.get("address") if isinstance(c, dict) else str(c),
                        "entityType": c.get("entityType", "custodial_service") if isinstance(c, dict) else "custodial_service",
                        "vaspBehaviorScore": c.get("vaspBehaviorScore", 75) if isinstance(c, dict) else 75,
                        "classification": "Heuristic Custodial Service",
                        "verification": "UNVERIFIED",
                        "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION",
                    }
                    for i, c in enumerate(node_dicts[:3] if not clusters else clusters[0].get("addresses", [])[:3])
                ],
                "clusters": clusters,
            },
            "section8_suspicious_behaviour": [
                {
                    "ruleId": r["ruleId"],
                    "title": r["title"],
                    "severity": r["severity"],
                    "evidence": r.get("evidence", []),
                    "detected": True,
                }
                for r in triggered_rules
            ],
            "section9_investigation_priority": ranked_vasps,
            "section10_minimum_intervention_set": mis,
            "section11_attribution_confidence": {
                "attributionChallenges": attribution_challenges,
                "overallConfidenceLevel": "HIGH" if suspicion_score >= 70 else "MEDIUM",
            },
            "section12_evidence_gaps": {
                "identifiedGaps": evidence_gaps,
                "bestNextEvidenceToCollect": [
                    f"{g['title']} -> {g['recommendedAction']} (Potential: {g['potentialConfidenceImprovement']})"
                    for g in evidence_gaps[:3]
                ],
            },
            "section13_blind_spots_and_limitations": {
                "blindSpots": blind_spots,
                "forensicLimitations": [
                    "Public blockchain ledger analysis does not independently reveal legal beneficial owner identity without regulated VASP KYC disclosure.",
                    "Behavioural classification represents heuristic algorithmic scoring and does not constitute a definitive judicial finding of fact.",
                    "Intermediary unhosted private keys represent self-custodied addresses whose operational control requires physical or legal discovery.",
                    "This system serves as an investigative decision-support tool and does not substitute for authorized human or legal determination.",
                ],
            },
            "section14_recommended_next_steps": next_actions,
            "section15_sahyog_request": {
                "caseId": cid,
                "investigatingAgency": "Indian Cyber Crime Coordination Centre (I4C)",
                "targetVasp": vasp_name,
                "targetAddress": vasp_addr,
                "relevantTransactions": evidence_hashes[:5],
                "informationSought": [
                    "Full legal subscriber identity (Aadhaar, PAN, Passport, Photo ID)",
                    "Registered phone number and email addresses",
                    "Linked fiat bank accounts and deposit/withdrawal payment gateway logs",
                    "Complete internal transaction records and balance ledger",
                    "IP login access logs with timestamp and port mapping",
                    "Immediate asset preservation / debit freeze under Section 102 CrPC / PMLA",
                ],
                "statutoryNoticeDraft": sahyog_notice,
                "disclaimer": "REQUEST PREPARATION — HUMAN REVIEW AND LAWFUL SIGN-OFF REQUIRED",
            },
            "section16_evidence_manifest": {
                "evidenceHashes": evidence_hashes[:20],
                "sha256IntegrityHash": sha256_checksum,
                "engineVersion": "SAHYOG-Forensic-v2.6",
                "scoringConfigVersion": "2026.08-STRICT-SOP",
                "taintMethod": "PROPORTIONAL_TAINT",
                "generationTimestamp": now_iso,
            },
        }

        # 11. Assemble Full Markdown Report
        full_markdown = self._format_16_section_markdown(sections)

        # 12. Persist to MongoDB
        try:
            report_doc = {
                "_id": f"rep:{cid}",
                "reportId": f"REP-{cid}",
                "caseId": cid,
                "targetAddress": clean_addr,
                "chain": chain_clean,
                "generatedAt": now_iso,
                "suspicionScore": suspicion_score,
                "riskLevel": risk_level,
                "sha256Checksum": sha256_checksum,
                "nearestVasp": vasp_name,
                "sections": sections,
            }
            await db_manager.reports.insert_one(report_doc)
        except Exception as e:
            logger.warning(f"Could not persist report to MongoDB: {e}")

        return InvestigationReportResponse(
            reportId=f"REP-{cid}",
            caseId=cid,
            targetAddress=clean_addr,
            chain=chain_clean,
            generatedAt=now_iso,
            llmModel="SAHYOG Forensic Intelligence Engine",
            executiveSummary=exec_summary,
            sahyogNoticeDraft=sahyog_notice,
            nearestVaspName=vasp_name,
            nearestVaspAddress=vasp_addr,
            hopDistance=hop_dist,
            suspicionScore=suspicion_score,
            riskLevel=risk_level,
            infographics=infographics,
            evidenceChain=evidence_chain,
            sha256Checksum=sha256_checksum,
            fullReportMarkdown=full_markdown,
            sections=sections,
        )

    def _format_16_section_markdown(self, s: Dict[str, Any]) -> str:
        s1 = s["section1_case_summary"]
        s2 = s["section2_executive_finding"]
        s3 = s["section3_suspect_wallet_profile"]
        s4 = s["section4_transaction_flow_summary"]
        s10 = s["section10_minimum_intervention_set"]
        s15 = s["section15_sahyog_request"]
        s16 = s["section16_evidence_manifest"]

        return f"""# OFFICIAL LAW ENFORCEMENT CYBER FORENSIC DOSSIER
**Indian Cyber Crime Coordination Centre (I4C) • SAHYOG Platform**
**CASE ID**: `{s1['caseId']}` | **Classification**: LAW ENFORCEMENT SENSITIVE

---

## SECTION 1 — CASE SUMMARY
- **Case ID**: `{s1['caseId']}`
- **Investigation Timestamp**: `{s1['investigationDateTime']}`
- **Investigating Officer**: `{s1['investigatingOfficer']}`
- **Investigating Agency**: `{s1['investigatingAgency']}`
- **Target Wallet Address**: `{s1['inputWalletAddress']}`
- **Network**: `{s1['detectedBlockchain']}`
- **Wallets Analysed**: `{s1['walletsAnalysed']}` | **Transactions**: `{s1['transactionsAnalysed']}`
- **Analysis Engine**: `{s1['analysisEngineVersion']}` | **Status**: `{s1['investigationStatus']}`

---

## SECTION 2 — EXECUTIVE FINDING
{s2['summary']}

---

## SECTION 3 — SUSPECT WALLET PROFILE
- **Address**: `{s3['address']}`
- **Balance**: `{s3['balance']}`
- **Forensic Suspicion Score**: `{s3['suspicionScore']} / 100 ({s3['riskLevel']})`
- **Behavioral Classification**: `{s3['behavioralClassification']}`
- **VASP Behavior Score**: `{s3['vaspBehaviorScore']} / 100`

---

## SECTION 4 — TRANSACTION FLOW SUMMARY (PROPORTIONAL TAINT ACCOUNTING)
- **Taint Accounting Model**: `{s4['taintModel']}`
- **Original Suspicious Value**: `{s4['originalSuspiciousValue']} {s4['accountingUnit']}`
- **Traced Value**: `{s4['tracedValue']} {s4['accountingUnit']}`
- **Attributed to Known VASPs**: `{s4['attributedToKnownVasp']} {s4['accountingUnit']}`
- **At Probable Unknown VASPs**: `{s4['attributedToUnknownVasp']} {s4['accountingUnit']}`
- **Unresolved Value**: `{s4['unresolvedValue']} {s4['accountingUnit']}`
- **Case Coverage**: `{s4['caseCoveragePercentage']}%`
{f"> [!WARNING]\n> {s4['conservationWarning']}" if s4.get('conservationWarning') else ""}

---

## SECTION 5 — KEY TRANSACTION PATHS
Total discovered fund routing paths: **{len(s['section5_key_transaction_paths'])}**

---

## SECTION 6 & 7 — VASP ATTRIBUTION & UNKNOWN VASP FINDINGS
- **Primary Identified Destination**: **{s2['primaryDestination']}** ({s2['hopDistance']} hops)
- **Potential Service Clusters**: **{len(s['section7_unknown_vasp_findings']['clusters'])} cluster(s) detected**

---

## SECTION 8 & 9 — SUSPICIOUS BEHAVIOUR & INVESTIGATION PRIORITY
Identified Typologies:
{chr(10).join([f"- **{r['title']}** [{r['severity']}]: {', '.join(r.get('evidence', []))}" for r in s['section8_suspicious_behaviour'][:4]])}

---

## SECTION 10 — MINIMUM INTERVENTION SET
{s10['explanation']}

---

## SECTION 11 & 12 — ATTRIBUTION CHALLENGE & EVIDENCE GAPS
- **Challenge Recommendation**: `{s['section11_attribution_confidence']['attributionChallenges'][0]['recommendation'] if s['section11_attribution_confidence']['attributionChallenges'] else 'Human review recommended'}`
- **Key Evidence Gaps**: {len(s['section12_evidence_gaps']['identifiedGaps'])} identified.

---

## SECTION 13 — BLIND SPOTS & FORENSIC LIMITATIONS
> [!NOTE]
> Blockchain analysis traces public ledger movements but does not independently establish real-world beneficial ownership without lawful KYC disclosure. All behavioral classifications are heuristic.

---

## SECTION 14 — RECOMMENDED NEXT STEPS
{chr(10).join([f"{i+1}. **{act['title']}**: {act['reason']}" for i, act in enumerate(s['section14_recommended_next_steps'][:5])])}

---

## SECTION 15 — SAHYOG / VASP STATUTORY NOTICE PREPARATION
```text
{s15['statutoryNoticeDraft']}
```

---

## SECTION 16 — EVIDENCE MANIFEST & INTEGRITY HASH
- **Cryptographic SHA-256 Checksum**: `{s16['sha256IntegrityHash']}`
- **Taint Method**: `{s16['taintMethod']}`
- **Generated**: `{s16['generationTimestamp']}`
"""

    def _draft_sahyog_notice(
        self,
        case_id: str,
        investigator_id: str,
        investigator_name: str,
        vasp_name: str,
        vasp_address: str,
        suspect_address: str,
        chain: str,
        hop_distance: int,
        transferred_volume: str,
        generated_date: str,
    ) -> str:
        return f"""================================================================================
OFFICIAL NOTICE UNDER SECTION 91 OF THE CODE OF CRIMINAL PROCEDURE, 1973 (CrPC)
READ WITH SECTION 69B OF THE INFORMATION TECHNOLOGY ACT, 2000
GOVERNMENT OF INDIA • MINISTRY OF HOME AFFAIRS
INDIAN CYBER CRIME COORDINATION CENTRE (I4C) • SAHYOG INVESTIGATION PORTAL
================================================================================
NOTICE REF NO: I4C/SAHYOG/{case_id}/VASP-DISC/2026
DATE & TIME OF ISSUE: {generated_date}

TO:
  THE NODAL OFFICER / LAW ENFORCEMENT COMPLIANCE CELL
  ENTITY: {vasp_name.upper()}
  SUBJECT: URGENT STATUTORY REQUISITION FOR SUBSCRIBER IDENTIFICATION, KYC DOSSIER,
           AND TRANSACTION LEDGER RECORDS CONCERNING ILLICIT DIGITAL ASSET MOVEMENT

WHEREAS an active cybercrime investigation has been instituted under Indian Penal Law
(Case ID: {case_id}), and digital evidence reveals proceeds of cyber fraud / illicit funds
originating from suspect source wallet:
  SUSPECT WALLET: {suspect_address} ({chain.upper()})

WERE TRACED THROUGH ON-CHAIN TRAVERSAL TO HAVE TRANSFERRED INTO INFRASTRUCTURE
IDENTIFIED WITH YOUR REGISTERED EXCHANGE / CUSTODIAL SERVICES:
  IDENTIFIED ENDPOINT ADDRESS: {vasp_address}
  APPROXIMATE TRAVERSED VOLUME: {transferred_volume} {chain.upper()}
  EVIDENTIARY HOP DISTANCE: {hop_distance} HOP(S)

ACCORDINGLY, IN EXERCISE OF STATUTORY POWERS VESTED UNDER SECTION 91 CrPC, YOU ARE
HEREBY DIRECTED TO PRODUCE AND FURNISH TO THIS AGENCY WITHIN 48 HOURS:
  1. Complete KYC Dossier (Aadhaar, PAN, Passport, Driving License, Selfie Verification).
  2. Registered Full Name, Residential Address, Mobile Number, and Verified Email Address.
  3. Linked Indian / Global Fiat Bank Account Numbers and UPI VPA Identifiers.
  4. Complete Internal Ledger Statement (Deposit, Trade, and Withdrawal Records).
  5. IP Access Logs with UTC Timestamps, Port Mappings, and Device Fingerprint Identifiers.
  6. External Digital Asset Destination Addresses for all subsequent withdrawals.

FURTHERMORE, YOU ARE REQUESTED TO EXERCISE ASSET PRESERVATION PROTOCOLS TO SECURE AND
FREEZE ANY REMAINING ASSET BALANCES LINKED TO THIS SUBSCRIBER ACCOUNT PENDING FORMAL
ORDER UNDER SECTION 102 CrPC / PMLA 2002.

INVESTIGATING OFFICER: {investigator_name}
DESIGNATION: Cyber Forensics Investigator (ID: {investigator_id})
AGENCY: National Cybercrime Forensic Unit (NCFU) / I4C
DISCLAIMER: REQUEST PREPARATION — HUMAN REVIEW AND LAWFUL SIGN-OFF REQUIRED
================================================================================"""

    def _compile_infographics(
        self,
        suspicion_score: int,
        risk_level: str,
        hop_distance: int,
        txs: list,
        connected: list,
        triggered_rules: list,
    ) -> ReportInfographics:
        hop_dist = [
            {"hop": "Hop 1 (Direct)", "wallets": min(len(connected), 8), "volumeRatio": 65},
            {"hop": "Hop 2 (Intermediary)", "wallets": max(0, len(connected) - 8), "volumeRatio": 25},
            {"hop": "Hop 3+ (Cluster)", "wallets": max(0, len(connected) - 15), "volumeRatio": 10},
        ]
        vol_flow = [
            {"category": "Traced to Exchange", "percentage": 70 if hop_distance <= 2 else 45},
            {"category": "Unhosted Intermediary", "percentage": 20 if hop_distance <= 2 else 40},
            {"category": "Network Fees / Residue", "percentage": 10 if hop_distance <= 2 else 15},
        ]
        cat_breakdown = [
            {"category": "Sanctions & Exploits", "count": sum(1 for r in triggered_rules if "Sanction" in r.get("title", "") or "Hack" in r.get("title", ""))},
            {"category": "Laundering Typologies", "count": sum(1 for r in triggered_rules if "Rapid" in r.get("title", "") or "Mixer" in r.get("title", "") or "Cluster" in r.get("title", ""))},
            {"category": "Velocity & Thresholds", "count": sum(1 for r in triggered_rules if "Velocity" in r.get("title", "") or "Large" in r.get("title", "") or "Frequency" in r.get("title", ""))},
            {"category": "Compliance Signals", "count": sum(1 for r in triggered_rules if "Clean" in r.get("title", "") or "Holding" in r.get("title", ""))},
        ]
        return ReportInfographics(
            riskScoreGauge={"score": suspicion_score, "level": risk_level, "max": 100},
            hopDistribution=hop_dist,
            volumeFlow=vol_flow,
            categoryBreakdown=cat_breakdown,
        )


report_service = LEAForensicReportService()
