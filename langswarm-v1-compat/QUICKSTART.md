# Quick Start: Publish to PyPI in 5 Minutes

## Step 1: Create PyPI Account (2 minutes)

1. Go to: https://pypi.org/account/register/
2. Fill in details, verify email

## Step 2: Get API Token (1 minute)

1. Log in to PyPI
2. Go to: https://pypi.org/manage/account/token/
3. Click "Add API token"
4. Name: "langswarm-v1-compat"
5. Scope: "Entire account" (or specific project after first upload)
6. Copy the token (starts with `pypi-...`)

## Step 3: Publish (2 minutes)

```bash
cd langswarm-v1-compat

# Install twine if not installed
pip install twine

# Upload to PyPI
python -m twine upload dist/*

# When prompted:
# Username: __token__
# Password: <paste your API token here>
```

## Step 4: Verify (30 seconds)

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # Windows: test_env\Scripts\activate

# Install from PyPI
pip install langswarm-v1-compat

# Test it
python -c "import langswarm_v1_compat; print('✅ Version:', langswarm_v1_compat.__version__)"
```

## Done! 🎉

Your package is now live at: https://pypi.org/project/langswarm-v1-compat/

V1 users can now install with:
```bash
pip install langswarm-v1-compat
```

## Optional: Test on TestPyPI First

If you want to be extra careful, test on TestPyPI first:

```bash
# 1. Create TestPyPI account: https://test.pypi.org/account/register/
# 2. Get TestPyPI token: https://test.pypi.org/manage/account/token/

# 3. Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# 4. Test install
pip install --index-url https://test.pypi.org/simple/ langswarm-v1-compat

# 5. If it works, upload to real PyPI (step 3 above)
```

## What Happens Next

1. **Package appears** on PyPI (takes ~5 minutes)
2. **Users can install** with `pip install langswarm-v1-compat`
3. **Download stats** available at https://pypistats.org/packages/langswarm-v1-compat

## Update Your Main README

Add this section:

````markdown
## For LangSwarm V1 Users

Using archived V1? Install the compatibility package:

```bash
pip install langswarm-v1-compat
```

Then in your code:

```python
import langswarm_v1_compat  # Auto-fixes applied!
```

Fixes:
- ✅ LangChain 0.3.x+ compatibility
- ✅ UTF-8 encoding (Swedish and all languages)

Details: https://pypi.org/project/langswarm-v1-compat/
````

## Troubleshooting

### "Package already exists"
You can't re-upload the same version. Increment version in:
- `langswarm_v1_compat/__init__.py`
- `setup.py`
- `pyproject.toml`

Then rebuild:
```bash
rm -rf build/ dist/ *.egg-info/
python -m build
python -m twine upload dist/*
```

### "Invalid credentials"
Make sure username is exactly `__token__` (with two underscores)

### "File already exists"
Delete old files first:
```bash
rm -rf dist/ build/ *.egg-info/
python -m build
```

---

That's it! Your V1 compatibility package is now on PyPI! 🚀

