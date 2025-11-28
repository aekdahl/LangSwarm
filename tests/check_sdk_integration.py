
from langfuse import Langfuse
try:
    l = Langfuse(public_key="pk", secret_key="sk", sdk_integration="litellm")
    print("✅ Langfuse v2 accepts sdk_integration")
except TypeError as e:
    print(f"❌ Langfuse v2 REJECTS sdk_integration: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")
