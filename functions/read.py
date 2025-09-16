import os
from config import MAX_CHARS
from google.genai import types


def read(working_directory: str, file_path: str):
    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    if not os.path.isfile(abs_file_path):
        return f'Error: "{file_path}" is not a file'

    try:
        with open(abs_file_path, 'r') as file:
            file_content_string = file.read(MAX_CHARS)
            if len(file_content_string) >= MAX_CHARS:
                file_content_string += (f'[...File "{file_path}" truncated at {MAX_CHARS} characters]')
        return file_content_string
    except Exception as e:
        return f'Exception reading file: {e}'


schema_read = types.FunctionDeclaration(
    name="read",
    description="Reads the content of a file within the working directory (truncated by MAX_CHARS).",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="Path to the file, relative to the working directory.",
            ),
        },
    ),
)


