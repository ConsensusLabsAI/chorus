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
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompts from storage - from system version files."""
        self.prompts = {}
        
        # Load from the most recent system version file
        system_files = self.list_system_files()
        if system_files:
            # Load from the most recent system file
            latest_file = system_files[0]
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    # Handle new format with metadata
                    if "prompts" in data:
                        for k, v in data["prompts"].items():
                            self.prompts[k] = PromptVersion.from_dict(v)
                return  # Use the latest system file as the source of truth
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not load latest file {latest_file}: {e}")
                self.prompts = {}
    
    def _save_prompts(self) -> None:
        """Save prompts to storage in system_name_version_timestamp.json format."""
        # Get current project version for this system
        current_project_version = self.get_project_version() or "1.0.0"
        
        # Create timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename in format: system_name_version_timestamp.json
        filename = f"{self.source_filename}_{current_project_version}_{timestamp}.json"
        system_file = self.storage_path / filename
        
        # Prepare data with metadata about this run
        run_data = {
            "system_name": self.source_filename,
            "project_version": current_project_version,
            "created_at": datetime.now().isoformat(),
            "total_prompts": len(self.prompts),
            "prompts": {k: v.to_dict() for k, v in self.prompts.items()}
        }
        
        # Save to system version file
        with open(system_file, 'w') as f:
            json.dump(run_data, f, indent=2)
    
    def add_prompt(self, prompt_version: PromptVersion) -> None:
        """Add a new prompt version."""
        key = f"{prompt_version.function_name}_{prompt_version.project_version}_{prompt_version.agent_version}"
        self.prompts[key] = prompt_version
        self._save_prompts()
    
    def get_prompt(self, function_name: str, project_version: str, agent_version: int) -> Optional[PromptVersion]:
        """Get a specific prompt version."""
        key = f"{function_name}_{project_version}_{agent_version}"
        return self.prompts.get(key)
    
    def list_prompts(self, function_name: Optional[str] = None) -> List[PromptVersion]:
        """List all prompts, optionally filtered by function name."""
        if function_name:
            return [pv for pv in self.prompts.values() if pv.function_name == function_name]
        return list(self.prompts.values())
    
    def list_system_files(self) -> List[Path]:
        """List all system version files, sorted by creation time."""
        # Look for files matching pattern: system_name_version_timestamp.json
        system_files = []
        for file_path in self.storage_path.glob("*.json"):
            # Skip project version file
            if file_path.name == "project_version.json":
                continue
            # Check if it matches the naming pattern: system_name_version_timestamp.json
            # Should have at least 2 underscores (system_version_timestamp)
            if file_path.stem.count("_") >= 2:
                system_files.append(file_path)
        return sorted(system_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
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
    
    def list_all_runs(self) -> List[dict]:
        """
        List all runs with their metadata.
        
        Returns:
            List of dictionaries with run metadata
        """
        runs = []
        for system_file in self.list_system_files():
            try:
                with open(system_file, 'r') as f:
                    data = json.load(f)
                    # Extract timestamp from filename
                    filename_parts = system_file.stem.split("_")
                    timestamp = filename_parts[-1] if len(filename_parts) >= 3 else "unknown"
                    
                    runs.append({
                        "system_name": data.get("system_name"),
                        "project_version": data.get("project_version"),
                        "timestamp": timestamp,
                        "created_at": data.get("created_at"),
                        "total_prompts": data.get("total_prompts"),
                        "file_path": str(system_file)
                    })
            except (json.JSONDecodeError, KeyError):
                continue
        return runs
