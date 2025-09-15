#!/usr/bin/env python3
"""
Chorus CLI - Command line tool
"""

import argparse
from pathlib import Path
from .core import PromptStorage
from .web_server import start_web_server


def extract_file(args):
    """Extract prompts from a single file."""
    print(f"🔍 Extracting prompts from: {args.file}")
    
    if not Path(args.file).exists():
        print(f"❌ File not found: {args.file}")
        return
    
    # For now, just show how to use the package
    print("Use the @chorus decorator in your Python files:")
    print("""
from chorus import chorus

@chorus(version="1.0.0", description="My prompt")
def my_function(text: str) -> str:
    \"\"\"
    You are a helpful assistant. Process: {text}
    \"\"\"
    return f"Processed: {text}"
    """)
    
    if args.track:
        print("✅ Prompts will be automatically tracked when you run your functions")


def list_prompts(args):
    """List all tracked prompts."""
    storage = PromptStorage()
    all_prompts = storage.list_prompts()
    
    if not all_prompts:
        print("No prompts found in storage.")
        print("Run some functions with @chorus decorator to track prompts.")
        return
    
    print(f"📊 Total prompts: {len(all_prompts)}")
    
    if args.function:
        # Filter by function name
        filtered = [p for p in all_prompts if args.function.lower() in p.function_name.lower()]
        if not filtered:
            print(f"No prompts found for function: {args.function}")
            return
        all_prompts = filtered
    
    # Group by function
    by_function = {}
    for prompt in all_prompts:
        func_name = prompt.function_name
        if func_name not in by_function:
            by_function[func_name] = []
        by_function[func_name].append(prompt)
    
    for func_name, prompts in by_function.items():
        print(f"\n🔧 {func_name}:")
        for prompt in sorted(prompts, key=lambda x: x.version):
            print(f"  📄 v{prompt.version} - {prompt.description}")
            print(f"      Created: {prompt.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      Tags: {', '.join(prompt.tags)}")
            
            # Show execution data if available
            if hasattr(prompt, 'execution_time') and prompt.execution_time is not None:
                print(f"      Execution Time: {prompt.execution_time:.3f}s")
            if hasattr(prompt, 'execution_id') and prompt.execution_id:
                print(f"      Execution ID: {prompt.execution_id}")
            if hasattr(prompt, 'output') and prompt.output is not None:
                output_str = str(prompt.output)
                if len(output_str) > 100:
                    output_str = output_str[:100] + "..."
                print(f"      Output: {output_str}")
            
            if args.verbose:
                print(f"      Prompt: {prompt.prompt}")
                if hasattr(prompt, 'inputs') and prompt.inputs:
                    print(f"      Inputs: {prompt.inputs}")
            print()


def show_prompt(args):
    """Show details of a specific prompt."""
    storage = PromptStorage()
    prompt = storage.get_prompt(args.function, args.version)
    
    if not prompt:
        print(f"❌ Prompt not found: {args.function} v{args.version}")
        return
    
    print(f"📄 Prompt Details: {prompt.function_name} v{prompt.version}")
    print("=" * 50)
    print(f"Description: {prompt.description}")
    print(f"Tags: {', '.join(prompt.tags)}")
    print(f"Created: {prompt.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Hash: {prompt.prompt_hash}")
    
    # Show execution data if available
    if hasattr(prompt, 'execution_id') and prompt.execution_id:
        print(f"Execution ID: {prompt.execution_id}")
    if hasattr(prompt, 'execution_time') and prompt.execution_time is not None:
        print(f"Execution Time: {prompt.execution_time:.3f}s")
    if hasattr(prompt, 'inputs') and prompt.inputs:
        print(f"\nInputs:")
        print("-" * 10)
        for key, value in prompt.inputs.items():
            print(f"  {key}: {value}")
    if hasattr(prompt, 'output') and prompt.output is not None:
        print(f"\nOutput:")
        print("-" * 10)
        print(prompt.output)
    
    print(f"\nPrompt:")
    print("-" * 20)
    print(prompt.prompt)


def export_prompts(args):
    """Export prompts to a file."""
    storage = PromptStorage()
    all_prompts = storage.list_prompts()
    
    if not all_prompts:
        print("No prompts to export.")
        return
    
    output_file = args.output or "prompts_export.json"
    
    import json
    export_data = {
        "exported_at": str(storage.prompts_file.stat().st_mtime),
        "total_prompts": len(all_prompts),
        "prompts": [prompt.to_dict() for prompt in all_prompts]
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"✅ Exported {len(all_prompts)} prompts to {output_file}")


def web_interface(args):
    """Start the web interface for prompt management."""
    start_web_server(port=args.port, open_browser=not args.no_browser)


def main():
    parser = argparse.ArgumentParser(
        description="Chorus CLI - LLM Prompt Versioning Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chorus list --verbose
  chorus show my_function 1.0.0
  chorus export --output my_prompts.json
  chorus web --port 3000
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List tracked prompts')
    list_parser.add_argument('--function', help='Filter by function name')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show full prompt text')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show specific prompt details')
    show_parser.add_argument('function', help='Function name')
    show_parser.add_argument('version', help='Version number')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export prompts to file')
    export_parser.add_argument('--output', '-o', help='Output file name')
    
    # Web command
    web_parser = subparsers.add_parser('web', help='Start web interface')
    web_parser.add_argument('--port', type=int, default=3000, help='Port to run server on')
    web_parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser automatically')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        list_prompts(args)
    elif args.command == 'show':
        show_prompt(args)
    elif args.command == 'export':
        export_prompts(args)
    elif args.command == 'web':
        web_interface(args)


if __name__ == "__main__":
    main()
