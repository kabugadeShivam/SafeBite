// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeBiteAudit {
    struct Record {
        bytes32 recordHash;
        uint256 timestamp;
        string entityType;
        uint256 entityId;
        address actor;
    }

    Record[] private records;

    event AuditRecorded(
        uint256 indexed recordId,
        bytes32 indexed recordHash,
        string entityType,
        uint256 entityId,
        address indexed actor
    );

    function addRecord(
        bytes32 recordHash,
        string calldata entityType,
        uint256 entityId
    ) external returns (uint256) {
        records.push(
            Record({
                recordHash: recordHash,
                timestamp: block.timestamp,
                entityType: entityType,
                entityId: entityId,
                actor: msg.sender
            })
        );

        uint256 id = records.length - 1;
        emit AuditRecorded(id, recordHash, entityType, entityId, msg.sender);
        return id;
    }

    function getRecord(uint256 recordId)
        external
        view
        returns (
            bytes32 recordHash,
            uint256 timestamp,
            string memory entityType,
            uint256 entityId,
            address actor
        )
    {
        Record memory record = records[recordId];
        return (
            record.recordHash,
            record.timestamp,
            record.entityType,
            record.entityId,
            record.actor
        );
    }

    function recordCount() external view returns (uint256) {
        return records.length;
    }
}
