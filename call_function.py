from functions.get_files_info import get_files_info
from functions.read import read
from functions.write import write
from functions.run_python import run_python
from functions.delete import delete
from functions.search_memory import search_memory
from google.genai import types

working_directory="code-files"

def call_function(function_call_part, verbose=False):
    if verbose :
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")



    result=""
    if function_call_part.name == "get_files_info":
        result = get_files_info(working_directory,**function_call_part.args)
    if function_call_part.name == "read":
        result = read(working_directory,**function_call_part.args)
    if function_call_part.name == "write":
        result = write(working_directory,**function_call_part.args)
    if function_call_part.name == "run_python":
        result = run_python(working_directory,**function_call_part.args)
    if function_call_part.name == "delete":
        result = delete(working_directory,**function_call_part.args)
    if function_call_part.name == "search_memory":
        result = search_memory(**function_call_part.args)
    if result=="":
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_call_part.name,
                    response={"error": f"Unknown function: {function_call_part.name}"},
                )
            ],
        )
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_call_part.name,
                response={"result": result},
            )
        ],
    )



    