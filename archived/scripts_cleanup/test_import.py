
import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"sys.path: {sys.path}")

try:
    import langswarm.core.errors
    print("✅ Successfully imported langswarm.core.errors")
    print(f"File: {langswarm.core.errors.__file__}")
except ImportError as e:
    print(f"❌ Failed to import langswarm.core.errors: {e}")
except Exception as e:
    print(f"❌ Exception during import: {e}")

try:
    from langswarm.core.errors import handle_error
    print("✅ Successfully imported handle_error")
except ImportError as e:
    print(f"❌ Failed to import handle_error: {e}")
