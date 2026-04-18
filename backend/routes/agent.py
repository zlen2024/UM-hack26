from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from database import get_db
from models import User
from auth import get_current_user
from agents.registry import FUNCTION_REGISTRY, validate_args, list_available_functions


router = APIRouter()


class AgentCommand(BaseModel):
    tool: str = "crm"
    function: str
    args: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    tool: str
    function: str
    result: Optional[Any] = None
    error: Optional[Dict[str, str]] = None


@router.post("/execute", response_model=AgentResponse)
def execute_agent_command(
    command: AgentCommand,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if command.tool != "crm":
        return AgentResponse(
            tool=command.tool,
            function=command.function,
            result=None,
            error={"code": "INVALID_TOOL", "message": f"Unknown tool: {command.tool}"},
        )

    func_name = command.function
    func_info = FUNCTION_REGISTRY.get(func_name)

    if not func_info:
        return AgentResponse(
            tool=command.tool,
            function=func_name,
            result=None,
            error={"code": "UNKNOWN_FUNCTION", "message": f"Unknown function: {func_name}"},
        )

    validation = validate_args(func_name, command.args)
    if not validation["valid"]:
        return AgentResponse(
            tool=command.tool,
            function=func_name,
            result=None,
            error={"code": "VALIDATION_ERROR", "message": validation["error"]},
        )

    try:
        handler = func_info["handler"]
        args = command.args.copy()
        args["db"] = db
        args["user_id"] = current_user.id

        result = handler(**args)

        if func_name.startswith("delete_") and result is True:
            result = {"message": "Deleted successfully"}

        return AgentResponse(
            tool=command.tool,
            function=func_name,
            result=result,
            error=None,
        )
    except Exception as e:
        return AgentResponse(
            tool=command.tool,
            function=func_name,
            result=None,
            error={"code": "EXECUTION_ERROR", "message": str(e)},
        )


@router.get("/functions")
def list_agent_functions(
    current_user: User = Depends(get_current_user),
):
    return {"functions": list_available_functions()}


@router.post("/batch")
def execute_batch_commands(
    commands: List[AgentCommand],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = []
    for command in commands:
        func_name = command.function
        func_info = FUNCTION_REGISTRY.get(func_name)

        if not func_info:
            results.append(
                AgentResponse(
                    tool=command.tool,
                    function=func_name,
                    result=None,
                    error={"code": "UNKNOWN_FUNCTION", "message": f"Unknown function: {func_name}"},
                )
            )
            continue

        validation = validate_args(func_name, command.args)
        if not validation["valid"]:
            results.append(
                AgentResponse(
                    tool=command.tool,
                    function=func_name,
                    result=None,
                    error={"code": "VALIDATION_ERROR", "message": validation["error"]},
                )
            )
            continue

        try:
            handler = func_info["handler"]
            args = command.args.copy()
            args["db"] = db
            args["user_id"] = current_user.id

            result = handler(**args)

            if func_name.startswith("delete_") and result is True:
                result = {"message": "Deleted successfully"}

            results.append(
                AgentResponse(
                    tool=command.tool,
                    function=func_name,
                    result=result,
                    error=None,
                )
            )
        except Exception as e:
            results.append(
                AgentResponse(
                    tool=command.tool,
                    function=func_name,
                    result=None,
                    error={"code": "EXECUTION_ERROR", "message": str(e)},
                )
            )

    return {"results": results}