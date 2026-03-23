import json
from tools import get_file_tree, get_repo_info


mapping_tool_function = {
    "get_repo_info": get_repo_info,
    "get_file_tree": get_file_tree
}

def execute_tool(tool_name, tool_args):
    if isinstance(tool_args, str):
        tool_args = json.loads(tool_args)

    result = mapping_tool_function[tool_name](**tool_args)

    if result is None:
        result = "The operation completed but didn't return any results."

    elif isinstance(result, list):
        result = ', '.join(result)

    elif isinstance(result, dict):
        # Convert dictionaries to formatted JSON strings
        result = json.dumps(result, indent=2)

    else:
        # For any other type, convert using str()
        result = str(result)
    return result