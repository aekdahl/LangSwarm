
import time
# pip install pyyaml
import yaml
import ast
import json
import re
import os
import unicodedata

from ...registry.agents import AgentRegistry

class Formatting:
    def __init__(self):
        pass
    
    # ToDo: Uses the old syntax
    def _is_valid_request_calls_in_text(self, text: str) -> str:
        """
        Determines if all 'request:' calls in `text` are valid given the rules:

        1) If there's no 'request:' substring at all, it's valid (no calls).
        2) If we see `request:someword`, and 'someword' is not in (tools|rags|retrievers|plugins),
           then it's valid only if there are 0 pipes in that snippet.
        3) If we see `request:(tools|rags|retrievers|plugins)`, 
           it must have exactly one pipe in that snippet, 
           and the substring after that pipe can contain spaces or any text. 
           If 0 or 2+ pipes => invalid.

        Returns True if all calls are valid or if none exist, otherwise False.
        """

        # 1) Find each snippet that starts with 'request:' 
        pattern = re.compile(r"(request:[^\n]+?)(?=\s*request:|\Z)", re.IGNORECASE | re.DOTALL)
        snippets = pattern.findall(text)
        if not snippets:
            # No 'request:' => valid
            return None

        # 2) Validate each snippet
        for snippet in snippets:
            if not self._validate_single_request_snippet(snippet.strip()):
                return """Incorrect format detected. Please correct it.

Request format:
- `request:tools|<tool_name>` or `request:tools|<query>` → Get details about a specific tool or search for one.  
- `request:rags|<rag_name>` or `request:rags|<query>` → Retrieve details about a rag or search for one.  
- `request:plugins|<plugin_name>` or `request:plugins|<query>` → Get details about a specific plugin or search for capabilities. 

Ensure your call follows the correct format.
"""

        return None

    # ToDo: Uses the old syntax
    def _validate_single_request_snippet(self, snippet: str) -> bool:
        """
        Validates a single substring that starts with 'request:' based on the rules:

        - If snippet doesn't match "request:something", we consider it not a real request => valid.
        - Otherwise parse the word after 'request:'.
          * If that word is not in (tools|rags|retrievers|plugins) => must have 0 pipes => valid, else invalid.
          * If that word is in (tools|rags|retrievers|plugins) => must have exactly 1 pipe => valid, else invalid.
        """

        # Quick prefix check
        if not snippet.lower().startswith("request:"):
            return None # Not a 'request:' snippet => valid

        # Extract the word after 'request:' (up to space/pipe)
        match_prefix = re.match(r"^request:([^\s|]+)", snippet, re.IGNORECASE)
        if not match_prefix:
            # e.g. "request: " with a space => handle if there's a pipe => invalid, else => valid
            return not ("|" in snippet)

        found_word = match_prefix.group(1)  # e.g. 'tools', 'myword', etc.
        valid_keywords = {"tools", "rags", "retrievers", "plugins"}

        # Count total pipes in snippet
        pipe_count = snippet.count("|")

        if found_word.lower() not in valid_keywords:
            # Then must have 0 pipes
            return (pipe_count == 0)
        else:
            # found_word is in (tools|rags|retrievers|plugins)
            # must have exactly 1 pipe
            return (pipe_count == 1)

    # ToDo: Uses the old syntax
    def _is_valid_use_calls_in_text(self, text: str) -> str:
        """
        Checks whether any 'execute_(tool|rag|retriever|plugin):...' calls in `text`
        are correctly formatted. If a snippet has "execute_tool:" (or rag/retriever/plugin)
        with fewer than 2 pipes, we decide:
            - 0 pipes => non-call => valid
            - 1 pipe => partial call => invalid
            - 2+ pipes => must strictly match a valid pattern

        Returns True if all calls are valid (or no calls exist), otherwise False.
        """

        # Regex to find each snippet starting with 'execute_tool|rag|retriever|plugin:'
        pattern = re.compile(
            r"(execute_+(?:tool|rag|retriever|plugin):[^\n]+?)(?=\s*execute_+(?:tool|rag|retriever|plugin)|$)",
            re.IGNORECASE | re.DOTALL
        )

        # Extract all occurrences
        matches = pattern.findall(text)
        if not matches:
            # No 'execute_' calls => valid
            return None

        for snippet in matches:
            if not self._validate_single_use_call(snippet.strip()):
                return """Incorrect format detected. Please correct it.

Execute format:
- `execute_tool:<tool_name>|<action_name>|{params_dictionary}` → Use the named tool to perform the named action, include params if required.
- `execute_rag:<rag_name>|<action_name>|{params_dictionary}` → Use the named rag to perform the named action, include params if required.
- `execute_retriever:<retriever_name>|<action_name>|{params_dictionary}` → Use the named retriever to perform the named action, include params if required.
- `execute_plugin:<plugin_name>|<action_name>|{params_dictionary}` → Use the named plugin to perform the named action, include params if required.

Ensure your call follows the correct format.
"""

        return None

    # ToDo: Uses the old syntax
    def _validate_single_use_call(self, use_call: str) -> bool:
        """
        Validates one snippet that starts with "execute_(tool|rag|retriever|plugin):".

        - 0 pipes => treat as non-call => valid
        - 1 pipe => partial call => invalid
        - 2+ pipes => must match the final pattern:
             execute_(tool|rag|retriever|plugin):<one_word>|<one_word>|<anything>

        Returns True if valid or no actual call, otherwise False.
        """

        prefix_pattern = re.compile(r"^execute_+(tool|rag|retriever|plugin):", re.IGNORECASE)
        prefix_match = prefix_pattern.match(use_call)
        if not prefix_match:
            # Not even starting with 'execute_tool|rag...', so treat as valid
            return True

        # Count how many '|' are present
        pipe_count = use_call.count('|')

        if pipe_count == 0:
            # "execute_tool: My favorite one" => no calls => valid
            return True
        elif pipe_count == 1:
            # "execute_tool:my_favorite_one|" => partial call => invalid
            return False
        else:
            # 2 or more pipes => parse strictly with a final pattern
            valid_pattern = re.compile(
                r"^execute_+(?:tool|rag|retriever|plugin):" 
                r"([A-Za-z0-9_\-]+)\|" 
                r"([A-Za-z0-9_\-]+)\|"  # second word
                r"(.*)$",
                re.IGNORECASE
            )
            return bool(valid_pattern.match(use_call))

    def _sanitize_json_string(self, json_string: str) -> str:
        """
        Cleans and corrects common issues in a JSON string before parsing with json.loads().
        """
        # Step 1: Escape unescaped newlines inside JSON values
        json_string = re.sub(r'(?<!\\)\n', r'\\n', json_string)
        
        # Step 2: Remove trailing commas before closing brackets or braces
        json_string = re.sub(r",\s*([\]}])", r"\1", json_string)
        
        # Step 3: Detect and fix unterminated string issues
        if json_string.count('"') % 2 != 0:
            json_string = json_string.rstrip('"') + '"'
            
        # Step 4: Escape double quotes inside string values
        json_string = re.sub(r'(?<!\\)"(.*?)"(?![:,\]\}])', lambda m: f'\"{m.group(1)}\"', json_string)

        # Step 5: Balance brackets/braces (without blindly adding them)
        json_string = self._balance_brackets(json_string)

        return json_string

    def _balance_brackets(self, json_string: str) -> str:
        """
        Ensures JSON has balanced curly braces `{}` and square brackets `[]`.
        """
        open_braces = json_string.count('{')
        close_braces = json_string.count('}')
        open_brackets = json_string.count('[')
        close_brackets = json_string.count(']')

        # If there are more opens than closes, append the missing ones
        if open_braces > close_braces:
            json_string += "}" * (open_braces - close_braces)
        if open_brackets > close_brackets:
            json_string += "]" * (open_brackets - close_brackets)

        return json_string

    def escape_unescaped_quotes_in_json_values(self, json_string: str) -> str:
        """
        Escapes any unescaped double quotes inside JSON values to prevent JSONDecodeError.
        """
        pattern = re.compile(r'("[^"]*"\s*:\s*")([^"]*)(?=")', flags=re.DOTALL)

        def escape_inner_quotes(match):
            prefix = match.group(1)
            value_content = match.group(2)

            # Escape any unescaped quotes inside value_content
            escaped_value = re.sub(r'(?<!\\)"', r'\"', value_content)

            return f'{prefix}{escaped_value}'

        return pattern.sub(escape_inner_quotes, json_string)

    def _fix_trailing_commas(self, json_string: str) -> str:
        """
        Removes trailing commas in nested JSON structures that cause parsing errors.
        """
        return re.sub(r',\s*([\]}])', r'\1', json_string)

    def safe_json_loads(self, json_string: str, agent=None, **kwargs):
        """
        Safely loads a JSON string after attempting corrections.
        """
        use_agent = False
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Initial JSON parsing failed: {e}. Attempting to sanitize...")

            # Sanitize JSON
            json_string = self._sanitize_json_string(json_string)

            try:
                return json.loads(json_string)
            except json.JSONDecodeError as final_error:
                #print(f"JSON parsing still failed after sanitization: {final_error}")
                
                # Fix unescaped quotes and trailing commas
                json_string = self.escape_unescaped_quotes_in_json_values(json_string)
                json_string = self._fix_trailing_commas(json_string)

                try:
                    return json.loads(json_string)
                except json.JSONDecodeError as e:
                    error_pos = e.pos  # Character position where the error occurred
                    error_char = json_string[error_pos] if error_pos < len(json_string) else "<END>"

                    # Extract context (1 word before and after)
                    start = max(0, error_pos - 10)  # Adjust for safety
                    end = min(len(json_string), error_pos + 10)
                    context = json_string[start:end]

                    #print(f"JSON Final Parse Error: {e.msg}")
                    #print(f"Error Character: '{error_char}' at position {error_pos}")
                    #print(f"Context: ...{context}...")
        
                    use_agent = True
                    
        if use_agent:
            result, json_string = self.to_json(
                json_string, 
                agent=agent, 
                requirements = kwargs.get('requirements', 'Output only a JSON dict.'),
                **kwargs
            )
            if result:
                return json.loads(json_string)
            else:
                return json_string
        
            
        return None

    def remove_all_triple_quoted_strings(self, code: str) -> str:
        """
        Removes triple-double-quoted (\"\"\"...\"\"\") and triple-single-quoted ('''...''') 
        docstrings from the code.

        Returns the code with those docstrings stripped.
        """
        triple_quotes_pattern = re.compile(
            r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\")', 
            re.DOTALL | re.IGNORECASE | re.MULTILINE
        )
        code = triple_quotes_pattern.sub("", code)
        
        triple_quotes_pattern = re.compile(
            r"('''[\s\S]*?'''|)", 
            re.DOTALL | re.IGNORECASE | re.MULTILINE
        )
        return triple_quotes_pattern.sub("", code)

    def remove_code_blocks_and_doc_examples(self, text: str) -> str:
        """
        Removes code fences (triple backticks) and docstring-like examples from the text
        so that lines inside them are not parsed as real actions.

        Returns the text stripped of these example blocks.
        """

        # 1) Remove triple-backtick code fences:
        #    Matches ``` (optional info) up to the next ```.
        code_fence_pattern = re.compile(r"```.*?```", re.DOTALL)
        text_no_fence = code_fence_pattern.sub("", text)

        # 2) Remove or mask lines labeled as "Example usage:" or "Examples:" 
        #    up until next blank line or next heading
        #    (Heuristic approach)
        
        # ToDo: Either remove or fix this.. It removes code that should not be removed..
        #example_usage_pattern = re.compile(
        #    r"(Example usage:|Examples?:).*?(?=\n\s*\n|^##|\Z)",
        #    re.DOTALL | re.IGNORECASE | re.MULTILINE
        #)
        #cleaned_text = example_usage_pattern.sub("", text_no_fence)

        return text_no_fence #cleaned_text

    # ToDo: Uses the old syntax
    def _remove_placeholder_requests(self, text: str) -> str:
        """
        Removes calls like `request:tools|<your_query>` from the text so they
        won't be treated as real actions.

        Returns the text with those placeholder requests removed.
        """
        # Regex pattern:
        # - request:
        # - (tools|rags|retrievers|plugins)
        # - A pipe `|`
        # - A `<...>` block with no extra pipe or quotes 
        #    For example: <my_stuff> or <any text> but not other calls
        pattern = re.compile(r"request:(?:tools|rags|retrievers|plugins)\|\s*<[^>]*>", re.DOTALL | re.IGNORECASE | re.MULTILINE)

        # Remove each match from the text
        return pattern.sub("", text)


    def _parse_for_actions(self, text: str) -> str:
        """
        Removes code blocks & doc examples, then searches for `action_pattern`.
        Returns True if found, otherwise False.
        """
        sanitized = self.remove_all_triple_quoted_strings(text)
        sanitized = self.remove_code_blocks_and_doc_examples(sanitized)
        # ToDo: Fix remove_placeholder_requests()
        #sanitized = self._remove_placeholder_requests(sanitized)
        return sanitized

    def to_json(self, data, agent=None, instructions = '', retries = 3, requirements = 'Output as JSON list.', **kwargs):
        """
        If agent is None, try to fetch the agent designated in the agent registry. Otherwise return None.
        """
        
        agent = agent or AgentRegistry.get("ls_json_parser")
        if agent is None:
            print('No JSON parser agent available. Returning original response.')
            return False, data
        
        if isinstance(agent, dict):
            agent = agent.get("agent")
        
        query = f"""Provide machine parseable json for the below data.
        {instructions}
        
        Data:
        ---
        {self.clear_markdown(data)}
        ---
        
        {requirements}
        """
        
        for n in range(retries):
            response = self.clear_markdown(agent.chat(q = query, reset = True, erase_query = True))

            if self.is_valid_json(response):
                print('Proper JSON returned!')
                return (True, response)
            else:
                query = query + '\n\nThe below is still not proper JSON, please correct it.\n\n' + response
        
        print('Unable to format text as proper JSON...')
        return (False, self.clear_markdown(data))
    
    def is_valid_json(self, json_string):
        try:
            json.loads(json_string)
        except ValueError:
            return False

        return True

    def is_valid_python(self, code):
        try:
            ast.parse(code)
        except SyntaxError:
            return False

        return True

    def is_valid_yaml(self, code):
        try:
            yaml.safe_load(code)
        except yaml.YAMLError:
            return False

        return True
    
    def clear_markdown(self, text):
        
        # Remove starting code markup
        if text.startswith('```python'):
            text = text.split('```python',1)[-1]
        elif text.startswith('```json'):
            text = text.split('```json',1)[-1]
        elif text.startswith('```yaml'):
            text = text.split('```yaml',1)[-1]
        elif text.startswith('```plaintext'):
            text = text.split('```plaintext',1)[-1]
        elif text.startswith('```javascript'):
            text = text.split('```javascript',1)[-1]
        elif text.startswith('```html'):
            text = text.split('```html',1)[-1]
        elif text.startswith('```css'):
            text = text.split('```css',1)[-1]
        elif text.startswith('```'):
            text = text.split('```',1)[-1]

        # Remove ending code markup
        if text.endswith('```'):
            text = text.rsplit('```',1)[0]

        return text
    
    def clean_text(self, text: str, remove_linebreaks: bool = False) -> str:
        # Normalize unicode and replace non-breaking space with normal space
        text = text.replace("\u00a0", " ")
        return unicodedata.normalize("NFKD", text)

    def strip_tags(self, text, remove_linebreaks = False):
        strip_tags = StripTags()
        strip_tags.reset()
        strip_tags.feed(text)
        txt = strip_tags.get_data().encode('ascii', 'ignore').decode()
        txt = txt.replace('\\n',' ')
        if remove_linebreaks:
            txt = txt.replace('\n',' ')
        return txt.replace('\\u00a0',' ')
    
    def safe_str_to_int(self, s):
        # Extract numeric part using regex
        match = re.search(r"[-+]?\d*\.?\d+", s)
        if match:
            return int(match.group())
        return 0  # Return 0 if no valid number is found