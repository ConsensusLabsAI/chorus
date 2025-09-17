"""
Dual versioning utilities for prompt changes.
- System version: Semantic versioning for project/system changes (set manually)
- Agent version: Incremental version for prompt changes (auto-incremented)
"""

import re
from typing import Tuple, Optional


def get_next_agent_version(current_agent_version: int) -> int:
    """
    Get the next agent version by incrementing the current version.
    
    Args:
        current_agent_version: Current agent version number
        
    Returns:
        Next agent version number
    """
    return current_agent_version + 1


def set_project_version(version: str) -> str:
    """
    Set the project version manually. Validates the version format.
    
    Args:
        version: Semantic version string (e.g., "1.0.0")
        
    Returns:
        The validated version string
        
    Raises:
        ValueError: If the version format is invalid
    """
    if not is_valid_version(version):
        raise ValueError(f"Invalid semantic version format: {version}")
    return version


def get_latest_agent_version_for_function(prompts: dict, function_name: str) -> int:
    """
    Get the latest agent version for a specific function.
    
    Args:
        prompts: Dictionary of prompt versions
        function_name: Name of the function
        
    Returns:
        Latest agent version number, or 0 if no versions exist
    """
    function_prompts = [pv for pv in prompts.values() if pv.function_name == function_name]
    if not function_prompts:
        return 0
    return max(pv.agent_version for pv in function_prompts)


def analyze_prompt_changes(old_prompt: str, new_prompt: str) -> str:
    """
    Analyze changes between old and new prompts to determine version bump type
    following Semantic Versioning principles.
    
    MAJOR: Incompatible changes that break existing functionality
    MINOR: New functionality added in a backward compatible manner  
    PATCH: Backward compatible bug fixes and small improvements
    
    Returns:
        'major', 'minor', or 'patch' based on the nature of changes
    """
    if old_prompt == new_prompt:
        return 'patch'  # No change, but still increment patch
    
    # Normalize prompts for comparison
    old_normalized = _normalize_prompt(old_prompt)
    new_normalized = _normalize_prompt(new_prompt)
    
    # Check for major changes (breaking changes) - highest priority
    if _is_major_change(old_normalized, new_normalized):
        return 'major'
    
    # Check for minor changes (new features/functionality) - second priority
    if _is_minor_change(old_normalized, new_normalized):
        return 'minor'
    
    # Default to patch for small changes, bug fixes, and improvements
    return 'patch'


def _normalize_prompt(prompt: str) -> str:
    """Normalize prompt for comparison by removing extra whitespace and standardizing format."""
    # Remove extra whitespace and normalize line endings
    normalized = re.sub(r'\s+', ' ', prompt.strip())
    # Convert to lowercase for comparison
    return normalized.lower()


def _is_major_change(old_prompt: str, new_prompt: str) -> bool:
    """
    Check if changes constitute a major version bump (breaking changes).
    
    MAJOR changes are incompatible changes that break existing functionality:
    - Changing the expected input/output format
    - Removing or significantly altering core functionality
    - Changing the fundamental approach or methodology
    """
    # Keywords that indicate breaking changes
    breaking_keywords = [
        'instead of', 'no longer', 'removed', 'deprecated', 'breaking',
        'change from', 'replaced with', 'completely different', 'new approach',
        'different format', 'different structure', 'different output',
        'must not', 'cannot', 'will not', 'discontinued', 'obsolete',
        'migrate to', 'upgrade to', 'switch to', 'abandoned'
    ]
    
    # Check if new prompt contains breaking change indicators
    for keyword in breaking_keywords:
        if keyword in new_prompt and keyword not in old_prompt:
            return True
    
    # Check for fundamental structural changes
    old_sentences = old_prompt.split('.')
    new_sentences = new_prompt.split('.')
    
    # If more than 60% of sentences changed, it's likely major
    if len(new_sentences) > 0 and len(old_sentences) > 0:
        changed_ratio = abs(len(new_sentences) - len(old_sentences)) / max(len(old_sentences), 1)
        if changed_ratio > 0.6:
            return True
    
    # Check for complete rewrite (very different content)
    if len(new_prompt) > 0 and len(old_prompt) > 0:
        # Calculate word-based similarity
        old_words = set(old_prompt.split())
        new_words = set(new_prompt.split())
        common_words = old_words & new_words
        total_words = old_words | new_words
        
        if len(total_words) > 0:
            similarity = len(common_words) / len(total_words)
            # If less than 25% similarity, consider it a major rewrite
            if similarity < 0.25:
                return True
    
    # Check for significant length changes that might indicate major restructuring
    if len(old_prompt) > 0:
        length_change_ratio = abs(len(new_prompt) - len(old_prompt)) / len(old_prompt)
        if length_change_ratio > 0.8:  # 80% change in length
            return True
    
    return False


def _is_minor_change(old_prompt: str, new_prompt: str) -> bool:
    """
    Check if changes constitute a minor version bump (new features).
    
    MINOR changes add new functionality in a backward compatible manner:
    - Adding new capabilities without breaking existing ones
    - Enhancing existing functionality
    - Adding new options or parameters
    - Extending the prompt's scope or capabilities
    """
    # Keywords that indicate new features or enhancements
    feature_keywords = [
        'also', 'additionally', 'new', 'enhanced', 'improved', 'better',
        'more', 'extra', 'additional', 'further', 'extended', 'expanded',
        'support for', 'now supports', 'can also', 'in addition',
        'optionally', 'option', 'feature', 'capability', 'functionality',
        'include', 'incorporate', 'integrate', 'combine', 'merge'
    ]
    
    # Check if new prompt contains feature indicators
    for keyword in feature_keywords:
        if keyword in new_prompt and keyword not in old_prompt:
            return True
    
    # Check for significant additions (new sentences/phrases)
    old_words = set(old_prompt.split())
    new_words = set(new_prompt.split())
    new_words_only = new_words - old_words
    
    # If significant new vocabulary was added, it might be minor
    if len(new_words_only) > 8:  # More than 8 new words indicates substantial addition
        return True
    
    # Check for length increase (new content added)
    if len(old_prompt) > 0 and len(new_prompt) > len(old_prompt) * 1.3:  # 30% increase in length
        return True
    
    # Check for new sentence additions (count sentences)
    old_sentences = [s.strip() for s in old_prompt.split('.') if s.strip()]
    new_sentences = [s.strip() for s in new_prompt.split('.') if s.strip()]
    
    if len(new_sentences) > len(old_sentences) + 1:  # More than one new sentence
        return True
    
    # Check for new functionality indicators (phrases that suggest new capabilities)
    functionality_indicators = [
        'you can now', 'it is now possible', 'added support',
        'new feature', 'enhanced with', 'upgraded to include',
        'now includes', 'now provides', 'now offers'
    ]
    
    for indicator in functionality_indicators:
        if indicator in new_prompt and indicator not in old_prompt:
            return True
    
    return False


def bump_project_version(current_version: str, bump_type: str) -> str:
    """Bump project version based on the change type."""
    major, minor, patch = parse_version_parts(current_version)
    
    if bump_type == 'major':
        return f"{major + 1}.0.0"
    elif bump_type == 'minor':
        return f"{major}.{minor + 1}.0"
    else:  # patch
        return f"{major}.{minor}.{patch + 1}"


def create_versioned_prompt(
    prompt: str,
    function_name: str,
    project_version: str,
    prompts: dict,
    description: Optional[str] = None,
    tags: Optional[list] = None
) -> 'PromptVersion':
    """
    Create a new versioned prompt with automatic agent version increment.
    
    Args:
        prompt: The prompt text
        function_name: Name of the function
        project_version: Current project version (semantic version)
        prompts: Dictionary of existing prompt versions
        description: Optional description
        tags: Optional tags
        
    Returns:
        New PromptVersion instance
    """
    from .models import PromptVersion
    
    # Get the next agent version for this function
    latest_agent_version = get_latest_agent_version_for_function(prompts, function_name)
    next_agent_version = get_next_agent_version(latest_agent_version)
    
    return PromptVersion(
        prompt=prompt,
        project_version=project_version,
        agent_version=next_agent_version,
        function_name=function_name,
        description=description,
        tags=tags
    )


def bump_agent_version(current_agent_version: int) -> int:
    """
    Bump agent version by incrementing the current version.
    
    Args:
        current_agent_version: Current agent version number
        
    Returns:
        Next agent version number
    """
    return current_agent_version + 1


def parse_version_parts(version: str) -> Tuple[int, int, int]:
    """
    Parse version string into major, minor, patch parts.
    
    Handles semantic versions with pre-release and build metadata:
    - 1.0.0 -> (1, 0, 0)
    - 1.0.0-alpha -> (1, 0, 0)
    - 1.0.0+20130313144700 -> (1, 0, 0)
    - 1.0.0-alpha+001 -> (1, 0, 0)
    """
    # Remove pre-release and build metadata for parsing
    clean_version = version.split('-')[0].split('+')[0]
    parts = clean_version.split('.')
    
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    
    return major, minor, patch


def is_valid_version(version: str) -> bool:
    """
    Check if version string is a valid semantic version.
    
    Supports:
    - Basic semantic version: 1.0.0
    - Pre-release versions: 1.0.0-alpha, 1.0.0-alpha.1, 1.0.0-beta.2
    - Build metadata: 1.0.0+20130313144700, 1.0.0-alpha+001
    """
    if not version or not isinstance(version, str):
        return False
    
    # Full semantic version pattern with pre-release and build metadata support
    pattern = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
    return bool(re.match(pattern, version.strip()))
