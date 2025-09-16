import os
from config import MAX_WRITE_CHARS
from google.genai import types


def write(working_directory: str, file_path: str, content: str):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    parent_dir = os.path.dirname(abs_file_path)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            return f"Could not create directory:{parent_dir}, error:{e}"
    try:
        if len(content) > MAX_WRITE_CHARS:
            return f"Error: content exceeds MAX_WRITE_CHARS ({MAX_WRITE_CHARS})."
        with open(abs_file_path, 'w') as file:
            file.write(content)
        return f'File "{file_path}" ({len(content)}) written successfully'
    except Exception as e:
        return f"Could not write to file:{abs_file_path}, error:{e}"


schema_write = types.FunctionDeclaration(
    name="write",
    description="Creates or overwrites a file within the working directory (size-limited).",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(type=types.Type.STRING, description="File to write"),
            "content": types.Schema(type=types.Type.STRING, description="Content to write"),
        },
    ),
)


