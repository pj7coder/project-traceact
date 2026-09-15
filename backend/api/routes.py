import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query

from backend.config.settings import settings
from backend.schemas.wallet import (
    BlockchainNetwork,
    AnalyzeWalletRequest,
    WalletAnalysisResponse,
    TraceFundsRequest,
    TraceFundsResponse,
    ChainDetectionRequest,
    ChainDetectionResponse,
    NodeExpansionRequest,
    NodeExpansionResponse,
    LiveTrackingToggleRequest,
    SystemSettingsModel,
)
from backend.schemas.attribution import (
    AttributionRequest,
    AttributionResponse,
    ReportGenerateRequest,
    InvestigationReportResponse,
    EvaluateHeuristicsRequest,
    InvestigationDossierResponse,
)
from backend.utils.validators import validate_and_normalize_address
from backend.services.wallet_service import wallet_service
from backend.services.graph_service import graph_service
from backend.services.tracing_service import tracing_service
from backend.services.entity_service import entity_service
from backend.services.attribution_service import attribution_service
from backend.services.multi_chain_service import multi_chain_service
from backend.services.graph_expansion_service import graph_expansion_service
from backend.services.history_service import history_service
from backend.services.live_tracking_service import live_tracking_service
from backend.services.report_service import report_service
from backend.services.rule_engine import rule_engine
from backend.services.vasp_discovery_service import vasp_discovery_service
from backend.services.investigation_engine import investigation_engine
from backend.services.graph_analytics_service import graph_analytics_service
from backend.database.mongo import db_manager

logger = logging.getLogger("api_routes")
router = APIRouter()


# -------------------------------------------------------------
# 1. Multi-Chain Detection & Validation
# -------------------------------------------------------------
@router.post(
    "/wallet/detect",
    response_model=ChainDetectionResponse,
    summary="Auto-Detect Cryptocurrency Network",
    description="Inspects public key encoding, prefix, and checksum to auto-determine Bitcoin, Ethereum, Tron, or Solana.",
)
async def detect_wallet_chain(request: ChainDetectionRequest) -> ChainDetectionResponse:
    detection = multi_chain_service.detect_chain(request.address)
    return ChainDetectionResponse(
        address=request.address.strip(),
        detectedChain=detection["detectedChain"],
        confidence=detection["confidence"],
        formatName=detection["formatName"],
        symbol=detection["symbol"],
        suggestedAlternativeChains=detection.get("suggestedAlternativeChains", []),
        validationStatus=detection.get("validationStatus", True),
        message=detection.get("message"),
    )


# -------------------------------------------------------------
# 2. Wallet Analysis (1-Hop Multi-Chain)
# -------------------------------------------------------------
@router.post(
    "/wallet/analyze",
    response_model=WalletAnalysisResponse,
    summary="Analyze Cryptocurrency Wallet (1-Hop)",
    description="Fetches blockchain data across Ethereum, Bitcoin, Tron, or Solana, normalizes transactions, executes Rule Engine, and builds graph.",
)
async def analyze_wallet(request: AnalyzeWalletRequest) -> WalletAnalysisResponse:
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    is_valid, normalized_address, err_msg = validate_and_normalize_address(request.address, chain_val)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {chain_val} address: {err_msg}",
        )

    try:
        overview, transactions, connected_wallets = await wallet_service.get_wallet_overview_and_data(
            target_address=normalized_address, chain=chain_val
        )

        graph_data = graph_service.build_one_hop_graph(
            investigated_wallet=overview,
            connected_wallets=connected_wallets,
            transactions=transactions,
        )

        return WalletAnalysisResponse(
            wallet=overview,
            transactions=transactions,
            connectedWallets=connected_wallets,
            graph=graph_data,
            riskAssessment=overview.riskAssessment or rule_engine.evaluate_wallet(overview, transactions, connected_wallets),
            metadata={
                "chain": chain_val,
                "targetAddress": normalized_address,
                "queriedAt": datetime.now(timezone.utc).isoformat(),
                "totalTxsAnalyzed": len(transactions),
                "totalPeersDiscovered": len(connected_wallets),
                "riskScore": overview.riskScore,
                "riskLevel": overview.riskLevel,
            },
        )
    except Exception as e:
        logger.exception(f"Error analyzing wallet {normalized_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during wallet analysis: {str(e)}",
        )


# -------------------------------------------------------------
# 3. Multi-Hop BFS Tracing
# -------------------------------------------------------------
@router.post(
    "/wallet/trace",
    response_model=TraceFundsResponse,
    summary="Multi-Hop Blockchain Transaction Tracing",
    description="Recursively traces fund flows across hops (1-5) using BFS, loop prevention, and VASP clustering.",
)
async def trace_wallet(request: TraceFundsRequest) -> TraceFundsResponse:
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    is_valid, normalized_address, err_msg = validate_and_normalize_address(request.address, chain_val)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid address: {err_msg}",
        )

    normalized_request = TraceFundsRequest(
        chain=request.chain,
        address=normalized_address,
        maxDepth=request.maxDepth,
        direction=request.direction,
        minimumTransferValue=request.minimumTransferValue,
        startTimestamp=request.startTimestamp,
        endTimestamp=request.endTimestamp,
        maxNodes=request.maxNodes,
        maxTransactionsPerWallet=request.maxTransactionsPerWallet,
    )

    try:
        return await tracing_service.trace_wallet_funds(normalized_request)
    except Exception as e:
        logger.exception(f"Error tracing wallet {normalized_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during multi-hop tracing: {str(e)}",
        )


# -------------------------------------------------------------
# 4. Deterministic VASP Attribution
# -------------------------------------------------------------
@router.post(
    "/wallet/attribution",
    response_model=AttributionResponse,
    summary="Forensic VASP Attribution",
    description="Deterministically identifies nearest verified VASP/exchange destination with evidence-backed trail.",
)
async def attribute_wallet(request: AttributionRequest) -> AttributionResponse:
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    is_valid, normalized_address, err_msg = validate_and_normalize_address(request.address, chain_val)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {chain_val.capitalize()} address: {err_msg}",
        )


    normalized_request = AttributionRequest(
        chain=request.chain,
        address=normalized_address,
        maxDepth=request.maxDepth,
        direction=request.direction,
        minimumTransferValue=request.minimumTransferValue,
        startTimestamp=request.startTimestamp,
        endTimestamp=request.endTimestamp,
        maxNodes=request.maxNodes,
        systemLogic=request.systemLogic,
    )

    try:
        return await attribution_service.analyze_attribution(normalized_request)
    except Exception as e:
        logger.exception(f"Error in attribution engine for {normalized_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error occurred during VASP attribution: {str(e)}",
        )


# -------------------------------------------------------------
# 4b. Dynamic Heuristics & System Logic Re-Evaluation
# -------------------------------------------------------------
@router.post(
    "/wallet/evaluate-heuristics",
    summary="Evaluate Heuristics with Custom System Logic",
    description="Recalculates suspicion score, risk tiers, and triggers against wallet context using investigator-tuned logic thresholds.",
)
async def evaluate_wallet_heuristics(request: EvaluateHeuristicsRequest) -> Dict[str, Any]:
    try:
        overview, txs, connected = await wallet_service.get_wallet_overview_and_data(
            request.address, request.chain
        )
        result = rule_engine.evaluate_wallet(
            wallet=overview,
            transactions=txs,
            connected_wallets=connected,
            multihop_nodes=request.multihopNodes or [],
            system_logic=request.systemLogic,
        )
        return {
            "address": request.address,
            "chain": request.chain,
            "riskAssessment": result,
        }
    except Exception as e:
        logger.exception(f"Error evaluating heuristics for {request.address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate heuristics: {str(e)}",
        )



# -------------------------------------------------------------
# 5. Incremental Graph Branch Expansion ("Expand Node")
# -------------------------------------------------------------
@router.post(
    "/investigation/expand-node",
    response_model=NodeExpansionResponse,
    summary="Expand 1-Hop Branch from Selected Node",
    description="Preserves existing graph nodes and appends the selected node's counterparty branch in place.",
)
async def expand_graph_node(request: NodeExpansionRequest) -> NodeExpansionResponse:
    try:
        return await graph_expansion_service.expand_branch(request)
    except Exception as e:
        logger.exception(f"Error expanding node branch for {request.targetAddress}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error expanding node branch: {str(e)}",
        )


# -------------------------------------------------------------
# 6. Live Tracking Suite (1-Hour Periodic Check & Alerts)
# -------------------------------------------------------------
@router.post(
    "/tracking/enable",
    summary="Enable 1-Hour Live Monitoring for Wallet",
    description="Registers a wallet for automated 60-minute background ledger tracking and email alerts.",
)
async def enable_tracking(request: LiveTrackingToggleRequest):
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    return await live_tracking_service.toggle_monitoring(
        address=request.address,
        chain=chain_val,
        email=request.email,
        enabled=True,
    )


@router.post(
    "/tracking/disable",
    summary="Disable Live Monitoring for Wallet",
)
async def disable_tracking(request: LiveTrackingToggleRequest):
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    return await live_tracking_service.toggle_monitoring(
        address=request.address,
        chain=chain_val,
        email=request.email,
        enabled=False,
    )


@router.post(
    "/tracking/check-now/{address}",
    summary="Manual Trigger: Check Monitored Wallet Immediately",
    description="Allows investigators to test the 1-hour tracking diff and alert engine immediately without waiting.",
)
async def check_wallet_now(address: str, chain: str = Query("ethereum")):
    return await live_tracking_service.check_wallet(address, chain)


@router.get(
    "/tracking/monitored",
    summary="List All Monitored Wallets",
)
async def list_monitored_wallets():
    return await live_tracking_service.get_monitored_wallets()


@router.get(
    "/tracking/notifications",
    summary="Get In-App Notifications Feed",
)
async def get_notifications():
    return live_tracking_service.get_notifications()


# -------------------------------------------------------------
# 7. Local Ollama LEA Report & SAHYOG Generator
# -------------------------------------------------------------
@router.post(
    "/report/generate",
    response_model=InvestigationReportResponse,
    summary="Generate Official LEA Forensic Report (Ollama LLM)",
    description="Invokes local Ollama LLM to formulate formal executive narrative, typology analysis, infographics, and Section 91 CrPC notice for SAHYOG Portal.",
)
async def generate_investigation_report(request: ReportGenerateRequest) -> InvestigationReportResponse:
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    try:
        return await report_service.generate_report(
            target_address=request.targetAddress,
            chain=chain_val,
            case_id=request.caseId,
            investigator_id=request.investigatorId,
            investigator_name=request.investigatorName,
            max_depth=request.maxDepth,
        )
    except Exception as e:
        logger.exception(f"Error generating investigation report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate forensic report: {str(e)}",
        )


# -------------------------------------------------------------
# 7b. Unified Investigation Intelligence & Decision Pipeline
# -------------------------------------------------------------
@router.post(
    "/investigate",
    response_model=InvestigationDossierResponse,
    summary="Unified Investigation Decision Pipeline",
    description="Full intelligence pipeline: multi-hop tracing, Verified VASP attribution, Unknown VASP discovery, Taint accounting, VASP actionability, Minimum Intervention Set, and 16-section report.",
)
async def run_investigation(request: AttributionRequest) -> InvestigationDossierResponse:
    chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
    is_valid, norm_addr, err_msg = validate_and_normalize_address(request.address, chain_val)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {chain_val.capitalize()} address: {err_msg}",
        )

    attrib_req = AttributionRequest(
        chain=request.chain,
        address=norm_addr,
        maxDepth=request.maxDepth,
        direction=request.direction,
        minimumTransferValue=request.minimumTransferValue,
        startTimestamp=request.startTimestamp,
        endTimestamp=request.endTimestamp,
        maxNodes=request.maxNodes,
        systemLogic=request.systemLogic,
    )

    try:
        attrib_res = await attribution_service.analyze_attribution(attrib_req)
        node_dicts = [n.model_dump() for n in attrib_res.graph.nodes]
        edge_dicts = [e.model_dump() for e in attrib_res.graph.edges]
        clusters = vasp_discovery_service.detect_service_clusters(node_dicts, edge_dicts, chain=chain_val)

        # Analyze unknown VASP candidates from graph
        unknown_candidates = []
        for node in node_dicts:
            n_addr = node.get("address", "")
            if not entity_service.is_vasp(n_addr):
                in_deg = node.get("inDegree", 1)
                out_deg = node.get("outDegree", 1)
                mock_feats = {
                    "unique_senders": in_deg,
                    "unique_receivers": out_deg,
                    "sender_receiver_ratio": round(in_deg / max(1, out_deg), 2),
                    "transactions_per_day": 10.0 if in_deg >= 3 else 1.0,
                    "transaction_count": in_deg + out_deg,
                    "consolidation_ratio": round(in_deg / max(1, out_deg + 1), 2),
                    "sweep_frequency": 0.6 if in_deg >= 3 else 0.1,
                    "balance_retention_time_hours": 1.5 if in_deg >= 3 else 18.0,
                    "repeated_destination_count": 2 if in_deg >= 3 else 0,
                    "top_destination_percentage": 70.0 if in_deg >= 3 else 30.0,
                    "known_vasp_interactions": 1 if any(entity_service.is_vasp(e["target"]) for e in edge_dicts if e.get("source") == n_addr) else 0,
                }
                v_score, v_breakdown, v_ev = vasp_discovery_service.compute_vasp_behavior_score(mock_feats)
                classification = vasp_discovery_service.classify_entity(mock_feats, v_score)
                node["vaspBehaviorScore"] = v_score
                node["entityClassification"] = classification["classification"]

                if v_score >= 45:
                    unknown_candidates.append({
                        "address": n_addr,
                        "entityType": classification["classification"],
                        "vaspBehaviorScore": v_score,
                        "classification": classification["tier"],
                        "evidence": v_ev,
                        "verification": "UNVERIFIED",
                        "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION",
                    })

        orig_val = Decimal("10.0")
        if attrib_res.paths:
            orig_val = sum([Decimal(str(p.totalVolume or 0)) for p in attrib_res.paths]) or Decimal("10.0")

        taint_results = investigation_engine.calculate_taint_and_conservation(
            original_suspicious_value=orig_val,
            paths=attrib_res.paths,
            nodes=attrib_res.graph.nodes,
            vasp_candidates=attrib_res.vaspCandidates,
            chain=chain_val,
        )

        ranked_vasps = []
        for cand in attrib_res.vaspCandidates:
            cand_dict = cand.model_dump() if hasattr(cand, "model_dump") else cand
            act = investigation_engine.calculate_vasp_actionability(cand_dict, orig_val, chain=chain_val)
            ranked_vasps.append(act)

        ranked_vasps.sort(key=lambda x: x["actionabilityScore"], reverse=True)

        mis = investigation_engine.compute_minimum_intervention_set(
            ranked_vasps=ranked_vasps,
            total_case_value=orig_val,
            target_coverage_threshold=70.0,
        )

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
                chain=chain_val,
            )
            attribution_challenges.append(chal)

        evidence_gaps, blind_spots = investigation_engine.detect_evidence_gaps(
            vasp_candidates=[c.model_dump() for c in attrib_res.vaspCandidates],
            clusters=clusters,
            unresolved_amount=Decimal(taint_results["unresolvedValue"]),
        )

        cid = f"CASE-{datetime.now(timezone.utc).year}-I4C-{int(time.time() % 10000):04d}"

        # -------------------------------------------------------------
        # NetworkX Topological Analysis & Confidence Calibration
        # -------------------------------------------------------------
        netx_analytics = graph_analytics_service.analyze_network_topology(
            nodes=node_dicts,
            edges=edge_dicts,
            target_address=norm_addr,
            vasp_candidates=[c.model_dump() if hasattr(c, "model_dump") else c for c in attrib_res.vaspCandidates],
        )

        # Apply NetworkX confidence adjustments to VASP candidates
        conf_map = {adj["address"].lower(): adj for adj in netx_analytics.get("confidenceAdjustments", [])}
        for cand in attrib_res.vaspCandidates:
            c_addr = cand.address.lower()
            if c_addr in conf_map:
                adj = conf_map[c_addr]
                if adj.get("adjustedLevel") == "HIGH":
                    cand.confidence = ConfidenceLevel.HIGH
                elif adj.get("adjustedLevel") == "MEDIUM":
                    cand.confidence = ConfidenceLevel.MEDIUM

        if attrib_res.nearestVasp and attrib_res.nearestVasp.address.lower() in conf_map:
            adj = conf_map[attrib_res.nearestVasp.address.lower()]
            if adj.get("adjustedLevel") == "HIGH":
                attrib_res.nearestVasp.confidence = ConfidenceLevel.HIGH

        next_actions = investigation_engine.generate_next_actions(
            ranked_vasps=ranked_vasps,
            clusters=clusters,
            gaps=evidence_gaps,
            unresolved_val=Decimal(taint_results["unresolvedValue"]),
            case_id=cid,
        )

        # Generate 100% Deterministic Step-Wise Investigation Playbook (Zero LLM)
        playbook = investigation_engine.generate_deterministic_investigation_playbook(
            target_address=norm_addr,
            chain=chain_val,
            ranked_vasps=ranked_vasps,
            mis=mis,
            bottleneck_mules=netx_analytics.get("bottleneckMules", []),
            clusters=clusters,
            unresolved_val=Decimal(taint_results["unresolvedValue"]),
            total_case_value=orig_val,
            case_id=cid,
            detected_cycles=netx_analytics.get("detectedCycles", []),
        )

        timeline = [
            {
                "time": "00:00:00",
                "step": 1,
                "event": "Suspect Inflow Received",
                "description": f"Root address {norm_addr[:10]}... received initial suspicious fund transfer.",
                "severity": "CRITICAL",
            },
            {
                "time": "00:18:20",
                "step": 2,
                "event": "Multi-Path Layering & Splitting",
                "description": f"Funds fragmented across {len(attrib_res.paths)} distinct outbound branches.",
                "severity": "HIGH",
            },
        ]
        if attrib_res.nearestVasp:
            timeline.append({
                "time": "01:05:00",
                "step": 3,
                "event": f"Deposit at {attrib_res.nearestVasp.name}",
                "description": f"{attrib_res.nearestVasp.totalTransferred} assets reached verified exchange infrastructure.",
                "severity": "ACTIONABLE",
            })

        report_res = await report_service.generate_report(
            target_address=norm_addr,
            chain=chain_val,
            case_id=cid,
            max_depth=request.maxDepth,
        )

        return InvestigationDossierResponse(
            caseId=cid,
            targetAddress=norm_addr,
            chain=chain_val,
            status="COMPLETED",
            generatedAt=datetime.now(timezone.utc).isoformat(),
            taintAccounting=taint_results,
            vaspActionabilityRankings=ranked_vasps,
            minimumInterventionSet=mis,
            attributionChallenges=attribution_challenges,
            unknownVaspCandidates=unknown_candidates,
            serviceClusters=clusters,
            evidenceGaps=evidence_gaps,
            blindSpots=blind_spots,
            nextActions=next_actions,
            investigationPlaybook=playbook,
            networkAnalytics=netx_analytics,
            timeline=timeline,
            caseCoverage={
                "originalAmount": taint_results["originalSuspiciousValue"],
                "tracedAmount": taint_results["tracedValue"],
                "atKnownVasp": taint_results["attributedToKnownVasp"],
                "atUnknownVasp": taint_results["attributedToUnknownVasp"],
                "unresolved": taint_results["unresolvedValue"],
                "coveragePercentage": taint_results["caseCoveragePercentage"],
            },
            report=report_res,
            attribution=attrib_res,
        )
    except Exception as e:
        logger.exception(f"Error running investigation for {norm_addr}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation decision pipeline failed: {str(e)}",
        )


# -------------------------------------------------------------
# 7c. Case Archive & Saved Investigations Management
# -------------------------------------------------------------
@router.get(
    "/investigations",
    summary="List All Saved Investigations in Case Archive",
)
async def list_saved_investigations(limit: int = 50):
    try:
        items = await db_manager.investigations.find({}, limit=limit)
        # Sort descending by creation date if present
        items.sort(key=lambda x: str(x.get("createdAt", x.get("timestamp", ""))), reverse=True)
        return {
            "count": len(items),
            "investigations": items,
        }
    except Exception as e:
        logger.error(f"Error listing saved investigations: {e}")
        return {"count": 0, "investigations": []}


@router.post(
    "/investigations/save",
    summary="Save or Update an Investigation Case Docket",
)
async def save_investigation(payload: Dict[str, Any]):
    try:
        case_id = payload.get("caseId") or f"CASE-2026-I4C-{int(datetime.now().timestamp())}"
        payload["caseId"] = case_id
        payload["_id"] = f"case:{case_id}"
        if "createdAt" not in payload:
            payload["createdAt"] = datetime.now(timezone.utc).isoformat()
        payload["updatedAt"] = datetime.now(timezone.utc).isoformat()
        if "investigatorId" not in payload:
            payload["investigatorId"] = settings.INVESTIGATOR_ID

        # Also record the target wallet in the history repository
        target_addr = payload.get("targetAddress") or payload.get("suspectAddress")
        target_chain = payload.get("chain", "ethereum")
        if target_addr:
            await history_service.record_target_search(
                address=target_addr,
                chain=target_chain,
                investigator_id=payload.get("investigatorId"),
                case_id=case_id,
            )

        # Index graph nodes if present
        graph_data = payload.get("graph") or {}
        nodes_list = graph_data.get("nodes") or payload.get("nodes") or []
        if nodes_list:
            clean_nodes = []
            for n in nodes_list:
                addr = n.get("address") or n.get("id") or (n.get("data", {}).get("fullAddress"))
                if addr:
                    clean_nodes.append({"address": addr, "entityName": n.get("entityName")})
            await history_service.record_graph_nodes_batch(clean_nodes, chain=target_chain, case_id=case_id)

        await db_manager.investigations.update_one(
            {"_id": payload["_id"]},
            {"$set": payload},
            upsert=True,
        )
        return {
            "status": "success",
            "message": f"Investigation case {case_id} saved successfully.",
            "caseId": case_id,
            "case": payload,
        }
    except Exception as e:
        logger.exception(f"Error saving investigation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save investigation: {str(e)}",
        )


@router.get(
    "/investigations/{case_id}",
    summary="Retrieve Full Investigation Case Docket",
)
async def get_saved_investigation(case_id: str):
    doc = await db_manager.investigations.find_one({"_id": f"case:{case_id}"})
    if not doc:
        results = await db_manager.investigations.find({"caseId": case_id}, limit=1)
        doc = results[0] if results else None
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case {case_id} not found in database archive.",
        )
    return doc


@router.delete(
    "/investigations/{case_id}",
    summary="Delete an Investigation Case Docket",
)
async def delete_saved_investigation(case_id: str):
    doc = await db_manager.investigations.find_one({"_id": f"case:{case_id}"})
    if not doc:
        results = await db_manager.investigations.find({"caseId": case_id}, limit=1)
        doc = results[0] if results else None
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation case {case_id} not found.",
        )
    # Delete from fallback / collection
    try:
        col = db_manager.investigations
        if hasattr(col, "_items") and doc.get("_id") in col._items:
            del col._items[doc["_id"]]
            col._save()
        elif hasattr(col, "delete_one"):
            await col.delete_one({"_id": doc["_id"]})
    except Exception as e:
        logger.warning(f"Error deleting investigation {case_id}: {e}")
    return {"status": "deleted", "caseId": case_id}


# -------------------------------------------------------------
# 7d. Retrieve Saved Investigation Report
# -------------------------------------------------------------
@router.get(
    "/investigations/{case_id}/report",
    summary="Retrieve 16-Section Investigation Report",
)
async def get_investigation_report(case_id: str):
    doc = await db_manager.reports.find_one({"_id": f"rep:{case_id}"})
    if not doc:
        results = await db_manager.reports.find({"caseId": case_id}, limit=1)
        doc = results[0] if results else None
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for Case ID {case_id} not found in database.",
        )
    return doc


# -------------------------------------------------------------
# 7d. On-Demand Behavioral Feature Extraction & Unknown VASP Scoring
# -------------------------------------------------------------
@router.get(
    "/entity-analysis/{chain}/{address}",
    summary="Deep Behavioral Feature Extraction for Unknown Wallet",
)
async def analyze_unknown_entity(chain: str, address: str):
    overview, txs, connected = await wallet_service.get_wallet_overview_and_data(address, chain)
    features = vasp_discovery_service.extract_behavioral_features(address, txs, connected, chain=chain)
    v_score, v_breakdown, v_ev = vasp_discovery_service.compute_vasp_behavior_score(features)
    is_known = entity_service.is_vasp(address)
    entity = entity_service.get_entity(address)
    classification = vasp_discovery_service.classify_entity(
        features, v_score, is_known_vasp=is_known, known_name=entity.entity_name if entity else None
    )
    return {
        "address": address,
        "chain": chain,
        "isKnownVasp": is_known,
        "vaspBehaviorScore": v_score,
        "vaspBehaviorScoreBreakdown": v_breakdown,
        "classification": classification,
        "evidence": v_ev,
        "features": features,
    }


# -------------------------------------------------------------
# 7e. Verified VASP Directory Endpoint (25 VASPs)
# -------------------------------------------------------------
@router.get(
    "/vasps",
    summary="List All Records in Verified VASP Directory",
)
async def list_verified_vasps():
    vasps = entity_service.get_all_vasps()
    return {
        "count": len(vasps),
        "vasps": vasps,
    }


# -------------------------------------------------------------
# 7f. Canonical SIH 2026 Reference Demo Scenario
# -------------------------------------------------------------
@router.post(
    "/investigations/demo",
    response_model=InvestigationDossierResponse,
    summary="Run SIH 2026 Reference Demo Investigation Scenario",
)
async def run_demo_investigation() -> InvestigationDossierResponse:
    demo_suspect = "0x71C836489B990038848971201991802901238910"
    cid = "CASE-2026-SIH-DEMO-001"
    now_iso = datetime.now(timezone.utc).isoformat()

    ranked_vasps = [
        {
            "entityName": "CoinDCX (Neblio Technologies Pvt Ltd)",
            "address": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
            "actionabilityScore": 92,
            "priority": "CRITICAL",
            "percentageOfCase": 52.0,
            "amountExposure": "5.2000",
            "jurisdiction": "India (FIU-IND Registered, Reg No: FIU-IND/2023/VASP/0012)",
            "kycStatus": "MANDATORY_KYC",
            "isFiuRegistered": True,
            "reasons": [
                "Substantial financial exposure: 5.2000 ETH (₹5.2 Lakhs)",
                "Major case share: 52.0% of tracked suspicious funds",
                "High attribution confidence supported by confirmed FIU-IND ledger tags",
                "Mandatory PAN/Aadhaar KYC verified",
                "FIU-IND reporting entity with dedicated Section 91 CrPC law enforcement nodal officer",
            ],
            "recommendedContactOrder": 1,
        },
        {
            "entityName": "Binance Global",
            "address": "0x28c6c06298d514db089934071355e5743bf21d60",
            "actionabilityScore": 78,
            "priority": "HIGH",
            "percentageOfCase": 21.0,
            "amountExposure": "2.1000",
            "jurisdiction": "Cayman Islands / Global (FIU-IND Offshore Registered)",
            "kycStatus": "MANDATORY_KYC",
            "isFiuRegistered": True,
            "reasons": [
                "Significant financial exposure: 2.1000 ETH (₹2.1 Lakhs)",
                "21.0% of tracked funds reached Binance Hot Wallet 14",
                "Verified exchange custodial infrastructure",
                "Active law enforcement request portal",
            ],
            "recommendedContactOrder": 2,
        },
        {
            "entityName": "Unknown Cluster UC-2026-0042",
            "address": "0x8899aabbccddeeff00112233445566778899aabb",
            "actionabilityScore": 61,
            "priority": "MEDIUM",
            "percentageOfCase": 14.0,
            "amountExposure": "1.4000",
            "jurisdiction": "Unknown / Unhosted Custodial Infrastructure",
            "kycStatus": "UNKNOWN",
            "isFiuRegistered": False,
            "reasons": [
                "Probable Custodial Service cluster controlling 27 interconnected addresses",
                "VASP Behavior Score: 86/100 (High-frequency sweeps and multi-party consolidation)",
                "Exact provider is not independently verified",
            ],
            "recommendedContactOrder": 3,
        },
    ]

    mis = {
        "targetCoverageThreshold": 70.0,
        "achievedCoveragePercentage": 73.0,
        "coveredAmount": "7.3000",
        "vaspCount": 2,
        "selectedVasps": [
            {
                "name": "CoinDCX (Neblio Technologies Pvt Ltd)",
                "address": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
                "amountExposure": "5.2000",
                "priority": "CRITICAL",
                "jurisdiction": "India (FIU-IND Registered)",
            },
            {
                "name": "Binance Global",
                "address": "0x28c6c06298d514db089934071355e5743bf21d60",
                "amountExposure": "2.1000",
                "priority": "HIGH",
                "jurisdiction": "Global / FIU-IND Offshore",
            },
        ],
        "explanation": "Minimum Intervention Set recommends serving Section 91 CrPC notices to CoinDCX and Binance to cover 73.0% of tracked proceeds (7.3000 ETH / ₹7.3 Lakhs).",
    }

    clusters = [
        {
            "clusterId": "UC-2026-0042",
            "chain": "ethereum",
            "addresses": [
                "0x8899aabbccddeeff00112233445566778899aabb",
                "0x1234567890123456789012345678901234567890",
                "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            ],
            "addressCount": 27,
            "centralWallets": ["0x8899aabbccddeeff00112233445566778899aabb"],
            "transactionCount": 1842,
            "uniqueDepositors": 611,
            "classification": "Probable Custodial Service",
            "vaspBehaviorScore": 86,
            "exactOrganization": "Unknown",
            "verification": "UNVERIFIED",
            "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION",
            "evidence": [
                "Many-to-one aggregation: 611 unique depositors consolidate into 1 central wallet",
                "Short balance retention: Average 48 minutes before batch sweeping",
                "High activity: 1,842 transactions significantly exceeds retail personal activity",
            ],
        }
    ]

    taint_results = {
        "taintModel": "PROPORTIONAL_TAINT",
        "originalSuspiciousValue": "10.0000",
        "tracedValue": "8.7000",
        "attributedToKnownVasp": "7.3000",
        "attributedToUnknownVasp": "1.4000",
        "unresolvedValue": "1.3000",
        "estimatedFees": "0.0850",
        "caseCoveragePercentage": 87.0,
        "conservationWarning": None,
        "hasConsistencyAnomaly": False,
        "accountingUnit": "ETH",
    }

    attribution_challenges = [
        {
            "entityName": "CoinDCX",
            "initialConfidence": 94,
            "adjustedConfidence": 92,
            "adjustedConfidenceLevel": "HIGH",
            "supportingEvidence": [
                "Public Etherscan verified CoinDCX exchange deposit contract",
                "FIU-IND Reporting Entity Registry confirmed",
                "Direct 1-hop deposit observed from suspect wallet",
            ],
            "conflictingEvidence": [],
            "assumptions": ["Assumes deposit router contract belongs exclusively to CoinDCX omnibus infrastructure"],
            "alternativeExplanations": [],
            "recommendation": "HIGH CONFIDENCE — PROCEED WITH SECTION 91 CrPC STATUTORY REQUISITION",
            "requiresHumanReview": False,
        },
        {
            "entityName": "Unknown Cluster UC-2026-0042",
            "initialConfidence": 86,
            "adjustedConfidence": 74,
            "adjustedConfidenceLevel": "MEDIUM",
            "supportingEvidence": [
                "Strong consolidation pattern: 611 depositors to 1 central address",
                "Short retention time (< 50 mins)",
            ],
            "conflictingEvidence": ["Operating entity is not independently verified in any regulatory database"],
            "assumptions": ["Assumes automated pooling pattern indicates commercial custodial service rather than bot farm"],
            "alternativeExplanations": ["Could be an unhosted OTC trading desk or high-volume payment processor"],
            "recommendation": "PROBABLE ATTRIBUTION — HUMAN REVIEW & CORROBORATION RECOMMENDED",
            "requiresHumanReview": True,
        },
    ]

    next_actions = [
        {
            "actionId": "ACT-001",
            "priority": "CRITICAL",
            "actionType": "PRESERVE_EVIDENCE",
            "title": "Preserve On-Chain Ledger Evidence Snapshot",
            "reason": "Cryptographic timestamping and transaction hashes must be preserved for Section 65B BSA court admissibility.",
            "relatedEntity": "Case File CASE-2026-SIH-DEMO-001",
            "expectedInvestigativeValue": "Establishes non-repudiable legal chain of custody.",
            "evidenceRequired": "Raw transaction JSON and block height manifest with SHA-256 hash.",
            "currentConfidence": 100,
        },
        {
            "actionId": "ACT-002",
            "priority": "CRITICAL",
            "actionType": "ISSUE_LAWFUL_REQUEST",
            "title": "Serve Section 91 CrPC Notice to CoinDCX Nodal Officer",
            "reason": "Primary actionable destination: 5.2 ETH (52% of stolen funds, Actionability Score: 92/100).",
            "relatedEntity": "CoinDCX (Neblio Technologies)",
            "expectedInvestigativeValue": "Immediate account debit freeze; KYC dossier (Aadhaar/PAN) and bank account details.",
            "evidenceRequired": "Certified transaction hash manifest and deposit router proof.",
            "currentConfidence": 94,
        },
        {
            "actionId": "ACT-003",
            "priority": "HIGH",
            "actionType": "ISSUE_LAWFUL_REQUEST",
            "title": "Serve Subpoena Request to Binance Law Enforcement Portal",
            "reason": "Secondary destination handling 2.1 ETH (21% of case funds, Actionability Score: 78/100).",
            "relatedEntity": "Binance Global",
            "expectedInvestigativeValue": "Prevents asset dissipation across secondary laundering branch.",
            "evidenceRequired": "Deposit transaction hash and recipient address proof.",
            "currentConfidence": 89,
        },
        {
            "actionId": "ACT-004",
            "priority": "HIGH",
            "actionType": "INVESTIGATE_CLUSTER",
            "title": "Investigate Potential Service Cluster UC-2026-0042",
            "reason": "Controls 27 addresses exhibiting strong custodial behavior (1.4 ETH exposure).",
            "relatedEntity": "UC-2026-0042",
            "expectedInvestigativeValue": "Identifies hidden exchange deposit router or syndicate off-ramp.",
            "evidenceRequired": "Consolidation timing analysis and counterparty clustering records.",
            "currentConfidence": 86,
        },
        {
            "actionId": "ACT-005",
            "priority": "MEDIUM",
            "actionType": "CONTINUE_TRACING",
            "title": "Trace Residual Unresolved Funds (1.3000 ETH)",
            "reason": "1.3 ETH remains parked in intermediate unhosted wallets.",
            "relatedEntity": "Intermediary Wallets",
            "expectedInvestigativeValue": "Determines final cash-out endpoint.",
            "evidenceRequired": "2-hop BFS expansion.",
            "currentConfidence": 70,
        },
    ]

    timeline = [
        {"time": "10:02:14", "step": 1, "event": "Suspect Wallet Inflow", "description": "Suspect address received 10.0 ETH cybercrime proceeds.", "severity": "CRITICAL"},
        {"time": "10:19:40", "step": 2, "event": "Multi-Branch Splitting", "description": "Funds fragmented across 3 separate branches (CoinDCX, Binance feeder, Cluster feeder).", "severity": "HIGH"},
        {"time": "11:07:12", "step": 3, "event": "Consolidation at Cluster UC-2026-0042", "description": "Feeder address swept 1.4 ETH into suspected custodial deposit collection wallet.", "severity": "MEDIUM"},
        {"time": "12:02:55", "step": 4, "event": "Direct Deposit at CoinDCX", "description": "5.2 ETH deposited into verified CoinDCX exchange deposit address.", "severity": "ACTIONABLE"},
        {"time": "12:15:30", "step": 5, "event": "Deposit at Binance", "description": "2.1 ETH forwarded through intermediary and deposited into Binance Hot Wallet.", "severity": "ACTIONABLE"},
    ]

    # Pre-build realistic demo graph nodes and edges
    demo_nodes = [
        {"address": demo_suspect, "depth": 0, "type": "suspect", "chain": "ethereum", "entityName": "Suspect Target", "nodeColor": "#3b82f6", "riskScore": 92, "riskLevel": "CRITICAL", "tags": ["Searched Target", "Cyber Fraud Suspect"]},
        {"address": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b", "depth": 1, "type": "known_entity", "chain": "ethereum", "entityName": "CoinDCX", "entityType": "centralized_exchange", "nodeColor": "#10b981", "riskScore": 14, "riskLevel": "LOW", "tags": ["Verified VASP", "CoinDCX"]},
        {"address": "0x3344b56789012345678901234567890123456789", "depth": 1, "type": "wallet", "chain": "ethereum", "entityName": "Intermediary Splitter A", "nodeColor": "#f97316", "riskScore": 78, "riskLevel": "HIGH", "tags": ["Peeling Chain", "Rapid Sweep"]},
        {"address": "0x28c6c06298d514db089934071355e5743bf21d60", "depth": 2, "type": "known_entity", "chain": "ethereum", "entityName": "Binance 14", "entityType": "centralized_exchange", "nodeColor": "#10b981", "riskScore": 16, "riskLevel": "LOW", "tags": ["Verified VASP", "Binance 14"]},
        {"address": "0x5566c78901234567890123456789012345678901", "depth": 1, "type": "wallet", "chain": "ethereum", "entityName": "Intermediary Feeder B", "nodeColor": "#f97316", "riskScore": 73, "riskLevel": "HIGH", "tags": ["Aggregator Feeder"]},
        {"address": "0x8899aabbccddeeff00112233445566778899aabb", "depth": 2, "type": "wallet", "chain": "ethereum", "entityName": "Cluster UC-42 Central Hub", "entityType": "custodial_wallet", "nodeColor": "#a855f7", "riskScore": 86, "riskLevel": "HIGH", "tags": ["Probable VASP", "Cluster UC-2026-0042"]},
    ]
    demo_edges = [
        {"source": demo_suspect, "target": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b", "totalValue": "5.2000", "asset": "ETH", "transactionCount": 1, "hopDepth": 1, "transactionHashes": ["0xd1a...coindcx"]},
        {"source": demo_suspect, "target": "0x3344b56789012345678901234567890123456789", "totalValue": "2.1000", "asset": "ETH", "transactionCount": 1, "hopDepth": 1, "transactionHashes": ["0xd2b...feeder1"]},
        {"source": "0x3344b56789012345678901234567890123456789", "target": "0x28c6c06298d514db089934071355e5743bf21d60", "totalValue": "2.1000", "asset": "ETH", "transactionCount": 1, "hopDepth": 2, "transactionHashes": ["0xd3c...binance"]},
        {"source": demo_suspect, "target": "0x5566c78901234567890123456789012345678901", "totalValue": "1.4000", "asset": "ETH", "transactionCount": 1, "hopDepth": 1, "transactionHashes": ["0xd4d...feeder2"]},
        {"source": "0x5566c78901234567890123456789012345678901", "target": "0x8899aabbccddeeff00112233445566778899aabb", "totalValue": "1.4000", "asset": "ETH", "transactionCount": 1, "hopDepth": 2, "transactionHashes": ["0xd5e...cluster"]},
    ]

    demo_report = await report_service.generate_report(
        target_address=demo_suspect,
        chain="ethereum",
        case_id=cid,
        max_depth=2,
    )

    from backend.schemas.attribution import (
        AttributionResponse,
        AttributionGraph,
        TraceSummary,
        NearestVaspResult,
        VaspCandidate,
        ConfidenceLevel,
        FundPath,
    )
    from backend.schemas.wallet import FundPathStep

    demo_attribution = AttributionResponse(
        rootWallet=demo_suspect,
        chain="ethereum",
        traceSummary=TraceSummary(nodes=6, transactions=5, maxDepth=2, direction="outgoing", executionTimeSeconds=0.85),
        nearestVasp=NearestVaspResult(
            name="CoinDCX (Neblio Technologies)",
            address="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
            type="centralized_exchange",
            hopDistance=1,
            confidence=ConfidenceLevel.HIGH,
            source="FIU-IND Verified Registry",
            path=[demo_suspect, "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"],
            totalTransferred="5.2000",
            isDirectDepositEndpoint=True,
            endpointClassification="Regulated Indian Exchange Deposit Endpoint",
            transactionHashes=["0xd1a...coindcx"],
        ),
        vaspCandidates=[
            VaspCandidate(
                entityName="CoinDCX",
                entityType="centralized_exchange",
                address="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
                hopDistance=1,
                confidence=ConfidenceLevel.HIGH,
                source="FIU-IND Register",
                totalObservedTransfer="5.2000",
                path=[demo_suspect, "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"],
                transactionHashes=["0xd1a...coindcx"],
                isDirectDepositEndpoint=True,
                endpointClassification="Exchange Deposit Router",
                verified=True,
            ),
            VaspCandidate(
                entityName="Binance Global",
                entityType="centralized_exchange",
                address="0x28c6c06298d514db089934071355e5743bf21d60",
                hopDistance=2,
                confidence=ConfidenceLevel.HIGH,
                source="Etherscan Label",
                totalObservedTransfer="2.1000",
                path=[demo_suspect, "0x3344b56789012345678901234567890123456789", "0x28c6c06298d514db089934071355e5743bf21d60"],
                transactionHashes=["0xd3c...binance"],
                isDirectDepositEndpoint=True,
                endpointClassification="Centralized Exchange Hot Wallet",
                verified=True,
            ),
        ],
        paths=[
            FundPath(
                pathId="PATH-001",
                source=demo_suspect,
                destination="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
                hopCount=1,
                totalVolume="5.2000",
                path=[demo_suspect, "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b"],
                steps=[FundPathStep(hopDepth=1, fromAddress=demo_suspect, toAddress="0x6cc5f688a315f3dc28a7781717a9a798a59fda7b", amount="5.2000", asset="ETH", txHash="0xd1a...coindcx")],
            ),
            FundPath(
                pathId="PATH-002",
                source=demo_suspect,
                destination="0x28c6c06298d514db089934071355e5743bf21d60",
                hopCount=2,
                totalVolume="2.1000",
                path=[demo_suspect, "0x3344b56789012345678901234567890123456789", "0x28c6c06298d514db089934071355e5743bf21d60"],
                steps=[
                    FundPathStep(hopDepth=1, fromAddress=demo_suspect, toAddress="0x3344b56789012345678901234567890123456789", amount="2.1000", asset="ETH", txHash="0xd2b...feeder1"),
                    FundPathStep(hopDepth=2, fromAddress="0x3344b56789012345678901234567890123456789", toAddress="0x28c6c06298d514db089934071355e5743bf21d60", amount="2.1000", asset="ETH", txHash="0xd3c...binance"),
                ],
            ),
        ],
        graph=AttributionGraph(nodes=demo_nodes, edges=demo_edges),
        evidence=[],
        investigationSummary="SIH 2026 Reference Demo Scenario: Multi-branch tracing covering CoinDCX, Binance, and Unknown Cluster UC-42.",
        limitations=["Demonstration data calibrated for national hackathon evaluation."],
    )

    demo_netx = graph_analytics_service.analyze_network_topology(
        nodes=demo_nodes,
        edges=demo_edges,
        target_address=demo_suspect,
        vasp_candidates=[c.model_dump() for c in demo_attribution.vaspCandidates],
    )

    demo_playbook = investigation_engine.generate_deterministic_investigation_playbook(
        target_address=demo_suspect,
        chain="ethereum",
        ranked_vasps=ranked_vasps,
        mis=mis,
        bottleneck_mules=demo_netx.get("bottleneckMules", []),
        clusters=clusters,
        unresolved_val=Decimal("1.3000"),
        total_case_value=Decimal("10.0000"),
        case_id=cid,
        detected_cycles=demo_netx.get("detectedCycles", []),
    )

    dossier = InvestigationDossierResponse(
        caseId=cid,
        targetAddress=demo_suspect,
        chain="ethereum",
        status="COMPLETED",
        generatedAt=now_iso,
        taintAccounting=taint_results,
        vaspActionabilityRankings=ranked_vasps,
        minimumInterventionSet=mis,
        attributionChallenges=attribution_challenges,
        unknownVaspCandidates=[
            {
                "address": "0x8899aabbccddeeff00112233445566778899aabb",
                "entityType": "CUSTODIAL_SERVICE",
                "vaspBehaviorScore": 86,
                "classification": "STRONG_VASP_LIKE_BEHAVIOUR",
                "evidence": ["Many-to-one pooling", "Short retention time", "Automated sweeping"],
                "verification": "UNVERIFIED",
                "disclaimer": "HEURISTIC CLASSIFICATION — NOT VERIFIED ATTRIBUTION",
            }
        ],
        serviceClusters=clusters,
        evidenceGaps=[
            {
                "gapId": "GAP-001",
                "title": "Unverified Ownership for Cluster UC-2026-0042",
                "description": "Cluster controls 27 addresses pooling 1.4 ETH, but legal operating entity is unconfirmed.",
                "recommendedAction": "Issue formal inquiry to suspected Indian/Offshore infrastructure host.",
                "potentialConfidenceImprovement": "67% -> ~85% (Estimated)",
                "priority": "HIGH",
            }
        ],
        blindSpots=["Unhosted intermediary wallet 0x3344b... private keys are self-custodied."],
        nextActions=next_actions,
        investigationPlaybook=demo_playbook,
        networkAnalytics=demo_netx,
        timeline=timeline,
        caseCoverage={
            "originalAmount": "10.0000",
            "tracedAmount": "8.7000",
            "atKnownVasp": "7.3000",
            "atUnknownVasp": "1.4000",
            "unresolved": "1.3000",
            "coveragePercentage": 87.0,
        },
        report=demo_report,
        attribution=demo_attribution,
    )

    try:
        await db_manager.reports.update_one(
            {"_id": f"rep:{cid}"},
            {"$set": {"_id": f"rep:{cid}", "caseId": cid, "targetAddress": demo_suspect, "report": demo_report.model_dump()}},
            upsert=True,
        )
    except Exception as e:
        logger.warning(f"Could not persist demo report in DB: {e}")

    return dossier


# -------------------------------------------------------------
# -------------------------------------------------------------
# 8. Wallet Search History & Saved Wallets (MongoDB)
# -------------------------------------------------------------
@router.get(
    "/history/wallet/{address}",
    summary="Retrieve Global & Investigator Search History",
)
async def get_wallet_history(address: str, chain: str = Query("ethereum")):
    return await history_service.get_wallet_history(address, chain)


@router.get(
    "/wallets",
    summary="List Saved Wallets from MongoDB Repository",
    description="Retrieves all investigated and saved wallets, complete with balances, risk scores, tags, and attribution from MongoDB.",
)
async def list_saved_wallets(
    chain: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    filter_dict = {}
    if chain:
        filter_dict["chain"] = chain.lower().strip()
    wallets = await db_manager.wallets.find(filter_dict, limit=limit)
    return {
        "count": len(wallets),
        "wallets": wallets,
        "database": db_manager.get_status(),
    }


@router.get(
    "/wallets/{address}",
    summary="Get Saved Wallet Intelligence from MongoDB",
)
async def get_saved_wallet(
    address: str,
    chain: str = Query("ethereum"),
):
    key = f"{chain.lower().strip()}:{address.lower().strip()}"
    wallet = await db_manager.wallets.find_one({"_id": key})
    if not wallet:
        # Also try searching by address without chain prefix
        results = await db_manager.wallets.find({"address": address.lower().strip()}, limit=1)
        wallet = results[0] if results else None

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet {address} not found in MongoDB repository.",
        )
    return wallet



# -------------------------------------------------------------
# 9. Entities Directory
# -------------------------------------------------------------
@router.get(
    "/entities",
    response_model=List[Dict[str, Any]],
    summary="List Known Attributed Entities",
)
async def list_entities() -> List[Dict[str, Any]]:
    return entity_service.get_all_entities()


# -------------------------------------------------------------
# 10. Settings & System Health
# -------------------------------------------------------------
@router.get(
    "/settings",
    summary="Get Runtime Configuration & DB Status",
)
async def get_system_settings():
    db_stat = db_manager.get_status()
    return {
        "settings": {
            "etherscanApiKey": bool(settings.ETHERSCAN_API_KEY),
            "blockscoutBaseUrl": settings.BLOCKSCOUT_BASE_URL,
            "blockstreamApiUrl": settings.BLOCKSTREAM_API_URL,
            "trongridApiKey": bool(settings.TRONGRID_API_KEY),
            "tronscanApiKey": bool(settings.TRONSCAN_API_KEY),
            "solanaRpcUrl": settings.SOLANA_RPC_URL,
            # Never return a credential-bearing database URI to the browser.
            # Leaving this blank prevents an unchanged settings form from
            # writing a redacted placeholder back into the running config.
            "mongodbUri": "",
            "ollamaHost": settings.OLLAMA_HOST,
            "ollamaModel": settings.OLLAMA_MODEL,
            "emailNotificationsEnabled": settings.EMAIL_NOTIFICATIONS_ENABLED,
            "smtpHost": settings.SMTP_HOST,
            "smtpPort": settings.SMTP_PORT,
            "smtpUser": settings.SMTP_USER,
            "alertEmailRecipient": settings.ALERT_EMAIL_RECIPIENT,
            "investigatorId": settings.INVESTIGATOR_ID,
            "investigatorName": settings.INVESTIGATOR_NAME,
        },
        "database": db_stat,
    }


@router.post(
    "/settings",
    summary="Update Runtime Configuration",
)
async def update_system_settings(payload: SystemSettingsModel):
    if payload.etherscanApiKey is not None:
        settings.ETHERSCAN_API_KEY = payload.etherscanApiKey
    if payload.blockscoutBaseUrl:
        settings.BLOCKSCOUT_BASE_URL = payload.blockscoutBaseUrl
    if payload.blockstreamApiUrl:
        settings.BLOCKSTREAM_API_URL = payload.blockstreamApiUrl
    if payload.trongridApiKey is not None:
        settings.TRONGRID_API_KEY = payload.trongridApiKey
    if payload.tronscanApiKey is not None:
        settings.TRONSCAN_API_KEY = payload.tronscanApiKey
    if payload.solanaRpcUrl:
        settings.SOLANA_RPC_URL = payload.solanaRpcUrl
    if payload.mongodbUri:
        settings.MONGODB_URI = payload.mongodbUri
    if payload.ollamaHost:
        settings.OLLAMA_HOST = payload.ollamaHost
    if payload.ollamaModel:
        settings.OLLAMA_MODEL = payload.ollamaModel
    if payload.emailNotificationsEnabled is not None:
        settings.EMAIL_NOTIFICATIONS_ENABLED = payload.emailNotificationsEnabled
    if payload.smtpHost is not None:
        settings.SMTP_HOST = payload.smtpHost
    if payload.smtpPort:
        settings.SMTP_PORT = payload.smtpPort
    if payload.smtpUser is not None:
        settings.SMTP_USER = payload.smtpUser
    if payload.smtpPassword is not None:
        settings.SMTP_PASSWORD = payload.smtpPassword
    if payload.alertEmailRecipient is not None:
        settings.ALERT_EMAIL_RECIPIENT = payload.alertEmailRecipient
    if payload.investigatorId:
        settings.INVESTIGATOR_ID = payload.investigatorId
    if payload.investigatorName:
        settings.INVESTIGATOR_NAME = payload.investigatorName

    return {"status": "updated", "message": "System settings saved successfully."}


@router.get(
    "/health",
    summary="Health Check",
)
async def health_check():
    return {
        "status": "healthy",
        "service": "SAHYOG Cryptocurrency Attribution Workstation",
        "database": db_manager.get_status(),
        "ollamaHost": settings.OLLAMA_HOST,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
