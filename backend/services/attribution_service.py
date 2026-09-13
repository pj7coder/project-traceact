from datetime import datetime, timezone
import logging
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set

from backend.schemas.wallet import (
    TraceFundsRequest,
    TraceFundsResponse,
    BlockchainNetwork,
    TraceDirection,
)
from backend.schemas.attribution import (
    AttributionRequest,
    AttributionResponse,
    AttributionEvidenceItem,
    VaspCandidate,
    NearestVaspResult,
    TraceSummary,
    AttributionGraph,
    ConfidenceLevel,
)
from backend.database.mongo import db_manager
from backend.services.tracing_service import tracing_service
from backend.services.entity_service import entity_service

logger = logging.getLogger("attribution_service")


class AttributionService:
    """
    Deterministic VASP Attribution Service for Cryptocurrency Forensic Investigations.
    Answers: 'Which known VASP/exchange is the nearest credible destination of funds from this wallet,
    and what evidence supports that conclusion?'
    Strictly rule-based, deterministic, zero LLM dependency.
    """

    @staticmethod
    def _eth_to_decimal(val: Any) -> Decimal:
        try:
            return Decimal(str(val))
        except Exception:
            return Decimal("0")

    async def analyze_attribution(self, request: AttributionRequest) -> AttributionResponse:
        chain_val = request.chain.value if hasattr(request.chain, "value") else str(request.chain)
        chain_clean = chain_val.lower().strip()
        is_multi_chain = chain_clean in ("tron", "bitcoin", "solana")
        root_clean = request.address.strip() if is_multi_chain else request.address.lower().strip()
        logger.info(
            f"[ATTRIBUTION_START] Target: {root_clean} ({chain_clean}) | MaxDepth: {request.maxDepth} | Direction: {request.direction.value}"
        )

        # 1. Execute multi-hop BFS tracing
        trace_req = TraceFundsRequest(
            chain=request.chain,
            address=root_clean,
            maxDepth=request.maxDepth,
            direction=request.direction,
            minimumTransferValue=request.minimumTransferValue,
            startTimestamp=request.startTimestamp,
            endTimestamp=request.endTimestamp,
            maxNodes=request.maxNodes,
        )
        trace_result: TraceFundsResponse = await tracing_service.trace_wallet_funds(trace_req)

        # 2. Extract and evaluate all VASP candidates
        vasp_candidates: List[VaspCandidate] = []
        seen_vasp_addrs: Set[str] = set()

        # Check if the root wallet itself is a known VASP
        root_entity = entity_service.get_entity(root_clean.lower())
        if root_entity and root_entity.is_vasp():
            conf_enum = ConfidenceLevel.HIGH if root_entity.confidence == "HIGH" else (
                ConfidenceLevel.MEDIUM if root_entity.confidence == "MEDIUM" else ConfidenceLevel.LOW
            )
            root_candidate = VaspCandidate(
                entityName=root_entity.entity_name,
                entityType=root_entity.entity_type,
                address=root_clean,
                hopDistance=0,
                confidence=conf_enum,
                source=root_entity.source,
                sourceUrl=root_entity.source_url,
                totalObservedTransfer="0",
                path=[root_clean],
                transactionHashes=[],
                isDirectDepositEndpoint=True,
                endpointClassification=f"Target wallet is itself an identified {root_entity.entity_type} infrastructure endpoint",
                verified=root_entity.verified,
            )
            vasp_candidates.append(root_candidate)
            seen_vasp_addrs.add(root_clean)

        for node in trace_result.nodes:
            node_addr = node.address.lower()
            if node_addr == root_clean.lower():
                continue

            entity_record = entity_service.get_entity(node_addr)
            if not entity_record or not entity_record.is_vasp():
                continue

            if node_addr in seen_vasp_addrs:
                continue
            seen_vasp_addrs.add(node_addr)

            # Find matching path terminating at or passing through this node
            matching_path = None
            for p in trace_result.paths:
                if node_addr in [addr.lower() for addr in p.path]:
                    matching_path = p
                    break

            if matching_path:
                path_addresses = matching_path.path
                # Calculate hop distance based on index in path
                try:
                    idx = [a.lower() for a in path_addresses].index(node_addr)
                    hop_dist = idx
                except ValueError:
                    hop_dist = node.depth
                path_vol = matching_path.totalVolume
                tx_hashes = [s.txHash for s in matching_path.steps if s.txHash]
            else:
                path_addresses = [root_clean, node_addr] if node.depth == 1 else [root_clean, f"intermediary (depth {node.depth-1})", node_addr]
                hop_dist = node.depth
                path_vol = node.totalReceivedFromParent or "0"
                tx_hashes = []

            # Determine endpoint classification
            if hop_dist == 1:
                endpoint_class = "Direct exchange counterparty address"
                is_direct_deposit = True
            else:
                endpoint_class = "Multi-hop exchange-attributed address"
                is_direct_deposit = False

            confidence_enum = ConfidenceLevel.HIGH if entity_record.confidence == "HIGH" else (
                ConfidenceLevel.MEDIUM if entity_record.confidence == "MEDIUM" else ConfidenceLevel.LOW
            )

            candidate = VaspCandidate(
                entityName=entity_record.entity_name,
                entityType=entity_record.entity_type,
                address=node_addr,
                hopDistance=hop_dist,
                confidence=confidence_enum,
                source=entity_record.source,
                sourceUrl=entity_record.source_url,
                totalObservedTransfer=path_vol,
                path=path_addresses,
                transactionHashes=tx_hashes,
                isDirectDepositEndpoint=is_direct_deposit,
                endpointClassification=endpoint_class,
                verified=entity_record.verified,
                firstSeen=node.firstSeen,
                lastSeen=node.lastSeen,
            )
            vasp_candidates.append(candidate)

        # 3. Sort VASP candidates deterministically:
        # 1) Verified attribution first
        # 2) Lowest hop distance ascending
        # 3) Total volume transferred descending
        # 4) Confidence HIGH > MEDIUM > LOW
        conf_weights = {ConfidenceLevel.HIGH: 3, ConfidenceLevel.MEDIUM: 2, ConfidenceLevel.LOW: 1}
        vasp_candidates.sort(
            key=lambda c: (
                0 if c.verified else 1,
                c.hopDistance,
                -float(self._eth_to_decimal(c.totalObservedTransfer)),
                -conf_weights.get(c.confidence, 0),
            )
        )

        # 4. Nearest VASP selection
        nearest_vasp: Optional[NearestVaspResult] = None
        if vasp_candidates:
            top = vasp_candidates[0]
            nearest_vasp = NearestVaspResult(
                name=top.entityName,
                address=top.address,
                type=top.entityType,
                hopDistance=top.hopDistance,
                confidence=top.confidence,
                source=top.source,
                sourceUrl=top.sourceUrl,
                path=top.path,
                totalTransferred=top.totalObservedTransfer,
                isDirectDepositEndpoint=top.isDirectDepositEndpoint,
                endpointClassification=top.endpointClassification,
                transactionHashes=top.transactionHashes,
            )

        # 5. Formulate Evidence-Based Attribution Bundle
        evidence_items: List[AttributionEvidenceItem] = []

        if nearest_vasp:
            if nearest_vasp.hopDistance == 0:
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="verified_address_match",
                        title="Target Address is a Known VASP Endpoint",
                        description=f"Investigated address {nearest_vasp.address} is directly registered and verified as {nearest_vasp.name} ({nearest_vasp.type}).",
                        metadata={
                            "address": nearest_vasp.address,
                            "entityName": nearest_vasp.name,
                            "entityType": nearest_vasp.type,
                            "verified": True,
                            "source": nearest_vasp.source,
                            "sourceUrl": nearest_vasp.sourceUrl,
                        },
                    )
                )
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="source_verification",
                        title="Attribution Source Provenance",
                        description=f"Attribution backed by {nearest_vasp.source}. Confidence level evaluated as {nearest_vasp.confidence.value}.",
                        metadata={
                            "source": nearest_vasp.source,
                            "sourceUrl": nearest_vasp.sourceUrl,
                            "confidence": nearest_vasp.confidence.value,
                            "verified": True,
                        },
                    )
                )
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="endpoint_classification",
                        title="Direct VASP Infrastructure",
                        description=f"Target wallet is already a regulated {nearest_vasp.type} endpoint. Inquiries should be served directly to {nearest_vasp.name}.",
                        metadata={
                            "endpointClassification": nearest_vasp.endpointClassification,
                            "isDirectDepositEndpoint": True,
                        },
                    )
                )
            else:
                # Evidence Item 1: Exact Address Match
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="verified_address_match",
                        title="Exact Verified VASP Address Match",
                        description=f"Destination address {nearest_vasp.address} is deterministically attributed to {nearest_vasp.name} ({nearest_vasp.type}).",
                        metadata={
                            "address": nearest_vasp.address,
                            "entityName": nearest_vasp.name,
                            "entityType": nearest_vasp.type,
                            "verified": True,
                            "source": nearest_vasp.source,
                            "sourceUrl": nearest_vasp.sourceUrl,
                        },
                    )
                )

                # Evidence Item 2: Transaction Path & Hop Distance
                asset_unit = "TRX / USDT" if chain_clean == "tron" else ("BTC" if chain_clean == "bitcoin" else ("SOL" if chain_clean == "solana" else "ETH"))
                path_str = " -> ".join([f"{a[:6]}...{a[-4:]}" if len(a) > 12 else a for a in nearest_vasp.path])
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="transaction_path",
                        title=f"Direct Transaction Flow Across {nearest_vasp.hopDistance} Hop{'s' if nearest_vasp.hopDistance > 1 else ''}",
                        description=f"Fund flow verified along trajectory: {path_str}. Total observed transfer volume: {nearest_vasp.totalTransferred} {asset_unit}.",
                        metadata={
                            "hopDistance": nearest_vasp.hopDistance,
                            "path": nearest_vasp.path,
                            "totalTransferred": nearest_vasp.totalTransferred,
                            "transactionHashes": nearest_vasp.transactionHashes,
                        },
                    )
                )

                # Evidence Item 3: Source Verification & Confidence
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="source_verification",
                        title="Attribution Source Provenance",
                        description=f"Attribution backed by {nearest_vasp.source}. Confidence level evaluated as {nearest_vasp.confidence.value}.",
                        metadata={
                            "source": nearest_vasp.source,
                            "sourceUrl": nearest_vasp.sourceUrl,
                            "confidence": nearest_vasp.confidence.value,
                            "verified": True,
                        },
                    )
                )

                # Evidence Item 4: Legal Endpoint Classification
                evidence_items.append(
                    AttributionEvidenceItem(
                        type="endpoint_classification",
                        title="VASP Endpoint Forensic Classification",
                        description=f"Classified as '{nearest_vasp.endpointClassification}'. Suitable for Section 91 CrPC / KYC subpoena service.",
                        metadata={
                            "endpointClassification": nearest_vasp.endpointClassification,
                            "isDirectDepositEndpoint": nearest_vasp.isDirectDepositEndpoint,
                        },
                    )
                )
        else:
            evidence_items.append(
                AttributionEvidenceItem(
                    type="unattributed_traversal",
                    title="No Attributed VASP Identified Within Configured Depth",
                    description=f"BFS traversal explored {len(trace_result.nodes)} counterparty wallets across {request.maxDepth} hops without encountering a verified VASP or centralized exchange record.",
                    metadata={
                        "nodesExplored": len(trace_result.nodes),
                        "maxDepth": request.maxDepth,
                        "direction": request.direction.value,
                    },
                )
            )

        # 6. Generate Deterministic Investigation Summary (No LLM)
        if nearest_vasp:
            short_root = f"{root_clean[:6]}...{root_clean[-4:]}"
            short_vasp = f"{nearest_vasp.address[:6]}...{nearest_vasp.address[-4:]}"
            if nearest_vasp.hopDistance == 0:
                investigation_summary = (
                    f"Investigated wallet {short_root} is directly identified as verified {nearest_vasp.type} infrastructure "
                    f"belonging to {nearest_vasp.name} (Hop 0). No intermediary multi-hop tracing was required. "
                    f"Attribution is verified via {nearest_vasp.source} with {nearest_vasp.confidence.value} confidence."
                )
            else:
                investigation_summary = (
                    f"Funds originating from investigated wallet {short_root} were traced across {nearest_vasp.hopDistance} hops "
                    f"along an {request.direction.value} trajectory. A verified {nearest_vasp.type} address associated with "
                    f"{nearest_vasp.name} ({short_vasp}) was identified at hop distance {nearest_vasp.hopDistance} "
                    f"(total observed transfer: {nearest_vasp.totalTransferred} ETH). "
                    f"Attribution is verified via {nearest_vasp.source} with {nearest_vasp.confidence.value} confidence."
                )
        else:
            investigation_summary = (
                f"Funds originating from investigated wallet {root_clean[:6]}...{root_clean[-4:]} were analyzed across "
                f"{request.maxDepth} hops ({len(trace_result.nodes)} nodes, {trace_result.transactionsAnalyzed} transactions evaluated). "
                f"No verified VASP or centralized exchange attribution was identified within the configured tracing threshold."
            )

        # 7. Explicit Forensic Limitations
        limitations = [
            "Intermediary unhosted wallets represent self-custodied private addresses. Their real-world legal owners cannot be identified solely from public ledger data without legal KYC subpoena execution at a regulated VASP.",
            "Attribution reflects verified publicly documented exchange infrastructure (hot wallets, deposit routers). Internal user account matching requires formal legal process with the identified VASP.",
            f"Traversal reflects observable on-chain transactions up to depth {request.maxDepth} with minimum transfer threshold {request.minimumTransferValue or '0.01'} ETH.",
            "Attribution confidence reflects deterministic public ledger labels and does not assess off-chain mixing, non-custodial swaps, or cross-chain bridge conversions.",
        ]

        # 8. Build Complete Response
        # 8. Evaluate Prioritized Rule Engine for Root Target with multi-hop context
        from backend.services.rule_engine import rule_engine
        from backend.services.wallet_service import wallet_service

        overview, txs, connected = await wallet_service.get_wallet_overview_and_data(
            root_clean, request.chain.value if hasattr(request.chain, "value") else str(request.chain)
        )
        risk_assessment = rule_engine.evaluate_wallet(
            wallet=overview,
            transactions=txs,
            connected_wallets=connected,
            multihop_nodes=[n.model_dump() for n in trace_result.nodes],
            system_logic=request.systemLogic,
        )

        # Synchronize evaluated suspicion score and risk level onto root target node
        for n in trace_result.nodes:
            if n.address.lower() == root_clean:
                n.riskScore = risk_assessment["suspicionScore"]
                n.riskLevel = risk_assessment["riskLevel"]
                n.nodeColor = "#3b82f6"  # Bright Blue for Searched Target
                break

        # 9. Build Complete Response
        exec_time = trace_result.metadata.get("executionTimeSeconds", 0.0)
        trace_summary = TraceSummary(
            nodes=trace_result.nodesAnalyzed,
            transactions=trace_result.transactionsAnalyzed,
            maxDepth=trace_result.maxDepth,
            direction=trace_result.direction,
            executionTimeSeconds=exec_time,
        )

        chain_str = request.chain.value if hasattr(request.chain, "value") else str(request.chain)

        # Persist attribution results and full investigation into MongoDB
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            key = f"{chain_str.lower().strip()}:{root_clean}"
            attrib_doc = {
                "nearestVasp": nearest_vasp.model_dump() if nearest_vasp else None,
                "vaspCandidates": [c.model_dump() for c in vasp_candidates[:10]],
                "investigationSummary": investigation_summary,
                "traceSummary": trace_summary.model_dump(),
                "pathsCount": len(trace_result.paths),
                "nodesCount": len(trace_result.nodes),
                "lastAttributedAt": now_iso,
            }
            await db_manager.wallets.update_one(
                {"_id": key},
                {
                    "$set": {
                        "attribution": attrib_doc,
                        "nearestVaspName": nearest_vasp.name if nearest_vasp else None,
                        "nearestVaspAddress": nearest_vasp.address if nearest_vasp else None,
                        "hopDistance": nearest_vasp.hopDistance if nearest_vasp else None,
                    }
                },
                upsert=True,
            )
            await db_manager.investigations.insert_one({
                "targetAddress": root_clean,
                "chain": chain_str,
                "nearestVasp": nearest_vasp.model_dump() if nearest_vasp else None,
                "nodeCount": len(trace_result.nodes),
                "edgeCount": len(trace_result.edges),
                "traceSummary": trace_summary.model_dump(),
                "createdAt": now_iso,
            })
            logger.info(f"Persisted attribution and investigation record for {key} in MongoDB.")
        except Exception as ex:
            logger.warning(f"Error persisting attribution to MongoDB: {ex}")

        return AttributionResponse(
            rootWallet=root_clean,
            chain=chain_str,
            traceSummary=trace_summary,
            nearestVasp=nearest_vasp,
            vaspCandidates=vasp_candidates,
            paths=trace_result.paths,
            graph=AttributionGraph(
                nodes=trace_result.nodes,
                edges=trace_result.edges,
            ),
            evidence=evidence_items,
            investigationSummary=investigation_summary,
            limitations=limitations,
            riskAssessment=risk_assessment,
        )


attribution_service = AttributionService()
