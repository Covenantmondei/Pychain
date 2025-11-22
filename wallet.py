import json
import os
from typing import Dict, Optional, Any
from eth_account import Account 
from web3 import Web3
from utils.validators import validate_key
import logging

logger = logging.getLogger(__name__)


class Wallet:
    """This function is to handle all wallet connections and signing for Ethereum"""
    def __init__(self, private_key: Optional[str] = None):
        if private_key:
            # self.private_key = private_key
            validate_key(private_key)
            self.account = Account.from_key(private_key)
        else:
            # create a new account
            self.account = Account.create()
            self.private_key = self.account.key.hex()

        self.address = self.account.address
        logger.info(f"Wallet initialized: {self.address}")

    @classmethod
    def from_env(cls, env_var: str = "WALLET_PRIVATE_KEY") -> "Wallet":
        """Create wallet from environment variable"""
        private_key = os.getenv(env_var)
        if not private_key:
            raise ValueError(f"Environment variable {env_var} not set")
        return cls(private_key)

    # @classmethod
    # def from_mnemonic(cls, mnemonic: str, account_index: int = 0) -> "Wallet":
    #     """Create wallet from mnemonic phrase"""
    #     Account.enable_unaudited_hdwallet_features()
    #     account = Account.from_mnemonic(mnemonic, account_path=account_index)
    #     return cls(account.key.hex())

    @classmethod
    def from_json(cls, json_data: Dict[str, Any], password: str) -> "Wallet":
        """Create wallet from JSON keystore"""
        with open(json_data, 'r') as f:
            json_data = f.read()
        private_key = Account.decrypt(json_data, password).hex()
        return cls(private_key)


    def sign_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Sign a transaction dictionary"""
        signed_tx = self.account.sign_transaction(transaction)
        logger.debug(f"Transaction signed: {signed_tx.hash.hex()}")
        return signed_tx
    
    def sign_message(self, message: str) -> Dict[str, Any]:
        """Sign a message"""
        signed_message = self.account.sign_message(Web3.to_bytes(text=message))
        return signed_message
    
    @property
    def get_key(self) -> str:
        """Get the private key of the wallet"""
        return self.private_key


    def export_key(self, password: str, path: str) -> str:
        """Export the private key as an encrypted json keystore"""
        encrypted = Account.encrypt(self.private_key, password)
        with open(path, 'w') as f:
            json.dump(encrypted, f)
        logger.info(f"Private key exported to {path}")
        return path
    
    def __repr__(self):
        return f"<Wallet address={self.address}>"