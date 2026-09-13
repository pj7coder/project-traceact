import re
from typing import Tuple, Optional


ETH_ADDRESS_REGEX = re.compile(r"^0x[a-fA-F0-9]{40}$")
BTC_BECH32_REGEX = re.compile(r"^(bc1[a-z0-9]{39,59}|bc1p[a-z0-9]{58})$", re.IGNORECASE)
BTC_BASE58_REGEX = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")
TRON_REGEX = re.compile(r"^T[a-zA-HJ-NP-Z0-9]{33}$")
SOLANA_REGEX = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def is_valid_eth_address(address: str) -> bool:
    """Validates if a given string is a valid Ethereum / EVM address format."""
    if not address or not isinstance(address, str):
        return False
    return bool(ETH_ADDRESS_REGEX.match(address.strip()))


def sanitize_eth_address(address: str) -> str:
    """Strips whitespace and returns standard lowercase Ethereum address."""
    return address.strip().lower() if address else ""


def validate_and_normalize_address(address: str, chain: str = "ethereum") -> Tuple[bool, str, str]:
    """
    Validates address according to specified blockchain network.
    Returns (is_valid, normalized_address, error_message).
    """
    if not address or not isinstance(address, str):
        return False, "", "Wallet address cannot be empty."

    clean = address.strip()
    chain_lower = (chain or "ethereum").lower().strip()

    # 1. Bitcoin validation
    if chain_lower == "bitcoin":
        if BTC_BECH32_REGEX.match(clean) or BTC_BASE58_REGEX.match(clean):
            return True, clean, ""
        return False, "", "Invalid Bitcoin address format. Expected Base58 (1, 3) or Bech32 (bc1)."

    # 2. Tron validation
    elif chain_lower == "tron":
        if TRON_REGEX.match(clean):
            return True, clean, ""
        return False, "", "Invalid Tron address. Must start with 'T' and be 34 characters."

    # 3. Solana validation
    elif chain_lower == "solana":
        if SOLANA_REGEX.match(clean):
            return True, clean, ""
        return False, "", "Invalid Solana public key format (expected 32-44 Base58 characters)."

    # 4. Ethereum / EVM (BNB, Polygon) validation
    else:
        # If user pasted BTC or Tron but left dropdown on Ethereum, auto-accept and normalize
        if BTC_BECH32_REGEX.match(clean) or BTC_BASE58_REGEX.match(clean) or TRON_REGEX.match(clean) or SOLANA_REGEX.match(clean):
            return True, clean, ""

        if not clean.startswith("0x"):
            return False, "", "EVM address must start with '0x'."

        if len(clean) != 42:
            return False, "", f"Invalid address length ({len(clean)} chars). Expected 42 characters including '0x'."

        if not ETH_ADDRESS_REGEX.match(clean):
            return False, "", "Address contains invalid non-hexadecimal characters."

        return True, clean.lower(), ""
