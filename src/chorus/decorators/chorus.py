"""
Main decorator for tracking and versioning LLM prompts.
"""

import functools
import inspect
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..core import PromptVersion, PromptStorage, analyze_prompt_changes, bump_version, is_valid_version
from ..utils import extract_prompt_from_function


def chorus(
    version: str,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    auto_version: bool = True
):
    """
    Decorator to track and version LLM prompts using Semantic Versioning (SemVer).
    Automatically extracts the prompt from the function's docstring or comments.
    
    Follows Semantic Versioning principles:
    - MAJOR: Incompatible changes that break existing functionality
    - MINOR: New functionality added in a backward compatible manner
    - PATCH: Backward compatible bug fixes and small improvements
    
    Args:
        version: Required version string following SemVer (e.g., "1.0.0", "1.0.0-alpha", "2.1.0+20231201") 
                or "auto" for intelligent automatic versioning
        description: Optional description of the prompt
        tags: Optional list of tags for categorization
        auto_version: Whether to automatically increment version on changes
    
    Version Format Support:
        - Basic: 1.0.0
        - Pre-release: 1.0.0-alpha, 1.0.0-beta.1, 1.0.0-rc.2
        - Build metadata: 1.0.0+20231201, 1.0.0-alpha+001
    
    Example:
        @chorus(version="1.0.0", description="Basic Q&A prompt")
        def ask_question(question: str) -> str:
            \"\"\"
            You are a helpful assistant. Answer: {question}
            \"\"\"
            return "Answer: " + question
        
        @chorus(version="auto", description="Auto-versioned prompt")
        def auto_versioned_function(text: str) -> str:
            \"\"\"
            Process this text: {text}
            \"\"\"
            return f"Processed: {text}"
    """
    # Validate version parameter
    if not version:
        raise ValueError("Version parameter is required and cannot be empty")
    
    if version != "auto" and not is_valid_version(version):
        raise ValueError(f"Invalid version format: {version}. Expected semantic version (e.g., '1.0.0') or 'auto'")
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start execution timing
            start_time = time.time()
            
            # Extract prompt from function's docstring or comments
            prompt = extract_prompt_from_function(func)
            
            if not prompt:
                print(f"Warning: No prompt found in function {func.__name__}")
                return func(*args, **kwargs)
            
            # Get function arguments for prompt formatting
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Format the prompt with function arguments
            try:
                formatted_prompt = prompt.format(**bound_args.arguments)
            except KeyError:
                # If prompt has placeholders not in function args, use original
                formatted_prompt = prompt
            
            # Get source filename for better file naming
            try:
                source_file = inspect.getfile(func)
                source_filename = Path(source_file).stem  # Get filename without extension
            except (OSError, TypeError):
                source_filename = "unknown"
            
            # Create storage and track the prompt
            storage = PromptStorage(source_filename=source_filename)
            
            # Check if this is a new prompt or version
            current_version = storage.get_latest_version(func.__name__)
            
            # Handle "auto" version option
            if version == "auto":
                if current_version:
                    # Analyze changes to determine appropriate version bump
                    bump_type = analyze_prompt_changes(current_version.prompt, formatted_prompt)
                    new_version = bump_version(current_version.version, bump_type)
                else:
                    # Start with 1.0.0 for auto versioning
                    new_version = "1.0.0"
            elif current_version and auto_version:
                # Check if prompt has changed
                if current_version.prompt != formatted_prompt:
                    # Analyze changes to determine appropriate version bump
                    bump_type = analyze_prompt_changes(current_version.prompt, formatted_prompt)
                    new_version = bump_version(current_version.version, bump_type)
                else:
                    new_version = current_version.version
            else:
                new_version = version
            
            # Execute the original function and capture output
            try:
                output = func(*args, **kwargs)
                execution_time = time.time() - start_time
                execution_success = True
            except Exception as e:
                output = f"ERROR: {str(e)}"
                execution_time = time.time() - start_time
                execution_success = False
                # Re-raise the exception after logging
                raise
            
            # Create prompt version with execution data
            prompt_version = PromptVersion(
                prompt=formatted_prompt,
                version=new_version,
                function_name=func.__name__,
                description=description,
                tags=tags or [],
                inputs=bound_args.arguments,
                output=output,
                execution_time=execution_time
            )
            
            # Store the prompt with execution data
            storage.add_prompt(prompt_version)
            
            # Add prompt info to function metadata
            func._chorus_info = {
                'prompt_version': prompt_version,
                'original_prompt': prompt,
                'formatted_prompt': formatted_prompt,
                'execution_success': execution_success,
                'execution_time': execution_time
            }
            
            # Return the output
            return output
        
        # Store metadata on the wrapper
        wrapper._chorus_metadata = {
            'version': version,
            'description': description,
            'tags': tags or [],
            'auto_version': auto_version
        }
        
        return wrapper
    return decorator


