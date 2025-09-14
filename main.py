import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
from functions.get_files_info import schema_get_files_info
from functions.get_files_content import schema_get_files_content
from functions.write_file import schema_write_file
from functions.run_python_file import schema_run_python_file
from functions.structured import schema_plan
from call_function import call_function



def main():
    
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client=genai.Client(api_key=api_key)

    system_prompt= """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read the contents of a file
    - Write to a file (create or update)
    - Run a Python file with optional arguments

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    If structured output is requested, return JSON with: goal, steps[{action, reason}], tool_calls[{tool, params_json}].
    Note: Structured JSON mode does not use tools; provide a plan only.
    """

    # sys.argv variable is a list of strings representing the command-line arguments passed to the script. First element is the script name, rest are the arguments passed to the script.

    if len(sys.argv)<2:
        print("I didn't receieve a prompt!")
        sys.exit(1)

    prompt=sys.argv[1]
    flags = set(sys.argv[2:])
    verbose_flag = ("-v" in flags) or ("--verbose" in flags)
    structured_flag = ("--structured" in flags)

    messages=[
        types.Content(
            role='user',
            parts=[
                types.Part(text=prompt)
            ]
        )
    ]

    # If structured, make a single JSON response call without tools
    if structured_flag:
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=schema_plan(),
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config,
        )
        print(response.text)
        return

    available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_files_content,
        schema_write_file,
        schema_run_python_file,
    ])

    max_iters=20
    for i in range(0,max_iters):

        config=types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config,
        )

        if response is None or response.usage_metadata is None:
            print("response is malformed")
            return
        if verbose_flag:
            print("User Prompt:",prompt)
            print(messages)
            print(sys.argv[1])
            print("Prompt tokens:",response.usage_metadata.prompt_token_count)
            print("Response tokens:",response.usage_metadata.candidates_token_count)

        if response.candidates:
            for candidate in response.candidates:
                if candidate is None or candidate.content is None:
                    continue
                messages.append(candidate.content)

        if response.function_calls:
            for function_call_part in response.function_calls:
                result=call_function(function_call_part, verbose_flag)
                messages.append(result)
        else: 
            # final agent text message 
            print(response.text)
            return
            

    # print(get_files_info("functions"))

main()