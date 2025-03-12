from types import SimpleNamespace

components = SimpleNamespace(
    instructions = """Usage Instructions:
    
    - create_file: Create a new file with content.
     - Important: Include complete content without truncation.
     - Parameters:
       - `filename` (str): File name of the file.
       - `content` (str): Content of the file.
    
    - read_file: Read the contents of a file.
     - Parameters:
       - `filename` (str): File name of the file.
    
    - update_file: Append or overwrite content in an existing file.
     - Important: Include complete content without truncation.
     - Parameters:
       - `filename` (str): File name of the file.
       - `content` (str): Content of the file.
       - `append` (bool): Append content, defaults to True.
    
    - delete_file: Delete a file.
     - Parameters:
       - `filename` (str): File name of the file.
    
    - list_files: List all files in the directory.
    
    - list_all_files_and_folders: List all files and folders in a given directory..
     - Parameters:
       - `base_dir` (str): The base directory to list files and folders from.
       - `recursive` (bool): If True, list all files and folders recursively.
       
    - help: Get help on how to use the tool.
    """,
    examples="""Example:
- To read a file if the tool name is `filesystem_tool`:

START>>>
{
  "calls": [
    {
      "type": "tool", 
      "method": "execute",
      "instance_name": "filesystem_tool",
      "action": "read_file",
      "parameters": {"filename": "hello_world.txt"}
    }
  ]
}
<<<END
"""
)

ToolSettings = SimpleNamespace(
    instructions=f"{components.instructions}\n\n{components.examples}"
)