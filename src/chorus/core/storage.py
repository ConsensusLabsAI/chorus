"""
Storage and retrieval of prompt versions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import PromptVersion


class PromptStorage:
    """Handles storage and retrieval of prompt versions."""
    
    def __init__(self, storage_path: str = ".prompts", source_filename: str = "run"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.source_filename = source_filename
        self.prompts_file = self.storage_path / "prompts.json"  # Keep for backward compatibility
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompts from storage - from both legacy file and timestamped files."""
        self.prompts = {}
        
        # First, try to load from the most recent timestamped file
        timestamped_files = self.list_timestamped_files()
        if timestamped_files:
            # Load from the most recent timestamped file
            latest_file = timestamped_files[0]
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.prompts[k] = PromptVersion.from_dict(v)
                return  # Use the latest timestamped file as the source of truth
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load latest file {latest_file}: {e}")
        
        # Fallback to legacy prompts.json file if no timestamped files or error
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.prompts[k] = PromptVersion.from_dict(v)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load legacy file {self.prompts_file}: {e}")
                self.prompts = {}
    
    def _save_prompts(self) -> None:
        """Save prompts to storage in timestamped file format."""
        data = {k: v.to_dict() for k, v in self.prompts.items()}
        
        # Create timestamped filename with source filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"prompts_{self.source_filename}_{timestamp}.json"
        timestamped_file = self.storage_path / filename
        
        # Save to timestamped file
        with open(timestamped_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Also update the legacy file for backward compatibility
        with open(self.prompts_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_prompt(self, prompt_version: PromptVersion) -> None:
        """Add a new prompt version."""
        key = f"{prompt_version.function_name}_{prompt_version.project_version}_{prompt_version.agent_version}"
        self.prompts[key] = prompt_version
        self._save_prompts()
    
    def get_prompt(self, function_name: str, project_version: str, agent_version: int) -> Optional[PromptVersion]:
        """Get a specific prompt version."""
        key = f"{function_name}_{project_version}_{agent_version}"
        return self.prompts.get(key)
    
    def get_prompt_by_combined_version(self, function_name: str, version: str) -> Optional[PromptVersion]:
        """Get a specific prompt version by combined version string (for backward compatibility)."""
        key = f"{function_name}_{version}"
        return self.prompts.get(key)
    
    def get_latest_version(self, function_name: str) -> Optional[PromptVersion]:
        """Get the latest version of a prompt for a function (by agent version)."""
        versions = [pv for pv in self.prompts.values() if pv.function_name == function_name]
        if not versions:
            return None
        return max(versions, key=lambda x: x.agent_version)
    
    def get_latest_project_version(self, function_name: str) -> Optional[PromptVersion]:
        """Get the latest version of a prompt for a function (by project version)."""
        versions = [pv for pv in self.prompts.values() if pv.function_name == function_name]
        if not versions:
            return None
        return max(versions, key=lambda x: self._parse_version(x.project_version))
    
    def _parse_version(self, version: str) -> tuple:
        """Parse semantic version for comparison."""
        from .versioning import parse_version_parts
        return parse_version_parts(version)
    
    def list_prompts(self, function_name: Optional[str] = None) -> List[PromptVersion]:
        """List all prompts, optionally filtered by function name."""
        if function_name:
            return [pv for pv in self.prompts.values() if pv.function_name == function_name]
        return list(self.prompts.values())
    
    def get_current_run_filename(self) -> str:
        """Get the filename for the current run's timestamped file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"prompts_{self.source_filename}_{timestamp}.json"
    
    def list_timestamped_files(self) -> List[Path]:
        """List all timestamped prompt files, sorted by creation time."""
        timestamped_files = list(self.storage_path.glob("prompts_*.json"))
        return sorted(timestamped_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def set_project_version(self, project_version: str) -> None:
        """
        Set the project version for the project. This should be called once manually.
        """
        from .versioning import set_project_version
        validated_version = set_project_version(project_version)
        
        # Load existing project versions
        project_versions = self._load_project_versions()
        
        # Update the version for this project
        project_versions[self.source_filename] = validated_version
        
        # Save back to file
        self._save_project_versions(project_versions)
    
    def get_project_version(self) -> Optional[str]:
        """
        Get the current project version for this project.
        """
        project_versions = self._load_project_versions()
        return project_versions.get(self.source_filename)
    
    def _load_project_versions(self) -> dict:
        """Load project versions from JSON file."""
        project_version_file = self.storage_path / "project_version.json"
        if project_version_file.exists():
            try:
                with open(project_version_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_project_versions(self, project_versions: dict) -> None:
        """Save project versions to JSON file."""
        project_version_file = self.storage_path / "project_version.json"
        with open(project_version_file, 'w') as f:
            json.dump(project_versions, f, indent=2)
    
    def list_all_project_versions(self) -> dict:
        """
        Get all project versions for all projects.
        
        Returns:
            Dictionary mapping project names to their project versions
        """
        return self._load_project_versions()
