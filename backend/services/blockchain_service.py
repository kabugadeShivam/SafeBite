import hashlib
import json
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import BlockchainRecord


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    previous_hash = previous.record_hash if previous else "0" * 64

    payload_hash = sha256_text(canonical_json(payload))
    audit_material = canonical_json({
        "record_type": record_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "actor_id": actor_id,
        "payload_hash": payload_hash,
        "previous_hash": previous_hash,
        "timestamp": datetime.utcnow().isoformat(),
    })
    record_hash = sha256_text(audit_material)

    record = BlockchainRecord(
        record_type=record_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        payload_hash=payload_hash,
        previous_hash=previous_hash,
        record_hash=record_hash,
        blockchain_tx_id=blockchain_tx_id,
    )

    db.add(record)
    db.flush()
    return record


def verify_audit_chain(db: Session):
    records = db.query(BlockchainRecord).order_by(BlockchainRecord.id.asc()).all()
    expected_previous = "0" * 64

    for record in records:
        if record.previous_hash != expected_previous:
            return False, f"Broken previous-hash link at record {record.id}"
        expected_previous = record.record_hash

    return True, "Audit chain verified"
