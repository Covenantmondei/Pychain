import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ABILoader:
    """
    Load contract ABIs from multiple sources.
    
    Examples:
        # From file
        abi = ABILoader.from_file("contracts/ERC20.json")
        
        # From directory (auto-search)
        abi = ABILoader.from_name("ERC20", search_dir="./contracts")
        
        # From dict
        abi = ABILoader.from_dict({"abi": [...]})
    """
    
    DEFAULT_ABI_DIRS = [
        "./contracts",
        "./abis",
        "./artifacts",
        "./build/contracts",
    ]
    
    @staticmethod
    def from_file(path: str) -> List[Dict[str, Any]]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"ABI file not found: {path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Truffle/Hardhat artifact format
            if "abi" in data:
                return data["abi"]
            # Foundry format
            elif "output" in data and "abi" in data["output"]:
                return data["output"]["abi"]
        
        raise ValueError(f"Invalid ABI format in {path}")
    
    @staticmethod
    def from_name(
        contract_name: str,
        search_dirs: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        if search_dirs is None:
            search_dirs = ABILoader.DEFAULT_ABI_DIRS
        
        # Common file patterns
        patterns = [
            f"{contract_name}.json",
            f"{contract_name}.abi.json",
            f"{contract_name}.sol/{contract_name}.json",
        ]
        
        for search_dir in search_dirs:
            dir_path = Path(search_dir)
            if not dir_path.exists():
                continue
            
            for pattern in patterns:
                file_path = dir_path / pattern
                if file_path.exists():
                    logger.info(f"Found ABI: {file_path}")
                    return ABILoader.from_file(str(file_path))
        
        raise FileNotFoundError(
            f"Could not find ABI for '{contract_name}' in {search_dirs}"
        )
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "abi" in data:
            return data["abi"]
        elif isinstance(data, list):
            return data
        raise ValueError("Invalid ABI dictionary format")
    
    @staticmethod
    def from_string(abi_json: str) -> List[Dict[str, Any]]:
        #  Load ABI from JSON string.

        data = json.loads(abi_json)
        return ABILoader.from_dict(data)
    

    @staticmethod
    def save(abi: List[Dict[str, Any]], path: str):
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(abi, f, indent=2)
        
        logger.info(f"Saved ABI to {path}")