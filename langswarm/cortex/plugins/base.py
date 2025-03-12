class BasePlugin:
    """
    Base class for agent capabilities.
    """
    def __init__(self, name, description, instruction):
        self.name = name
        self.description = description
        self.instruction = instruction

    def use(self, *args, **kwargs):
        """Override this method to execute the plugin."""
        raise NotImplementedError("This method should be implemented in a subclass.")

    def run(self, *args, **kwargs):
        """Redirects to the `use` method for compatibility."""
        return self.use(*args, **kwargs)