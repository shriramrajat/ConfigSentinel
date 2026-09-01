"""
mapping.errors
~~~~~~~~~~~~~~

Domain-specific exceptions for the AI Semantic Mapping module.
"""

class LLMIntegrationError(Exception):
    """Raised when the LLM provider fails (e.g., timeout, 500, invalid JSON).
    
    This ensures that raw provider tracebacks or secrets do not leak
    to the application layer.
    """
    pass

class ProviderNotConfiguredError(Exception):
    """Raised when AI operations are requested but no provider is configured."""
    pass
