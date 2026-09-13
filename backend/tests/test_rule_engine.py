import pytest
from backend.services.rule_engine import rule_engine
from backend.schemas.wallet import WalletOverview, NormalizedTransaction, TransactionDirection


def test_rule_engine_clean_wallet():
    """Wallet with standard transfers to verified exchange gets low suspicion score."""
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"
    target = "0x1111111111111111111111111111111111111111"

    wallet = WalletOverview(
        address=target,
        chain="ethereum",
        balance="1.5",
        transactionCount=4,
        asset="ETH",
    )
    txs = [
        NormalizedTransaction(
            txHash="0x1",
            chain="ethereum",
            fromAddress=target,
            toAddress=binance_addr,
            value="0.5",
            asset="ETH",
            timestamp="2026-08-01T12:00:00Z",
            blockNumber=100,
            status="confirmed",
            direction=TransactionDirection.OUTGOING,
        )
    ]

    res = rule_engine.evaluate_wallet(wallet, txs)
    assert res["suspicionScore"] < 35
    assert res["riskLevel"] == "LOW"
    assert res["nodeColor"] == "#10b981"


def test_rule_engine_sanction_match():
    """Direct interaction with sanctioned entity triggers Critical Threat."""
    sanctioned_addr = "0x098b716b8aaf21512996dc57eb0615e2383e2f96"  # Ronin / Lazarus
    target = "0x2222222222222222222222222222222222222222"

    wallet = WalletOverview(
        address=target,
        chain="ethereum",
        balance="50.0",
        transactionCount=2,
        asset="ETH",
    )
    txs = [
        NormalizedTransaction(
            txHash="0x2",
            chain="ethereum",
            fromAddress=sanctioned_addr,
            toAddress=target,
            value="25.0",
            asset="ETH",
            timestamp="2026-08-01T12:00:00Z",
            blockNumber=100,
            status="confirmed",
            direction=TransactionDirection.INCOMING,
        )
    ]

    res = rule_engine.evaluate_wallet(wallet, txs)
    assert res["suspicionScore"] >= 90
    assert res["riskLevel"] == "CRITICAL"
    assert res["nodeColor"] == "#ef4444"
    assert any("Sanctioned" in r["title"] for r in res["triggeredRules"])


def test_rule_engine_rapid_movement():
    """Rapid movement / peeling chain typology triggers High Risk rule."""
    target = "0x3333333333333333333333333333333333333333"
    wallet = WalletOverview(address=target, chain="ethereum", balance="0.1", transactionCount=2)
    txs = [
        NormalizedTransaction(
            txHash="0x3a",
            chain="ethereum",
            fromAddress="0x4444444444444444444444444444444444444444",
            toAddress=target,
            value="10.0",
            timestamp="2026-08-01T12:00:00Z",
            direction=TransactionDirection.INCOMING,
        ),
        NormalizedTransaction(
            txHash="0x3b",
            chain="ethereum",
            fromAddress=target,
            toAddress="0x5555555555555555555555555555555555555555",
            value="9.8",
            timestamp="2026-08-01T12:05:00Z",
            direction=TransactionDirection.OUTGOING,
        ),
    ]

    res = rule_engine.evaluate_wallet(wallet, txs)
    assert any("Rapid Movement" in r["title"] for r in res["triggeredRules"])


def test_rule_engine_system_logic_profile_and_multiplier():
    """Investigator can apply strict profile and custom sensitivity multiplier to elevate risk."""
    from backend.schemas.attribution import SystemLogicConfig, SystemLogicProfile

    target = "0x3333333333333333333333333333333333333333"
    wallet = WalletOverview(address=target, chain="ethereum", balance="0.1", transactionCount=2)
    txs = [
        NormalizedTransaction(
            txHash="0x3a",
            chain="ethereum",
            fromAddress="0x4444444444444444444444444444444444444444",
            toAddress=target,
            value="10.0",
            timestamp="2026-08-01T12:00:00Z",
            direction=TransactionDirection.INCOMING,
        ),
        NormalizedTransaction(
            txHash="0x3b",
            chain="ethereum",
            fromAddress=target,
            toAddress="0x5555555555555555555555555555555555555555",
            value="9.8",
            timestamp="2026-08-01T12:05:00Z",
            direction=TransactionDirection.OUTGOING,
        ),
    ]

    # Evaluate with standard baseline
    res_base = rule_engine.evaluate_wallet(wallet, txs)

    # Evaluate with strict profile (1.25x multiplier + strict thresholds)
    strict_logic = SystemLogicConfig(profile=SystemLogicProfile.STRICT, sensitivityMultiplier=1.5)
    res_strict = rule_engine.evaluate_wallet(wallet, txs, system_logic=strict_logic)

    assert res_strict["suspicionScore"] >= res_base["suspicionScore"]
    assert res_strict["systemLogicApplied"]["profile"] == "strict"
    assert res_strict["systemLogicApplied"]["sensitivityMultiplier"] == 1.5


def test_rule_engine_rule_disabling_and_custom_weights():
    """Investigator can disable specific rules and override point weights."""
    from backend.schemas.attribution import SystemLogicConfig

    target = "0x3333333333333333333333333333333333333333"
    wallet = WalletOverview(address=target, chain="ethereum", balance="0.1", transactionCount=2)
    txs = [
        NormalizedTransaction(
            txHash="0x3a",
            chain="ethereum",
            fromAddress="0x4444444444444444444444444444444444444444",
            toAddress=target,
            value="10.0",
            timestamp="2026-08-01T12:00:00Z",
            direction=TransactionDirection.INCOMING,
        ),
        NormalizedTransaction(
            txHash="0x3b",
            chain="ethereum",
            fromAddress=target,
            toAddress="0x5555555555555555555555555555555555555555",
            value="9.8",
            timestamp="2026-08-01T12:05:00Z",
            direction=TransactionDirection.OUTGOING,
        ),
    ]

    # Disable rapid movement rule P5
    disabled_logic = SystemLogicConfig(disabledRuleIds=["RULE_P5_RAPID_MOVEMENT"])
    res_disabled = rule_engine.evaluate_wallet(wallet, txs, system_logic=disabled_logic)

    # Rapid movement should NOT be triggered
    assert not any(r["ruleId"] == "RULE_P5_RAPID_MOVEMENT" for r in res_disabled["triggeredRules"])


def test_rule_engine_bitcoin_thresholds():
    """Bitcoin transactions are calibrated to BTC asset denominations."""
    target = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
    wallet = WalletOverview(address=target, chain="bitcoin", balance="0.01", transactionCount=2, asset="BTC")
    txs = [
        NormalizedTransaction(
            txHash="tx_btc_in",
            chain="bitcoin",
            fromAddress="1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
            toAddress=target,
            value="2.0",  # 2 BTC is significant (threshold is 0.5 BTC)
            asset="BTC",
            timestamp="2026-08-01T12:00:00Z",
            direction=TransactionDirection.INCOMING,
        ),
        NormalizedTransaction(
            txHash="tx_btc_out",
            chain="bitcoin",
            fromAddress=target,
            toAddress="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
            value="1.95",
            asset="BTC",
            timestamp="2026-08-01T12:08:00Z",
            direction=TransactionDirection.OUTGOING,
        ),
    ]

    res = rule_engine.evaluate_wallet(wallet, txs)
    assert any("Rapid Movement" in r["title"] for r in res["triggeredRules"])

