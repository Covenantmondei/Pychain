from regex import R
from web3 import Web3
from typing import Any, Dict, Optional, Callable
from eth_account.signers.local import LocalAccount
from web3.types import TxReceipt
from .wallet import Wallet
from .provider import Provider

import logging

logger = logging.getLogger(__name__)

class TransactionStatus:
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REPLACED = "replaced"

class TransactionManager:
    """
    Manages Ethereum transactions including sending, tracking status, and handling receipts.
    
    Examples:
        wallet = Wallet.from_env()
        provider = Provider.from_env()
        tx_manager = TransactionManager(wallet, provider)
        
        tx_hash = tx_manager.send_transaction({
            "to": "0xRecipientAddress",
            "value": Web3.to_wei(0.01, 'ether'),
            "gas": 21000,
            "gasPrice": Web3.to_wei(50, 'gwei'),
            "nonce": provider.web3.eth.get_transaction_count(wallet.address),
        })
        
        receipt = tx_manager.wait_for_receipt(tx_hash)
    """

    def __init__(self, wallet: Wallet, provider: Provider, auto_nonce: bool = True, confirm_blocks: int = 1):
        self.wallet = wallet
        self.provider = provider
        self.auto_nonce = auto_nonce
        self.confirm_blocks = confirm_blocks
        self.nonce_cache: Optional[int] = None

        self.pending_txs: Dict[str, Dict[str, Any]] = {}


    def get_nonce(self, use_pending: bool = False) -> int:
        if self.auto_nonce:
            if use_pending and self.nonce_cache is not None:
                return self.nonce_cache
            return self.provider.web3.eth.get_transaction_count(self.wallet.address)
        return self.nonce_cache or 0

    def send_transaction(self, transaction: Dict[str, Any]) -> str:
        """Sign and send a transaction, returning the transaction hash."""
        signed_tx = self.wallet.sign_transaction(transaction)
        tx_hash = self.provider.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        return tx_hash.hex()
    
    def await_receipt(self, tx_hash: str, timeout: int = 120) -> TxReceipt:
        """Wait for a transaction receipt."""
        receipt = self.provider.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        logger.info(f"Transaction receipt received: {receipt.transactionHash.hex()}")
        return receipt