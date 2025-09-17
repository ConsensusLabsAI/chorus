# Chorus

A Python package for LLM prompt versioning and tracking with dual versioning system and web interface.

## Features

- **Dual Versioning System**: Project version (semantic) + Agent version (incremental)
- **Automatic Prompt Extraction**: Extracts prompts from function docstrings
- **Execution Tracking**: Captures inputs, outputs, and execution times
- **Web Interface**: Beautiful web UI for prompt management and visualization
- **CLI Tools**: Command-line interface for prompt management
- **Export/Import**: JSON export/import for prompt data
- **Semantic Versioning**: Full support for semantic versioning of prompts

## Installation

```bash
pip install prompt-chorus
```

## Quick Start

### 1. Basic Usage

```python
from chorus import chorus

@chorus(project_version="1.0.0", description="Basic Q&A prompt")
def ask_question(question: str) -> str:
    """
    You are a helpful assistant. Answer: {question}
    """
    return "Answer: " + question

# Run the function - prompts are automatically tracked
result = ask_question("What is Python?")
```

### 2. Auto-versioning

```python
@chorus(description="Auto-versioned prompt")
def process_text(text: str) -> str:
    """
    Process this text: {text}
    """
    return f"Processed: {text}"

# Each time you modify the prompt, agent version auto-increments
```

### 3. CLI Usage

```bash
# List all tracked prompts
chorus list

# Show specific prompt details
chorus show ask_question 1.0.0

# Start web interface
chorus web

# Export prompts
chorus export --output my_prompts.json
```

### 4. Web Interface

```bash
chorus web --port 3000
```

Open your browser to `http://localhost:3000` for a beautiful web interface to manage your prompts.

## Advanced Features

### Dual Versioning System

Chorus uses a dual versioning approach:
- **Project Version**: Semantic version for project changes (e.g., "1.0.0")
- **Agent Version**: Incremental version for prompt changes (auto-incremented)

### Prompt Tracking

- Automatic extraction from function docstrings
- Execution time tracking
- Input/output capture
- Error handling and logging

### Web Interface Features

- Visual prompt management
- Version comparison
- Execution history
- Export/import functionality

## Development

### Setup

```bash
git clone https://github.com/ConsensusLabsAI/prompt-chorus.git
cd src/prompt-chorus
pip install -e .
```

### Testing

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.