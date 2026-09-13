import pytest
from backend.services.vasp_discovery_service import vasp_discovery_service
from backend.schemas.wallet import NormalizedTransaction, TransactionDirection


def test_behavioral_feature_extraction_empty():
    """Empty transactions return zeroed features safely."""
    features = vasp_discovery_service.extract_behavioral_features("0x123", [])
    assert features["transaction_count"] == 0
    assert features["unique_senders"] == 0
    assert features["sweep_frequency"] == 0.0


def test_vasp_behavior_scoring_custodial_pattern():
    """Multiple unique senders depositing and sweeping out quickly gets high VASP behavior score."""
    target = "0x9999999999999999999999999999999999999999"
    central_hub = "0x8888888888888888888888888888888888888888"

    # Simulate 6 depositors sending into target, and target sweeping to central hub
    txs = []
    for i in range(6):
        txs.append(
            NormalizedTransaction(
                txHash=f"0x_in_{i}",
                chain="ethereum",
                fromAddress=f"0x111111111111111111111111111111111111110{i}",
                toAddress=target,
                value="2.0",
                timestamp=f"2026-08-01T12:0{i}:00Z",
                direction=TransactionDirection.INCOMING,
            )
        )

    # Sweeps to central hub
    txs.append(
        NormalizedTransaction(
            txHash="0x_sweep",
            chain="ethereum",
            fromAddress=target,
            toAddress=central_hub,
            value="11.8",
            timestamp="2026-08-01T12:30:00Z",
            direction=TransactionDirection.OUTGOING,
        )
    )

    features = vasp_discovery_service.extract_behavioral_features(target, txs)
    assert features["unique_senders"] == 6
    assert features["unique_receivers"] == 1
    assert features["consolidation_ratio"] >= 3.0

    score, breakdown, evidence = vasp_discovery_service.compute_vasp_behavior_score(features)
    assert score >= 60  # PROBABLE_VASP or STRONG_VASP_LIKE_BEHAVIOUR
    assert "many_unique_senders" in breakdown
    assert "consolidation" in breakdown
    assert len(evidence) >= 2

    classification = vasp_discovery_service.classify_entity(features, score)
    assert classification["verified"] is False
    assert "HEURISTIC CLASSIFICATION" in classification["disclaimer"]
    assert classification["tier"] in ["PROBABLE_VASP", "STRONG_VASP_LIKE_BEHAVIOUR"]


def test_service_cluster_detection():
    """Detects multi-party consolidation cluster from graph nodes and edges."""
    hub = "0xHubAddress123"
    f1 = "0xFeeder1"
    f2 = "0xFeeder2"
    f3 = "0xFeeder3"

    nodes = [
        {"address": hub, "vaspBehaviorScore": 85},
        {"address": f1, "vaspBehaviorScore": 40},
        {"address": f2, "vaspBehaviorScore": 40},
        {"address": f3, "vaspBehaviorScore": 40},
    ]
    edges = [
        {"source": f1, "target": hub},
        {"source": f2, "target": hub},
        {"source": f3, "target": hub},
    ]

    clusters = vasp_discovery_service.detect_service_clusters(nodes, edges, chain="ethereum")
    assert len(clusters) >= 1
    c = clusters[0]
    assert c["clusterId"].startswith("UC-2026-")
    assert c["uniqueDepositors"] == 3
    assert hub in c["centralWallets"]
    assert c["verification"] == "UNVERIFIED"
