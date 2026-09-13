import pytest
from decimal import Decimal
from backend.services.investigation_engine import investigation_engine


def test_taint_and_conservation_check():
    """Calculates proportional taint and flags fund conservation consistency."""
    original_val = Decimal("10.0")
    vasp_candidates = [
        {"entityName": "CoinDCX", "totalObservedTransfer": "6.0", "verified": True},
        {"entityName": "Unknown Cluster", "totalObservedTransfer": "2.5", "verified": False},
    ]
    paths = [{"totalVolume": "8.5", "hopCount": 2}]
    nodes = []

    res = investigation_engine.calculate_taint_and_conservation(
        original_suspicious_value=original_val,
        paths=paths,
        nodes=nodes,
        vasp_candidates=vasp_candidates,
        chain="ethereum",
    )

    assert res["taintModel"] == "PROPORTIONAL_TAINT"
    assert res["attributedToKnownVasp"] == "6"
    assert res["attributedToUnknownVasp"] == "2.5"
    assert Decimal(res["unresolvedValue"]) > Decimal("0")
    assert res["hasConsistencyAnomaly"] is False
    assert res["caseCoveragePercentage"] == 85.0


def test_fund_conservation_warning_on_inflation():
    """Detects when accounted volume exceeds root inflow due to unrelated contamination."""
    original_val = Decimal("5.0")
    vasp_candidates = [
        {"entityName": "Binance", "totalObservedTransfer": "8.0", "verified": True},
    ]
    res = investigation_engine.calculate_taint_and_conservation(
        original_suspicious_value=original_val,
        paths=[],
        nodes=[],
        vasp_candidates=vasp_candidates,
        chain="ethereum",
    )
    assert res["hasConsistencyAnomaly"] is True
    assert "FUND FLOW CONSISTENCY WARNING" in res["conservationWarning"]


def test_path_confidence_decay():
    """Confidence decays along multi-hop paths, with extra penalty for mixers and bridges."""
    path = ["0xRoot", "0xHop1", "0xHop2", "0xVasp"]
    decay = investigation_engine.calculate_path_confidence_decay(
        path_addresses=path,
        base_confidence=0.99,
        has_mixer=True,
    )
    assert len(decay["decaySteps"]) == 4
    assert decay["finalConfidence"] < 70.0
    assert decay["decaySteps"][0]["confidence"] == 99.0
    assert any("Mixer" in s["decayFactor"] for s in decay["decaySteps"])


def test_vasp_actionability_and_minimum_intervention_set():
    """Computes actionability score and greedy minimum intervention set."""
    vasp_a = {
        "entityName": "CoinDCX",
        "address": "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",
        "totalObservedTransfer": "4.2",
        "verified": True,
        "confidence": "HIGH",
        "hopDistance": 1,
    }
    vasp_b = {
        "entityName": "Binance",
        "address": "0x28c6c06298d514db089934071355e5743bf21d60",
        "totalObservedTransfer": "3.1",
        "verified": True,
        "confidence": "HIGH",
        "hopDistance": 2,
    }
    vasp_c = {
        "entityName": "Bybit",
        "address": "0xf89d7b9c372f2561063640e4f3a76378e907913d",
        "totalObservedTransfer": "1.0",
        "verified": True,
        "confidence": "HIGH",
        "hopDistance": 3,
    }

    total_val = Decimal("10.0")
    act_a = investigation_engine.calculate_vasp_actionability(vasp_a, total_val)
    act_b = investigation_engine.calculate_vasp_actionability(vasp_b, total_val)
    act_c = investigation_engine.calculate_vasp_actionability(vasp_c, total_val)

    assert act_a["actionabilityScore"] >= 70
    assert act_a["priority"] in ["HIGH", "CRITICAL"]

    # Minimum Intervention Set: covering >= 70% of 10.0 ETH
    mis = investigation_engine.compute_minimum_intervention_set(
        ranked_vasps=[act_a, act_b, act_c],
        total_case_value=total_val,
        target_coverage_threshold=70.0,
    )
    # CoinDCX (4.2) + Binance (3.1) = 7.3 (73%), which satisfies >= 70%
    assert mis["vaspCount"] == 2
    assert mis["achievedCoveragePercentage"] >= 70.0
    assert mis["selectedVasps"][0]["name"] == "CoinDCX"
    assert mis["selectedVasps"][1]["name"] == "Binance"
