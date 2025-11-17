from enum import Enum


class Network(Enum):
    ETHEREUM_MAINNET = "ethereum"
    ETHEREUM_SEPOLIA = "sepolia"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"
    BSC = "bsc"
    AVALANCHE = "avalanche"


# Default RPC endpoints (public, rate-limited)
DEFAULT_RPCS = {
    Network.ETHEREUM_MAINNET: "https://ethereum-rpc.publicnode.com",
    Network.ETHEREUM_SEPOLIA: "https://ethereum-sepolia-rpc.publicnode.com",
    Network.POLYGON: "https://polygon-bor-rpc.publicnode.com",
    Network.ARBITRUM: "https://arbitrum-one-rpc.publicnode.com",
    Network.OPTIMISM: "https://optimism-rpc.publicnode.com",
    Network.BASE: "https://base-rpc.publicnode.com",
    Network.BSC: "https://bsc-rpc.publicnode.com",
    Network.AVALANCHE: "https://avalanche-c-chain-rpc.publicnode.com",
}

# Chain IDs
CHAIN_IDS = {
    Network.ETHEREUM_MAINNET: 1,
    Network.ETHEREUM_SEPOLIA: 11155111,
    Network.POLYGON: 137,
    Network.ARBITRUM: 42161,
    Network.OPTIMISM: 10,
    Network.BASE: 8453,
    Network.BSC: 56,
    Network.AVALANCHE: 43114,
}

# Block explorers
EXPLORERS = {
    Network.ETHEREUM_MAINNET: "https://etherscan.io",
    Network.ETHEREUM_SEPOLIA: "https://sepolia.etherscan.io",
    Network.POLYGON: "https://polygonscan.com",
    Network.ARBITRUM: "https://arbiscan.io",
    Network.OPTIMISM: "https://optimistic.etherscan.io",
    Network.BASE: "https://basescan.org",
    Network.BSC: "https://bscscan.com",
    Network.AVALANCHE: "https://snowtrace.io",
}