import json
import base64
from typing import Dict, List, Optional
import bittensor as bt
from bittensor.core.chain_data import decode_account_id
from bittensor.utils.balance import tao
from app.core.config import settings
from app.core.redis import get_redis_client
import os
import asyncio

def encrypt_password_base64(key: str, value: str) -> str:
    """
    Encrypts a password using XOR with a key and returns base64 encoded result
    """
    encrypted_bytes = bytes(ord(value[i]) ^ ord(key[i % len(key)]) for i in range(len(value)))
    return base64.b64encode(encrypted_bytes).decode()

class BittensorService:
    def __init__(self):
        self.subtensor = bt.AsyncSubtensor(network=settings.BITTENSOR_NETWORK)
        self.wallet = bt.wallet(
            name=settings.WALLET_NAME, 
            hotkey=settings.WALLET_HOTKEY,
            path=settings.WALLET_PATH
        )

        pw_env_var_name = self.wallet.coldkey_file.env_var_name()
        enc_pw = encrypt_password_base64(pw_env_var_name, settings.WALLET_COLDKEY_PASSWORD)
        os.environ[pw_env_var_name] = enc_pw
        self.wallet.unlock_coldkey()
        self._request_futures: Dict[str, asyncio.Task] = {}


    async def _get_all_subnets(self):
        redis = get_redis_client()
        cached_subnets = await redis.get("subnets")
        netuids = []
        if cached_subnets:
            netuids = json.loads(cached_subnets)
        else:
            netuids = await self.subtensor.get_subnets()
            await redis.set("subnets", json.dumps(netuids), ex=settings.REDIS_CACHE_EXPIRY)
        return netuids

    async def get_tao_dividends(self, netuid: Optional[int] = None, hotkey: Optional[str] = None) -> Dict:
        """
            Get Tao dividends for a specific netuid and/or hotkey, or all netuids if netuid is None.
        """
        
        redis = get_redis_client()
        try:
            netuids = [netuid] if netuid else await self._get_all_subnets()
            dividends = {}
            cache_hit = False
            cache_miss = False

            for n in netuids:
                cache_key = f"tao_dividends:{n}"
                if hotkey:
                    cached_dividend = await redis.hget(cache_key, hotkey)
                    if cached_dividend:
                        cache_hit = True
                        dividends[str(n)] = {hotkey: int(cached_dividend)}
                    else:
                        cache_miss = True
                        dividends[str(n)] = await self._get_subnet_dividends(n, hotkey)
                        await redis.hset(cache_key, hotkey, dividends[str(n)][hotkey])
                        await redis.hexpire(cache_key, settings.REDIS_CACHE_EXPIRY, hotkey)
                        self._request_futures.pop(f"{netuid}:{hotkey}", None)
                else:
                    cached_dividends = await redis.hgetall(cache_key)
                    if cached_dividends:
                        cache_hit = True
                        dividends[str(n)] = {k: int(v) for k, v in cached_dividends.items()}
                    else:
                        cache_miss = True
                        dividends[str(n)] = await self._get_subnet_dividends(n)
                        await redis.hset(cache_key, mapping=dividends[str(n)])
                        await redis.expire(cache_key, settings.REDIS_CACHE_EXPIRY)
                        self._request_futures.pop(f"{netuid}:{hotkey}", None)
                        

            cache_status = "hit" if (cache_hit and not cache_miss) else \
                          "partial" if (cache_hit and cache_miss) else \
                          "miss"

            return {"dividends": dividends, "cache_status": cache_status}
        except Exception as e:
            raise Exception(f"Error getting Tao dividends: {str(e)}")

    async def _get_subnet_dividends(self, netuid: Optional[int] = None, hotkey: Optional[str] = None) -> Dict:
        """Get dividends for a specific subnet and optional hotkey."""
        
        request_key = f"{netuid}:{hotkey}"
        if request_key in self._request_futures:
            task = self._request_futures[request_key]
        else:
            if hotkey is None:
                task = asyncio.create_task(self._query_map(netuid))
            else:
                task = asyncio.create_task(self.subtensor.substrate.query("SubtensorModule", "TaoDividendsPerSubnet", [netuid, hotkey]))
            self._request_futures[request_key] = task
            
        if hotkey is None:
            return await task
        else:
            return { hotkey: (await task).value }
        
    async def _query_map(self, netuid: int):
        dividends = {}
        result = await self.subtensor.substrate.query_map("SubtensorModule", "TaoDividendsPerSubnet", [netuid])
        async for k, v in result:
            dividends[decode_account_id(k)] = v.value

        return dividends

    async def stake_tao(self, amount: float, netuid: int, hotkey: str) -> Dict:
        """Stake TAO tokens."""
        try:
            result = await self.subtensor.add_stake(
                wallet=self.wallet,
                netuid=netuid,
                hotkey_ss58=hotkey,
                amount=tao(amount)
            )
            return {"result": result}
        except Exception as e:
            raise Exception(f"Error staking TAO: {str(e)}")

    async def unstake_tao(self, amount: float, netuid: int, hotkey: str) -> Dict:
        """Unstake TAO tokens."""
        try:
            result = await self.subtensor.unstake(
                wallet=self.wallet,
                netuid=netuid,
                hotkey_ss58=hotkey,
                amount=tao(amount)
            )
            return {"result": result}
        except Exception as e:
            raise Exception(f"Error unstaking TAO: {str(e)}")

bittensor_service = BittensorService() 