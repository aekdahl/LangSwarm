# LangSwarm Debug Configuration

The LangSwarm debug system uses a centralized configuration file to manage API keys, database connections, and project settings. This eliminates the need to set environment variables manually and provides a consistent debugging experience.

## Quick Start

### 1. Initialize Configuration

```bash
python -m langswarm.core.debug.cli init-config
```

This creates a sample configuration file at `langswarm/core/debug/debug_config.yaml`.

### 2. Edit Configuration

Open `debug_config.yaml` and add your actual credentials:

```yaml
# LangSwarm Debug Configuration
openai:
  api_key: sk-your-actual-openai-api-key-here
  model: gpt-4o-mini

google_cloud:
  project_id: your-actual-gcp-project-id
  credentials_path: /path/to/your/actual/service-account.json

bigquery:
  dataset_id: vector_search
  table_name: embeddings
  embedding_model: text-embedding-3-small
  max_results: 10
  similarity_threshold: 0.7

output_dir: debug_traces
log_level: INFO
```

### 3. Validate Configuration

```bash
python -m langswarm.core.debug.cli validate-config
```

### 4. Start Debugging

```bash
python -m langswarm.core.debug.cli run-case-1
```

## Configuration Locations

The system searches for configuration files in the following order:

1. `./debug_config.yaml` (current directory)
2. `./debug_config.json`
3. `./langswarm/core/debug/debug_config.yaml`
4. `./langswarm/core/debug/debug_config.json`
5. `~/.langswarm/debug_config.yaml`
6. `~/.langswarm/debug_config.json`

## Configuration Sections

### OpenAI Configuration

```yaml
openai:
  api_key: sk-your-openai-api-key      # Required
  model: gpt-4o-mini                   # Default model for all debug cases
  base_url: null                       # Optional: custom OpenAI endpoint
  organization: null                   # Optional: OpenAI organization ID
```

### Google Cloud Configuration

```yaml
google_cloud:
  project_id: your-gcp-project-id      # Required for BigQuery
  credentials_path: null               # Optional: explicit service account file
                                       # If not set, uses gcloud auth (recommended)
  service_account_key: null            # Alternative: inline JSON object
```

**Authentication Methods (in order of preference):**
1. **`gcloud auth application-default login`** (recommended for local development)
2. **`gcloud auth login`** (also works)
3. **Service account file** (`credentials_path`)
4. **Inline service account** (`service_account_key`)
5. **Metadata server** (when running on GCP)

**Check your gcloud authentication:**
```bash
# Check if you're authenticated
gcloud auth list

# Check application default credentials
gcloud auth application-default print-access-token

# If needed, authenticate
gcloud auth application-default login
```

### BigQuery Configuration

```yaml
bigquery:
  dataset_id: vector_search            # BigQuery dataset name
  table_name: embeddings               # BigQuery table name
  embedding_model: text-embedding-3-small  # OpenAI embedding model
  max_results: 10                      # Maximum search results
  similarity_threshold: 0.7            # Similarity cutoff
```

### Database Configuration

```yaml
database:
  postgres_url: null                   # Optional: PostgreSQL connection
  mysql_url: null                      # Optional: MySQL connection
  sqlite_path: null                    # Optional: SQLite database file
```

### Debug Settings

```yaml
output_dir: debug_traces               # Directory for trace files
log_level: INFO                        # Logging level
enable_file_logging: true              # Write logs to files
enable_console_logging: true           # Print logs to console
```

## Environment Variable Overrides

Environment variables always take precedence over configuration file values:

| Environment Variable | Configuration Path |
|---------------------|-------------------|
| `OPENAI_API_KEY` | `openai.api_key` |
| `OPENAI_BASE_URL` | `openai.base_url` |
| `OPENAI_ORGANIZATION` | `openai.organization` |
| `GOOGLE_CLOUD_PROJECT` | `google_cloud.project_id` |
| `GOOGLE_APPLICATION_CREDENTIALS` | `google_cloud.credentials_path` |
| `DATABASE_URL` / `POSTGRES_URL` | `database.postgres_url` |
| `MYSQL_URL` | `database.mysql_url` |

## CLI Commands

### Configuration Management

```bash
# Create sample configuration
python -m langswarm.core.debug.cli init-config

# Validate current configuration
python -m langswarm.core.debug.cli validate-config

# Show current configuration (with masked credentials)
python -m langswarm.core.debug.cli show-config
```

### Debug Cases

```bash
# Run individual debug cases
python -m langswarm.core.debug.cli run-case-1    # Simple agent
python -m langswarm.core.debug.cli run-case-2    # Agent with memory
python -m langswarm.core.debug.cli run-case-3    # BigQuery tool
python -m langswarm.core.debug.cli run-case-4    # Multiple tools

# Run all basic cases
python -m langswarm.core.debug.cli run-all-basic
```

### Trace Analysis

```bash
# Analyze trace files
python -m langswarm.core.debug.cli analyze debug_traces/case_1_simple_agent.jsonl

# Watch for new traces
python -m langswarm.core.debug.cli watch debug_traces/

# Generate summary
python -m langswarm.core.debug.cli summary debug_traces/
```

## Configuration in Code

You can also access configuration programmatically:

```python
from langswarm.core.debug import get_debug_config, validate_debug_config

# Load configuration
config = get_debug_config()
print(f"Using model: {config.openai.model}")

# Validate configuration
is_valid, errors = validate_debug_config()
if not is_valid:
    for error in errors:
        print(f"Error: {error}")
```

## Security Best Practices

1. **Never commit API keys to version control**
   - Add `debug_config.yaml` to `.gitignore`
   - Use environment variables in CI/CD

2. **Use service account files for Google Cloud**
   - Store credentials outside the project directory
   - Use restricted service accounts with minimal permissions

3. **Rotate credentials regularly**
   - Update API keys periodically
   - Monitor for unauthorized usage

## Troubleshooting

### Configuration Not Found

If you see "Configuration not found" errors:

1. Run `init-config` to create a sample file
2. Check file permissions
3. Verify the file is in a searched location

### Validation Failures

Common validation issues:

1. **Missing OpenAI API key**
   - Set `OPENAI_API_KEY` environment variable
   - Add `api_key` to config file

2. **Google Cloud credentials not found**
   - Verify file path in `credentials_path`
   - Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

3. **BigQuery access issues**
   - Check GCP project permissions
   - Verify dataset and table exist
   - Ensure service account has BigQuery access

### Debug Case Failures

If debug cases fail with configuration issues:

1. Run `validate-config` first
2. Check that all required services are accessible
3. Verify network connectivity
4. Review debug trace files for detailed error information

## Example Configurations

### Local Development (with gcloud auth)

```yaml
openai:
  api_key: sk-local-development-key
  model: gpt-4o-mini

google_cloud:
  project_id: my-dev-project
  # No credentials_path needed - uses `gcloud auth`

output_dir: debug_traces
log_level: DEBUG
enable_console_logging: true
```

### Full Production Testing

```yaml
openai:
  api_key: sk-production-testing-key
  model: gpt-4o

google_cloud:
  project_id: my-production-project
  credentials_path: /secure/path/service-account.json

bigquery:
  dataset_id: production_vector_search
  table_name: embeddings
  max_results: 50

output_dir: /var/log/langswarm/debug
log_level: INFO
```

This configuration system provides a robust foundation for debugging LangSwarm components in any environment, from local development to production troubleshooting.
