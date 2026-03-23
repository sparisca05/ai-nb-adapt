import json
from typing import Dict, List
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = [
    {
        "role": "system",
        "content": (
            "You are a GitHub repository auditor. "
            "When the user mentions a repository, always identify the owner and repo name. "
            "Repositories are usually written as 'owner/repo' (e.g. 'vercel/next.js'). "
            "If the user provides them separately or informally, infer both before calling any tool. "
            "If you cannot determine the owner, ask the user before proceeding."
            "NEVER reproduce the raw output of a tool in your response. The UI already displays tool results separately."
        )
    }
]

CONVERSATIONS: Dict[str, List[dict]] = {}

def chat(query: str, tools: list, execute_tool, conversation_id: str = "default") -> str:
    
    if conversation_id not in CONVERSATIONS:
        CONVERSATIONS[conversation_id] = SYSTEM_PROMPT.copy()

    history = CONVERSATIONS[conversation_id]
    history.append({'role': 'user', 'content': query})

    recorded_tool_calls: list[dict] = []

    while True:

        response = client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = history,
            tools = tools,
            max_completion_tokens = 500
        )

        message = response.choices[0].message

        if not message.tool_calls:
            history.append({'role': 'assistant', 'content': message.content})
            return message.content, recorded_tool_calls

        history.append({
            'role': 'assistant',
            'content': message.content or "",
            "tool_calls": message.tool_calls
        })

        for tool_call in message.tool_calls:

            tool_id = tool_call.id
            tool_args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name

            # Record for the response payload
            tool_record: dict = {
                "tool": tool_name,
                "args": tool_args,
                "status": "completed",
            }

            try:
                print(f"Calling tool {tool_name}({tool_args})")
                result = execute_tool(tool_name, tool_args)
                tool_record["result"] = result
            except Exception as e:
                result = f"Tool error: {str(e)}"
                tool_record["status"] = "error"
                tool_record["error"] = str(e)

            recorded_tool_calls.append(tool_record)

            history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": json.dumps(result),
            })