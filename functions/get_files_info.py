# Building Tool #1: Get Files Info

import os

def get_files_info(working_directory, directory="."):
    abs_working_directory=os.path.abspath(working_directory)
    abs_directory=os.path.abspath(os.path.join(working_directory, directory))
    if not abs_directory.startswith(abs_working_directory):
        return f'Error: "{directory}" is not in the working directory'
    
    final_response=""
    contents=os.listdir(abs_directory)
    for content in contents:
        content_path=os.path.join(abs_directory, content)
        is_directory=os.path.isdir(content_path)
        size=os.path.getsize(content_path)
        final_response+=f"-{content} : file_size={size} bytes, is_directory={is_directory}\n"

    return final_response