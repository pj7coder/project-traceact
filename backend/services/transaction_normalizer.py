import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional

from backend.schemas.wallet import NormalizedTransaction, TransactionDirection

logger = logging.getLogger("transaction_normalizer")


class TransactionNormalizer:
    """
    Normalizes provider-specific transaction payloads (Blockscout, Etherscan, RPC)
    into a standardized, canonical transaction model for multi-chain support.
    """

    @staticmethod
    def wei_to_eth_str(wei_val: Any) -> str:
        """Converts Wei string/int to ETH formatted string without arbitrary zero truncation."""
        if wei_val is None:
            return "0"
        try:
            val = Decimal(str(wei_val))
            if val == Decimal("0"):
                return "0"
            eth = val / Decimal("1000000000000000000")
            formatted = f"{eth:.18f}".rstrip("0").rstrip(".")
            return formatted if formatted else "0"
        except Exception:
            return "0"

    @classmethod
    def normalize_transaction(
        cls, raw_tx: Dict[str, Any], target_address: str, chain: str = "ethereum"
    ) -> Optional[NormalizedTransaction]:
        """
        Normalizes a single raw transaction object.
        Detects whether it comes from Blockscout v2 or Etherscan standard API.
        """
        try:
            target_clean = target_address.strip().lower()

            # Check if Blockscout v2 format
            if "from" in raw_tx and isinstance(raw_tx["from"], dict):
                return cls._normalize_blockscout_tx(raw_tx, target_clean, chain)
            
            # Check if Etherscan format
            if "timeStamp" in raw_tx or ("from" in raw_tx and isinstance(raw_tx["from"], str)):
                return cls._normalize_etherscan_tx(raw_tx, target_clean, chain)

            # Generic fallback
            return cls._normalize_generic_tx(raw_tx, target_clean, chain)

        except Exception as e:
            logger.error(f"Error normalizing transaction {raw_tx.get('hash') or raw_tx}: {e}")
            return None

    @classmethod
    def _normalize_blockscout_tx(
        cls, tx: Dict[str, Any], target_address: str, chain: str
    ) -> NormalizedTransaction:
        tx_hash = tx.get("hash", "")
        
        from_obj = tx.get("from") or {}
        from_addr = from_obj.get("hash", "").lower() if isinstance(from_obj, dict) else str(from_obj).lower()

        to_obj = tx.get("to")
        to_addr = None
        if to_obj and isinstance(to_obj, dict):
            to_addr = to_obj.get("hash", "").lower()
        elif to_obj and isinstance(to_obj, str):
            to_addr = to_obj.lower()

        value_wei = str(tx.get("value", "0"))
        value_eth = cls.wei_to_eth_str(value_wei)

        raw_timestamp = tx.get("timestamp", "")
        # Normalize ISO timestamp or unix
        timestamp_str = str(raw_timestamp)
        if not timestamp_str and tx.get("block_timestamp"):
            timestamp_str = str(tx.get("block_timestamp"))

        block_number = int(tx.get("block_number", 0) or 0)
        
        raw_status = tx.get("status", "ok")
        status = "ok" if str(raw_status).lower() in ["ok", "1", "success"] else "error"

        gas_used = str(tx.get("gas_used", "0") or "0")
        
        fee_obj = tx.get("fee")
        fee_wei = "0"
        if isinstance(fee_obj, dict):
            fee_wei = str(fee_obj.get("value", "0") or "0")
        elif fee_obj is not None:
            fee_wei = str(fee_obj)
        fee_eth = cls.wei_to_eth_str(fee_wei)

        # Determine direction relative to target_address
        if from_addr == target_address and to_addr == target_address:
            direction = TransactionDirection.SELF
        elif from_addr == target_address:
            direction = TransactionDirection.OUTGOING
        else:
            direction = TransactionDirection.INCOMING

        return NormalizedTransaction(
            txHash=tx_hash,
            chain=chain,
            fromAddress=from_addr,
            toAddress=to_addr,
            value=value_eth,
            valueWei=value_wei,
            asset="ETH",
            timestamp=timestamp_str,
            blockNumber=block_number,
            status=status,
            direction=direction,
            gasUsed=gas_used,
            fee=fee_eth,
            feeWei=fee_wei,
        )

    @classmethod
    def _normalize_etherscan_tx(
        cls, tx: Dict[str, Any], target_address: str, chain: str
    ) -> NormalizedTransaction:
        tx_hash = tx.get("hash", "")
        from_addr = str(tx.get("from", "")).lower()
        to_addr = str(tx.get("to", "")).lower() if tx.get("to") else None

        value_wei = str(tx.get("value", "0"))
        value_eth = cls.wei_to_eth_str(value_wei)

        # Etherscan timestamps are UNIX epoch seconds
        raw_ts = tx.get("timeStamp")
        if raw_ts:
            try:
                dt = datetime.fromtimestamp(int(raw_ts), tz=timezone.utc)
                timestamp_str = dt.isoformat()
            except Exception:
                timestamp_str = str(raw_ts)
        else:
            timestamp_str = datetime.now(timezone.utc).isoformat()

        block_number = int(tx.get("blockNumber", 0) or 0)
        
        is_error = tx.get("isError", "0")
        receipt_status = tx.get("txreceipt_status", "1")
        status = "ok" if is_error == "0" and receipt_status == "1" else "error"

        gas_used = str(tx.get("gasUsed", "0"))
        gas_price = str(tx.get("gasPrice", "0"))
        try:
            fee_wei = str(int(gas_used) * int(gas_price))
        except Exception:
            fee_wei = "0"
        fee_eth = cls.wei_to_eth_str(fee_wei)

        if from_addr == target_address and to_addr == target_address:
            direction = TransactionDirection.SELF
        elif from_addr == target_address:
            direction = TransactionDirection.OUTGOING
        else:
            direction = TransactionDirection.INCOMING

        return NormalizedTransaction(
            txHash=tx_hash,
            chain=chain,
            fromAddress=from_addr,
            toAddress=to_addr,
            value=value_eth,
            valueWei=value_wei,
            asset="ETH",
            timestamp=timestamp_str,
            blockNumber=block_number,
            status=status,
            direction=direction,
            gasUsed=gas_used,
            fee=fee_eth,
            feeWei=fee_wei,
        )

    @classmethod
    def _normalize_generic_tx(
        cls, tx: Dict[str, Any], target_address: str, chain: str
    ) -> NormalizedTransaction:
        tx_hash = tx.get("hash") or tx.get("txHash") or ""
        from_addr = str(tx.get("from") or tx.get("fromAddress") or "").lower()
        to_addr = str(tx.get("to") or tx.get("toAddress") or "").lower() if (tx.get("to") or tx.get("toAddress")) else None

        value_wei = str(tx.get("valueWei") or tx.get("value") or "0")
        value_eth = cls.wei_to_eth_str(value_wei) if not tx.get("valueEth") else str(tx.get("valueEth"))

        timestamp_str = str(tx.get("timestamp") or datetime.now(timezone.utc).isoformat())
        block_number = int(tx.get("blockNumber") or tx.get("block_number") or 0)
        status = str(tx.get("status", "ok"))

        if from_addr == target_address and to_addr == target_address:
            direction = TransactionDirection.SELF
        elif from_addr == target_address:
            direction = TransactionDirection.OUTGOING
        else:
            direction = TransactionDirection.INCOMING

        return NormalizedTransaction(
            txHash=tx_hash,
            chain=chain,
            fromAddress=from_addr,
            toAddress=to_addr,
            value=value_eth,
            valueWei=value_wei,
            asset="ETH",
            timestamp=timestamp_str,
            blockNumber=block_number,
            status=status,
            direction=direction,
            gasUsed=str(tx.get("gasUsed", "0")),
            fee=cls.wei_to_eth_str(tx.get("fee", "0")),
            feeWei=str(tx.get("fee", "0")),
        )

    @classmethod
    def normalize_batch(
        cls, raw_txs: List[Dict[str, Any]], target_address: str, chain: str = "ethereum"
    ) -> List[NormalizedTransaction]:
        """Normalizes a list of transactions, ignoring any that fail to parse."""
        normalized = []
        for raw in raw_txs:
            norm = cls.normalize_transaction(raw, target_address, chain)
            if norm:
                normalized.append(norm)
        return normalized


transaction_normalizer = TransactionNormalizer()
