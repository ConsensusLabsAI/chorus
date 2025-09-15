"""
Utilities for extracting prompts from function source code.
"""

import inspect
import re
from typing import Optional, Callable


def extract_prompt_from_function(func: Callable) -> Optional[str]:
    """Extract prompt from function's docstring or comments."""
    # Get the source code of the function
    try:
        source_lines = inspect.getsourcelines(func)
        source_code = ''.join(source_lines[0])
    except (OSError, TypeError):
        return None
    
    # First, try to get from docstring
    if func.__doc__:
        docstring = func.__doc__.strip()
        # If docstring looks like a prompt (not just description), use it
        if len(docstring) > 20 and not docstring.startswith(('Args:', 'Returns:', 'Raises:', 'Example')):
            return docstring
    
    # Look for prompt patterns in the source code
    prompt_patterns = [
        r'#\s*@prompt\s*["\'](.*?)["\']',  # # @prompt "text"
        r'["\'](.*?)["\']\s*#\s*@prompt',  # "text" # @prompt
        r'prompt\s*=\s*["\'](.*?)["\']',   # prompt = "text"
        r'["\'](.*?)["\']\s*#\s*prompt',   # "text" # prompt
    ]
    
    for pattern in prompt_patterns:
        matches = re.findall(pattern, source_code, re.DOTALL)
        if matches:
            # Return the first match, cleaned up
            prompt = matches[0].strip()
            if len(prompt) > 10:  # Basic validation
                return prompt
    
    # Look for multiline string assignments
    multiline_patterns = [
        r'prompt\s*=\s*"""([^"]*)"""',
        r'prompt\s*=\s*\'\'\'([^\']*)\'\'\'',
        r'["\'](.*?)["\']\s*#\s*@prompt',
    ]
    
    for pattern in multiline_patterns:
        matches = re.findall(pattern, source_code, re.DOTALL)
        if matches:
            prompt = matches[0].strip()
            if len(prompt) > 10:
                return prompt
    
    return None
