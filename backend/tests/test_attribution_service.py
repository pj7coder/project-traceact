import pytest
from unittest.mock import AsyncMock, patch

from backend.schemas.attribution import AttributionRequest, ConfidenceLevel
from backend.schemas.wallet import (
    BlockchainNetwork,
    TraceDirection,
    TraceFundsResponse,
    TraceNode,
    TraceEdge,
    FundPath,
    FundPathStep,
)
from backend.services.attribution_service import attribution_service


@pytest.mark.anyio
async def test_attribution_direct_vasp_match():
    """Verify that a 1-hop direct transfer to a VASP produces nearestVasp at hop 1."""
    root_addr = "0x1111111111111111111111111111111111111111"
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"

    mock_trace_response = TraceFundsResponse(
        rootWallet=root_addr,
        maxDepth=3,
        direction="outgoing",
        nodesAnalyzed=2,
        transactionsAnalyzed=1,
        nodes=[
            TraceNode(address=root_addr, depth=0, type="suspect", balanceEth="5.0"),
            TraceNode(
                address=binance_addr,
                depth=1,
                type="known_entity",
                entityName="Binance 14",
                entityType="centralized_exchange",
                confidence="HIGH",
                totalReceivedFromParent="2.5",
                transactionCount=1,
            ),
        ],
        edges=[
            TraceEdge(
                source=root_addr,
                target=binance_addr,
                totalValue="2.5",
                transactionCount=1,
                hopDepth=1,
                transactionHashes=["0xabc123"],
            )
        ],
        paths=[
            FundPath(
                path=[root_addr, binance_addr],
                hopCount=1,
                totalVolume="2.5",
                steps=[
                    FundPathStep(
                        fromAddress=root_addr,
                        toAddress=binance_addr,
                        amount="2.5",
                        hopDepth=1,
                        txHash="0xabc123",
                    )
                ],
                terminatesAtEntity=binance_addr,
                entityName="Binance 14",
            )
        ],
        nearestEntity=None,
        traceIncomplete=False,
        metadata={"executionTimeSeconds": 0.25},
    )

    with patch("backend.services.attribution_service.tracing_service.trace_wallet_funds", new=AsyncMock(return_value=mock_trace_response)):
        request = AttributionRequest(
            chain=BlockchainNetwork.ETHEREUM,
            address=root_addr,
            maxDepth=3,
            direction=TraceDirection.OUTGOING,
        )
        res = await attribution_service.analyze_attribution(request)

        assert res.nearestVasp is not None
        assert res.nearestVasp.address == binance_addr
        assert res.nearestVasp.hopDistance == 1
        assert "Binance" in res.nearestVasp.name
        assert res.nearestVasp.confidence == ConfidenceLevel.HIGH
        assert res.nearestVasp.totalTransferred == "2.5"
        assert res.nearestVasp.isDirectDepositEndpoint is True
        assert len(res.evidence) >= 3
        assert "Binance" in res.investigationSummary


@pytest.mark.anyio
async def test_attribution_multi_hop_ranking():
    """Verify that multiple VASPs are ranked primarily by lowest hop distance."""
    root_addr = "0x1111111111111111111111111111111111111111"
    interm_addr = "0x2222222222222222222222222222222222222222"
    kraken_addr = "0x2910543af39aba0cd09dbb2d50200b3e800a63d2"  # at hop 1
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"  # at hop 2

    mock_trace_response = TraceFundsResponse(
        rootWallet=root_addr,
        maxDepth=3,
        direction="outgoing",
        nodesAnalyzed=4,
        transactionsAnalyzed=3,
        nodes=[
            TraceNode(address=root_addr, depth=0, type="suspect"),
            TraceNode(
                address=kraken_addr,
                depth=1,
                type="known_entity",
                entityName="Kraken 1",
                entityType="centralized_exchange",
                confidence="HIGH",
                totalReceivedFromParent="1.0",
            ),
            TraceNode(address=interm_addr, depth=1, type="wallet"),
            TraceNode(
                address=binance_addr,
                depth=2,
                type="known_entity",
                entityName="Binance 14",
                entityType="centralized_exchange",
                confidence="HIGH",
                totalReceivedFromParent="5.0",
            ),
        ],
        edges=[],
        paths=[
            FundPath(
                path=[root_addr, kraken_addr],
                hopCount=1,
                totalVolume="1.0",
                steps=[FundPathStep(fromAddress=root_addr, toAddress=kraken_addr, amount="1.0", hopDepth=1)],
            ),
            FundPath(
                path=[root_addr, interm_addr, binance_addr],
                hopCount=2,
                totalVolume="5.0",
                steps=[
                    FundPathStep(fromAddress=root_addr, toAddress=interm_addr, amount="5.0", hopDepth=1),
                    FundPathStep(fromAddress=interm_addr, toAddress=binance_addr, amount="5.0", hopDepth=2),
                ],
            ),
        ],
        nearestEntity=None,
        metadata={"executionTimeSeconds": 0.4},
    )

    with patch("backend.services.attribution_service.tracing_service.trace_wallet_funds", new=AsyncMock(return_value=mock_trace_response)):
        request = AttributionRequest(
            chain=BlockchainNetwork.ETHEREUM,
            address=root_addr,
            maxDepth=3,
            direction=TraceDirection.OUTGOING,
        )
        res = await attribution_service.analyze_attribution(request)

        assert len(res.vaspCandidates) == 2
        # Nearest VASP must be Kraken (hop 1), beating Binance (hop 2)
        assert res.nearestVasp is not None
        assert res.nearestVasp.address == kraken_addr
        assert res.nearestVasp.hopDistance == 1
        assert res.vaspCandidates[0].address == kraken_addr
        assert res.vaspCandidates[1].address == binance_addr
        assert res.vaspCandidates[1].hopDistance == 2


@pytest.mark.anyio
async def test_attribution_no_vasp_found():
    """Verify that when no known entity is hit, nearestVasp is None and explanation is clear."""
    root_addr = "0x1111111111111111111111111111111111111111"
    unknown_addr = "0x9999999999999999999999999999999999999999"

    mock_trace_response = TraceFundsResponse(
        rootWallet=root_addr,
        maxDepth=3,
        direction="outgoing",
        nodesAnalyzed=2,
        transactionsAnalyzed=1,
        nodes=[
            TraceNode(address=root_addr, depth=0, type="suspect"),
            TraceNode(address=unknown_addr, depth=1, type="wallet"),
        ],
        edges=[],
        paths=[
            FundPath(
                path=[root_addr, unknown_addr],
                hopCount=1,
                totalVolume="0.5",
                steps=[],
            )
        ],
        nearestEntity=None,
        metadata={"executionTimeSeconds": 0.1},
    )

    with patch("backend.services.attribution_service.tracing_service.trace_wallet_funds", new=AsyncMock(return_value=mock_trace_response)):
        request = AttributionRequest(
            chain=BlockchainNetwork.ETHEREUM,
            address=root_addr,
            maxDepth=3,
            direction=TraceDirection.OUTGOING,
        )
        res = await attribution_service.analyze_attribution(request)

        assert res.nearestVasp is None
        assert len(res.vaspCandidates) == 0
        assert "No verified VASP" in res.investigationSummary
        assert len(res.limitations) > 0


def test_api_route_invalid_address():
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    resp = client.post("/api/wallet/attribution", json={"chain": "ethereum", "address": "not_an_address"})
    assert resp.status_code == 400
    assert "Invalid Ethereum address" in resp.json()["detail"]


@pytest.mark.anyio
async def test_attribution_root_wallet_is_vasp():
    """Verify that investigating a wallet that is itself a known VASP returns Hop 0 attribution immediately."""
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"

    mock_trace_response = TraceFundsResponse(
        rootWallet=binance_addr,
        maxDepth=3,
        direction="outgoing",
        nodesAnalyzed=1,
        transactionsAnalyzed=0,
        nodes=[
            TraceNode(address=binance_addr, depth=0, type="known_entity", entityName="Binance 14"),
        ],
        edges=[],
        paths=[],
        nearestEntity=None,
        metadata={"executionTimeSeconds": 0.05},
    )

    with patch("backend.services.attribution_service.tracing_service.trace_wallet_funds", new=AsyncMock(return_value=mock_trace_response)):
        request = AttributionRequest(
            chain=BlockchainNetwork.ETHEREUM,
            address=binance_addr,
            maxDepth=3,
            direction=TraceDirection.OUTGOING,
        )
        res = await attribution_service.analyze_attribution(request)

        assert res.nearestVasp is not None
        assert res.nearestVasp.address == binance_addr
        assert res.nearestVasp.hopDistance == 0
        assert "Binance" in res.nearestVasp.name
        assert res.nearestVasp.isDirectDepositEndpoint is True
        assert len(res.evidence) >= 3
        assert "Hop 0" in res.investigationSummary


