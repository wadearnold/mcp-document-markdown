"""
Token counting utilities for LLM optimization
"""
import re
from typing import Optional

# Optional but recommended for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

class TokenCounter:
    """Handles token counting for various LLM models"""
    
    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize token counter
        
        Args:
            model: Target LLM model for token counting
        """
        self.model = model
        self.tokenizer = None
        
        if TIKTOKEN_AVAILABLE:
            try:
                self.tokenizer = tiktoken.encoding_for_model(model)
            except:
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Approximation: ~4 characters per token
            return len(text) // 4
    
    def recommend_model_for_tokens(self, token_count: int) -> str:
        """Recommend appropriate LLM model based on token count"""
        if token_count <= 3500:
            return "gpt-3.5-turbo (4K context)"
        elif token_count <= 7500:
            return "gpt-4 (8K context)"
        elif token_count <= 30000:
            return "gpt-4-32k (32K context)"
        elif token_count <= 95000:
            return "claude-2 (100K context)"
        else:
            return "claude-2 (requires chunking)"
    
    def fits_in_context(self, text: str, context_window: int = 4000) -> bool:
        """Check if text fits in specified context window"""
        return self.count_tokens(text) <= context_window
    
    def estimate_processing_cost(self, token_count: int, model: str = "gpt-3.5-turbo") -> float:
        """Estimate processing cost based on token count and model"""
        # Rough cost estimates (as of 2024)
        costs_per_1k_tokens = {
            "gpt-3.5-turbo": 0.0015,
            "gpt-4": 0.03,
            "gpt-4-32k": 0.06,
            "claude-2": 0.008
        }
        
        base_cost = costs_per_1k_tokens.get(model, 0.002)
        return (token_count / 1000) * base_cost