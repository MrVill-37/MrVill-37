import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class NetworkConfig:
    name: str
    chain_id: int
    rpc_url: str


@dataclass(frozen=True)
class TokenConfig:
    symbol: str
    address: str
    decimals: int


@dataclass(frozen=True)
class NftConfig:
    name: str
    address: str
    token_ids: Optional[List[int]]


@dataclass(frozen=True)
class AirdropConfig:
    name: str
    contract_address: str
    abi_path: str
    eligibility_method: str
    claim_method: str
    claim_args: List[Any]


@dataclass(frozen=True)
class AppConfig:
    vault_address: str
    networks: Dict[str, NetworkConfig]
    tokens: Dict[str, List[TokenConfig]]
    nfts: Dict[str, List[NftConfig]]
    airdrops: Dict[str, List[AirdropConfig]]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_config(config_path: Path) -> AppConfig:
    payload = _load_json(config_path)
    networks: Dict[str, NetworkConfig] = {}
    for name, cfg in payload["networks"].items():
        networks[name] = NetworkConfig(
            name=name,
            chain_id=int(cfg["chain_id"]),
            rpc_url=cfg["rpc_url"],
        )

    tokens: Dict[str, List[TokenConfig]] = {}
    for network, token_list in payload.get("tokens", {}).items():
        tokens[network] = [
            TokenConfig(
                symbol=token["symbol"],
                address=token["address"],
                decimals=int(token["decimals"]),
            )
            for token in token_list
        ]

    nfts: Dict[str, List[NftConfig]] = {}
    for network, nft_list in payload.get("nfts", {}).items():
        nfts[network] = [
            NftConfig(
                name=nft["name"],
                address=nft["address"],
                token_ids=nft.get("token_ids"),
            )
            for nft in nft_list
        ]

    airdrops: Dict[str, List[AirdropConfig]] = {}
    for network, airdrop_list in payload.get("airdrops", {}).items():
        airdrops[network] = [
            AirdropConfig(
                name=drop["name"],
                contract_address=drop["contract_address"],
                abi_path=drop["abi_path"],
                eligibility_method=drop["eligibility_method"],
                claim_method=drop["claim_method"],
                claim_args=drop.get("claim_args", []),
            )
            for drop in airdrop_list
        ]

    return AppConfig(
        vault_address=payload["vault_address"],
        networks=networks,
        tokens=tokens,
        nfts=nfts,
        airdrops=airdrops,
    )


def load_abi(abi_path: Path) -> List[Dict[str, Any]]:
    return _load_json(abi_path)


def resolve_path(base_dir: Path, maybe_relative: str) -> Path:
    path = Path(maybe_relative)
    if path.is_absolute():
        return path
    return base_dir / path
