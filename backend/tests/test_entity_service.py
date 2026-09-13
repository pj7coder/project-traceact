import pytest
from backend.services.entity_service import entity_service, EntityService, KnownEntity


def test_known_entities_loaded():
    """Verify that known entities dataset is loaded properly on startup."""
    entities = entity_service.get_all_entities()
    assert len(entities) > 0
    # Check known Binance address
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"
    match = entity_service.get_entity(binance_addr)
    assert match is not None
    assert "Binance" in match.entity_name
    assert match.entity_type in ["centralized_exchange", "exchange"]
    assert match.is_vasp() is True
    assert match.confidence == "HIGH"
    assert match.verified is True
    assert match.source_url != ""


def test_entity_case_insensitivity():
    """Verify that entity lookup handles uppercase and mixed case addresses."""
    mixed_addr = "0x28C6C06298d514DB089934071355E5743Bf21D60"
    match = entity_service.get_entity(mixed_addr)
    assert match is not None
    assert "Binance" in match.entity_name
    assert entity_service.is_known_entity(mixed_addr) is True
    assert entity_service.is_vasp(mixed_addr) is True


def test_unknown_address_returns_none():
    """Verify that random unknown address returns None and is_known_entity is False."""
    unknown = "0x000000000000000000000000000000000000dEaD"
    assert entity_service.get_entity(unknown) is None
    assert entity_service.is_known_entity(unknown) is False
    assert entity_service.is_vasp(unknown) is False
    assert entity_service.get_entity("") is None


def test_vasp_directory_loaded():
    """Verify that the Verified VASP Directory is loaded with 25 records and compliance metadata."""
    vasps = entity_service.get_all_vasps()
    assert len(vasps) >= 20

    # Check CoinDCX
    coindcx = entity_service.get_vasp("VASP-IN-COINDCX")
    assert coindcx is not None
    assert "CoinDCX" in coindcx.name
    assert coindcx.country == "India"
    assert coindcx.verification_status == "OFFICIAL_SOURCE"
    assert "nodalofficer" in coindcx.compliance_contact

    # Check Binance via address
    binance_vasp = entity_service.get_vasp_by_address("0x28c6c06298d514db089934071355e5743bf21d60")
    assert binance_vasp is not None
    assert "Binance" in binance_vasp.name

