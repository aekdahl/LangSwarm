import json
import re
import inspect

from typing import Type, Optional, List

from langswarm.core.utils.utilities import Utils
from langchain_community.utilities.github import GitHubAPIWrapper
from langswarm.memory.adapters.database_adapter import DatabaseAdapter
from ..base import BaseTool
from .config import ToolSettings

class GitHubTool(BaseTool):
    """
    A tool for interacting with GitHub repositories to fetch, update, and manage source code.
    
    This tool allows the agent to:
    - Fetch code files or repositories from GitHub and store them in a vector database for efficient querying.
    - Query and retrieve relevant code snippets from stored data.
    - Create, update, and delete files in GitHub repositories.
    - Create branches and pull requests to manage code contributions.
    
    Use cases:
    - Extracting code for analysis or retrieval.
    - Updating files with comments, docstrings, or refactored code.
    - Creating new branches or pull requests for code changes.
    
    """
    def __init__(
        self, 
        identifier,
        github_repository, 
        github_app_id, 
        github_app_private_key,
        adapter: Optional[Type[DatabaseAdapter]] = None,
        agents: Optional[List[str]] = None
    ):      
        if adapter is not None and not isinstance(adapter, DatabaseAdapter):
            raise TypeError(
                f"Argument 'adapter' must be a subclass of DatabaseAdapter if provided, got {type(adapter).__name__}")

        super().__init__(
            name="GitHubTool",
            description=(
                f"Use this tool to interact with the GitHub repository `{github_repository.split('/')[-1]}`, "
                f"owned by `{github_repository.split('/')[0]}`. The connection is already configured and ready. "
                "Supports fetching files and write them to database, creating branches, pull requests, and file operations."
            ),
            instruction=ToolSettings.instructions
        )
        self.github_tool = GitHubAPIWrapper(
            github_repository=github_repository, 
            github_app_id=github_app_id, 
            github_app_private_key=github_app_private_key
        )
        
        self.identifier = identifier
        self.brief = (
            f"Interact with the GitHub repository `{github_repository.split('/')[-1]}`, "
            f"owned by `{github_repository.split('/')[0]}`. "
            f"Use the help action to get instructions: execute_tool:{identifier}|help|"+"{}"
        )

        self.vectorstore = adapter
        self.agents = agents
        self.utils = Utils()
    
    def _safe_call(self, func, *args, **kwargs):
        """Safely calls a function and detects incorrect arguments."""
        # ToDo: Now it returns if any argument is invalid, it should only return if
        # required arguments are missing, else we just skip invalid ones.

        func_signature = inspect.signature(func)
        accepted_args = func_signature.parameters.keys()  # Valid argument names

        # Separate valid and invalid arguments
        valid_kwargs = {k: v for k, v in kwargs.items() if k in accepted_args}
        invalid_kwargs = {k: v for k, v in kwargs.items() if k not in accepted_args}

        # If there are invalid arguments, return an error message instead of calling
        if invalid_kwargs:
            return f"Error: Unexpected arguments {list(invalid_kwargs.keys())}. Expected: {list(accepted_args)}"

        # Call the function with only valid arguments
        return func(*args, **valid_kwargs)

    def run(self, payload = {}, action="fetch_and_store", retries=3):
        """
        Execute the tool's actions with automatic retries on failure.

        :param payload: dict - The input query or tool details.
        :param action: str - The action to perform: 'fetch_and_store' or other available actions.
        :param retries: int - Number of retries before failing.
        :param info: str - Additional information for debugging.

        :return: str or List[str] - The result of the action.
        """
        if payload is None:
            return (
                f"The payload was not proper JSON. Make sure the payload part is valid json and try again."
            )
        
        if isinstance(self.agents, list) and len(self.agents) == 1:
            self.agents[0].reset()
            tool_call = "{" + f'"action": "{action}", "payload": {payload}' + "}"
            review_query = f"{ToolSettings.review_prompt}\n\n---\n\nProvided input: `{tool_call}`"
            
        retries = retries if self.agents else 1  # If no agents, only attempt once
        
        for attempt in range(1, retries + 1):
            response = None

            # Map actions to corresponding functions
            action_map = {
                "help": self._help,
                "fetch_and_store": self.fetch_and_store_code,
                "create_branch": self.create_branch,
                "create_pull_request": self.create_pull_request,
                "read_file": self.read_file,
                "create_file": self.create_file,
                "update_file": self.update_file,
                "delete_file": self.delete_file,
                "set_active_branch": self.set_active_branch,
                "list_all_files": self.list_all_files,
                "replace_file": self.replace_file,
                "list_branches_in_repo": self.list_branches_in_repo,
                "list_issues": self.list_issues,
                "get_issue": self.get_issue,
                "comment_on_issue": self.comment_on_issue,
                "close_issue": self.close_issue,
            }

            # Execute the corresponding action
            if action in action_map:
                if isinstance(self.agents, list) and len(self.agents) == 1:
                    # TODO: Implement multi Tool Agents when they exist.

                    review = self._parse_tool_agent_output(self.agents[0].chat(review_query))

                    if review['status'] == 'error':
                        return (
                            f"{review['message']}.\n\n"
                            f"{review.get('errors', '')}"
                        )
                    elif review['status'] == 'corrected':
                        payload = review.get('payload', payload)
                    
                #response = action_map[action](**payload)
                response =  self._safe_call(action_map[action], **payload)
            else:
                return (
                    f"Unsupported action: {action}. Available actions are:\n\n"
                    f"{self.instruction}"
                )

            # Check if the response is successful
            if self.agents:  # Implement `is successful` check
                review_query = f"{ToolSettings.evaluate_response_prompt}\n\n---\n\nThe response: `{response}`"
                evaluate = self._parse_tool_agent_output(self.agents[0].chat(review_query))
                
                if evaluate['status'] == 'error':
                    review_query = f"{evaluate['message']}"
                else:
                    return response  # Return if no error

            # If not successful and retries remain, log and retry
            if attempt < retries:
                print(f"Attempt {attempt} failed. Retrying {retries - attempt} more times...")

        # If all retries fail, return the last response or an error message
        return response or f"Action '{action}' failed after {retries} retries."
       
    def set_active_branch(self, branch="main"):
        """
        Set the active branch.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        action = self.github_tool.set_active_branch(branch_name=branch)
        # print(action)
        return action
    
    def list_branches_in_repo(self):
        """
        List all branches.
        :return: str - String of branches.
        """
        action = self.github_tool.list_branches_in_repo()
        # print(action)
        return action
    
    def list_issues(self):
        """
        List all open issues.
        :return: str - String of issues.
        """
        action = self.github_tool.get_issues()
        # print(action)
        return action
    
    def get_issue(self, issue_number: int):
        """
        Get an issue by issue number.
        :return: dict.
        """
        action = self.github_tool.get_issue(issue_number)
        # print(action) 
        return action
    
    def comment_on_issue(self, issue_number: int, comment: str):
        """
        Comment an issue by issue number.
        :return: str.
        """
        issue = self.github_tool.github_repo_instance.get_issue(number=issue_number)
        return issue.create_comment(comment)
    
    def close_issue(self, issue_number: int):
        """
        Close an issue by issue number.
        :return: str.
        """
        issue = self.github_tool.github_repo_instance.get_issue(number=issue_number)
        return issue.edit(state="closed")
    
    def create_pull_request(self, pr_title, pr_body):
        """
        Makes a pull request from the bot's branch to the base branch
        Parameters:
            pr_query(str): a string which contains the PR title
            and the PR body. The title is the first line
            in the string, and the body are the rest of the string.
            For example, "Updated README\nmade changes to add info"
        Returns:
            str: A success or failure message
        """
        pr_query = f"{pr_title}\n{pr_body}"
    
        action = self.github_tool.create_pull_request(pr_query)
        # print(action)
        return action
        
    def read_file(self, file_path):
        """
        Read a file from the repository in a case-insensitive manner.
        Read a file from this agent's branch, defined by self.active_branch,
        which supports PR branches.
        Parameters:
            file_path(str): the file path
        Returns:
            str: The file decoded as a string, or an error message if not found
        """
        # Extract the directory and file name
        directory = "/".join(file_path.split("/")[:-1])  # Get the directory path (if any)
        file_name = file_path.split("/")[-1]            # Get the file name

        # Get all files in the directory
        contents = self.github_tool.github_repo_instance.get_contents(
            directory or "", ref=self.github_tool.active_branch)
   
        for content_file in contents:
            if content_file.name.lower() == file_name.lower():
                file_content = self.github_tool.read_file(file_path=content_file.path)
                return file_content  # Return the matching file object

        return 'File not found'
        
    def create_file(self, file_path, content):
        """
        Creates a new file on the Github repo
        Parameters:
            file_query(str): a string which contains the file path
            and the file contents. The file path is the first line
            in the string, and the contents are the rest of the string.
            For example, "hello_world.md\n# Hello World!"
        Returns:
            str: A success or failure message
        """
        file_query = f"{file_path}\n{content}"
        
        check_format = self._validate_filepath_format(file_query)
        if check_format is not None:
            return check_format
        
        action = self.github_tool.create_file(file_query)
        print("Create file completed", action)
        return action
        
    def update_file(self, file_path, old_content, new_content):
        """
        Updates a file with new content.
        Ensures there is a newline after the file path before content changes.
        Parameters:
            file_query(str): Contains the file path and the file contents.
                The old file contents is wrapped in OLD <<<< and >>>> OLD
                The new file contents is wrapped in NEW <<<< and >>>> NEW
                For example:
                /test/hello.txt
                OLD <<<<
                Hello Earth!
                >>>> OLD
                NEW <<<<
                Hello Mars!
                >>>> NEW
        Returns:
            A success or failure message
        """
        file_query = f"{file_path}\n OLD <<<< {old_content} >>>> OLD NEW <<<< {new_content} >>>> NEW"
    
        check_format = self._validate_filepath_format(file_query)
        if check_format is not None:
            return check_format

        # Regex to detect cases where the file path is immediately followed by "OLD <<<<"
        pattern = r"([a-zA-Z0-9_/.-]+)(?<!\n) (OLD <<<<)"

        # Replace with file path + newline + content indicator
        fixed_output = re.sub(pattern, r"\1\n\2", file_query)
    
        action = self.github_tool.update_file(fixed_output)
        print("Update file completed", action)
        return action
    
    def replace_file(self, file_path, content):
        """
        Updates an entire file in the Github repo
        Parameters:
            file_query(str): a string which contains the file path
            and the file contents. The file path is the first line
            in the string, and the contents are the rest of the string.
            For example, "hello_world.md\n# Hello World!"
        Returns:
            str: A success or failure message
        """
        file_query = f"{file_path}\n{content}"
        
        check_format = self._validate_filepath_format(file_query)
        if check_format is not None:
            return check_format
        
        file_path: str = file_query.split("\n", 1)[0]
        file_content: str = file_query.split("\n", 1)[-1]
        action = self.github_tool.github_repo_instance.update_file(
            path=file_path,
            message="Update " + str(file_path),
            content=file_content,
            branch=self.github_tool.active_branch,
            sha=self.github_tool.github_repo_instance.get_contents(
                file_path, ref=self.github_tool.active_branch
            ).sha,
        )
        print("Replaced file completed", action)
        return action
        
    def delete_file(self, file_path):
        """
        Deletes a file from the repo
        Parameters:
            file_path(str): Where the file is
        Returns:
            str: Success or failure message
        """
        action = self.github_tool.delete_file(file_path)
        print("Delete file completed", action)
        return action

    def create_branch(self, proposed_branch_name):
        """
        Create a new branch, and set it as the active bot branch.
        Equivalent to `git switch -c proposed_branch_name`
        If the proposed branch already exists, we append _v1 then _v2...
        until a unique name is found.

        Returns:
            str: A plaintext success message.
        """
        action = self.github_tool.create_branch(proposed_branch_name)
        print(action)
        return action

    def _read_and_store(self, file_path, branch="main"):
        if hasattr(file_path, 'path'):
            file_path = file_path.path
        file_content = self.github_tool.read_file(file_path=file_path)
        metadata = {"repo": self.github_tool.github_repository, "path": file_path, "branch": branch}
        document = {"key": file_path, "text": file_content, "metadata": metadata}
        self.vectorstore.add_documents([document])
        print(
            f"Code from {file_path} in {self.github_tool.github_repository} (branch: {branch}) has been processed and stored.")

    def fetch_and_store_code(self, file_path=None, branch="main"):
        """
        Fetch code from GitHub and store it in the vector database.
        :param file_path: str - The path to the file in the repository.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        print(self.github_tool.set_active_branch(branch_name=branch))
        if file_path:
            self._read_and_store(file_path, branch=branch)
        else:
            contents = self.github_tool.github_repo_instance.get_contents("", ref=self.github_tool.active_branch)
            while contents:
                file_path = contents.pop(0)
                if file_path.type == "dir":
                    contents.extend(
                        self.github_tool.github_repo_instance.get_contents(
                            file_path.path, ref=self.github_tool.active_branch))
                else:
                    self._read_and_store(file_path, branch=branch)
        
        return 'done'

    def list_all_files(self, file_path=None, branch="main"):
        """
        Fetch code from GitHub and store it in the vector database.
        :param file_path: str - The path to the file in the repository.
        :param branch: str - The branch to fetch from (default: 'main').
        :return: str - Success message.
        """
        print(self.github_tool.set_active_branch(branch_name=branch))
        files = []
        
        if file_path:
            # Extract the directory and file name
            directory = "/".join(file_path.split("/")[:-1])  # Get the directory path (if any)
            file_name = file_path.split("/")[-1]            # Get the file name

            # Get all files in the directory
            contents = self.github_tool.github_repo_instance.get_contents(
                directory or "", ref=self.github_tool.active_branch)
        else:
            # Get all files
            contents = self.github_tool.github_repo_instance.get_contents(
                "", ref=self.github_tool.active_branch)
            
        while contents:
            file_path = contents.pop(0)
            if file_path.type == "dir":
                contents.extend(
                    self.github_tool.github_repo_instance.get_contents(
                        file_path.path, ref=self.github_tool.active_branch))
            else:
                files.append(file_path.path)
        
        return json.dumps(files)
    
    def _help(self):
        return self.instruction

    def _validate_filepath_format(self, text: str) -> Optional[str]:
        """
        Checks if the given text starts with a valid filepath and ensures it ends with a newline (\n).

        Returns:
        - False if the text does not start with a valid filepath.
        - "Filepath does not end with a newline." if a filepath is detected but is not followed by \n.
        - True if the filepath is correctly formatted.
        """
        # Regex pattern for a valid filepath (handles Windows and Unix paths)
        # filepath_pattern = re.compile(r"^([a-zA-Z]:\\[^\n\r]+|\/[^ \n\r]+)")
        filepath_pattern = re.compile(r"^(?:[a-zA-Z]:\\|\/|(?:\.\.?\/)?)[^\n\r ]+\.[a-zA-Z0-9]+")

        match = filepath_pattern.match(text)

        if not match:
            return f"Incorrect call format, no valid filepath at the start of {text}"  # No valid filepath at the start

        filepath = match.group(0)  # Extract matched filepath

        # Check if the filepath is immediately followed by a newline
        if not text.startswith(filepath + "\n"):
            return "Incorrect call format, the filepath does not end with a newline (\n)."

        return None
    
    def _parse_tool_agent_output(self, response_str):
        """
        Attempts to parse a tool call response from a JSON string.
        If `json.loads` fails, extracts key values manually.

        :param response_str: str - The JSON response as a string.
        :return: dict - Parsed response.
        """
        try:
            # First, try normal JSON parsing
            return json.loads(response_str)

        except json.JSONDecodeError:
            print("Warning: JSON parsing failed. Attempting backup extraction.")

            # Initialize extracted values
            extracted_data = {"status": "error", "message": "Failed to extract values."}

            # Extract `status`
            status_match = re.search(r'"status"\s*:\s*"([^"]+)"', response_str)
            if status_match:
                extracted_data["status"] = status_match.group(1)

            # Extract `message`
            message_match = re.search(r'"message"\s*:\s*"([^"]+)"', response_str)
            if message_match:
                extracted_data["message"] = message_match.group(1)

            if extracted_data["status"] == 'corrected':
                # Extract `action`
                action_match = re.search(r'"action"\s*:\s*"([^"]+)"', response_str)
                if action_match:
                    extracted_data["action"] = action_match.group(1)

                # Extract `payload` (attempts to capture everything inside `{}` after `"payload"`)
                payload_match = re.search(r'"payload"\s*:\s*(\{.*?\})', response_str, re.DOTALL)
                if payload_match:
                    try:
                        extracted_data["payload"] = self.utils.safe_json_loads(payload_match.group(1))
                    except json.JSONDecodeError:
                        extracted_data["payload"] = "Malformed payload"
                else:
                    extracted_data["payload"] = {}

            # Extract `errors` (if present)
            errors_match = re.search(r'"errors"\s*:\s*(\[[^\]]+\])', response_str, re.DOTALL)
            if errors_match:
                try:
                    extracted_data["errors"] = json.loads(errors_match.group(1))
                except json.JSONDecodeError:
                    extracted_data["errors"] = "Malformed errors"

            return extracted_data