
import inspect
import sys
try:
    import langswarm_memory
    print("langswarm_memory version:", langswarm_memory.__version__)
    
    # Try to find BigQueryBackend
    if hasattr(langswarm_memory, 'BigQueryBackend'):
        print("Found BigQueryBackend in top level")
        cls = langswarm_memory.BigQueryBackend
        print(inspect.getdoc(cls))
        print(inspect.signature(cls.__init__))
    else:
        print("BigQueryBackend not found in top level")
        # Try to find where it might be
        import pkgutil
        print("Submodules:", [name for _, name, _ in pkgutil.iter_modules(langswarm_memory.__path__)])
        
except ImportError as e:
    print("Could not import langswarm_memory:", e)
