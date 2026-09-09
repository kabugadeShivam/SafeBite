// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SafeBiteAudit {
    struct AuditRecord {
        bytes32 recordHash;
        string entityType;
        uint256 entityId;
        uint256 timestamp;
        address submittedBy;
    }

    AuditRecord[] private records;

    event AuditRecorded(
        uint256 indexed recordId,
        bytes32 indexed recordHash,
        string entityType,
        uint256 entityId,
        uint256 timestamp,
        address submittedBy
    );

    function recordAudit(bytes32 recordHash, string calldata entityType, uint256 entityId) external {
        records.push(AuditRecord({
            recordHash: recordHash,
            entityType: entityType,
            entityId: entityId,
            timestamp: block.timestamp,
            submittedBy: msg.sender
        }));

        emit AuditRecorded(
            records.length - 1,
            recordHash,
            entityType,
            entityId,
            block.timestamp,
            msg.sender
        );
    }

    function getRecord(uint256 index) external view returns (AuditRecord memory) {
        return records[index];
    }

    function totalRecords() external view returns (uint256) {
        return records.length;
    }
}
