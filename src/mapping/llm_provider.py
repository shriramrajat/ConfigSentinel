"""
mapping.llm_provider
~~~~~~~~~~~~~~~~~~~~

Concrete implementation of the AI Semantic Mapper using an LLM.

This module connects to an OpenAI-compatible /v1/chat/completions REST endpoint.
It strictly validates structured output to ensure the LLM cannot bypass
the trust boundary.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.mapping.ai_provider import AIMapper
from src.mapping.model import HumanApprovalState, SemanticMapping, UnknownPattern
from src.mapping.errors import LLMIntegrationError


class LLMResponse(BaseModel):
    """Strictly controlled schema for the LLM output.
    
    CRITICAL: `extra="forbid"` prevents the LLM from attempting to inject
    fields like `approval_state`, `severity`, or `compliance_status`. If the
    LLM returns these, the payload is explicitly rejected as malformed.
    """
    model_config = ConfigDict(extra="forbid")
    
    proposed_key: str = Field(..., min_length=1, max_length=255)
    proposed_value: str | None = Field(default=None, max_length=1000)
    explanation: str = Field(..., min_length=1, max_length=2000)
    confidence: float = Field(..., ge=0.0, le=1.0)


from src.mapping.redaction import redact_secrets


def sanitize_llm_prompt(text: str) -> str:
    """Sanitize user-provided text before inserting into LLM prompt.

    1. Redacts sensitive credentials (passwords, hashes, community strings, tokens).
    2. Strips prompt injection attempts and system instruction overrides.
    """
    if not text:
        return ""
    # First redact secret credentials
    sanitized = redact_secrets(text)
    # Strip dangerous role injection attempts and system instruction overrides
    sanitized = sanitized.replace("System:", "[REDACTED_ROLE]:").replace("SYSTEM:", "[REDACTED_ROLE]:")
    sanitized = sanitized.replace("Ignore all instructions", "[REDACTED_INSTRUCTION]")
    sanitized = sanitized.replace("ignore previous instructions", "[REDACTED_INSTRUCTION]")
    return sanitized



class LLMMapper(AIMapper):
    """Real LLM provider hitting an OpenAI-compatible REST API."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = "https://api.openai.com/v1") -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        
    def _build_system_prompt(self, pattern: UnknownPattern) -> str:
        return (
            "You are an expert network engineer assisting with ConfigSentinel's semantic mapping.\n"
            "The user will provide a network configuration directive that is currently UNKNOWN to the system.\n"
            f"Vendor: {pattern.vendor}\n\n"
            "Your objective is to propose a semantic mapping (a key and an optional value) that represents the underlying meaning of this directive.\n\n"
            "CRITICAL RULES:\n"
            "1. You MUST output ONLY valid JSON matching the exact requested schema.\n"
            "2. You MUST NOT make compliance decisions. You are strictly translating syntax to semantics.\n"
            "3. You MUST NOT determine if the configuration passes or fails an audit.\n"
            "4. You MUST NOT determine the severity of the configuration.\n"
            "5. You MUST NOT invent configuration lines.\n"
            "6. Be honest about your confidence level (0.0 to 1.0).\n"
            "7. Do not include any fields other than proposed_key, proposed_value, explanation, and confidence."
        )
        
    def _build_user_prompt(self, pattern: UnknownPattern) -> str:
        context = f"Context Section: {sanitize_llm_prompt(pattern.section_context)}\n" if pattern.section_context else ""
        return f"{context}Raw Directive: {sanitize_llm_prompt(pattern.raw_directive)}"


    def propose_mapping(self, pattern: UnknownPattern) -> SemanticMapping:
        """Call the LLM to propose a semantic mapping."""
        system_prompt = self._build_system_prompt(pattern)
        user_prompt = self._build_user_prompt(pattern)
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "ConfigSentinel/1.0"
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=15.0) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as e:
            raise LLMIntegrationError(f"Network error communicating with AI provider: {e}")
        except TimeoutError:
            raise LLMIntegrationError("Timeout communicating with AI provider.")
            
        try:
            data = json.loads(body)
            # OpenAI /v1/chat/completions standard response format
            content = data["choices"][0]["message"]["content"]
            llm_json = json.loads(content)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            raise LLMIntegrationError(f"Failed to parse LLM provider response: {e}")
            
        try:
            # Strictly validate the JSON payload
            validated = LLMResponse(**llm_json)
        except ValidationError as e:
            raise LLMIntegrationError(f"LLM returned invalid or forbidden fields: {e}")
            
        # Return a domain model in the PENDING state.
        # Note: SemanticMapping defaults to PENDING, and the LLMResponse schema
        # strictly forbids the LLM from providing an approval_state.
        return SemanticMapping(
            pattern_id=pattern.id,
            original_syntax=pattern.raw_directive,
            proposed_key=validated.proposed_key,
            proposed_value=validated.proposed_value,
            explanation=validated.explanation,
            confidence=validated.confidence,
            approval_state=HumanApprovalState.PENDING
        )
