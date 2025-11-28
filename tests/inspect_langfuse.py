
import langfuse
import sys

print(f"Langfuse version: {langfuse.version.__version__}")
print(f"dir(langfuse): {dir(langfuse)}")

try:
    from langfuse import Langfuse
    print(f"Langfuse class: {Langfuse}")
    print(f"dir(Langfuse): {dir(Langfuse)}")
    
    # Check if trace is in the class or instance
    if hasattr(Langfuse, 'trace'):
        print("✅ Langfuse.trace exists on class")
    else:
        print("❌ Langfuse.trace does NOT exist on class")
        
    try:
        instance = Langfuse(public_key="pk", secret_key="sk")
        if hasattr(instance, 'trace'):
             print("✅ instance.trace exists")
        else:
             print("❌ instance.trace does NOT exist")
    except:
        pass

except ImportError:
    print("Could not import Langfuse from langfuse")
