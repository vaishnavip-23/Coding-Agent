# from functions.get_files_info import get_files_info
# from functions.get_files_content import get_files_content
from functions.write_file import write_file

def main():
    working_directory="calculator"
    print(write_file(working_directory, "", "Hello, World!"))

main()