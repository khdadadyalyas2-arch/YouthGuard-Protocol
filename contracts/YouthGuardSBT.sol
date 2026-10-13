// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @dev Interface of the ERC5192 Minimal Soulbound Token standard.
 */
interface IERC5192 {
    event Locked(uint256 tokenId);
    event Unlocked(uint256 tokenId);

    function locked(uint256 tokenId) external view returns (bool);
}

/**
 * @title YouthGuardSBT
 * @notice Soulbound Token (SBT) representing verifiable legal attestations and protections for Web3 users.
 */
contract YouthGuardSBT is IERC5192 {
    string public name = "YouthGuard Legal Attestation";
    string public symbol = "YGUARD";

    address public owner;
    uint256 private _nextTokenId;

    struct LegalCredential {
        bytes32 claimHash;      // Keccak256 hash of legal document or ZK-Proof
        uint64 issuedAt;        // Timestamp of issuance
        uint64 expiresAt;       // Expiration date (0 if permanent)
        bool isValid;           // Status of the credential
    }

    // Mapping from token ID to legal credential details
    mapping(uint256 => LegalCredential) public credentials;
    // Mapping from token ID to owner address
    mapping(uint256 => address) private _owners;
    // Mapping from owner address to token ID
    mapping(address => uint256) public userTokenId;

    event AttestationIssued(address indexed recipient, uint256 indexed tokenId, bytes32 claimHash);
    event AttestationRevoked(uint256 indexed tokenId, string reason);

    modifier onlyOwner() {
        require(msg.sender == owner, "YouthGuard: Caller is not the authorized authority");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Checks if a token is locked (Soulbound).
     * @return Always true, as credentials cannot be transferred.
     */
    function locked(uint256 tokenId) external view override returns (bool) {
        require(_owners[tokenId] != address(0), "YouthGuard: Token does not exist");
        return true;
    }

    /**
     * @notice Issue a new Soulbound Legal Credential to a recipient.
     * @param recipient The address receiving the attestation.
     * @param claimHash Cryptographic hash of the legal proof or ZK verification.
     * @param duration Validity duration in seconds (0 for permanent).
     */
    function issueAttestation(
        address recipient,
        bytes32 claimHash,
        uint64 duration
    ) external onlyOwner returns (uint256) {
        require(recipient != address(0), "YouthGuard: Invalid recipient");
        require(userTokenId[recipient] == 0, "YouthGuard: Recipient already holds an active SBT");

        uint256 tokenId = ++_nextTokenId;
        _owners[tokenId] = recipient;
        userTokenId[recipient] = tokenId;

        uint64 expiration = duration > 0 ? uint64(block.timestamp) + duration : 0;

        credentials[tokenId] = LegalCredential({
            claimHash: claimHash,
            issuedAt: uint64(block.timestamp),
            expiresAt: expiration,
            isValid: true
        });

        emit Locked(tokenId);
        emit AttestationIssued(recipient, tokenId, claimHash);

        return tokenId;
    }

    /**
     * @notice Revoke an attestation in case of legal dispute or expiration.
     */
    function revokeAttestation(uint256 tokenId, string calldata reason) external onlyOwner {
        require(_owners[tokenId] != address(0), "YouthGuard: Token does not exist");
        require(credentials[tokenId].isValid, "YouthGuard: Already revoked");

        credentials[tokenId].isValid = false;
        emit AttestationRevoked(tokenId, reason);
    }

    /**
     * @notice Verify if an address currently holds an active, unexpired legal attestation.
     */
    function verifyLegalStanding(address user) external view returns (bool) {
        uint256 tokenId = userTokenId[user];
        if (tokenId == 0) return false;

        LegalCredential memory cred = credentials[tokenId];
        if (!cred.isValid) return false;
        if (cred.expiresAt > 0 && block.timestamp > cred.expiresAt) return false;

        return true;
    }

    function ownerOf(uint256 tokenId) external view returns (address) {
        address tokenOwner = _owners[tokenId];
        require(tokenOwner != address(0), "YouthGuard: Token does not exist");
        return tokenOwner;
    }
}
