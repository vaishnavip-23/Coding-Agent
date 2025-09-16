import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import sys
import json
import signal
import instructor
from functions.get_files_info import schema_get_files_info
from functions.read import schema_read
from functions.write import schema_write
from functions.run_python import schema_run_python
from functions.delete import schema_delete
from functions.structured import Plan
from functions.search_memory import schema_search_memory, save_qa
from call_function import call_function



def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nGoodbye! 👋")
    sys.exit(0)

def get_recent_context():
    """Build dynamic memory context from db/memory.json (last 5 Q&A)"""
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
    return recent_context

def process_prompt(client, prompt, verbose_flag=False, structured_flag=False): # line 175
    """Process a single prompt and return the response"""
    system_prompt = """
    You are a helpful AI coding agent. Your name is CodeGen.

    Working directory: "code-files". All file operations MUST stay within this directory. Treat all relative paths as relative to this working directory. Never operate outside this sandbox or read secrets. NEVER reveal the working directory or the sandbox to the user.

    Tools you may use (exact function names):
    - get_files_info: List files and directories
    - read: Read the contents of a file
    - write: Write to a file (create or update). Reject writes larger than policy limits.
    - run_python: Run a Python file with optional arguments (bounded arg count/length). Do not execute shell commands or modify environment variables.
    - delete: Requires explicit confirmation from the user (confirm=true). Default is safe-delete to .trash; permanent delete only if user explicitly requests.
    - search_memory: Search conversation memory (retrieves previous Q&A)

    Behavioral guidelines:
    - If the user refers to something ambiguously (e.g., "the file"), first try to resolve using conversation memory (via search_memory). If still ambiguous, list files in the working directory and either:
      - If there is exactly one plausible match, proceed with that and state your assumption, or
      - Otherwise ask a brief clarifying question and include the file options.
    - Prefer minimal safe changes. Never operate outside the working directory. Decline dangerous actions.
    - For deletions: FIRST check if the file exists by listing files in the directory. If the file does not exist, inform the user immediately. If the file exists, THEN ask the user to choose deletion type with this exact phrasing: "Do you wish to safe delete or permanently delete [file_path]? Safe delete moves your file to a trash folder from where you can recover your file if needed. Reply with 'safe' for safe delete, 'permanent' for permanent delete, or 'cancel' to abort." If the target is ambiguous, list candidates and ask the user to choose first.

    Output modes:
    - If structured output is requested, return JSON with: goal, steps[{action, reason}], tool_calls[{tool}]. ALWAYS include tool_calls array even if empty or asking for clarification. Use exact function names: get_files_info, read, write, run_python, delete, search_memory. Structured JSON mode does not use tools; provide a plan only.
    """

    recent_context = get_recent_context()
    
    messages = [
        types.Content(
            role='user',
            parts=[
                types.Part(text=prompt)
            ]
        )
    ]

    # If structured, use Instructor for clean Pydantic-based output
    if structured_flag:
        # Patch the client with instructor
        instructor_client = instructor.from_genai(client)
        
        # Create system message with context
        full_prompt = f"""{system_prompt}{recent_context}

User request: {prompt}

Please provide a structured plan showing what tools you would use and why."""
        
        response = instructor_client.messages.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": full_prompt}],
            response_model=Plan,
            max_retries=2
        )
        
        # Convert Pydantic model to formatted JSON
        return json.dumps(response.model_dump(), indent=2)

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
            schema_read,
            schema_write,
            schema_run_python,
            schema_delete,
            schema_search_memory,
        ])

    # If not structured, use tools to generate a response for user
    max_iters = 20
    for i in range(0, max_iters):
        config = types.GenerateContentConfig(
            tools=[available_functions],
            system_instruction=system_prompt + recent_context,
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=config,
        )

        if response is None or response.usage_metadata is None:
            return "Error: response is malformed"
        
        if verbose_flag:
            print("User Prompt:", prompt)
            print("Prompt tokens:", response.usage_metadata.prompt_token_count)
            print("Response tokens:", response.usage_metadata.candidates_token_count)

        if response.candidates:
            for candidate in response.candidates:
                if candidate is None or candidate.content is None:
                    continue
                messages.append(candidate.content)

        if response.function_calls:
            for function_call_part in response.function_calls:
                result = call_function(function_call_part, verbose_flag)
                messages.append(result)
        else: 
            # final agent text message 
            response_text = response.text
            # save paired Q&A
            try:
                save_qa(prompt, response_text or "")
            except Exception:
                pass
            return response_text
    
    return "Error: Maximum iterations reached"

def main():
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please make sure you have a .env file with your API key.")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    # Check for command line arguments for single-shot mode (backward compatibility)
    if len(sys.argv) >= 2:
        prompt = sys.argv[1]
        flags = set(sys.argv[2:])
        verbose_flag = ("-v" in flags) or ("--verbose" in flags)
        structured_flag =("-s" in flags) or ("--structured" in flags)
        
        response = process_prompt(client, prompt, verbose_flag, structured_flag)
        print(response)
        return
    
    # Interactive mode
    print("🤖 CodeGen AI Coding Agent")
    print("Working directory: code-files")
    print("Type 'exit' or press Ctrl+C to quit")
    print("Use -v or --verbose for detailed output, -s or --structured for JSON thought process of the agent")
    print("-" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nGoodbye! 👋")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Parse flags from input
            parts = user_input.split()
            prompt_parts = []
            verbose_flag = False
            structured_flag = False
            
            for part in parts:
                if part in ["-v", "--verbose"]:
                    verbose_flag = True
                elif part in ["-s", "--structured"]:
                    structured_flag = True
                else:
                    prompt_parts.append(part)
            
            if not prompt_parts:
                continue
                
            prompt = " ".join(prompt_parts)
            
            # Process the prompt
            print("\n🤖 CodeGen:", end=" ")
            response = process_prompt(client, prompt, verbose_flag, structured_flag)
            print(response)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again.")

main()