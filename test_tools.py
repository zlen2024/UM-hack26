import json
from backend.agents.graph.tools import CRM_TOOLS

def format_tool_to_openai(tool) -> dict:
    if hasattr(tool, "args_schema") and tool.args_schema:
        if hasattr(tool.args_schema, "model_json_schema"):
            parameters = tool.args_schema.model_json_schema()
        else:
            parameters = tool.args_schema.schema()
    else:
        parameters = {"type": "object", "properties": {}}
        
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": parameters
        }
    }

openai_tools = [format_tool_to_openai(t) for t in CRM_TOOLS]
print(json.dumps(openai_tools[0], indent=2))
