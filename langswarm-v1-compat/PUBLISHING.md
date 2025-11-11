# Publishing langswarm-v1-compat to PyPI

## Prerequisites

1. Create accounts on:
   - PyPI: https://pypi.org/account/register/
   - TestPyPI (for testing): https://test.pypi.org/account/register/

2. Install build tools:
```bash
pip install build twine
```

3. Create API tokens:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

## Build the Package

```bash
cd langswarm-v1-compat

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build the package
python -m build
```

This creates:
- `dist/langswarm_v1_compat-1.0.0-py3-none-any.whl` (wheel)
- `dist/langswarm-v1-compat-1.0.0.tar.gz` (source)

## Test on TestPyPI First

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# When prompted, use your TestPyPI API token:
# Username: __token__
# Password: pypi-... (your token)
```

Test the installation:
```bash
# Create a test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ langswarm-v1-compat

# Test it
python -c "import langswarm_v1_compat; print(langswarm_v1_compat.__version__)"
```

## Publish to PyPI

Once tested, publish to the real PyPI:

```bash
# Upload to PyPI
python -m twine upload dist/*

# When prompted, use your PyPI API token:
# Username: __token__
# Password: pypi-... (your token)
```

## Verify Installation

```bash
# In a fresh environment
pip install langswarm-v1-compat

# Test it
python -c "import langswarm_v1_compat; print('✅ Version:', langswarm_v1_compat.__version__)"
```

## For V1 Users

Once published, V1 users just need:

```bash
pip install langswarm-v1-compat
```

Then in their code:
```python
import langswarm_v1_compat  # Auto-applies patches

# Use LangSwarm V1 normally
from archived.v1.core.config import LangSwarmConfigLoader
# ... rest of code
```

## Update Version

To release a new version:

1. Update version in:
   - `langswarm_v1_compat/__init__.py` (`__version__`)
   - `setup.py` (`version`)
   - `pyproject.toml` (`version`)

2. Rebuild and republish:
```bash
rm -rf build/ dist/ *.egg-info/
python -m build
python -m twine upload dist/*
```

## Automated Publishing (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: |
        cd langswarm-v1-compat
        python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        cd langswarm-v1-compat
        python -m twine upload dist/*
```

Then create a GitHub release to trigger automatic publishing.

## Links After Publishing

- Package page: https://pypi.org/project/langswarm-v1-compat/
- Installation stats: https://pypistats.org/packages/langswarm-v1-compat

## Notes

- First publish may take a few minutes to appear
- Can't re-upload the same version (must increment)
- TestPyPI uploads don't count against limits
- Keep API tokens secure (use environment variables or secrets)

