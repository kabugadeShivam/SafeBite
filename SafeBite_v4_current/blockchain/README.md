# SafeBite Blockchain Layer

The SafeBite backend first creates a tamper-evident SHA-256 audit chain. The included `SafeBiteAudit.sol` contract can anchor record hashes on a local EVM network such as Hardhat or Ganache.

## Contract

`SafeBiteAudit.sol` exposes:

- `recordAudit(bytes32 recordHash, string entityType, uint256 entityId)`
- `getRecord(uint256 index)`
- `totalRecords()`

## Backend anchoring

Set these environment variables when a local EVM node and deployed contract are available:

```text
SAFEBITE_BLOCKCHAIN_ENABLED=true
SAFEBITE_BLOCKCHAIN_RPC=http://127.0.0.1:8545
SAFEBITE_CONTRACT_ADDRESS=0x...
SAFEBITE_PRIVATE_KEY=0x...
SAFEBITE_CONTRACT_ABI=blockchain/SafeBiteAudit.abi.json
```

The backend keeps local audit records even when blockchain anchoring is disabled, so the application remains usable without the EVM node.
