"""
Chorus - A Python package for LLM prompt versioning and tracking.
"""

__version__ = "0.1.1"
__author__ = "Maya Lekhi"
__email__ = "maya@consensuslabs.ai"

# Import main classes/functions here
from .decorators import chorus, save_system_prompts, save_all_system_prompts
from .core import PromptVersion, PromptStorage

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "chorus",
    "save_system_prompts",
    "save_all_system_prompts",
    "PromptVersion",
    "PromptStorage"
]
