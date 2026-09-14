import pytest
from decimal import Decimal
from backend.services.graph_analytics_service import graph_analytics_service
from backend.services.investigation_engine import investigation_engine


def test_networkx_graph_analytics_and_mule_identification():
    nodes = [
        {"address": "0xSuspect", "entityName": "Suspect Target", "depth": 0},
        {"address": "0xMule1", "entityName": "Intermediary Mule 1", "depth": 1},
        {"address": "0xVasp", "entityName": "CoinDCX", "entityType": "centralized_exchange", "depth": 2},
        {"address": "0xLeaf", "entityName": "Side Wallet", "depth": 1},
    ]
    edges = [
        {"source": "0xSuspect", "target": "0xMule1", "totalValue": "5.0"},
        {"source": "0xMule1", "target": "0xVasp", "totalValue": "5.0"},
        {"source": "0xSuspect", "target": "0xLeaf", "totalValue": "1.0"},
    ]

    res = graph_analytics_service.analyze_network_topology(
        nodes=nodes,
        edges=edges,
        target_address="0xSuspect",
        vasp_candidates=[{"address": "0xVasp", "entityName": "CoinDCX", "confidence": "HIGH"}],
    )

    assert res["graphSummary"]["nodeCount"] == 4
    assert res["graphSummary"]["edgeCount"] == 3
    assert res["graphSummary"]["isDirectedAcyclic"] is True

    # 0xMule1 bridges 0xSuspect to 0xVasp and should have high betweenness centrality
    mules = res["bottleneckMules"]
    assert len(mules) >= 1
    top_mule = mules[0]
    assert top_mule["address"].lower() == "0xmule1"
    assert top_mule["betweennessCentrality"] > 0

    # Confidence adjustment check
    adjustments = res["confidenceAdjustments"]
    assert len(adjustments) >= 1
    assert adjustments[0]["entityName"] == "CoinDCX"
    assert adjustments[0]["adjustedLevel"] == "HIGH"


def test_deterministic_investigation_playbook_generation():
    ranked_vasps = [
        {
            "entityName": "CoinDCX",
            "address": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
            "amountExposure": "5.2000",
            "percentageOfCase": 52.0,
            "actionabilityScore": 92,
            "priority": "CRITICAL",
            "jurisdiction": "India (FIU-IND Registered)",
        },
        {
            "entityName": "Binance Global",
            "address": "0x28c6c06298d514db089934071355e5743bf21d60",
            "amountExposure": "2.1000",
            "percentageOfCase": 21.0,
            "actionabilityScore": 78,
            "priority": "HIGH",
            "jurisdiction": "Global / Offshore",
        },
    ]

    mis = {
        "achievedCoveragePercentage": 73.0,
        "vaspCount": 2,
        "selectedVasps": ranked_vasps,
    }

    bottlenecks = [
        {
            "address": "0x3344b56789012345678901234567890123456789",
            "entityName": "Intermediary Mule A",
            "betweennessCentrality": 0.50,
            "significance": "Carries 50% of paths",
        }
    ]

    playbook = investigation_engine.generate_deterministic_investigation_playbook(
        target_address="0xSuspectTarget123",
        chain="ethereum",
        ranked_vasps=ranked_vasps,
        mis=mis,
        bottleneck_mules=bottlenecks,
        clusters=[],
        unresolved_val=Decimal("1.3"),
        total_case_value=Decimal("10.0"),
        case_id="CASE-2026-TEST-001",
    )

    assert len(playbook) >= 6
    # Step 1 must be Evidence Preservation (Section 65B BSA)
    assert playbook[0]["stepNumber"] == 1
    assert "Section 65B" in playbook[0]["statutoryReference"]
    assert playbook[0]["phase"] == "GOLDEN_WINDOW"

    # Step 2 must be Emergency Debit Freeze on CoinDCX
    assert playbook[1]["stepNumber"] == 2
    assert "CoinDCX" in playbook[1]["title"]
    assert "Section 91 & 102 CrPC" in playbook[1]["statutoryReference"]

    # Step 3 must target the bottleneck mule discovered by NetworkX
    assert playbook[2]["stepNumber"] == 3
    assert "Bottleneck Mule" in playbook[2]["title"]
    assert bottlenecks[0]["address"] in playbook[2]["targetAddress"]

    # Step 4 must target secondary VASP (Binance)
    assert playbook[3]["stepNumber"] == 4
    assert "Binance Global" in playbook[3]["title"]
