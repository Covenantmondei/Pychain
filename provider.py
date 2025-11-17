from typing import Optional, List, Dict, Any, Union
from enum import Enum
import os
from web3 import Web3
from web3.providers import HTTPProvider, WebsocketProvider
from web3.middleware import geth_poa_middleware
import logging

logger = logging.getLogger(__name__)


class Chain(Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"
    AVALANCHE = "avalanche"
    BASE = "base"
    LOCAL = "local"


class ProviderType(Enum):
    """Provider connection types"""
    HTTP = "http"
    WEBSOCKET = "ws"


class Provider:
    """
    Blockchain provider with multi-chain support and automatic failover.
    
    Examples:
        # From environment variable
        provider = Provider.from_env()
        
        # Infura
        provider = Provider.infura(api_key="YOUR_KEY", chain=Chain.ETHEREUM)
        
        # Alchemy
        provider = Provider.alchemy(api_key="YOUR_KEY", chain=Chain.POLYGON)
        
        # Custom RPC
        provider = Provider("https://rpc.ankr.com/eth")
        
        # Multiple endpoints with failover
        provider = Provider([
            "https://eth-mainnet.g.alchemy.com/v2/KEY1",
            "https://mainnet.infura.io/v3/KEY2"
        ])
    """
    
    # Default RPC endpoints
    DEFAULT_RPCS = {
        Chain.ETHEREUM: "https://ethereum-rpc.publicnode.com",
        Chain.POLYGON: "https://polygon-bor-rpc.publicnode.com",
        Chain.ARBITRUM: "https://arbitrum-one-rpc.publicnode.com",
        Chain.OPTIMISM: "https://optimism-rpc.publicnode.com",
        Chain.BSC: "https://bsc-rpc.publicnode.com",
        Chain.AVALANCHE: "https://avalanche-c-chain-rpc.publicnode.com",
        Chain.BASE: "https://base-rpc.publicnode.com",
        Chain.LOCAL: "http://127.0.0.1:8545",
    }
    
    def __init__(
        self,
        rpc_url: Union[str, List[str]],
        provider_type: ProviderType = ProviderType.HTTP,
        timeout: int = 30,
        retry_count: int = 3,
        chain: Optional[Chain] = None,
    ):
        self.rpc_urls = [rpc_url] if isinstance(rpc_url, str) else rpc_url
        self.provider_type = provider_type
        self.timeout = timeout
        self.retry_count = retry_count
        self.chain = chain
        self._current_provider_index = 0
        self._w3: Optional[Web3] = None
        
        self.connect()
    
    def connect(self):
        """Establish connection to RPC endpoint"""
        rpc_url = self.rpc_urls[self._current_provider_index]
        
        try:
            if self.provider_type == ProviderType.HTTP:
                provider = HTTPProvider(
                    rpc_url,
                    request_kwargs={"timeout": self.timeout}
                )
            else:
                provider = WebsocketProvider(
                    rpc_url,
                    websocket_timeout=self.timeout
                )
            
            self._w3 = Web3(provider)
            
            # Add PoA middleware for chains that need it
            if self.chain in [Chain.POLYGON, Chain.BSC]:
                self._w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Test connection
            if not self._w3.isconnected():
                raise ConnectionError(f"Failed to connect to {rpc_url}")
            
            logger.info(f"Connected to {rpc_url}")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.failover()
    
    def failover(self):
        """Switch to next RPC endpoint"""
        if self._current_provider_index < len(self.rpc_urls) - 1:
            self._current_provider_index += 1
            logger.warning(f"Switching to fallback provider {self._current_provider_index + 1}")
            self.connect()
        else:
            raise ConnectionError("All RPC endpoints failed")
    
    @property
    def w3(self) -> Web3:
        """Get Web3 instance"""
        if not self._w3 or not self._w3.isconnected():
            self.connect()
        return self._w3
    
    @classmethod
    def from_env(cls, var_name: str = "RPC_URL") -> "Provider":

        rpc_url = os.getenv(var_name)
        if not rpc_url:
            raise ValueError(f"Environment variable {var_name} not set")
        return cls(rpc_url)
    
    @classmethod
    def infura(cls, api_key: str, chain: Chain = Chain.ETHEREUM) -> "Provider":
        """Create Infura provider"""
        network_map = {
            Chain.ETHEREUM: "mainnet",
            Chain.POLYGON: "polygon-mainnet",
            Chain.ARBITRUM: "arbitrum-mainnet",
            Chain.OPTIMISM: "optimism-mainnet",
        }
        network = network_map.get(chain, "mainnet")
        rpc_url = f"https://{network}.infura.io/v3/{api_key}"
        return cls(rpc_url, chain=chain)
    
    @classmethod
    def alchemy(cls, api_key: str, chain: Chain = Chain.ETHEREUM) -> "Provider":
        """Create Alchemy provider"""
        network_map = {
            Chain.ETHEREUM: "eth-mainnet",
            Chain.POLYGON: "polygon-mainnet",
            Chain.ARBITRUM: "arb-mainnet",
            Chain.OPTIMISM: "opt-mainnet",
        }
        network = network_map.get(chain, "eth-mainnet")
        rpc_url = f"https://{network}.g.alchemy.com/v2/{api_key}"
        return cls(rpc_url, chain=chain)
    
    @classmethod
    def quicknode(cls, endpoint: str) -> "Provider":
        """Create QuickNode provider"""
        return cls(endpoint)
    
    @classmethod
    def local(cls, port: int = 8545) -> "Provider":
        """Create local node provider (Hardhat/Ganache)"""
        return cls(f"http://127.0.0.1:{port}", chain=Chain.LOCAL)
    
    @classmethod
    def auto(cls, chain: Chain = Chain.ETHEREUM) -> "Provider":
        """
        Auto-select provider from environment or use default public RPC.
        Priority: ENV_VAR > Default Public RPC
        """
        # Try common env vars
        for var in ["RPC_URL", "WEB3_PROVIDER_URI", "ETH_RPC_URL"]:
            rpc_url = os.getenv(var)
            if rpc_url:
                logger.info(f"Using RPC from {var}")
                return cls(rpc_url, chain=chain)
        
        # Fall back to public RPC
        logger.warning(f"No RPC URL in env, using public RPC for {chain.value}")
        return cls(cls.DEFAULT_RPCS[chain], chain=chain)
    
    def get_balance(self, address: str) -> int:
        """Get ETH/native token balance in wei"""
        return self.w3.eth.get_balance(Web3.to_checksum_address(address))
    
    def get_block_number(self) -> int:
        """Get latest block number"""
        return self.w3.eth.block_number
    
    def get_gas_price(self) -> int:
        """Get current gas price in wei"""
        return self.w3.eth.gas_price
    
    def wait_for_transaction(self, tx_hash: str, timeout: int = 120) -> Dict[str, Any]:
        return self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)


# Convenience function
def get_provider(
    rpc_url: Optional[str] = None,
    chain: Chain = Chain.ETHEREUM
) -> Provider:
    if rpc_url:
        return Provider(rpc_url, chain=chain)
    return Provider.auto(chain)