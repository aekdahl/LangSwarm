# Codebase Indexer Tool

## Description

Intelligent code search and analysis with semantic understanding of codebases for code navigation, refactoring, and documentation.

## Instructions

This tool provides codebase operations with two calling approaches:

### Intent-Based Calling (Smart Code Search)

Use **`codebase_indexer`** with intent for intelligent code exploration:

**Parameters:**
- `intent`: What you're looking for in the codebase
- `context`: Relevant details (language, file types, functionality)

**When to use:**
- Finding code: "Where is user authentication handled?"
- Understanding patterns: "Show me all API endpoints"
- Refactoring prep: "Find all uses of the old payment method"
- Documentation: "What does the email service do?"

**Examples:**
- "Find authentication code" → intent="locate where user authentication is implemented", context="security, login flow"
- "Show API endpoints" → intent="list all REST API endpoints in the application", context="API documentation"

### Direct Method Calling

**`codebase_indexer.search`** - Search code semantically
- **Parameters:** query, file_patterns, scope
- **Use when:** Searching with specific criteria

**`codebase_indexer.index`** - Index codebase
- **Parameters:** directory, languages, exclude_patterns
- **Use when:** Building or updating code index

**`codebase_indexer.analyze`** - Code analysis
- **Parameters:** file_path or directory, analysis_type
- **Use when:** Getting code metrics or structure

## Brief

Intelligent codebase search and analysis with semantic code understanding.
