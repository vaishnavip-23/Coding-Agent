from functions.get_files_info import get_files_info

def main():
    working_directory="calculator"

    root_contents=get_files_info(working_directory)
    print(root_contents)

    pkg_contents=get_files_info(working_directory, "pkg")
    print(pkg_contents)

    pkg_contents=get_files_info(working_directory, "/bin")
    print(pkg_contents)

    pkg_contents=get_files_info(working_directory, "../")
    print(pkg_contents)

main()