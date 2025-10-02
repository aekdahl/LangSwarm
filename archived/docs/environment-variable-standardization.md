# Environment Variable Standardization

## Google Cloud Project Variable

**Standard**: `GOOGLE_CLOUD_PROJECT`

This document describes the standardization of Google Cloud project environment variables across the LangSwarm repository.

## Background

Previously, the codebase used multiple inconsistent environment variable names for the Google Cloud project ID:
- `GOOGLE_CLOUD_PROJECT_ID` (custom variant)
- `PROJECT_ID` (generic)
- `GOOGLE_CLOUD_PROJECT` (official Google standard)

## Standardization Decision

**Standard Variable**: `GOOGLE_CLOUD_PROJECT`

**Rationale**:
1. **Official Google Cloud Standard**: This is the canonical environment variable used by Google Cloud libraries and tools
2. **Library Compatibility**: Google Cloud Python libraries automatically recognize this variable
3. **Authentication Integration**: The `google-auth` library uses this variable by default
4. **Consistency**: Aligns with Google's recommended practices

## Implementation

All instances of `GOOGLE_CLOUD_PROJECT_ID` and inappropriate `PROJECT_ID` references have been replaced with `GOOGLE_CLOUD_PROJECT` across:

### Updated Files
- Debug and test scripts (`debug/`)
- Configuration files (`.yaml`, `.env` templates)
- Documentation files
- Example configurations
- Main codebase (`langswarm/`)

### Key Changes
- Environment variable references in Python code
- YAML configuration files with `${GOOGLE_CLOUD_PROJECT}` substitution
- Documentation and README files
- Shell scripts and Makefiles

## Usage

### Setting the Environment Variable
```bash
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### In Python Code
```python
import os
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
```

### In YAML Configuration
```yaml
config:
  project_id: "${GOOGLE_CLOUD_PROJECT:-default-project}"
```

## Migration Notes

- All existing `GOOGLE_CLOUD_PROJECT_ID` references have been updated
- No breaking changes for users who already use `GOOGLE_CLOUD_PROJECT`
- Users with `GOOGLE_CLOUD_PROJECT_ID` in their environment will need to rename it to `GOOGLE_CLOUD_PROJECT`

## Future Guidelines

When adding new Google Cloud functionality:
1. **Always use** `GOOGLE_CLOUD_PROJECT` for the project ID
2. **Never create** custom variants like `*_PROJECT_ID`
3. **Follow** Google Cloud's official environment variable conventions
4. **Document** any new environment variables in this standardization guide

## Related Variables

These variables remain unchanged as they serve different purposes:
- `ANALYTICS_PROJECT_ID` - For analytics services (if different from main project)
- `GCP_PROJECT_ID` - Legacy references (being phased out)
- Other service-specific project IDs

---

*This standardization was completed on 2025-09-28 to improve consistency and align with Google Cloud best practices.*
