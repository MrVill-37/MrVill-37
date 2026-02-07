import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class WalletRecord:
    address: str
    private_key: Optional[str]


def load_wallets(path: Path) -> List[WalletRecord]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text())
        return [
            WalletRecord(address=entry["address"], private_key=entry.get("private_key"))
            for entry in payload
        ]

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            WalletRecord(address=row["address"], private_key=row.get("private_key"))
            for row in reader
        ]


def save_wallets(path: Path, wallets: Iterable[WalletRecord]) -> None:
    payload = [
        {"address": wallet.address, "private_key": wallet.private_key}
        for wallet in wallets
    ]
    path.write_text(json.dumps(payload, indent=2))
