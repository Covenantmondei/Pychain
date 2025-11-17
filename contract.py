from typing import Any, Dict, List, Optional, Union
from web3 import Web3
from web3.contract import Contract as Web3Contract
from eth_account import Account
import logging
from utils.abi import ABILoader
from .provider import Provider, get_provider

logger = logging.getLogger(__name__)


class Contract:
    """
    Smart contract interface with auto-generated methods.
    
    Examples:
        # Basic usage
        contract = Contract(
            address="0x...",
            abi="ERC20.json",
            provider="https://eth.llamarpc.com"
        )
        
        # Auto-load from config
        contract = Contract.from_config("MyToken")
        
        # Call view function
        balance = contract.balanceOf("0x123...")
        
        # Send transaction
        tx_hash = contract.transfer("0xabc...", 1000, signer=wallet)
    """
    
    def __init__(
        self,
        address: str,
        abi: Union[str, List[Dict[str, Any]]],
        provider: Optional[Union[str, Provider]] = None,
    ):

        self.address = Web3.to_checksum_address(address)
        
        # Load ABI
        if isinstance(abi, str):
            if abi.endswith('.json'):
                self.abi = ABILoader.from_file(abi)
            else:
                self.abi = ABILoader.from_name(abi)
        else:
            self.abi = abi
        
        # Setup provider
        if isinstance(provider, Provider):
            self.provider = provider
        elif isinstance(provider, str):
            self.provider = Provider(provider)
        else:
            self.provider = get_provider()
        
        # Create Web3 contract instance
        self._contract: Web3Contract = self.provider.w3.eth.contract(
            address=self.address,
            abi=self.abi
        )
        
        # Auto-generate methods
        self.generate_methods()
    
    def generate_methods(self):
        """Auto-generate Python methods from ABI"""
        for item in self.abi:
            if item.get("type") != "function":
                continue
            
            func_name = item["name"]
            
            # Skip if method already exists
            if hasattr(self, func_name):
                continue
            
            # Determine if it's a view/pure function
            state_mutability = item.get("stateMutability", "")
            is_view = state_mutability in ["view", "pure"]
            
            if is_view:
                # Create view function wrapper
                def make_view_method(name):
                    def method(*args, **kwargs):
                        return self.call(name, *args, **kwargs)
                    return method
                
                setattr(self, func_name, make_view_method(func_name))
            else:
                # Create transaction function wrapper
                def make_tx_method(name):
                    def method(*args, signer=None, **kwargs):
                        return self.send(name, *args, signer=signer, **kwargs)
                    return method
                
                setattr(self, func_name, make_tx_method(func_name))
    
    def call(self, function_name: str, *args, **kwargs) -> Any:
        func = getattr(self._contract.functions, function_name)
        return func(*args).call(**kwargs)
    
    def send(
        self,
        function_name: str,
        *args,
        signer: Optional[str] = None,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        value: int = 0,
        **kwargs
    ) -> str:
        """
        Send transaction (costs gas).
        
        Args:
            function_name: Function name
            *args: Function arguments
            signer: Private key or Account
            gas: Gas limit
            gas_price: Gas price in wei
            value: ETH to send (in wei)
            **kwargs: Additional transaction parameters
            
        Returns:
            Transaction hash
        """
        if not signer:
            raise ValueError("Signer (private key) required for transactions")
        
        # Load account
        if isinstance(signer, str):
            account = Account.from_key(signer)
        else:
            account = signer
        
        # Build transaction
        func = getattr(self._contract.functions, function_name)
        tx = func(*args).build_transaction({
            "from": account.address,
            "gas": gas or 200000,  # Default gas limit
            "gasPrice": gas_price or self.provider.get_gas_price(),
            "nonce": self.provider.w3.eth.get_transaction_count(account.address),
            "value": value,
            **kwargs
        })
        
        # Sign transaction
        signed_tx = account.sign_transaction(tx)
        
        # Send transaction
        tx_hash = self.provider.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        return tx_hash.hex()
    
    def estimate_gas(self, function_name: str, *args, **kwargs) -> int:
        """
        Estimate gas for transaction.
        
        Args:
            function_name: Function name
            *args: Function arguments
            **kwargs: Additional options
            
        Returns:
            Estimated gas
        """
        func = getattr(self._contract.functions, function_name)
        return func(*args).estimate_gas(kwargs)
    
    @classmethod
    def from_config(
        cls,
        contract_name: str,
        config_path: str = "contracts.json"
    ) -> "Contract":
        """
        Load contract from configuration file.
        
        Config format:
        {
            "MyToken": {
                "address": "0x...",
                "abi": "path/to/abi.json",
                "network": "ethereum"
            }
        }
        
        Args:
            contract_name: Contract identifier
            config_path: Path to config file
            
        Returns:
            Contract instance
        """
        import json
        from pathlib import Path
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file) as f:
            config = json.load(f)
        
        if contract_name not in config:
            raise ValueError(f"Contract '{contract_name}' not found in config")
        
        contract_config = config[contract_name]
        
        return cls(
            address=contract_config["address"],
            abi=contract_config.get("abi", contract_name),
            provider=contract_config.get("rpc_url")
        )