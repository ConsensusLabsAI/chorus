# Chorus

A Python package for LLM prompt versioning and tracking with dual versioning system and web interface.

## Features

- **Dual Versioning System**: Project version (semantic) + Agent version (incremental)
- **Automatic Prompt Interception**: Automatically intercepts and extracts prompts from LLM API calls
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
from prompt_chorus import chorus

@chorus(system_name="my_ai_system", project_version="1.0.0", description="Basic Q&A prompt")
def ask_question(question: str) -> str:
    # Your LLM API calls are automatically intercepted and prompts extracted
    import openai
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Answer: {question}"}
        ]
    )
    return response.choices[0].message.content

# Run the function - prompts are automatically tracked
result = ask_question("What is Python?")
```

### 2. Auto-versioning

```python
@chorus(system_name="text_processor", description="Auto-versioned prompt")
def process_text(text: str) -> str:
    # Prompts from any LLM API call are automatically captured
    import anthropic
    response = anthropic.Anthropic().messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"Process this text: {text}"}
        ]
    )
    return response.content[0].text

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

## How It Works

Chorus automatically intercepts LLM API calls made within decorated functions and extracts the prompts for versioning. No need to manually specify prompts - just use your existing LLM libraries normally.

### Supported LLM Providers

- **OpenAI**: `openai.ChatCompletion.create()`, `openai.Completion.create()`
- **Anthropic**: `anthropic.Anthropic().messages.create()`
- **Google**: `google.generativeai.GenerativeModel.generate_content()`
- **Cohere**: `cohere.Client().chat()`, `cohere.Client().generate()`
- **LangChain**: All LangChain LLM calls
- **And more**: Extensible architecture for additional providers


## Advanced Features

### Dual Versioning System

Chorus uses a dual versioning approach:
- **Project Version**: Semantic version for project changes (e.g., "1.0.0")
- **Agent Version**: Incremental version for prompt changes (auto-incremented)

### Prompt Tracking

- Automatic interception of LLM API calls (OpenAI, Anthropic, etc.)
- Real-time prompt extraction from intercepted messages
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
cd prompt-chorus
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