import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.database.mongo import db_manager
from backend.config.settings import settings

logger = logging.getLogger("history_service")


class HistoryService:
    """
    Manages global search records, investigator-specific histories,
    and cross-case node graph correlation.
    """

    @staticmethod
    def _make_key(chain: str, address: str) -> str:
        return f"{chain.lower().strip()}:{address.lower().strip()}"

    async def record_target_search(
        self,
        address: str,
        chain: str = "ethereum",
        investigator_id: Optional[str] = None,
        case_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Records an investigator's search on a target wallet:
        - Increments global search count
        - Adds investigator ID to distinct investigators list
        - Returns historical statistics and generated tag labels
        """
        clean_addr = address.lower().strip()
        chain_clean = chain.lower().strip()
        key = self._make_key(chain_clean, clean_addr)
        inv_id = investigator_id or settings.INVESTIGATOR_ID
        now_iso = datetime.now(timezone.utc).isoformat()

        # Check existing record
        existing = await db_manager.wallets.find_one({"_id": key})
        if not existing:
            doc = {
                "_id": key,
                "address": clean_addr,
                "chain": chain_clean,
                "globalSearchCount": 1,
                "investigators": [inv_id],
                "firstSearchedAt": now_iso,
                "lastSearchedAt": now_iso,
                "appearanceCountInGraphs": 1,
                "associatedCaseIds": [case_id] if case_id else [],
                "tags": [],
            }
            await db_manager.wallets.insert_one(doc)
            return {
                "globalSearchCount": 1,
                "previousSearches": 0,
                "isFirstSearch": True,
                "tags": [],
            }
        else:
            prev_count = existing.get("globalSearchCount", 1)
            new_count = prev_count + 1
            investigators = existing.get("investigators", [])
            if inv_id not in investigators:
                investigators.append(inv_id)

            cases = existing.get("associatedCaseIds", [])
            if case_id and case_id not in cases:
                cases.append(case_id)

            await db_manager.wallets.update_one(
                {"_id": key},
                {
                    "$set": {
                        "globalSearchCount": new_count,
                        "lastSearchedAt": now_iso,
                        "investigators": investigators,
                        "associatedCaseIds": cases,
                    }
                }
            )

            # Generate historical tags
            tags = []
            inv_count = len(investigators) if len(investigators) > 1 else new_count
            if inv_count > 1:
                tags.append(f"Searched by {inv_count} investigators before")
            elif inv_count == 1:
                tags.append("Searched by 1 investigator before")

            curr_apps = existing.get("appearanceCountInGraphs", 0)
            if curr_apps > 1:
                tags.append(f"Appeared in {curr_apps} previous investigations")
            elif curr_apps == 1:
                tags.append("This wallet appeared in your previous investigations")

            if len(cases) > 1:
                tags.append(f"Linked to {len(cases)} active cases")

            return {
                "globalSearchCount": new_count,
                "previousSearches": prev_count,
                "isFirstSearch": False,
                "investigatorCount": len(investigators),
                "tags": tags,
            }

    async def record_graph_nodes_batch(
        self,
        nodes: List[Dict[str, Any]],
        chain: str = "ethereum",
        case_id: Optional[str] = None
    ):
        """
        Indexes all nodes in an investigation graph into the database so that subsequent
        searches recognize any node that previously appeared in past investigations.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        chain_clean = chain.lower().strip()

        for n in nodes:
            addr = n.get("address", "").lower().strip()
            if not addr:
                continue
            key = self._make_key(chain_clean, addr)
            existing = await db_manager.wallets.find_one({"_id": key})

            if not existing:
                doc = {
                    "_id": key,
                    "address": addr,
                    "chain": chain_clean,
                    "globalSearchCount": 0,
                    "investigators": [],
                    "firstSearchedAt": now_iso,
                    "lastSearchedAt": now_iso,
                    "appearanceCountInGraphs": 1,
                    "associatedCaseIds": [case_id] if case_id else [],
                    "entityName": n.get("entityName"),
                    "entityType": n.get("entityType"),
                    "tags": ["Appeared in 1 past case"],
                }
                await db_manager.wallets.insert_one(doc)
            else:
                curr_apps = existing.get("appearanceCountInGraphs", 1) + 1
                cases = existing.get("associatedCaseIds", [])
                if case_id and case_id not in cases:
                    cases.append(case_id)

                await db_manager.wallets.update_one(
                    {"_id": key},
                    {
                        "$set": {
                            "appearanceCountInGraphs": curr_apps,
                            "associatedCaseIds": cases,
                            "lastSeen": now_iso,
                        }
                    }
                )

    async def get_wallet_history(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """Looks up a wallet in the historical repository to retrieve tags and cross-case links."""
        clean_addr = address.lower().strip()
        key = self._make_key(chain, clean_addr)
        record = await db_manager.wallets.find_one({"_id": key})

        if not record:
            return {
                "address": clean_addr,
                "chain": chain,
                "globalSearchCount": 0,
                "appearanceCountInGraphs": 0,
                "tags": [],
                "associatedCaseIds": [],
            }

        searched = record.get("globalSearchCount", 0)
        investigators = record.get("investigators", [])
        appeared = record.get("appearanceCountInGraphs", 0)
        tags = list(record.get("tags", []))

        inv_count = len(investigators) if len(investigators) > 1 else searched
        if inv_count > 1:
            tags.append(f"Searched by {inv_count} investigators before")
        elif inv_count == 1:
            tags.append("Searched by 1 investigator before")

        if appeared > 1:
            tags.append(f"Appeared in {appeared} previous investigations")
        elif appeared == 1:
            tags.append("This wallet appeared in your previous investigations")

        return {
            "address": clean_addr,
            "chain": chain,
            "globalSearchCount": searched,
            "appearanceCountInGraphs": appeared,
            "investigators": investigators,
            "firstSearchedAt": record.get("firstSearchedAt"),
            "lastSearchedAt": record.get("lastSearchedAt"),
            "associatedCaseIds": record.get("associatedCaseIds", []),
            "tags": list(dict.fromkeys(tags)),
        }


history_service = HistoryService()
