import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.database.mongo import db_manager
from backend.config.settings import settings
from backend.services.multi_chain_service import multi_chain_service
from backend.services.wallet_service import wallet_service
from backend.services.email_service import email_service
from backend.services.rule_engine import rule_engine

logger = logging.getLogger("live_tracking_service")


class LiveTrackingService:
    """
    Automated Hourly Monitoring Engine for Suspect Cryptocurrency Wallets.
    Periodically queries on-chain ledgers every 60 minutes (or on demand),
    detects newly broadcast transactions or VASP hops, and pushes notifications/emails.
    """

    def __init__(self):
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._notifications: List[Dict[str, Any]] = []

    def start_scheduler(self):
        """Launches the background 1-hour tracking daemon."""
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._tracking_loop())
            logger.info(f"Live Tracking background scheduler started (Interval: {settings.LIVE_TRACKING_INTERVAL_MINUTES} min).")

    def stop_scheduler(self):
        """Stops the background scheduler."""
        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Live Tracking background scheduler stopped.")

    async def _tracking_loop(self):
        """Periodic background evaluation loop."""
        while self._is_running:
            try:
                await self.check_all_monitored_wallets()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in live tracking execution cycle: {e}")

            # Sleep for configured interval (default 60 minutes = 3600 seconds)
            sleep_secs = max(60, settings.LIVE_TRACKING_INTERVAL_MINUTES * 60)
            await asyncio.sleep(sleep_secs)

    async def toggle_monitoring(
        self,
        address: str,
        chain: str = "ethereum",
        email: Optional[str] = None,
        enabled: bool = True,
        investigator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enables or disables 1-hour live tracking for a target wallet."""
        clean_addr = address.lower().strip()
        chain_clean = chain.lower().strip()
        key = f"{chain_clean}:{clean_addr}"
        now_iso = datetime.now(timezone.utc).isoformat()
        inv_id = investigator_id or settings.INVESTIGATOR_ID

        if not enabled:
            await db_manager.monitored_wallets.update_one(
                {"_id": key},
                {"$set": {"isActive": False, "updatedAt": now_iso}}
            )
            return {"address": clean_addr, "chain": chain_clean, "isMonitored": False}

        # Fetch baseline count
        overview, txs = await self._fetch_wallet_snapshot(clean_addr, chain_clean)
        next_check = datetime.fromtimestamp(time.time() + settings.LIVE_TRACKING_INTERVAL_MINUTES * 60, timezone.utc).isoformat()

        doc = {
            "_id": key,
            "address": clean_addr,
            "chain": chain_clean,
            "investigatorId": inv_id,
            "investigatorEmail": email or settings.ALERT_EMAIL_RECIPIENT,
            "isActive": True,
            "intervalMinutes": settings.LIVE_TRACKING_INTERVAL_MINUTES,
            "lastCheckedAt": now_iso,
            "nextCheckAt": next_check,
            "lastKnownTxCount": len(txs),
            "lastKnownBalance": overview.balance if overview else "0",
            "alertsCount": 0,
            "alerts": [],
            "createdAt": now_iso,
        }

        await db_manager.monitored_wallets.update_one(
            {"_id": key},
            {"$set": doc},
            upsert=True
        )

        return {
            "address": clean_addr,
            "chain": chain_clean,
            "isMonitored": True,
            "intervalMinutes": settings.LIVE_TRACKING_INTERVAL_MINUTES,
            "lastKnownTxCount": len(txs),
            "nextCheckAt": next_check,
        }

    async def check_all_monitored_wallets(self) -> List[Dict[str, Any]]:
        """Executes a monitoring check across all active registered wallets."""
        active_wallets = await db_manager.monitored_wallets.find({"isActive": True})
        results = []
        for w in active_wallets:
            res = await self.check_wallet(w["address"], w.get("chain", "ethereum"))
            results.append(res)
        return results

    async def check_wallet(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Executes on-demand or periodic inspection of a single monitored wallet.
        Compares current on-chain state against stored snapshot and triggers alerts if differences found.
        """
        clean_addr = address.lower().strip()
        chain_clean = chain.lower().strip()
        key = f"{chain_clean}:{clean_addr}"
        now_iso = datetime.now(timezone.utc).isoformat()

        record = await db_manager.monitored_wallets.find_one({"_id": key})
        if not record:
            return {"status": "not_monitored", "address": clean_addr}

        prev_tx_count = record.get("lastKnownTxCount", 0)
        prev_balance = record.get("lastKnownBalance", "0")
        recipient_email = record.get("investigatorEmail")

        # Query live blockchain snapshot
        overview, txs = await self._fetch_wallet_snapshot(clean_addr, chain_clean)
        curr_tx_count = len(txs)
        curr_balance = overview.balance if overview else prev_balance

        alerts_triggered = []

        # Check 1: New transactions detected
        if curr_tx_count > prev_tx_count:
            diff = curr_tx_count - prev_tx_count
            latest_tx = txs[0] if txs else None
            tx_hash = latest_tx.txHash if latest_tx else None
            alert_desc = f"Detected {diff} new on-chain transaction(s) on wallet {clean_addr[:10]}... Latest Tx: {tx_hash or 'N/A'}"

            alert_item = {
                "id": f"alt_{int(time.time()*1000)}",
                "timestamp": now_iso,
                "type": "new_transaction",
                "title": "New On-Chain Activity Detected",
                "description": alert_desc,
                "address": clean_addr,
                "chain": chain_clean,
                "txHash": tx_hash,
            }
            alerts_triggered.append(alert_item)
            self._notifications.insert(0, alert_item)

            # Dispatch email alert if configured
            email_service.send_wallet_activity_alert(
                target_address=clean_addr,
                chain=chain_clean,
                alert_type="New On-Chain Transaction",
                description=alert_desc,
                tx_hash=tx_hash,
                recipient_email=recipient_email,
            )

        # Check 2: Balance fluctuation
        if curr_balance != prev_balance:
            bal_desc = f"Balance changed from {prev_balance} to {curr_balance} on {clean_addr[:10]}..."
            alert_item = {
                "id": f"alt_bal_{int(time.time()*1000)}",
                "timestamp": now_iso,
                "type": "balance_change",
                "title": "Wallet Balance Fluctuation",
                "description": bal_desc,
                "address": clean_addr,
                "chain": chain_clean,
            }
            alerts_triggered.append(alert_item)
            self._notifications.insert(0, alert_item)

        # Update record in database
        next_check = datetime.fromtimestamp(time.time() + settings.LIVE_TRACKING_INTERVAL_MINUTES * 60, timezone.utc).isoformat()
        curr_alerts = record.get("alerts", []) + alerts_triggered

        await db_manager.monitored_wallets.update_one(
            {"_id": key},
            {
                "$set": {
                    "lastCheckedAt": now_iso,
                    "nextCheckAt": next_check,
                    "lastKnownTxCount": curr_tx_count,
                    "lastKnownBalance": curr_balance,
                    "alertsCount": len(curr_alerts),
                    "alerts": curr_alerts[-20:],  # keep last 20
                }
            }
        )

        return {
            "address": clean_addr,
            "chain": chain_clean,
            "checkedAt": now_iso,
            "prevTxCount": prev_tx_count,
            "currentTxCount": curr_tx_count,
            "newTransactions": max(0, curr_tx_count - prev_tx_count),
            "alertsTriggered": len(alerts_triggered),
            "alerts": alerts_triggered,
        }

    async def get_monitored_wallets(self) -> List[Dict[str, Any]]:
        """Returns all tracked wallets and their status."""
        return await db_manager.monitored_wallets.find({"isActive": True})

    def get_notifications(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Returns the in-app notification feed for the UI bell icon."""
        return self._notifications[:limit]

    async def _fetch_wallet_snapshot(self, address: str, chain: str):
        """Internal helper to query current wallet state according to chain."""
        chain_clean = chain.lower().strip()
        if chain_clean == "bitcoin":
            return await multi_chain_service.fetch_bitcoin_data(address)
        elif chain_clean == "tron":
            return await multi_chain_service.fetch_tron_data(address)
        elif chain_clean == "solana":
            return await multi_chain_service.fetch_solana_data(address)
        else:
            overview, txs, _ = await wallet_service.get_wallet_overview_and_data(address, chain_clean)
            return overview, txs


live_tracking_service = LiveTrackingService()
