from dataclasses import dataclass
from pathlib import Path
from typing import List

from web3 import Web3

from airdrop_nexus.config import AirdropConfig, load_abi
from airdrop_nexus.io_utils import WalletRecord


@dataclass(frozen=True)
class ClaimResult:
    airdrop_name: str
    tx_hash: str


def claim_airdrop(
    web3: Web3,
    wallet: WalletRecord,
    airdrop: AirdropConfig,
    config_dir: Path,
) -> ClaimResult:
    if not wallet.private_key:
        raise ValueError(f"Missing private key for wallet {wallet.address}")

    abi = load_abi(config_dir / airdrop.abi_path)
    contract = web3.eth.contract(
        address=web3.to_checksum_address(airdrop.contract_address),
        abi=abi,
    )
    method = getattr(contract.functions, airdrop.claim_method)
    tx = method(*airdrop.claim_args).build_transaction(
        {
            "from": web3.to_checksum_address(wallet.address),
            "nonce": web3.eth.get_transaction_count(wallet.address),
            "gasPrice": web3.eth.gas_price,
        }
    )
    gas_estimate = web3.eth.estimate_gas(tx)
    balance = web3.eth.get_balance(wallet.address)
    if balance < gas_estimate * web3.eth.gas_price:
        raise ValueError(f"Insufficient gas for {wallet.address}")

    signed = web3.eth.account.sign_transaction(tx, wallet.private_key)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    return ClaimResult(airdrop_name=airdrop.name, tx_hash=tx_hash.hex())
