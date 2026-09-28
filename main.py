"""
YouthGuard Protocol - Core Gateway & AI Agent Delegation Engine
BLI LegalTech Hackathon 2
License: MIT
"""

import time
import base64
from typing import Dict, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from cryptography.hazmat.primitives.asymmetric import ed25519

app = FastAPI(
    title="YouthGuard Protocol Gateway",
    description="Autonomous Agent Authority Delegation & Budget Control",
    version="1.0.0"
)

delegation_tokens_db: Dict[str, dict] = {}
transaction_logs: List[dict] = []

class KeyAuthority:
    def __init__(self):
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self._private_key.public_key()

    def sign_payload(self, message: bytes) -> str:
        signature = self._private_key.sign(message)
        return base64.b64encode(signature).decode("utf-8")

    def verify_payload(self, signature_b64: str, message: bytes) -> bool:
        try:
            raw_sig = base64.b64decode(signature_b64.encode("utf-8"))
            self.public_key.verify(raw_sig, message)
            return True
        except Exception:
            return False

authority = KeyAuthority()

class DelegateRequest(BaseModel):
    agent_id: str = Field(..., description="Agent Public ID")
    max_budget_usdc: float = Field(..., gt=0, description="Max spend limit in USDC")
    duration_seconds: int = Field(default=3600, gt=0, description="Token validity in seconds")

class ExecutionRequest(BaseModel):
    token_id: str = Field(..., description="Delegation Token ID")
    agent_id: str = Field(..., description="Executing Agent ID")
    target_contract: str = Field(..., description="Target Contract Address")
    amount_usdc: float = Field(..., ge=0, description="Amount to spend")

@app.get("/")
def health_check():
    return {
        "protocol": "YouthGuard",
        "status": "ONLINE",
        "version": "1.0.0",
        "crypto_backend": "Ed25519"
    }

@app.post("/api/v1/delegate", status_code=status.HTTP_201_CREATED)
def issue_delegation(req: DelegateRequest):
    token_id = f"yg_{int(time.time())}_{req.agent_id[:6]}"
    expires_at = int(time.time()) + req.duration_seconds
    payload_bytes = f"{token_id}:{req.agent_id}:{req.max_budget_usdc}:{expires_at}".encode("utf-8")
    
    token_data = {
        "token_id": token_id,
        "agent_id": req.agent_id,
        "max_budget": req.max_budget_usdc,
        "remaining_budget": req.max_budget_usdc,
        "expires_at": expires_at,
        "signature": authority.sign_payload(payload_bytes),
        "status": "ACTIVE"
    }
    delegation_tokens_db[token_id] = token_data
    return {"status": "SUCCESS", "token": token_data}

@app.post("/api/v1/execute")
def execute_agent_call(req: ExecutionRequest):
    if req.token_id not in delegation_tokens_db:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token = delegation_tokens_db[req.token_id]
    if time.time() > token["expires_at"]:
        token["status"] = "EXPIRED"
        raise HTTPException(status_code=400, detail="Delegation token expired")
        
    if token["agent_id"] != req.agent_id:
        raise HTTPException(status_code=403, detail="Agent ID mismatch")
        
    if req.amount_usdc > token["remaining_budget"]:
        raise HTTPException(status_code=400, detail="Budget limit exceeded")
        
    token["remaining_budget"] -= req.amount_usdc
    tx_log = {
        "tx_id": f"tx_{int(time.time() * 1000)}",
        "token_id": req.token_id,
        "agent_id": req.agent_id,
        "target": req.target_contract,
        "spent": req.amount_usdc,
        "remaining": token["remaining_budget"],
        "timestamp": int(time.time())
    _usdc > token["remaining_budget"]:
        raise HTTPException(status_code=400, detail="Budget limit exceeded")
        
    token["remaining_budget"] -= req.amount_usdc
    tx_log = {
        "tx_id": f"tx_{int(time.time() * 1000)}",
        "token_id": req.token_id,
        "agent_id": req.agent_id,
        "target": req.target_contract,
        "spent": req.amount_usdc,
        "remaining": token["remaining_budget"],
        "timestamp": int(time.time())
    }
    transaction_logs.append(tx_log)
    return {"status": "APPROVED", "tx": tx_log}

@app.get("/api/v1/audit/logs")
def get_logs():
    return {"total": len(transaction_logs), "logs": transaction_logs}
