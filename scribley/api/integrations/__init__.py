"""
LLM integrations for Scribley.

This package provides integrations with various local LLM providers
for enhancing articles and providing AI-assisted features.
"""

import os
import logging
from typing import Optional, Union, Dict, Any, List

logger = logging.getLogger(__name__)

# Import the integration clients
try:
    from .ollama import OllamaClient
except ImportError:
    logger.debug("Ollama integration not available")
    OllamaClient = None

try:
    from .lmstudio import LMStudioClient
except ImportError:
    logger.debug("LM Studio integration not available")
    LMStudioClient = None

class LLMFactory:
    """Factory for creating and managing LLM client instances."""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = None
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers."""
        # Check for Ollama
        if OllamaClient is not None:
            try:
                # Pass the requests library to OllamaClient constructor
                import requests
                client = OllamaClient(sync_requests_lib=requests)
                if client.initialized_successfully: # Use the new status attribute
                    self.providers["ollama"] = client
                    if self.default_provider is None:
                        self.default_provider = "ollama"
                    logger.info("Ollama integration available")
                else:
                    logger.warning("Ollama client initialization failed. Ollama may not be running or no models available.")
            except Exception as e:
                logger.warning(f"Error initializing Ollama client: {str(e)}")
        
        # Check for LM Studio
        if LMStudioClient is not None:
            try:
                client = LMStudioClient()
                if client._validate_connection():
                    self.providers["lmstudio"] = client
                    if self.default_provider is None:
                        self.default_provider = "lmstudio"
                    logger.info("LM Studio integration available")
                else:
                    logger.warning("LM Studio connection failed. LM Studio may not be running.")
            except Exception as e:
                logger.warning(f"Error initializing LM Studio client: {str(e)}")
        
        # Set preferred provider from environment variable if available
        preferred_provider = os.environ.get("SCRIBLEY_LLM_PROVIDER", "").lower()
        if preferred_provider in self.providers:
            self.default_provider = preferred_provider
            logger.info(f"Using {preferred_provider} as the default LLM provider")
    
    def get_client(self, provider: Optional[str] = None):
        """
        Get a client for the specified provider.
        
        Args:
            provider (str, optional): The provider name ('ollama' or 'lmstudio'). 
                                      If None, uses the default provider.
        
        Returns:
            Union[OllamaClient, LMStudioClient, None]: The LLM client or None if not available
        """
        if provider is None:
            provider = self.default_provider
        
        client = self.providers.get(provider)
        if client is None:
            logger.warning(f"Provider '{provider}' not available. Available providers: {list(self.providers.keys())}")
            # Fall back to default provider if specified provider not available
            if provider != self.default_provider and self.default_provider in self.providers:
                logger.info(f"Falling back to default provider '{self.default_provider}'")
                return self.providers[self.default_provider]
        
        return client
    
    def get_available_providers(self) -> List[str]:
        """Get a list of available provider names."""
        return list(self.providers.keys())
    
    def is_available(self) -> bool:
        """Check if any LLM provider is available."""
        return len(self.providers) > 0


# Create a singleton factory instance
llm_factory = LLMFactory()

# Convenience function to get the default client
def get_llm_client(provider: Optional[str] = None):
    """
    Get an LLM client instance.
    
    Args:
        provider (str, optional): The provider name. If None, uses the default provider.
    
    Returns:
        Union[OllamaClient, LMStudioClient, None]: The LLM client or None if not available
    """
    return llm_factory.get_client(provider)


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Get available providers
    providers = llm_factory.get_available_providers()
    print(f"Available LLM providers: {providers}")
    
    # Get the default client
    client = get_llm_client()
    if client:
        print(f"Using {client.__class__.__name__}")
        
        # Test summarization
        test_article = """
        Artificial intelligence has rapidly transformed industries across the globe.
        From healthcare to finance, AI is enabling new possibilities and efficiencies.
        However, with these advancements come significant ethical considerations
        that must be addressed by policymakers and technologists alike.
        """
        
        summary = client.summarize_article(test_article)
        print(f"Summary: {summary}")
    else:
        print("No LLM providers available. Please install and run Ollama or LM Studio locally.") 