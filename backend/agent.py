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
        )
    }
]

CONVERSATIONS: Dict[str, List[dict]] = {}

def chat(query: str, tools: list, execute_tool, conversation_id: str = "default") -> str:
    
    if conversation_id not in CONVERSATIONS:
        CONVERSATIONS[conversation_id] = SYSTEM_PROMPT.copy()

    history = CONVERSATIONS[conversation_id]
    history.append({'role': 'user', 'content': query})
    
    response = client.chat.completions.create(
        model = 'gpt-4o-mini',
        messages = history,
        tools = tools,
        max_completion_tokens = 500
    )

    while True:

        message = response.choices[0].message

        if not message.tool_calls:
            history.append({'role': 'assistant', 'content': message.content})
            return message.content

        history.append({
            'role': 'assistant',
            'content': message.content or "",
            "tool_calls": message.tool_calls
        })

        for tool_call in message.tool_calls:

            tool_id = tool_call.id
            tool_args = json.loads(tool_call.function.arguments)
            tool_name = tool_call.function.name

            print(f"Calling tool {tool_name}({tool_args})")
            result = execute_tool(tool_name, tool_args)

            history.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": json.dumps(result),
            })

        response = client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = history,
            tools = tools,
            max_completion_tokens = 500
        )