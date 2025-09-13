import os


def write_file(working_directory, file_path, content):
    abs_working_dir=os.path.abspath(working_directory)
    abs_file_path=os.path.abspath(os.path.join(working_directory, file_path))
    if not abs_file_path.startswith(abs_working_dir):
        return f'Error: "{file_path}" is not in the working directory'
    parent_dir=os.path.dirname(abs_file_path)
    if not os.path.exists(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            return f"Could not create create directory:{parent_dir}, error:{e}"
    try:
        with open(abs_file_path, 'w') as file:
            file.write(content)
        return f'File "{file_path}" ({len(content)}) written successfully'
    except Exception as e:
        return f"Could not write to file:{abs_file_path}, error:{e}"

