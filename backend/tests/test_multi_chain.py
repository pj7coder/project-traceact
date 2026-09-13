import pytest
from backend.services.multi_chain_service import multi_chain_service
from backend.schemas.wallet import BlockchainNetwork


def test_chain_detection_ethereum():
    eth_addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    res = multi_chain_service.detect_chain(eth_addr)
    assert res["detectedChain"] == BlockchainNetwork.ETHEREUM
    assert res["symbol"] == "ETH"
    assert res["validationStatus"] is True


def test_chain_detection_bitcoin():
    # Bech32
    btc_bech32 = "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
    res = multi_chain_service.detect_chain(btc_bech32)
    assert res["detectedChain"] == BlockchainNetwork.BITCOIN
    assert res["symbol"] == "BTC"

    # Legacy
    btc_legacy = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    res2 = multi_chain_service.detect_chain(btc_legacy)
    assert res2["detectedChain"] == BlockchainNetwork.BITCOIN


def test_chain_detection_tron():
    tron_addr = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    res = multi_chain_service.detect_chain(tron_addr)
    assert res["detectedChain"] == BlockchainNetwork.TRON
    assert res["symbol"] == "TRX"


def test_chain_detection_solana():
    sol_addr = "2AQdpHJ2JpcEgPiATUXjQxA8QmaNJZjagGRNAnSpVnPr"
    res = multi_chain_service.detect_chain(sol_addr)
    assert res["detectedChain"] == BlockchainNetwork.SOLANA
    assert res["symbol"] == "SOL"


@pytest.mark.anyio
async def test_bitcoin_sandbox_transactions():
    btc_addr = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    overview, txs = await multi_chain_service.fetch_bitcoin_data(btc_addr)
    assert overview.chain == "bitcoin"
    assert len(txs) > 0
    assert txs[0].asset == "BTC"
