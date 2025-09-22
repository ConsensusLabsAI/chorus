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
from ..utils import extract_prompt_from_messages_runtime, interceptor, _trace_context

# Global storage manager to share storage instances by system name
_storage_instances = {}

def save_system_prompts(system_name: str) -> None:
    """Save all prompts for a specific system."""
    if system_name in _storage_instances:
        _storage_instances[system_name].save_all_prompts()

def save_all_system_prompts() -> None:
    """Save all prompts for all systems."""
    for storage in _storage_instances.values():
        storage.save_all_prompts()


def chorus(
    system_name: str,
    project_version: str = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    auto_version: bool = True
):
    """
    Decorator to track and version LLM prompts using dual versioning system.
    Automatically extracts the prompt from the messages variable in the function.
    
    Dual Versioning System:
    - Project Version: Semantic version for project changes (set manually)
    - Agent Version: Incremental version for prompt changes (auto-incremented)
    
    Args:
        project_version: Project version string (e.g., "1.0.0"). If None, uses project's current project version.
        description: Optional description of the prompt
        tags: Optional list of tags for categorization
        auto_version: Whether to automatically increment agent version on changes
        system_name: Optional system name. If None, uses the source filename.
    
    Example:
        @chorus(system_name="my_ai_system", project_version="1.0.0", description="Basic Q&A prompt")
        def ask_question(question: str) -> str:
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Answer: {question}"}
            ]
            return "Answer: " + question
    """
    # Validate project_version parameter if provided
    if project_version is not None and not is_valid_version(project_version):
        raise ValueError(f"Invalid project version format: {project_version}. Expected semantic version (e.g., '1.0.0')")
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start execution timing
            start_time = time.time()
            
            # Set up API interception and context
            interceptor.start_interception()
            context = {'api_calls': []}
            token = _trace_context.set(context)
            
            try:
                # Execute the function (API calls will be intercepted)
                result = func(*args, **kwargs)
                
                # Extract prompt from intercepted API calls
                prompt = extract_prompt_from_messages_runtime(func, *args, **kwargs)
                
                if not prompt:
                    print(f"Warning: No prompt found in function {func.__name__}")
                    return result
            finally:
                # Clean up
                _trace_context.reset(token)
                interceptor.stop_interception()
            
            # Get function arguments for prompt formatting
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Use the intercepted prompt as-is (no formatting needed)
            formatted_prompt = prompt
            
            # Use the provided system_name
            # Get or create shared storage instance for this system
            if system_name not in _storage_instances:
                _storage_instances[system_name] = PromptStorage(source_filename=system_name)
            storage = _storage_instances[system_name]
            
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
            
            # Update prompt version with execution data
            prompt_version.inputs = bound_args.arguments
            prompt_version.output = result
            prompt_version.execution_time = time.time() - start_time
            
            # Store the prompt with execution data
            storage.add_prompt(prompt_version)
            
            # Add prompt info to function metadata
            func._chorus_info = {
                'prompt_version': prompt_version,
                'original_prompt': prompt,
                'formatted_prompt': formatted_prompt,
                'execution_success': True,
                'execution_time': time.time() - start_time
            }
            
            # Return the result
            return result
        
        # Store metadata on the wrapper
        wrapper._chorus_metadata = {
            'project_version': project_version,
            'description': description,
            'tags': tags or [],
            'auto_version': auto_version
        }
        
        return wrapper
    return decorator


