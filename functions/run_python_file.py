import os
import subprocess
from config import MAX_RUN_ARGS, MAX_ARG_LEN
from google.genai import types


def run_python_file(working_directory:str, file_path:str,args=[]):
    abs_working_dir=os.path.abspath(working_directory)
    abs_file_path=os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'
    if not file_path.endswith('.py'):
        return f'Error: "{file_path}" is not a Python file'
    try:
        if args is None:
            args = []
        if not isinstance(args, list) or any(not isinstance(a, str) for a in args):
            return 'Error: "args" must be a list of strings'
        if len(args) > MAX_RUN_ARGS:
            return f"Error: too many args (>{MAX_RUN_ARGS})"
        for a in args:
            if len(a) > MAX_ARG_LEN:
                return f"Error: arg exceeds MAX_ARG_LEN ({MAX_ARG_LEN})"
        final_args=['python3', file_path]
        final_args.extend(args)
        output = subprocess.run(
            final_args,
            cwd=abs_working_dir,
            timeout=30,
            capture_output=True,
            text=True
        )
        final_string = f"STDOUT:{output.stdout}\nSTDERR:{output.stderr}\n"
        if output.stdout == "" and output.stderr == "":
            final_string = "No output produced.\n"
        if output.returncode != 0:
            final_string += f"Process exited with code {output.returncode}"
        return final_string
    except Exception as e:
        return f'Error: "{file_path}" ran with error: {e}'

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Runs a Python file with the python3 interpreter. Accepts additional CLI args as an optional array.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The file to run, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                description="An optional array of strings to be used as the CLI args for the python files",
                items=types.Schema(
                    type=types.Type.STRING
                )
            ),
        },
    ),
)