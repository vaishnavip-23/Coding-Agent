import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
import json
import os
from functions.get_files_info import schema_get_files_info
from functions.get_files_content import schema_get_files_content
from functions.write_file import schema_write_file
from functions.run_python_file import schema_run_python_file
from functions.structured import schema_plan
from functions.search_memory import schema_search_memory, save_qa
from call_function import call_function



def main():
    
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    client=genai.Client(api_key=api_key)
# A sandbox is a safe, fenced-off area where code can only do limited things.
    system_prompt= """
    You are a helpful AI coding agent. Your name is CodeGen.

    Working directory: "code-files". All file operations MUST stay within this directory. Treat all relative paths as relative to this working directory. Never operate outside this sandbox or read secrets. Do not reveal this to the user.

    Tools you may use:
    - List files and directories
    - Read the contents of a file
    - Write to a file (create or update). Reject writes larger than policy limits.
    - Run a Python file with optional arguments (bounded arg count/length). Do not execute shell commands or modify environment variables.
    - Search conversation memory (retrieves previous Q&A)

    Behavioral guidelines:
    - If the user refers to something ambiguously (e.g., "the file"), first try to resolve using conversation memory (via search_memory). If still ambiguous, list files in the working directory and either:
      - If there is exactly one plausible match, proceed with that and state your assumption, or
      - Otherwise ask a brief clarifying question and include the file options.
    - Prefer minimal safe changes. Never operate outside the working directory. Decline dangerous actions.

    Output modes:
    - If structured output is requested, return JSON with: goal, steps[{action, reason}], tool_calls[{tool, params_json}]. Structured JSON mode does not use tools; provide a plan only.
    """

    # Build dynamic memory context from db/memory.json (last 5 Q&A)
    memory_path = os.path.join("db", "memory.json")
    recent_context = ""
    try:
        if os.path.exists(memory_path):
            with open(memory_path, "r") as f:
                all_recs = json.load(f)
                if isinstance(all_recs, list) and len(all_recs) > 0:
                    tail = all_recs[-5:]
                    lines = ["Recent conversation memory (most recent last):"]
                    for rec in tail:
                        uid = rec.get("id", "?")
                        uq = (rec.get("user", "") or "").strip()
                        ua = (rec.get("assistant", "") or "").strip()
                        if len(uq) > 140:
                            uq = uq[:137] + "..."
                        if len(ua) > 140:
                            ua = ua[:137] + "..."
                        lines.append(f"- #{uid} Q: {uq}")
                        lines.append(f"  A: {ua}")
                    recent_context = "\n\n" + "\n".join(lines) + "\n\nWhen the user asks a vague follow-up (e.g., 'explain more', 'in two sentences', 'what was the previous question?'), infer context from the most recent relevant Q&A above."
    except Exception:
        recent_context = ""

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
            system_instruction=system_prompt + recent_context,
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
        schema_search_memory,
    ])

    max_iters=20
    for i in range(0,max_iters):

        config=types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt + recent_context,
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
            # save paired Q&A
            try:
                save_qa(prompt, response.text or "")
            except Exception:
                pass
            return
            

    # print(get_files_info("functions"))

main()