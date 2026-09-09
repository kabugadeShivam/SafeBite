import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from ..models import BlockchainRecord

ZERO_HASH = "0" * 64


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _record_material(record_type, entity_type, entity_id, actor_id, payload_hash, previous_hash, timestamp):
    return canonical_json({
        "record_type": record_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor_id": actor_id,
        "payload_hash": payload_hash,
        "previous_hash": previous_hash,
        "timestamp": timestamp.isoformat(),
    })


def create_audit_record(
    db: Session,
    record_type: str,
    entity_type: str,
    entity_id: int,
    actor_id: int | None,
    payload: dict,
    blockchain_tx_id: str | None = None,
):
    previous = db.query(BlockchainRecord).order_by(BlockchainRecord.id.desc()).first()
    previous_hash = previous.record_hash if previous else ZERO_HASH
    timestamp = datetime.utcnow()
    payload_hash = sha256_text(canonical_json(payload))
    material = _record_material(
        record_type,
        entity_type,
        entity_id,
        actor_id,
        payload_hash,
        previous_hash,
        timestamp,
    )
    record_hash = sha256_text(material)

    record = BlockchainRecord(
        record_type=record_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        payload_hash=payload_hash,
        previous_hash=previous_hash,
        record_hash=record_hash,
        timestamp=timestamp,
        blockchain_tx_id=blockchain_tx_id,
        verification_status="LOCAL_HASH_CHAIN",
    )
    db.add(record)
    db.flush()
    return record


def verify_audit_chain(db: Session):
    records = db.query(BlockchainRecord).order_by(BlockchainRecord.id.asc()).all()
    expected_previous = ZERO_HASH

    for record in records:
        if record.previous_hash != expected_previous:
            return False, f"Broken previous-hash link at record {record.id}"

        expected_hash = sha256_text(_record_material(
            record.record_type,
            record.entity_type,
            record.entity_id,
            record.actor_id,
            record.payload_hash,
            record.previous_hash,
            record.timestamp,
        ))

        if record.record_hash != expected_hash:
            return False, f"Record hash mismatch at record {record.id}"

        expected_previous = record.record_hash

    return True, "Audit chain verified"


def anchor_record_to_evm(record_hash: str, entity_type: str, entity_id: int):
    """Optionally anchor a SafeBite record hash to a deployed EVM contract.

    Set SAFEBITE_BLOCKCHAIN_ENABLED=true only after a local Hardhat/Ganache
    node and deployed SafeBiteAudit contract are ready.
    """
    if os.getenv("SAFEBITE_BLOCKCHAIN_ENABLED", "false").lower() != "true":
        return None

    try:
        from web3 import Web3
    except ImportError as exc:
        raise RuntimeError("Install web3 to enable EVM blockchain anchoring") from exc

    rpc_url = os.getenv("SAFEBITE_BLOCKCHAIN_RPC", "http://127.0.0.1:8545")
    contract_address = os.getenv("SAFEBITE_CONTRACT_ADDRESS")
    private_key = os.getenv("SAFEBITE_PRIVATE_KEY")
    abi_path = os.getenv("SAFEBITE_CONTRACT_ABI", "blockchain/SafeBiteAudit.abi.json")

    if not contract_address or not private_key:
        raise RuntimeError("SAFEBITE_CONTRACT_ADDRESS and SAFEBITE_PRIVATE_KEY are required")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Unable to connect to blockchain RPC: {rpc_url}")

    abi_file = Path(abi_path)
    if not abi_file.exists():
        raise RuntimeError(f"Contract ABI file not found: {abi_file}")

    abi = json.loads(abi_file.read_text(encoding="utf-8"))
    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=abi,
    )
    hash_bytes = Web3.to_bytes(hexstr=record_hash)

    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions.recordAudit(
        hash_bytes,
        entity_type,
        entity_id,
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "chainId": w3.eth.chain_id,
        "gas": 300000,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()
