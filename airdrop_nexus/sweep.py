from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional

from web3 import Web3
from web3.contract import Contract

from airdrop_nexus.config import NftConfig, TokenConfig
from airdrop_nexus.io_utils import WalletRecord

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

ERC721_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "index", "type": "uint256"},
        ],
        "name": "tokenOfOwnerByIndex",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "from", "type": "address"},
            {"name": "to", "type": "address"},
            {"name": "tokenId", "type": "uint256"},
        ],
        "name": "safeTransferFrom",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


@dataclass(frozen=True)
class SweepResult:
    submitted: List[str]
    skipped: List[str]


def _to_checksum(web3: Web3, address: str) -> str:
    return web3.to_checksum_address(address)


def _erc20_contract(web3: Web3, address: str) -> Contract:
    return web3.eth.contract(address=_to_checksum(web3, address), abi=ERC20_ABI)


def _erc721_contract(web3: Web3, address: str) -> Contract:
    return web3.eth.contract(address=_to_checksum(web3, address), abi=ERC721_ABI)


def _require_private_key(wallet: WalletRecord) -> str:
    if not wallet.private_key:
        raise ValueError(f"Missing private key for wallet {wallet.address}")
    return wallet.private_key


def _build_base_tx(web3: Web3, sender: str) -> dict:
    return {
        "from": sender,
        "nonce": web3.eth.get_transaction_count(sender),
        "gasPrice": web3.eth.gas_price,
    }


def _has_balance_for_gas(web3: Web3, sender: str, gas_estimate: int) -> bool:
    balance = web3.eth.get_balance(sender)
    return balance >= gas_estimate * web3.eth.gas_price


def sweep_erc20(
    web3: Web3,
    wallet: WalletRecord,
    vault_address: str,
    tokens: Iterable[TokenConfig],
    dry_run: bool = False,
) -> SweepResult:
    sender = _to_checksum(web3, wallet.address)
    vault = _to_checksum(web3, vault_address)
    submitted: List[str] = []
    skipped: List[str] = []

    for token in tokens:
        contract = _erc20_contract(web3, token.address)
        balance = contract.functions.balanceOf(sender).call()
        if balance == 0:
            skipped.append(f"{token.symbol}: zero balance")
            continue

        tx = contract.functions.transfer(vault, balance).build_transaction(
            _build_base_tx(web3, sender)
        )
        gas_estimate = web3.eth.estimate_gas(tx)
        if not _has_balance_for_gas(web3, sender, gas_estimate):
            skipped.append(f"{token.symbol}: insufficient gas")
            continue

        if dry_run:
            submitted.append(f"{token.symbol}: prepared")
            continue

        signed = web3.eth.account.sign_transaction(tx, _require_private_key(wallet))
        tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
        submitted.append(f"{token.symbol}: {tx_hash.hex()}")

    return SweepResult(submitted=submitted, skipped=skipped)


def _resolve_erc721_token_ids(
    contract: Contract,
    owner: str,
    configured_ids: Optional[List[int]],
) -> List[int]:
    if configured_ids:
        return configured_ids
    token_ids: List[int] = []
    balance = contract.functions.balanceOf(owner).call()
    for index in range(balance):
        token_id = contract.functions.tokenOfOwnerByIndex(owner, index).call()
        token_ids.append(token_id)
    return token_ids


def sweep_erc721(
    web3: Web3,
    wallet: WalletRecord,
    vault_address: str,
    nfts: Iterable[NftConfig],
    dry_run: bool = False,
) -> SweepResult:
    sender = _to_checksum(web3, wallet.address)
    vault = _to_checksum(web3, vault_address)
    submitted: List[str] = []
    skipped: List[str] = []

    for nft in nfts:
        contract = _erc721_contract(web3, nft.address)
        token_ids = _resolve_erc721_token_ids(contract, sender, nft.token_ids)
        if not token_ids:
            skipped.append(f"{nft.name}: no token IDs")
            continue

        for token_id in token_ids:
            tx = contract.functions.safeTransferFrom(
                sender,
                vault,
                token_id,
            ).build_transaction(_build_base_tx(web3, sender))
            gas_estimate = web3.eth.estimate_gas(tx)
            if not _has_balance_for_gas(web3, sender, gas_estimate):
                skipped.append(f"{nft.name} #{token_id}: insufficient gas")
                continue

            if dry_run:
                submitted.append(f"{nft.name} #{token_id}: prepared")
                continue

            signed = web3.eth.account.sign_transaction(tx, _require_private_key(wallet))
            tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
            submitted.append(f"{nft.name} #{token_id}: {tx_hash.hex()}")

    return SweepResult(submitted=submitted, skipped=skipped)
