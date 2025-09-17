"""
Core data models for Chorus prompt versioning.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional


class PromptVersion:
    """Versioned prompt with semantic versioning and execution tracking."""
    
    def __init__(
        self,
        prompt: str,
        project_version: str,
        agent_version: int,
        function_name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        inputs: Optional[Dict[str, Any]] = None,
        output: Optional[Any] = None,
        execution_time: Optional[float] = None,
        execution_id: Optional[str] = None
    ):
        self.prompt = prompt
        self.project_version = project_version  # Semantic version for project
        self.agent_version = agent_version      # Incremental version for prompt changes
        self.function_name = function_name
        self.description = description or ""
        self.tags = tags or []
        self.created_at = created_at or datetime.now()
        self.prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        
        # Execution tracking
        self.inputs = inputs or {}
        self.output = output
        self.execution_time = execution_time
        self.execution_id = execution_id or f"{self.created_at.strftime('%Y%m%d_%H%M%S')}_{self.prompt_hash}"
    
    @property
    def version(self) -> str:
        """Get the combined version string for backward compatibility."""
        return f"{self.project_version}.{self.agent_version}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'prompt': self.prompt,
            'project_version': self.project_version,
            'agent_version': self.agent_version,
            'function_name': self.function_name,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'prompt_hash': self.prompt_hash,
            'inputs': self.inputs,
            'output': self.output,
            'execution_time': self.execution_time,
            'execution_id': self.execution_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptVersion':
        """Create from dictionary."""
        # Handle backward compatibility for old version field
        if 'version' in data and 'project_version' not in data and 'system_version' not in data:
            project_version = data['version']
            agent_version = 1  # Default agent version for backward compatibility
        elif 'system_version' in data:
            # Handle old system_version field
            project_version = data['system_version']
            agent_version = data['agent_version']
        else:
            project_version = data['project_version']
            agent_version = data['agent_version']
        
        return cls(
            prompt=data['prompt'],
            project_version=project_version,
            agent_version=agent_version,
            function_name=data['function_name'],
            description=data.get('description'),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            inputs=data.get('inputs', {}),
            output=data.get('output'),
            execution_time=data.get('execution_time'),
            execution_id=data.get('execution_id')
        )
