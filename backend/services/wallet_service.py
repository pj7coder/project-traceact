from datetime import datetime, timezone
import logging
from decimal import Decimal
from typing import List, Dict, Tuple, Any, Optional

from backend.schemas.wallet import (
    NormalizedTransaction,
    ConnectedWallet,
    ConnectedWalletDirection,
    TransactionDirection,
    WalletOverview,
)
from backend.config.settings import settings
from backend.database.mongo import db_manager
from backend.services.blockchain_service import blockchain_service
from backend.services.transaction_normalizer import transaction_normalizer
from backend.services.multi_chain_service import multi_chain_service
from backend.services.history_service import history_service
from backend.services.rule_engine import rule_engine

logger = logging.getLogger("wallet_service")


class WalletService:
    """
    Coordinates wallet balance discovery, multi-chain transaction normalization,
    counterparty connection analysis, history tracking, and risk evaluation.
    """

    @staticmethod
    def _wei_to_eth_str(wei_val: int | str | Decimal) -> str:
        try:
            val = Decimal(str(wei_val))
            if val == Decimal("0"):
                return "0"
            eth = val / Decimal("1000000000000000000")
            formatted = f"{eth:.18f}".rstrip("0").rstrip(".")
            return formatted if formatted else "0"
        except Exception:
            return "0"

    def compute_counterparties(
        self, target_address: str, transactions: List[NormalizedTransaction]
    ) -> List[ConnectedWallet]:
        """Convenience method returning just connected counterparties."""
        wallets, _, _ = self.analyze_connected_wallets(target_address, transactions)
        return wallets

    def analyze_connected_wallets(
        self, target_address: str, transactions: List[NormalizedTransaction]
    ) -> Tuple[List[ConnectedWallet], int, int]:
        """
        Extracts and aggregates unique directly connected counterparties from transaction history.
        Returns (connected_wallets_list, incoming_tx_count, outgoing_tx_count).
        """
        target_clean = target_address.strip().lower()
        connected_map: Dict[str, Dict[str, Any]] = {}

        incoming_tx_count = 0
        outgoing_tx_count = 0

        for tx in transactions:
            from_addr = tx.fromAddress.lower() if tx.fromAddress else ""
            to_addr = tx.toAddress.lower() if tx.toAddress else ""

            is_incoming = (to_addr == target_clean and from_addr != target_clean)
            is_outgoing = (from_addr == target_clean and to_addr != target_clean and bool(to_addr))
            is_self = (from_addr == target_clean and to_addr == target_clean)

            if is_incoming:
                incoming_tx_count += 1
                counterparty = from_addr
            elif is_outgoing:
                outgoing_tx_count += 1
                counterparty = to_addr
            elif is_self:
                outgoing_tx_count += 1
                counterparty = target_clean
            else:
                if from_addr == target_clean and to_addr:
                    counterparty = to_addr
                    outgoing_tx_count += 1
                elif to_addr == target_clean and from_addr:
                    counterparty = from_addr
                    incoming_tx_count += 1
                else:
                    continue

            if not counterparty or counterparty == target_clean:
                continue

            if counterparty not in connected_map:
                connected_map[counterparty] = {
                    "address": counterparty,
                    "txCount": 0,
                    "incomingCount": 0,
                    "outgoingCount": 0,
                    "totalWei": Decimal("0"),
                    "sentToTargetWei": Decimal("0"),
                    "receivedFromTargetWei": Decimal("0"),
                    "timestamps": [],
                    "asset": tx.asset,
                }

            entry = connected_map[counterparty]
            entry["txCount"] += 1
            entry["timestamps"].append(tx.timestamp)

            try:
                tx_val_wei = Decimal(str(tx.valueRaw)) if tx.valueRaw else Decimal(str(tx.value))
            except Exception:
                tx_val_wei = Decimal("0")

            entry["totalWei"] += tx_val_wei

            if is_incoming:
                entry["incomingCount"] += 1
                entry["sentToTargetWei"] += tx_val_wei
            elif is_outgoing:
                entry["outgoingCount"] += 1
                entry["receivedFromTargetWei"] += tx_val_wei

        connected_wallets: List[ConnectedWallet] = []

        for addr, data in connected_map.items():
            if data["incomingCount"] > 0 and data["outgoingCount"] > 0:
                direction = ConnectedWalletDirection.BIDIRECTIONAL
            elif data["incomingCount"] > 0:
                direction = ConnectedWalletDirection.INCOMING
            else:
                direction = ConnectedWalletDirection.OUTGOING

            timestamps = sorted(data["timestamps"])
            first_ts = timestamps[0] if timestamps else None
            last_ts = timestamps[-1] if timestamps else None

            # Display value
            if data.get("asset") in ("BTC", "TRX", "SOL", "USDT"):
                total_disp = f"{data['totalWei'] / Decimal('100000000' if data['asset'] == 'BTC' else '1000000'):.4f}".rstrip("0").rstrip(".") if data['totalWei'] > 100000 else str(data['totalWei'])
            else:
                total_disp = self._wei_to_eth_str(data["totalWei"])

            connected_wallets.append(
                ConnectedWallet(
                    address=addr,
                    direction=direction,
                    transactionCount=data["txCount"],
                    totalAmount=total_disp or "0",
                    totalAmountRaw=str(data["totalWei"]),
                    asset=data.get("asset", "ETH"),
                    incomingTxCount=data["incomingCount"],
                    outgoingTxCount=data["outgoingCount"],
                    totalSentToInvestigated=self._wei_to_eth_str(data["sentToTargetWei"]),
                    totalReceivedFromInvestigated=self._wei_to_eth_str(data["receivedFromTargetWei"]),
                    firstInteractionTimestamp=first_ts,
                    lastInteractionTimestamp=last_ts,
                )
            )

        connected_wallets.sort(key=lambda w: w.transactionCount, reverse=True)
        return connected_wallets, incoming_tx_count, outgoing_tx_count

    async def get_wallet_overview_and_data(
        self, target_address: str, chain: str = "ethereum"
    ) -> Tuple[WalletOverview, List[NormalizedTransaction], List[ConnectedWallet]]:
        """
        Fetches multi-chain ledger data, evaluates risk, logs search history, and compiles overview.
        """
        chain_clean = chain.lower().strip()
        is_multi_chain = chain_clean in ("tron", "bitcoin", "solana")
        target_clean = target_address.strip() if is_multi_chain else target_address.strip().lower()

        # Multi-chain dispatch
        if chain_clean == "bitcoin":
            overview, txs = await multi_chain_service.fetch_bitcoin_data(target_clean)
            connected_wallets = self.compute_counterparties(target_clean, txs)
        elif chain_clean == "tron":
            overview, txs = await multi_chain_service.fetch_tron_data(target_clean)
            connected_wallets = self.compute_counterparties(target_clean, txs)
        elif chain_clean == "solana":
            overview, txs = await multi_chain_service.fetch_solana_data(target_clean)
            connected_wallets = self.compute_counterparties(target_clean, txs)
        else:
            # Ethereum / EVM
            balance_eth, balance_wei = await blockchain_service.get_balance(target_clean)
            raw_txs = await blockchain_service.get_transactions(target_clean, limit=settings.MAX_TRANSACTIONS_FETCH)
            txs = transaction_normalizer.normalize_batch(raw_txs, target_clean, chain_clean)
            connected_wallets, in_count, out_count = self.analyze_connected_wallets(target_clean, txs)

            overview = WalletOverview(
                address=target_clean,
                chain=chain_clean,
                balance=balance_eth,
                balanceRaw=balance_wei,
                asset="ETH",
                transactionCount=len(txs),
                incomingCount=in_count,
                outgoingCount=out_count,
                uniqueConnectedWallets=len(connected_wallets),
                firstSeen=txs[-1].timestamp if txs else None,
                lastSeen=txs[0].timestamp if txs else None,
            )

        # 1. Record search in History Service (Global counter & distinct investigators)
        hist_res = await history_service.record_target_search(
            address=target_clean,
            chain=chain_clean,
        )
        overview.globalSearchCount = hist_res.get("globalSearchCount", 1)

        # 2. Run Prioritized Forensic Rule Engine
        risk_res = rule_engine.evaluate_wallet(overview, txs, connected_wallets)
        overview.riskScore = risk_res["suspicionScore"]
        overview.riskLevel = risk_res["riskLevel"]

        # 3. Compile tags (Historical + Risk tags)
        tags = list(hist_res.get("tags", []))
        tags.append(risk_res["tagLabel"])
        overview.tags = list(set(tags))

        # 4. Save full wallet data to MongoDB
        await self.save_wallet_data_to_db(overview, txs, connected_wallets)

        return overview, txs, connected_wallets

    async def save_wallet_data_to_db(
        self,
        overview: WalletOverview,
        txs: List[NormalizedTransaction],
        connected_wallets: List[ConnectedWallet],
        attribution: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Persists full wallet forensic data into MongoDB:
        - Address, network, balances, transaction counts
        - Evaluated risk score, severity, and tags
        - Normalized transactions (recent 50)
        - Connected counterparty wallets
        - Attributed VASP data if provided
        """
        chain_clean = overview.chain.lower().strip()
        addr_clean = overview.address.lower().strip()
        key = f"{chain_clean}:{addr_clean}"
        now_iso = datetime.now(timezone.utc).isoformat()

        serialized_txs = []
        for t in txs[:50]:
            try:
                serialized_txs.append(t.model_dump() if hasattr(t, "model_dump") else dict(t))
            except Exception:
                pass

        serialized_counterparties = []
        for c in connected_wallets[:50]:
            try:
                serialized_counterparties.append(c.model_dump() if hasattr(c, "model_dump") else dict(c))
            except Exception:
                pass

        doc_update = {
            "address": addr_clean,
            "chain": chain_clean,
            "balance": overview.balance,
            "balanceRaw": overview.balanceRaw,
            "asset": overview.asset,
            "transactionCount": overview.transactionCount,
            "incomingCount": overview.incomingCount,
            "outgoingCount": overview.outgoingCount,
            "uniqueConnectedWallets": overview.uniqueConnectedWallets,
            "riskScore": overview.riskScore or 0,
            "riskLevel": overview.riskLevel or "LOW",
            "tags": list(overview.tags or []),
            "firstSeen": overview.firstSeen,
            "lastSeen": overview.lastSeen,
            "globalSearchCount": overview.globalSearchCount or 1,
            "transactions": serialized_txs,
            "connectedWallets": serialized_counterparties,
            "lastAnalyzedAt": now_iso,
        }

        if attribution:
            doc_update["attribution"] = attribution

        try:
            await db_manager.wallets.update_one(
                {"_id": key},
                {
                    "$set": doc_update,
                    "$setOnInsert": {
                        "_id": key,
                        "createdAt": now_iso,
                        "investigators": [settings.INVESTIGATOR_ID],
                        "associatedCaseIds": [],
                    },
                },
                upsert=True,
            )
            logger.info(f"Successfully saved wallet data for {key} in MongoDB.")
        except Exception as e:
            logger.error(f"Failed to persist wallet data for {key} in MongoDB: {e}")

        return doc_update


wallet_service = WalletService()
