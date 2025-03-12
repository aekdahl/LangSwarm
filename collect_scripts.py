import os

# Function to write all files into a single output file
def collect_scripts(start_folder="START_FOLDER", output_file="collected_scripts.txt", include_root_files=False):
    # Determine the repository root and the start path
    repo_root = os.getenv("GITHUB_WORKSPACE", os.getcwd())
    start_path = os.path.join(repo_root, start_folder)

    if not os.path.exists(start_path):
        print(f"Error: The folder '{start_folder}' does not exist.")
        return

    total_length = 0  # Variable to track the total length of the document

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Include files from the root folder of the repository if the flag is set
        if include_root_files:
            for file in os.listdir(repo_root):
                file_path = os.path.join(repo_root, file)
                if os.path.isfile(file_path) and not file.startswith("."):  # Exclude hidden files
                    try:
                        # Write the relative file name and path as a header
                        relative_path = os.path.relpath(file_path, repo_root)
                        outfile.write(f"\n{'-'*80}\n")
                        outfile.write(f"File: {relative_path}\n")
                        outfile.write(f"{'-'*80}\n\n")

                        # Read the file content and write it
                        with open(file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()
                            total_length += len(content)
                            outfile.write(content)
                            outfile.write("\n\n")
                    except Exception as e:
                        # Log files that couldn't be read
                        error_message = f"[ERROR READING FILE: {file} - {e}]\n\n"
                        total_length += len(error_message)
                        outfile.write(error_message)

        # Walk through the specified folder and its subfolders
        for root, _, files in os.walk(start_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, start_path)

                try:
                    # Write the relative file name and path as a header
                    outfile.write(f"\n{'-'*80}\n")
                    outfile.write(f"File: {relative_path}\n")
                    outfile.write(f"{'-'*80}\n\n")

                    # Read the file content and write it
                    with open(file_path, "r", encoding="utf-8") as infile:
                        content = infile.read()
                        total_length += len(content)
                        outfile.write(content)
                        outfile.write("\n\n")
                except Exception as e:
                    # Log files that couldn't be read
                    error_message = f"[ERROR READING FILE: {relative_path} - {e}]\n\n"
                    total_length += len(error_message)
                    outfile.write(error_message)

    # Prepend the total document length to the file
    prepend_length_comment(output_file, total_length)


def prepend_length_comment(output_file, total_length):
    """
    Prepend a comment with the total document length to the output file.
    """
    with open(output_file, "r+", encoding="utf-8") as f:
        content = f.read()
        f.seek(0, 0)  # Move to the start of the file
        f.write(f"# Total Document Length: {total_length} characters\n\n")
        f.write(content)


if __name__ == "__main__":
    output_filename = "collected_scripts.txt"
    start_folder = "langswarm"  # Specify the start folder (e.g., "/" for the root of the repository)
    include_root = True  # Set this flag to True to include files in the repository root folder
    print(f"Collecting scripts from '{start_folder}' into {output_filename}...")
    collect_scripts(start_folder=start_folder, output_file=output_filename, include_root_files=include_root)
    print(f"All scripts have been collected into {output_filename}.")
