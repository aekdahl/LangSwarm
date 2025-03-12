RagInstructions = """-- RAGs (retrievers) --
Use RAGs to retrieve or store data using vector-based databases.

Request information about a specific rag, or search for available rags:
START>>>
{
  "calls": [
    {
      "type": "rags", # Type can be any of rag, rags, retriever or retrievers
      "method": "request",
      "instance_name": "<exact_rag_name> or <search query>", # E.g “code_base“ or “Find function doc for X“
      "action": "",
      "parameters": {}
    }
  ]
}
<<<END

Once the correct rag is identified, execute it using one of the below:
START>>>
{
  "calls": [
    {
      "type": "rag", # Type can be any of rag, rags, retriever or retrievers
      "method": "execute",
      "instance_name": "<exact_rag_name>", # E.g “code_base“
      "action": "<action_name>",
      "parameters": {params_dictionary}
    }
  ]
}
<<<END

Database Metadata Querying Instructions:
When retrieving documents from a database, you may use filters to search the metadata.

Required Filter Format:
- **conditions**: A list of dictionaries, each specifying:
  - `field`: The metadata field to filter by (e.g., `"category"`, `"year"`, `"language"`).
  - `operator`: The comparison operator (e.g., `"=="`, `">="`, `"<="`).
  - `value`: The expected value for filtering.
- **logic**: `"AND"` or `"OR"` to define how multiple conditions are combined.

Required top_k Format:
- **top_k**: The maximum number of documents to retrieve (unlimited: None).

Example Usage:
To retrieve AI-related documents from 2020 or later, construct the filter as follows:
filters = { "conditions": [ {"field": "category", "operator": "==", "value": "AI"}, {"field": "year", "operator": ">=", "value": 2020} ], "logic": "AND" }

START>>>
{
  "calls": [
    {
      "type": "rag",
      "method": "execute", # Filters only works for `execute`
      "instance_name": "<exact_rag_name>",
      "action": "query", # Filters only works for `query`
      "parameters": {"filters": filters, top_k=10}
    }
  ]
}
<<<END
"""
