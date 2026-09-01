"""
mapping.ai_provider
~~~~~~~~~~~~~~~~~~~

Interface for AI Semantic Mappers.

This module defines the dependency-inverted interface for the LLM component.
The core engine MUST NEVER couple directly to a specific AI provider.
"""

from __future__ import annotations

from src.mapping.model import SemanticMapping, UnknownPattern


class AIMapper:
    """Abstract interface for AI mapping providers.
    
    Implementations of this class are responsible for calling external LLMs
    (e.g., OpenAI, Gemini) to propose mappings for unknown patterns.
    """
    
    def propose_mapping(self, pattern: UnknownPattern) -> SemanticMapping:
        """Propose a semantic mapping for the given unknown pattern.
        
        The resulting SemanticMapping MUST have an approval_state of PENDING.
        It is strictly a proposal and cannot define compliance rules.
        
        Parameters
        ----------
        pattern:
            The unknown configuration pattern to translate.
            
        Returns
        -------
        SemanticMapping
            A proposed mapping containing the translation and explanation.
            
        Raises
        ------
        NotImplementedError
            Always raised in this structural prototype phase.
        """
        raise NotImplementedError(
            "AI integration is not implemented in this phase. "
            "Implement an AIMapper subclass to connect an LLM."
        )
