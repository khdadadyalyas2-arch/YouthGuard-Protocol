const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("YouthGuard Protocol Tests", function () {
  let sbt, arbitration, owner, user, arbitrator;

  beforeEach(async function () {
    [owner, user, arbitrator] = await ethers.getSigners();

    const YouthGuardSBT = await ethers.getContractFactory("YouthGuardSBT");
    sbt = await YouthGuardSBT.deploy();
    await sbt.waitForDeployment();

    const LegalArbitration = await ethers.getContractFactory("LegalArbitration");
    arbitration = await LegalArbitration.deploy(await sbt.getAddress());
    await arbitration.waitForDeployment();
  });

  it("Should issue SBT attestation to user", async function () {
    const claimHash = ethers.keccak256(ethers.toUtf8Bytes("Legal_Verified_Claim_1"));
    await sbt.issueAttestation(user.address, claimHash, 0);

    expect(await sbt.verifyLegalStanding(user.address)).to.equal(true);
    expect(await sbt.locked(1)).to.equal(true);
  });

  it("Should allow user with SBT to file a dispute", async function () {
    const claimHash = ethers.keccak256(ethers.toUtf8Bytes("Verified_Identity"));
    await sbt.issueAttestation(user.address, claimHash, 0);

    const evidenceHash = ethers.keccak256(ethers.toUtf8Bytes("Contract_Breach_Evidence"));
    await expect(
      arbitration.connect(user).fileDispute(owner.address, evidenceHash, "IP Infringement")
    ).to.emit(arbitration, "DisputeFiled");
  });
});
