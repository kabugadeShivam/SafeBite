import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import BlockchainRecord


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEPLOYMENT_FILE = (
    PROJECT_ROOT
    / "blockchain"
    / "deployment.json"
)


# ============================================================
# JSON / HASH HELPERS
# ============================================================

def canonical_json(data: dict) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


# ============================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================

def get_rpc_url() -> str:
    return os.getenv(
        "BLOCKCHAIN_RPC_URL",
        "http://127.0.0.1:8545",
    )


def load_deployment():
    if not DEPLOYMENT_FILE.exists():
        return None

    try:
        with open(
            DEPLOYMENT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except (OSError, json.JSONDecodeError):
        return None


# ============================================================
# BLOCKCHAIN STATUS
# ============================================================

def blockchain_status() -> dict:
    deployment = load_deployment()

    if not deployment:
        return {
            "enabled": False,
            "connected": False,
            "message": "Contract not deployed",
        }

    try:
        from web3 import Web3

        w3 = Web3(
            Web3.HTTPProvider(
                get_rpc_url(),
                request_kwargs={"timeout": 3},
            )
        )

        if not w3.is_connected():
            return {
                "enabled": True,
                "connected": False,
                "message": "Blockchain node unavailable",
                "contract_address":
                    deployment.get("contractAddress"),
            }

        record_count = 0

        try:
            contract = w3.eth.contract(
                address=deployment[
                    "contractAddress"
                ],
                abi=deployment["abi"],
            )

            record_count = (
                contract.functions.recordCount().call()
            )

        except Exception:
            pass

        return {
            "enabled": True,
            "connected": True,
            "message": "Blockchain connected",
            "contract_address":
                deployment.get("contractAddress"),
            "record_count": record_count,
        }

    except ImportError:
        return {
            "enabled": True,
            "connected": False,
            "message": "web3 package is not installed",
        }

    except Exception as exc:
        return {
            "enabled": True,
            "connected": False,
            "message": str(exc),
        }


# ============================================================
# CREATE AUDIT RECORD
# ============================================================

def create_audit_record(
    db: Session,
    record_type: str,
    entity_type: str,
    entity_id: int,
    actor_id: int | None,
    payload: dict,
):
    previous = (
        db.query(BlockchainRecord)
        .order_by(
            BlockchainRecord.id.desc()
        )
        .first()
    )

    previous_hash = (
        previous.record_hash
        if previous
        else "0" * 64
    )

    payload_hash = sha256_text(
        canonical_json(payload)
    )

    timestamp = datetime.utcnow().isoformat()

    audit_material = canonical_json(
        {
            "record_type": record_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "payload_hash": payload_hash,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
        }
    )

    record_hash = sha256_text(
        audit_material
    )

    record = BlockchainRecord(
        record_type=record_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        payload_hash=payload_hash,
        previous_hash=previous_hash,
        record_hash=record_hash,
        blockchain_tx_id=None,
        verification_status="LOCAL_HASH_CHAIN",
    )

    db.add(record)
    db.flush()

    # --------------------------------------------------------
    # Attempt on-chain anchoring.
    # --------------------------------------------------------

    tx_id = anchor_audit_record(
        record
    )

    if tx_id:

        record.blockchain_tx_id = tx_id

        record.verification_status = (
            "BLOCKCHAIN_ANCHORED"
        )

        db.flush()

    return record


# ============================================================
# ANCHOR AUDIT RECORD TO SMART CONTRACT
# ============================================================

def anchor_audit_record(
    record: BlockchainRecord,
) -> str | None:

    private_key = os.getenv(
        "BLOCKCHAIN_PRIVATE_KEY"
    )

    if not private_key:
        print(
            "[SafeBite Blockchain] "
            "Private key not configured."
        )
        return None

    deployment = load_deployment()

    if not deployment:
        print(
            "[SafeBite Blockchain] "
            "deployment.json not found."
        )
        return None

    try:
        from web3 import Web3

        w3 = Web3(
            Web3.HTTPProvider(
                get_rpc_url(),
                request_kwargs={"timeout": 5},
            )
        )

        if not w3.is_connected():
            print(
                "[SafeBite Blockchain] "
                "Hardhat node is unavailable."
            )
            return None

        account = w3.eth.account.from_key(
            private_key
        )

        contract = w3.eth.contract(
            address=deployment[
                "contractAddress"
            ],
            abi=deployment["abi"],
        )

        nonce = w3.eth.get_transaction_count(
            account.address
        )

        transaction = (
            contract.functions.addRecord(
                bytes.fromhex(
                    record.record_hash
                ),
                record.entity_type,
                record.entity_id,
            )
            .build_transaction(
                {
                    "from": account.address,
                    "nonce": nonce,
                    "chainId": 31337,
                    "gas": 200000,
                    "gasPrice":
                        w3.eth.gas_price,
                }
            )
        )

        signed = account.sign_transaction(
            transaction
        )

        tx_hash = (
            w3.eth.send_raw_transaction(
                signed.raw_transaction
            )
        )

        receipt = (
            w3.eth.wait_for_transaction_receipt(
                tx_hash,
                timeout=30,
            )
        )

        if receipt.status != 1:
            print(
                "[SafeBite Blockchain] "
                "Transaction failed."
            )
            return None

        tx_id = tx_hash.hex()

        print(
            "[SafeBite Blockchain] "
            f"Audit anchored: {tx_id}"
        )

        return tx_id

    except Exception as exc:

        print(
            "[SafeBite Blockchain] "
            f"Anchoring failed: {exc}"
        )

        return None


# ============================================================
# VERIFY LOCAL HASH CHAIN
# ============================================================

def verify_audit_chain(
    db: Session,
):

    records = (
        db.query(BlockchainRecord)
        .order_by(
            BlockchainRecord.id.asc()
        )
        .all()
    )

    expected_previous = "0" * 64

    for record in records:

        if (
            record.previous_hash
            != expected_previous
        ):
            return (
                False,
                "Broken previous-hash link "
                f"at record {record.id}",
            )

        expected_previous = (
            record.record_hash
        )

    return (
        True,
        "Audit chain verified",
    )


# ============================================================
# VERIFY ON-CHAIN RECORD
# ============================================================

def verify_blockchain_record(
    record: BlockchainRecord,
) -> dict:

    if not record.blockchain_tx_id:
        return {
            "verified": False,
            "message":
                "No blockchain transaction recorded",
        }

    deployment = load_deployment()

    if not deployment:
        return {
            "verified": False,
            "message":
                "Blockchain deployment not found",
        }

    try:
        from web3 import Web3

        w3 = Web3(
            Web3.HTTPProvider(
                get_rpc_url(),
                request_kwargs={"timeout": 5},
            )
        )

        if not w3.is_connected():
            return {
                "verified": False,
                "message":
                    "Blockchain node unavailable",
            }

        receipt = (
            w3.eth.get_transaction_receipt(
                record.blockchain_tx_id
            )
        )

        if receipt.status != 1:
            return {
                "verified": False,
                "message":
                    "Blockchain transaction failed",
            }

        contract = w3.eth.contract(
            address=deployment[
                "contractAddress"
            ],
            abi=deployment["abi"],
        )

        count = (
            contract.functions
            .recordCount()
            .call()
        )

        for index in range(count):

            saved = (
                contract.functions
                .getRecord(index)
                .call()
            )

            saved_hash = saved[0].hex()

            if saved_hash == record.record_hash:

                return {
                    "verified": True,
                    "message":
                        "Blockchain audit verified",
                    "transaction_id":
                        record.blockchain_tx_id,
                    "chain_record": {
                        "record_id":
                            index,
                        "record_hash":
                            saved_hash,
                        "timestamp":
                            saved[1],
                        "entity_type":
                            saved[2],
                        "entity_id":
                            saved[3],
                        "actor":
                            saved[4],
                    },
                }

        return {
            "verified": False,
            "message":
                "Audit hash not found on blockchain",
        }

    except Exception as exc:
        return {
            "verified": False,
            "message": str(exc),
        }