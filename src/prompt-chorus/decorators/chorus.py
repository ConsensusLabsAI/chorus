"""
Main decorator for tracking and versioning LLM prompts.
"""

import functools
import inspect
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..core import (
    PromptVersion, PromptStorage, analyze_prompt_changes, 
    bump_project_version, is_valid_version, create_versioned_prompt
)
from ..utils import extract_prompt_from_function


def chorus(
    project_version: str = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    auto_version: bool = True
):
    """
    Decorator to track and version LLM prompts using dual versioning system.
    Automatically extracts the prompt from the function's docstring or comments.
    
    Dual Versioning System:
    - Project Version: Semantic version for project changes (set manually)
    - Agent Version: Incremental version for prompt changes (auto-incremented)
    
    Args:
        project_version: Project version string (e.g., "1.0.0"). If None, uses project's current project version.
        description: Optional description of the prompt
        tags: Optional list of tags for categorization
        auto_version: Whether to automatically increment agent version on changes
    
    Example:
        @chorus(project_version="1.0.0", description="Basic Q&A prompt")
        def ask_question(question: str) -> str:
            \"\"\"
            You are a helpful assistant. Answer: {question}
            \"\"\"
            return "Answer: " + question
        
        @chorus(description="Auto-versioned prompt")  # Uses project's project version
        def auto_versioned_function(text: str) -> str:
            \"\"\"
            Process this text: {text}
            \"\"\"
            return f"Processed: {text}"
    """
    # Validate project_version parameter if provided
    if project_version is not None and not is_valid_version(project_version):
        raise ValueError(f"Invalid project version format: {project_version}. Expected semantic version (e.g., '1.0.0')")
    
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
            
            # Get or set project version
            if project_version is not None:
                # Set the project version for this project
                storage.set_project_version(project_version)
                current_project_version = project_version
            else:
                # Use existing project version or default to 1.0.0
                current_project_version = storage.get_project_version()
                if current_project_version is None:
                    storage.set_project_version("1.0.0")
                    current_project_version = "1.0.0"
            
            # Create versioned prompt using the new dual versioning system
            prompt_version = create_versioned_prompt(
                prompt=formatted_prompt,
                function_name=func.__name__,
                project_version=current_project_version,
                prompts=storage.prompts,
                description=description,
                tags=tags
            )
            
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
            
            # Update prompt version with execution data
            prompt_version.inputs = bound_args.arguments
            prompt_version.output = output
            prompt_version.execution_time = execution_time
            
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
            'project_version': project_version,
            'description': description,
            'tags': tags or [],
            'auto_version': auto_version
        }
        
        return wrapper
    return decorator


