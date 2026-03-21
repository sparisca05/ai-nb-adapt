from openai import OpenAI

client = OpenAI()

history = []

def chat(query: str, tools: list, execute_tool):

    history.append({'role': 'user', 'content': query})
    
    response = client.responses.create(model = 'gpt-4o-mini', input = history, tools = tools)

    process_query_flag = True
    while process_query_flag:

        for content in response.output:
            if content.type == 'message':

                print(content.content)
                history.append({'role': 'assistant', 'content': content.content})

                if len(response.output) == 1:
                    process_query_flag = False

            elif content.type == 'function_call':

                history.append({'role': 'assistant', 'content': [content]})

                tool_id = content.call_id
                tool_args = content.arguments
                tool_name = content.name
                print(f"Calling tool {tool_name} with args {tool_args}")

                result = execute_tool(tool_name, tool_args)
                history.append({"role": "user",
                                  "content": [
                                      {
                                          "type": "function_call_output",
                                          "call_id": tool_id,
                                          "output": result
                                      }
                                  ]
                                })
                response = client.responses.create(model = 'gpt-4o-mini', input = history, tools = tools)

                if len(response.output) == 1 and response.output[0].type == "text":
                    print(response.output[0].text)
                    process_query_flag = False