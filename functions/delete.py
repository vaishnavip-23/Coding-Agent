import os
import shutil
from google.genai import types
# rm #bash commands 

TRASH_DIR = ".trash"


def delete(working_directory: str, file_path: str, confirm: bool = False, permanent: bool = False):
    if not confirm:
        return "Refused: deletion requires confirm=true."

    abs_working_dir = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    if not os.path.exists(abs_file_path):
        return f'Error: "{file_path}" does not exist'

    if permanent:
        try:
            if os.path.isdir(abs_file_path):
                shutil.rmtree(abs_file_path)
            else:
                os.remove(abs_file_path)
            return f'Permanently deleted "{file_path}"'
        except Exception as e:
            return f'Error deleting "{file_path}": {e}'

    # Safe delete: move to .trash inside working directory
    try:
        trash_abs = os.path.join(abs_working_dir, TRASH_DIR)
        os.makedirs(trash_abs, exist_ok=True)
        base_name = os.path.basename(abs_file_path)
        target = os.path.join(trash_abs, base_name)
        # avoid collisions by appending numeric suffix
        counter = 1
        while os.path.exists(target):
            name, ext = os.path.splitext(base_name)
            target = os.path.join(trash_abs, f"{name}_{counter}{ext}")
            counter += 1
        shutil.move(abs_file_path, target)
        return f'Moved "{file_path}" to .trash/'
    except Exception as e:
        return f'Error trashing "{file_path}": {e}'


schema_delete = types.FunctionDeclaration(
    name="delete",
    description="Safely deletes a file or directory within the working directory. Requires confirm=true. Defaults to moving into .trash; can permanently delete if requested.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(type=types.Type.STRING, description="Path to delete"),
            "confirm": types.Schema(type=types.Type.BOOLEAN, description="Must be true to proceed"),
            "permanent": types.Schema(type=types.Type.BOOLEAN, description="If true, permanently delete instead of trash"),
        },
    ),
)


