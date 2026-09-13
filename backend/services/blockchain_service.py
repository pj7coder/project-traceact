import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import httpx

from backend.config.settings import settings

logger = logging.getLogger("blockchain_service")


class BlockchainProviderError(Exception):
    """Base exception for blockchain provider errors."""
    pass


class RateLimitError(BlockchainProviderError):
    """Raised when API rate limit is exceeded."""
    pass


class NetworkConnectionError(BlockchainProviderError):
    """Raised when network connectivity fails."""
    pass


class BaseBlockchainProvider(ABC):
    """Abstract interface for blockchain providers."""

    @abstractmethod
    async def get_balance(self, address: str) -> Tuple[str, str]:
        """Returns (balance_in_eth, balance_in_wei)."""
        pass

    @abstractmethod
    async def get_transactions(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns raw list of transactions for an address."""
        pass


class EthereumBlockchainService(BaseBlockchainProvider):
    """
    Production-grade Ethereum blockchain intelligence service.
    Supports Blockscout v2 REST API, Etherscan API, and Ethereum JSON-RPC with automatic fallback
    and in-memory TTL caching to protect against rate limits and duplicate queries across graph branches.
    """

    def __init__(self, cache_ttl_seconds: float = 300.0):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }
        self.timeout = settings.API_TIMEOUT_SECONDS
        self._cache_ttl = cache_ttl_seconds
        
        # In-memory caches: address -> (timestamp, data)
        self._balance_cache: Dict[str, Tuple[float, Tuple[str, str]]] = {}
        self._tx_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}

    def clear_cache(self):
        """Clears all in-memory caches."""
        self._balance_cache.clear()
        self._tx_cache.clear()

    @staticmethod
    def wei_to_eth(wei_val: int | str | Decimal) -> str:
        """Converts Wei to ETH with exact decimal precision without arbitrary rounding to zero."""
        try:
            val = Decimal(str(wei_val))
            if val == Decimal("0"):
                return "0"
            eth = val / Decimal("1000000000000000000")  # 10^18
            formatted = f"{eth:.18f}".rstrip("0").rstrip(".")
            return formatted if formatted else "0"
        except Exception:
            return "0"

    async def get_balance(self, address: str) -> Tuple[str, str]:
        """
        Fetches the ETH balance for the given address with cache lookup.
        Tries Blockscout v2 first, then JSON-RPC fallback.
        """
        addr_clean = address.lower().strip()
        now = time.time()

        # Check in-memory cache
        if addr_clean in self._balance_cache:
            ts, cached_val = self._balance_cache[addr_clean]
            if now - ts < self._cache_ttl:
                return cached_val

        # 1. Try Blockscout v2
        try:
            url = f"{settings.BLOCKSCOUT_BASE_URL}/addresses/{addr_clean}"
            async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_balance = data.get("coin_balance")
                    if raw_balance is not None:
                        balance_wei = str(raw_balance)
                        balance_eth = self.wei_to_eth(balance_wei)
                        result = (balance_eth, balance_wei)
                        self._balance_cache[addr_clean] = (now, result)
                        return result
        except Exception as e:
            logger.warning(f"Blockscout balance fetch failed for {addr_clean}: {e}. Falling back to JSON-RPC.")

        # 2. Try JSON-RPC fallback
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [addr_clean, "latest"],
                "id": 1
            }
            async with httpx.AsyncClient(headers={"Content-Type": "application/json"}, timeout=self.timeout) as client:
                rpc_resp = await client.post(settings.ETHEREUM_RPC_URL, json=payload)
                if rpc_resp.status_code == 200:
                    rpc_data = rpc_resp.json()
                    hex_val = rpc_data.get("result")
                    if hex_val:
                        wei_int = int(hex_val, 16)
                        balance_wei = str(wei_int)
                        balance_eth = self.wei_to_eth(balance_wei)
                        result = (balance_eth, balance_wei)
                        self._balance_cache[addr_clean] = (now, result)
                        return result
        except Exception as e:
            logger.error(f"JSON-RPC balance fetch failed for {addr_clean}: {e}")

        # Default if unreachable
        return "0", "0"

    async def get_transactions(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetches transactions for the given address with cache lookup,
        rate-limit detection, and fallback retry.
        """
        addr_clean = address.lower().strip()
        now = time.time()

        # Check in-memory cache
        cache_key = f"{addr_clean}_{limit}"
        if cache_key in self._tx_cache:
            ts, cached_txs = self._tx_cache[cache_key]
            if now - ts < self._cache_ttl:
                return cached_txs

        # If user configured Etherscan API key and explicitly wants Etherscan
        if settings.ETHERSCAN_API_KEY:
            try:
                etherscan_txs = await self._fetch_from_etherscan(addr_clean, limit)
                if etherscan_txs:
                    self._tx_cache[cache_key] = (now, etherscan_txs)
                    return etherscan_txs
            except Exception as e:
                logger.warning(f"Etherscan fetch failed: {e}. Falling back to Blockscout.")

        # Primary provider: Blockscout v2 with rate limit backoff
        for attempt in range(2):
            try:
                url = f"{settings.BLOCKSCOUT_BASE_URL}/addresses/{addr_clean}/transactions"
                async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
                    resp = await client.get(url)
                    
                    if resp.status_code == 429:
                        if attempt == 0:
                            logger.warning(f"Rate limited on {addr_clean}. Waiting 1s before retry...")
                            await asyncio.sleep(1.0)
                            continue
                        raise RateLimitError("Blockchain API rate limit exceeded. Please try again in a few seconds.")
                    
                    if resp.status_code != 200:
                        raise BlockchainProviderError(f"Blockchain provider returned HTTP {resp.status_code}: {resp.text}")

                    data = resp.json()
                    items = data.get("items", [])
                    result = items[:limit]
                    self._tx_cache[cache_key] = (now, result)
                    return result

            except httpx.RequestError as e:
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                logger.error(f"Network error querying blockchain provider: {e}")
                raise NetworkConnectionError(f"Failed to connect to Ethereum provider: {str(e)}")
            except BlockchainProviderError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching transactions for {addr_clean}: {e}")
                raise BlockchainProviderError(f"Error fetching blockchain data: {str(e)}")

        return []

    async def get_transactions_batch(
        self, addresses: List[str], limit: int = 25, max_concurrency: int = 4
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Concurrently fetches transactions for multiple addresses using an asyncio.Semaphore.
        Prevents rate-limit flooding while executing level-by-level BFS safely and reliably.
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results: Dict[str, List[Dict[str, Any]]] = {}

        async def _fetch_single(addr: str):
            async with semaphore:
                try:
                    txs = await self.get_transactions(addr, limit=limit)
                    return addr, txs
                except RateLimitError as rle:
                    logger.warning(f"Rate limited for batch target {addr}: {rle}. Proceeding with cached/empty set.")
                    cache_key = f"{addr.lower().strip()}_{limit}"
                    if cache_key in self._tx_cache:
                        return addr, self._tx_cache[cache_key][1]
                    return addr, []
                except Exception as ex:
                    logger.warning(f"Batch fetch error for {addr}: {ex}")
                    return addr, []

        tasks = [_fetch_single(a) for a in addresses]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        for item in batch_results:
            if isinstance(item, tuple) and len(item) == 2:
                addr, tx_list = item
                results[addr] = tx_list

        return results

    async def _fetch_from_etherscan(self, address: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Optional Etherscan API provider endpoint (Supports V1 & V2 with chainid=1)."""
        chain_param = "&chainid=1" if "v2" in settings.ETHERSCAN_BASE_URL.lower() else ""
        url = (
            f"{settings.ETHERSCAN_BASE_URL}?module=account&action=txlist{chain_param}"
            f"&address={address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc"
            f"&apikey={settings.ETHERSCAN_API_KEY}"
        )
        async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1" and "result" in data:
                    return data["result"]
        return []


blockchain_service = EthereumBlockchainService()

