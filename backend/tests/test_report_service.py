import pytest
from backend.services.report_service import report_service


@pytest.mark.anyio
async def test_report_generation_and_sahyog_notice():
    """Report generation creates formal Section 91 notice and SHA-256 integrity hash."""
    binance_addr = "0x28c6c06298d514db089934071355e5743bf21d60"
    report = await report_service.generate_report(
        target_address=binance_addr,
        chain="ethereum",
        case_id="CASE-2026-I4C-TEST",
        investigator_id="LEA-TEST-001",
        max_depth=2,
    )

    assert report.reportId.startswith("REP-")
    assert report.caseId == "CASE-2026-I4C-TEST"
    assert "SECTION 91 OF THE CODE OF CRIMINAL PROCEDURE" in report.sahyogNoticeDraft
    assert len(report.sha256Checksum) == 64
    assert report.infographics.riskScoreGauge["max"] == 100
