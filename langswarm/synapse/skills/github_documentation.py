GitHubDocumentation = """### Instructions for the Agent to Enhance Documentation

#### Step 1: Review Existing Documentation
1. **Fetch the Documentation Files**:
   - The agent will read all relevant documentation files from the `docs` folder in the GitHub repository to understand the current state of the documentation.

2. **Identify Areas for Improvement**:
   - The agent will analyze the content for:
     - Clarity and comprehensiveness: Are the explanations clear? Is any information missing?
     - Consistency: Check for consistent terminology and formatting across documents.
     - Accuracy: Verify that all provided information is accurate and up to date, especially in relation to recent code changes.

#### Step 2: Update Documentation Content
1. **Update Markdown Files**:
   - The agent will modify the existing markdown files to:
     - Include any new features or updates that have been added to the codebase.
     - Clarify any confusing sections or add examples where needed.
     - Ensure that the formatting adheres to markdown standards for headers, lists, code blocks, etc.

2. **Add New Documentation Sections**:
   - If necessary, the agent will create new markdown files or sections in existing files to cover:
     - New features or modules.
     - Detailed usage examples and API references.
     - Contribution guidelines if they aren’t already included.

3. **Ensure Proper Linking**:
   - The agent will check that all internal links between documentation files are functioning correctly and update them as needed.

#### Step 3: Generate a Documentation Report

1. **Create a Summary Report**:
   - After updating the documentation, the agent will create a `documentation_update_report.md` file in the root of the repository. This report should include:
     - An overview of what changes were made.
     - A summary of any new sections added.
     - Notes on any areas that still require further attention or improvement in the future.

2. **Write the Documentation Update Report**:
   - The report should follow a markdown format similar to this:

```markdown
# Documentation Update Report

## Overview of Changes
- Updated sections in README.md to include new usage examples.
- Added new documentation for the `AgentFactory` class.
- Clarified existing documentation on logging integration.

## New Sections Added
- **API Reference**: Detailed descriptions of the main classes and functions.
- **Contribution Guidelines**: Instructions for contributing to the project.

## Areas for Further Attention
- Review the documentation for memory management to ensure it aligns with recent code changes.
- Expand examples for using Hugging Face integration.
```

#### Step 4: Store the Updated Documentation
1. **Commit the Changes**:
   - The agent will commit the updated documentation files and the documentation report to the repository with an appropriate commit message, such as "Enhance documentation with updates and new sections".

2. **Push Changes to GitHub**:
   - Finally, the agent will push the changes to the main branch of the repository.
"""