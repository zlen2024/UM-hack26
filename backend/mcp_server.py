import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

if __package__:
    from .agents.registry import FUNCTION_REGISTRY, list_available_functions, validate_args
    from .database import SessionLocal
    from .models import IntegrationCredential, User
else:
    backend_dir = Path(__file__).resolve().parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from agents.registry import FUNCTION_REGISTRY, list_available_functions, validate_args
    from database import SessionLocal
    from models import IntegrationCredential, User


try:
    FastMCP = importlib.import_module("mcp.server.fastmcp").FastMCP
except ModuleNotFoundError as exc:
    raise RuntimeError(
        "The 'mcp' package is required to run backend/mcp_server.py. Install it with 'uv pip install mcp'."
    ) from exc


ZAPIER_PROVIDER = "zapier"
mcp = FastMCP("UM CRM MCP")


def get_db() -> Session:
    return SessionLocal()


def _get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def _get_zapier_credential(db: Session, user_id: int) -> Optional[IntegrationCredential]:
    return db.query(IntegrationCredential).filter(
        IntegrationCredential.user_id == user_id,
        IntegrationCredential.provider == ZAPIER_PROVIDER,
    ).first()


@mcp.tool()
def crm_list_functions() -> list[Dict[str, Any]]:
    return list_available_functions()


@mcp.tool()
def crm_execute(user_id: int, function_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    db = get_db()
    try:
        user = _get_user(db, user_id)
        if not user:
            return {"ok": False, "error": f"Unknown user_id: {user_id}"}

        func_info = FUNCTION_REGISTRY.get(function_name)
        if not func_info:
            return {"ok": False, "error": f"Unknown function: {function_name}"}

        payload = args or {}
        validation = validate_args(function_name, payload)
        if not validation["valid"]:
            return {"ok": False, "error": validation["error"]}

        handler = func_info["handler"]
        handler_args = payload.copy()
        handler_args["db"] = db
        handler_args["user_id"] = user.id
        result = handler(**handler_args)

        if function_name.startswith("delete_") and result is True:
            result = {"message": "Deleted successfully"}

        return {"ok": True, "result": result}
    finally:
        db.close()


@mcp.tool()
def zapier_status(user_id: int) -> Dict[str, Any]:
    db = get_db()
    try:
        credential = _get_zapier_credential(db, user_id)
        return {
            "provider": ZAPIER_PROVIDER,
            "connected": credential is not None,
            "has_key": credential is not None,
            "updated_at": credential.updated_at.isoformat() if credential and credential.updated_at else None,
            "last4": credential.secret_value[-4:] if credential and credential.secret_value else None,
        }
    finally:
        db.close()


@mcp.tool()
def zapier_save_key(user_id: int, api_key: str) -> Dict[str, Any]:
    db = get_db()
    try:
        user = _get_user(db, user_id)
        if not user:
            return {"ok": False, "error": f"Unknown user_id: {user_id}"}

        secret_value = api_key.strip()
        if not secret_value:
            return {"ok": False, "error": "api_key is required"}

        credential = _get_zapier_credential(db, user_id)
        if credential:
            credential.secret_value = secret_value
        else:
            credential = IntegrationCredential(
                user_id=user_id,
                provider=ZAPIER_PROVIDER,
                secret_value=secret_value,
            )
            db.add(credential)

        db.commit()
        db.refresh(credential)
        return {"ok": True, "provider": ZAPIER_PROVIDER, "connected": True}
    finally:
        db.close()


@mcp.tool()
def zapier_clear_key(user_id: int) -> Dict[str, Any]:
    db = get_db()
    try:
        credential = _get_zapier_credential(db, user_id)
        if credential:
            db.delete(credential)
            db.commit()
        return {"ok": True, "provider": ZAPIER_PROVIDER, "connected": False}
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()