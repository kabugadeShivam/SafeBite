const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("Deploying SafeBiteAudit...");

  const SafeBiteAudit =
    await hre.ethers.getContractFactory("SafeBiteAudit");

  const contract = await SafeBiteAudit.deploy();

  await contract.waitForDeployment();

  const address = await contract.getAddress();

  console.log("SafeBiteAudit deployed to:");
  console.log(address);

  const artifact =
    await hre.artifacts.readArtifact("SafeBiteAudit");

  const deployment = {
    network: "localhost",
    chainId: 31337,
    contractAddress: address,
    abi: artifact.abi
  };

  const deploymentPath = path.join(
    __dirname,
    "..",
    "deployment.json"
  );

  fs.writeFileSync(
    deploymentPath,
    JSON.stringify(deployment, null, 2)
  );

  console.log("Deployment information saved.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
