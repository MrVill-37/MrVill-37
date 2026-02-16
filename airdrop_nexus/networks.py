from dataclasses import dataclass
from typing import Dict

from web3 import Web3

from airdrop_nexus.config import NetworkConfig


@dataclass(frozen=True)
class NetworkClient:
    config: NetworkConfig
    web3: Web3


def create_clients(networks: Dict[str, NetworkConfig]) -> Dict[str, NetworkClient]:
    clients: Dict[str, NetworkClient] = {}
    for name, cfg in networks.items():
        web3 = Web3(Web3.HTTPProvider(cfg.rpc_url))
        clients[name] = NetworkClient(config=cfg, web3=web3)
    return clients
