import asyncio
from decimal import Decimal
from unittest.mock import patch

from backend.schemas.wallet import (
    TraceFundsRequest,
    TraceDirection,
)
from backend.services.tracing_service import MultiHopTracingEngine
from backend.services.blockchain_service import (
    RateLimitError,
    BlockchainProviderError,
)
from backend.utils.validators import validate_and_normalize_address

# Test wallet addresses
SUSPECT = "0x1111111111111111111111111111111111111111"
WALLET_A = "0x2222222222222222222222222222222222222222"
WALLET_B = "0x3333333333333333333333333333333333333333"
WALLET_C = "0x4444444444444444444444444444444444444444"
WALLET_D = "0x5555555555555555555555555555555555555555"
BINANCE_EXCHANGE = "0x28c6c06298d514db089934071355e5743bf21d60"


def make_mock_tx(from_addr: str, to_addr: str, value_eth: str, tx_hash: str = "0xabc", ts: str = "2026-09-01T12:00:00Z"):
    """Helper to generate mock raw Blockscout-like transaction."""
    wei_val = str(int(Decimal(value_eth) * Decimal("1000000000000000000")))
    return {
        "hash": tx_hash,
        "from": {"hash": from_addr},
        "to": {"hash": to_addr},
        "value": wei_val,
        "timestamp": ts,
        "block_number": 19000000,
        "status": "ok",
        "gas_used": "21000",
        "fee": {"value": "42000000000000"},
    }


def test_address_validation():
    """Test 7: Address validation & normalization."""
    valid, norm, msg = validate_and_normalize_address("0x28C6C06298d514DB089934071355E5743Bf21D60")
    assert valid is True
    assert norm == "0x28c6c06298d514db089934071355e5743bf21d60"

    valid_bad, _, err = validate_and_normalize_address("invalid_address")
    assert valid_bad is False
    assert "0x" in err

    valid_short, _, err_short = validate_and_normalize_address("0x123")
    assert valid_short is False
    assert "Invalid address length" in err_short


def test_trace_wallet_few_transactions():
    """Test 1: Simple linear 2-hop trace: Suspect -> Wallet A -> Wallet B."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [make_mock_tx(SUSPECT, WALLET_A, "2.5", "0xtx1")],
        WALLET_A: [make_mock_tx(WALLET_A, WALLET_B, "2.0", "0xtx2")],
        WALLET_B: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "10.0", "10000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=2,
                direction=TraceDirection.OUTGOING,
                minimumTransferValue="0.0",
            )
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.rootWallet == SUSPECT
    assert resp.nodesAnalyzed == 3
    assert len(resp.edges) == 2
    assert len(resp.paths) >= 1
    
    path_strs = ["->".join(p.path) for p in resp.paths]
    assert f"{SUSPECT}->{WALLET_A}->{WALLET_B}" in path_strs
    assert resp.traceIncomplete is False


def test_trace_wallet_cyclic_relationship_prevention():
    """Test 3: Cyclic relationships: A -> B -> C -> A. Engine must NOT infinite loop."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [make_mock_tx(SUSPECT, WALLET_A, "5.0", "0xtx1")],
        WALLET_A: [make_mock_tx(WALLET_A, WALLET_B, "4.0", "0xtx2")],
        WALLET_B: [
            make_mock_tx(WALLET_B, WALLET_C, "3.0", "0xtx3"),
            make_mock_tx(WALLET_B, SUSPECT, "1.0", "0xtx_cycle"),  # Cycle back to suspect
        ],
        WALLET_C: [
            make_mock_tx(WALLET_C, WALLET_A, "2.0", "0xtx_cycle2")  # Cycle back to Wallet A
        ],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "5.0", "5000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=4,
                direction=TraceDirection.OUTGOING,
            )
            return await asyncio.wait_for(tracing_engine.trace_wallet_funds(req), timeout=3.0)

    resp = asyncio.run(runner())

    assert resp.rootWallet == SUSPECT
    analyzed_addrs = {n.address for n in resp.nodes}
    assert analyzed_addrs == {SUSPECT, WALLET_A, WALLET_B, WALLET_C}
    assert resp.traceIncomplete is False


def test_trace_wallet_repeated_wallets_across_branches():
    """Test 4: Repeated wallet across branches (Suspect -> A -> C, Suspect -> B -> C)."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [
            make_mock_tx(SUSPECT, WALLET_A, "3.0", "0xtx1"),
            make_mock_tx(SUSPECT, WALLET_B, "2.0", "0xtx2"),
        ],
        WALLET_A: [make_mock_tx(WALLET_A, WALLET_C, "2.5", "0xtx3")],
        WALLET_B: [make_mock_tx(WALLET_B, WALLET_C, "1.5", "0xtx4")],
        WALLET_C: [make_mock_tx(WALLET_C, WALLET_D, "3.0", "0xtx5")],
        WALLET_D: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=3,
                direction=TraceDirection.OUTGOING,
            )
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.nodesAnalyzed == 5  # SUSPECT, A, B, C, D
    assert resp.traceIncomplete is False


def test_max_depth_stopping():
    """Test 5: Traversal stops strictly after maxDepth hops."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [make_mock_tx(SUSPECT, WALLET_A, "10.0", "0xtx1")],
        WALLET_A: [make_mock_tx(WALLET_A, WALLET_B, "9.0", "0xtx2")],
        WALLET_B: [make_mock_tx(WALLET_B, WALLET_C, "8.0", "0xtx3")],
        WALLET_C: [make_mock_tx(WALLET_C, WALLET_D, "7.0", "0xtx4")],
        WALLET_D: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            # Depth 1: Suspect -> A
            req1 = TraceFundsRequest(address=SUSPECT, maxDepth=1)
            resp1 = await tracing_engine.trace_wallet_funds(req1)

            # Depth 2: Suspect -> A -> B
            req2 = TraceFundsRequest(address=SUSPECT, maxDepth=2)
            resp2 = await tracing_engine.trace_wallet_funds(req2)

            # Depth 3: Suspect -> A -> B -> C
            req3 = TraceFundsRequest(address=SUSPECT, maxDepth=3)
            resp3 = await tracing_engine.trace_wallet_funds(req3)

            return resp1, resp2, resp3

    r1, r2, r3 = asyncio.run(runner())

    assert {n.address for n in r1.nodes} == {SUSPECT, WALLET_A}
    assert {n.address for n in r2.nodes} == {SUSPECT, WALLET_A, WALLET_B}
    assert {n.address for n in r3.nodes} == {SUSPECT, WALLET_A, WALLET_B, WALLET_C}
    assert WALLET_D not in {n.address for n in r3.nodes}


def test_max_nodes_limit_stopping():
    """Test 6: Stops with traceIncomplete: True when maxNodes limit is reached."""
    tracing_engine = MultiHopTracingEngine()
    fanout = [make_mock_tx(SUSPECT, f"0x{i:040x}", "1.0", f"0xtx_{i}") for i in range(1, 15)]
    mock_db = {SUSPECT: fanout}

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=2,
                maxNodes=5,  # Force limit of 5 nodes
            )
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.traceIncomplete is True
    assert resp.reason == "NODE_LIMIT_REACHED"


def test_known_entity_matching_and_nearest_vasp():
    """Test 9: Identify nearest known entity candidate during BFS."""
    tracing_engine = MultiHopTracingEngine()
    # Suspect -> Wallet A -> Binance Exchange
    mock_db = {
        SUSPECT: [make_mock_tx(SUSPECT, WALLET_A, "4.2", "0xtx1")],
        WALLET_A: [make_mock_tx(WALLET_A, BINANCE_EXCHANGE, "3.8", "0xtx2")],
        BINANCE_EXCHANGE: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=3,
                direction=TraceDirection.OUTGOING,
            )
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.nearestEntity is not None
    assert resp.nearestEntity.address == BINANCE_EXCHANGE
    assert resp.nearestEntity.hopDistance == 2
    assert "Binance" in resp.nearestEntity.name
    assert resp.nearestEntity.path == [SUSPECT, WALLET_A, BINANCE_EXCHANGE]

    binance_node = next(n for n in resp.nodes if n.address == BINANCE_EXCHANGE)
    assert binance_node.type == "known_entity"
    assert binance_node.entityName == resp.nearestEntity.name


def test_no_known_entity_returns_none():
    """Test 10: Trace with no known entities returns nearestEntity: null."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [make_mock_tx(SUSPECT, WALLET_A, "1.0", "0xtx1")],
        WALLET_A: [make_mock_tx(WALLET_A, WALLET_B, "0.5", "0xtx2")],
        WALLET_B: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(address=SUSPECT, maxDepth=2)
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.nearestEntity is None


def test_minimum_transfer_filter_and_decimal_math():
    """Test 12: Sub-threshold transfers and 0-value calls are filtered, Decimal precision maintained."""
    tracing_engine = MultiHopTracingEngine()
    mock_db = {
        SUSPECT: [
            make_mock_tx(SUSPECT, WALLET_A, "0.005", "0xtx_dust"),
            make_mock_tx(SUSPECT, WALLET_B, "0.000", "0xtx_zero"),
            make_mock_tx(SUSPECT, WALLET_C, "1.23456789", "0xtx_valid"),
        ],
        WALLET_C: [],
    }

    async def mock_get_txs(addr, limit=25):
        return mock_db.get(addr.lower(), [])

    async def mock_get_bal(addr):
        return "2.0", "2000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(
                address=SUSPECT,
                maxDepth=1,
                minimumTransferValue="0.01",
            )
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    analyzed_addrs = {n.address for n in resp.nodes}
    assert analyzed_addrs == {SUSPECT, WALLET_C}
    assert len(resp.edges) == 1
    assert resp.edges[0].totalValue == "1.23456789"


def test_api_failure_graceful_handling():
    """Test 8: Blockchain API failure on counterparty wallet continues gracefully without crashing."""
    tracing_engine = MultiHopTracingEngine()
    
    async def mock_get_txs(addr, limit=25):
        if addr.lower() == SUSPECT:
            return [make_mock_tx(SUSPECT, WALLET_A, "1.0", "0xtx1")]
        # Fail on WALLET_A
        raise BlockchainProviderError("Provider temporary outage")

    async def mock_get_bal(addr):
        return "1.0", "1000000000000000000"

    async def runner():
        with patch("backend.services.tracing_service.blockchain_service.get_transactions", side_effect=mock_get_txs), \
             patch("backend.services.tracing_service.blockchain_service.get_balance", side_effect=mock_get_bal):

            req = TraceFundsRequest(address=SUSPECT, maxDepth=2)
            return await tracing_engine.trace_wallet_funds(req)

    resp = asyncio.run(runner())

    assert resp.rootWallet == SUSPECT
    assert resp.nodesAnalyzed == 2
    assert len(resp.edges) == 1
