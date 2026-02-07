from dataclasses import dataclass
from pathlib import Path
from typing import List

from web3 import Web3

from airdrop_nexus.config import AirdropConfig, load_abi
from airdrop_nexus.io_utils import WalletRecord


@dataclass(frozen=True)
class EligibilityResult:
    airdrop_name: str
    eligible: bool


def check_eligibility(
    web3: Web3,
    wallet: WalletRecord,
    airdrop: AirdropConfig,
    config_dir: Path,
) -> EligibilityResult:
    abi = load_abi(config_dir / airdrop.abi_path)
    contract = web3.eth.contract(
        address=web3.to_checksum_address(airdrop.contract_address),
        abi=abi,
    )
    method = getattr(contract.functions, airdrop.eligibility_method)
    eligible = bool(method(web3.to_checksum_address(wallet.address)).call())
    return EligibilityResult(airdrop_name=airdrop.name, eligible=eligible)
