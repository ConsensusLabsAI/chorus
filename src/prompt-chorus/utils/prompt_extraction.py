"""
Utilities for extracting prompts from API calls and function source code.
"""

import inspect
import re
import functools
from contextvars import ContextVar
from typing import Optional, Callable, Dict, List, Any

# Context to store intercepted API calls
_trace_context: ContextVar[Dict] = ContextVar('trace_context', default=None)

class APIInterceptor:
    def __init__(self):
        self.original_methods = {}
        self.active = False
    
    def start_interception(self):
        """Begin intercepting API calls"""
        if self.active:
            return
        
        self._patch_openai()
        self._patch_anthropic()
        self._patch_google()
        self._patch_cohere()
        self._patch_langchain()
        self.active = True
    
    def stop_interception(self):
        """Restore original methods"""
        for key, original_method in self.original_methods.items():
            self._restore_method(key, original_method)
        self.original_methods.clear()
        self.active = False
    
    def _patch_openai(self):
        """Patch OpenAI API calls"""
        try:
            from openai import OpenAI
            from openai.resources.chat import completions
            
            # Patch the new OpenAI v1.0+ API
            original_create = completions.Completions.create
            self.original_methods['openai_chat_create'] = original_create
            
            def intercepted_create(self, **kwargs):
                # Use the global interceptor instance
                prompt_data = interceptor._extract_openai_prompt(kwargs)
                interceptor._store_api_call('openai', prompt_data, kwargs)
                return original_create(self, **kwargs)
            
            completions.Completions.create = intercepted_create
                    
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch OpenAI: {e}")
    
    def _patch_anthropic(self):
        """Patch Anthropic API calls"""
        try:
            import anthropic
            
            # Store the original class
            original_anthropic_class = anthropic.Anthropic
            self.original_methods['anthropic_class'] = original_anthropic_class
            
            # Create a custom Anthropic class with intercepted messages
            class InterceptedAnthropic(original_anthropic_class):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # Store the original messages
                    self._original_messages = super().messages
                
                @property
                def messages(self):
                    return InterceptedMessages(self._original_messages)
            
            class InterceptedMessages:
                def __init__(self, original_messages):
                    self._original = original_messages
                
                def create(self, **kwargs):
                    prompt_data = interceptor._extract_anthropic_prompt(kwargs)
                    interceptor._store_api_call('anthropic', prompt_data, kwargs)
                    return self._original.create(**kwargs)
            
            # Replace the Anthropic class
            anthropic.Anthropic = InterceptedAnthropic
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch Anthropic: {e}")
    
    def _patch_google(self):
        """Patch Google Gemini API calls"""
        try:
            import google.generativeai as genai
            
            # Patch the generate_content method
            original_generate = genai.GenerativeModel.generate_content
            self.original_methods['google_generate_content'] = original_generate
            
            def intercepted_generate(self, contents, **kwargs):
                prompt_data = self._extract_google_prompt(contents, kwargs)
                self._store_api_call('google', prompt_data, kwargs)
                return original_generate(self, contents, **kwargs)
            
            genai.GenerativeModel.generate_content = intercepted_generate
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch Google: {e}")
    
    def _patch_cohere(self):
        """Patch Cohere API calls"""
        try:
            import cohere
            
            # Patch the chat method
            original_chat = cohere.Client.chat
            self.original_methods['cohere_chat'] = original_chat
            
            def intercepted_chat(self, message, **kwargs):
                prompt_data = self._extract_cohere_prompt(message, kwargs)
                self._store_api_call('cohere', prompt_data, kwargs)
                return original_chat(self, message, **kwargs)
            
            cohere.Client.chat = intercepted_chat
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch Cohere: {e}")
    
    def _patch_langchain(self):
        """Patch LangChain LLM calls"""
        try:
            # Patch common LangChain LLM classes
            self._patch_langchain_llm()
            self._patch_langchain_chat_models()
            self._patch_langchain_chains()
            
        except Exception as e:
            print(f"Failed to patch LangChain: {e}")
    
    def _patch_langchain_llm(self):
        """Patch LangChain LLM classes"""
        try:
            from langchain.llms.base import LLM
            from langchain.llms.openai import OpenAI
            from langchain.llms.anthropic import Anthropic
            
            # Patch base LLM invoke method
            original_invoke = LLM.invoke
            self.original_methods['langchain_llm_invoke'] = original_invoke
            
            def intercepted_invoke(self, input, **kwargs):
                prompt_data = self._extract_langchain_prompt(input, kwargs)
                self._store_api_call('langchain_llm', prompt_data, kwargs)
                return original_invoke(self, input, **kwargs)
            
            LLM.invoke = intercepted_invoke
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch LangChain LLM: {e}")
    
    def _patch_langchain_chat_models(self):
        """Patch LangChain Chat Models"""
        try:
            from langchain.chat_models.base import BaseChatModel
            from langchain.schema import HumanMessage, SystemMessage
            
            # Patch chat model invoke method
            original_invoke = BaseChatModel.invoke
            self.original_methods['langchain_chat_invoke'] = original_invoke
            
            def intercepted_invoke(self, input, **kwargs):
                prompt_data = self._extract_langchain_chat_prompt(input, kwargs)
                self._store_api_call('langchain_chat', prompt_data, kwargs)
                return original_invoke(self, input, **kwargs)
            
            BaseChatModel.invoke = intercepted_invoke
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch LangChain Chat Models: {e}")
    
    def _patch_langchain_chains(self):
        """Patch LangChain Chains"""
        try:
            from langchain.chains.base import Chain
            from langchain.chains.llm import LLMChain
            
            # Patch chain invoke method
            original_invoke = Chain.invoke
            self.original_methods['langchain_chain_invoke'] = original_invoke
            
            def intercepted_invoke(self, input, **kwargs):
                prompt_data = self._extract_langchain_chain_prompt(input, kwargs)
                self._store_api_call('langchain_chain', prompt_data, kwargs)
                return original_invoke(self, input, **kwargs)
            
            Chain.invoke = intercepted_invoke
            
        except ImportError:
            pass
        except Exception as e:
            print(f"Failed to patch LangChain Chains: {e}")
    
    def _extract_openai_prompt(self, kwargs):
        """Extract meaningful prompt parts from OpenAI API call"""
        messages = kwargs.get('messages', [])
        
        system_prompt = None
        user_prompt = None
        conversation_history = []
        
        for message in messages:
            role = message.get('role')
            content = message.get('content', '')
            
            if role == 'system':
                system_prompt = content
            elif role == 'user':
                user_prompt = content  # Take the last user message
            elif role == 'assistant':
                conversation_history.append(content)
        
        return {
            'messages': messages,
            'system_prompt': system_prompt,
            'user_prompt': user_prompt,
            'conversation_history': conversation_history
        }
    
    def _extract_anthropic_prompt(self, kwargs):
        """Extract prompt from Anthropic API call"""
        messages = kwargs.get('messages', [])
        
        # Find the last user message
        user_prompt = None
        for message in reversed(messages):
            if message.get('role') == 'user':
                content = message.get('content')
                if isinstance(content, str):
                    user_prompt = content
                elif isinstance(content, list):
                    # Handle multi-part content (text + images)
                    text_parts = [part['text'] for part in content if part.get('type') == 'text']
                    user_prompt = ' '.join(text_parts)
                break
        
        return {
            'messages': messages,
            'user_prompt': user_prompt,
            'system_prompt': kwargs.get('system', '')
        }
    
    def _extract_google_prompt(self, contents, kwargs):
        """Extract prompt from Google Gemini API call"""
        # Google Gemini uses different parameter names
        system_instruction = kwargs.get('system_instruction', '')
        
        # Contents can be a string or list of parts
        if isinstance(contents, str):
            user_prompt = contents
        elif isinstance(contents, list):
            # Handle multi-part content
            text_parts = []
            for part in contents:
                if hasattr(part, 'text'):
                    text_parts.append(part.text)
                elif isinstance(part, str):
                    text_parts.append(part)
            user_prompt = ' '.join(text_parts)
        else:
            user_prompt = str(contents)
        
        return {
            'user_prompt': user_prompt,
            'system_prompt': system_instruction,
            'contents': contents
        }
    
    def _extract_cohere_prompt(self, message, kwargs):
        """Extract prompt from Cohere API call"""
        # Cohere uses different parameter names
        system_prompt = kwargs.get('preamble', '')
        
        # Message can be a string or list
        if isinstance(message, str):
            user_prompt = message
        elif isinstance(message, list):
            # Handle conversation history
            user_prompt = message[-1].get('message', '') if message else ''
        else:
            user_prompt = str(message)
        
        return {
            'user_prompt': user_prompt,
            'system_prompt': system_prompt,
            'message': message
        }
    
    def _extract_langchain_prompt(self, input, kwargs):
        """Extract prompt from LangChain LLM call"""
        # LangChain LLMs typically take a string input
        user_prompt = str(input) if input else ""
        
        return {
            'user_prompt': user_prompt,
            'system_prompt': None,
            'input': input
        }
    
    def _extract_langchain_chat_prompt(self, input, kwargs):
        """Extract prompt from LangChain Chat Model call"""
        system_prompt = None
        user_prompt = None
        
        if isinstance(input, list):
            # Handle list of messages
            for message in input:
                if hasattr(message, 'content'):
                    if hasattr(message, 'type') and message.type == 'system':
                        system_prompt = message.content
                    elif hasattr(message, 'type') and message.type == 'human':
                        user_prompt = message.content
                    elif hasattr(message, '__class__') and 'SystemMessage' in str(message.__class__):
                        system_prompt = message.content
                    elif hasattr(message, '__class__') and 'HumanMessage' in str(message.__class__):
                        user_prompt = message.content
        elif hasattr(input, 'content'):
            # Single message object
            if hasattr(input, 'type') and input.type == 'system':
                system_prompt = input.content
            elif hasattr(input, 'type') and input.type == 'human':
                user_prompt = input.content
            elif hasattr(input, '__class__') and 'SystemMessage' in str(input.__class__):
                system_prompt = input.content
            elif hasattr(input, '__class__') and 'HumanMessage' in str(input.__class__):
                user_prompt = input.content
        else:
            # String input
            user_prompt = str(input)
        
        return {
            'user_prompt': user_prompt,
            'system_prompt': system_prompt,
            'input': input
        }
    
    def _extract_langchain_chain_prompt(self, input, kwargs):
        """Extract prompt from LangChain Chain call"""
        # Chains can have complex input structures
        if isinstance(input, dict):
            # Look for common prompt keys
            user_prompt = input.get('question', input.get('query', input.get('input', '')))
            system_prompt = input.get('system', input.get('instructions', ''))
        else:
            user_prompt = str(input)
            system_prompt = None
        
        return {
            'user_prompt': user_prompt,
            'system_prompt': system_prompt,
            'input': input
        }
    
    def _store_api_call(self, provider: str, prompt_data: Dict, raw_kwargs: Dict):
        """Store the API call data in context"""
        context = _trace_context.get()
        if context is not None:
            api_call = {
                'provider': provider,
                'model': raw_kwargs.get('model'),
                'prompt': prompt_data.get('user_prompt'),
                'system_prompt': prompt_data.get('system_prompt'),
                'full_messages': prompt_data.get('messages'),
                'raw_kwargs': raw_kwargs
            }
            context.setdefault('api_calls', []).append(api_call)
            print(f"🔍 Stored API call: {provider} - {prompt_data.get('user_prompt', 'No prompt')[:50]}...")
        else:
            print(f"⚠️ No context available for API call: {provider}")
    
    def _restore_method(self, key: str, original_method):
        """Restore the original method"""
        if key == 'openai_chat_create':
            try:
                import openai
                if hasattr(openai, 'ChatCompletion'):
                    openai.ChatCompletion.create = original_method
                else:
                    from openai.resources.chat import completions
                    completions.Completions.create = original_method
            except ImportError:
                pass
        elif key == 'anthropic_class':
            try:
                import anthropic
                anthropic.Anthropic = original_method
            except ImportError:
                pass
        elif key == 'google_generate_content':
            try:
                import google.generativeai as genai
                genai.GenerativeModel.generate_content = original_method
            except ImportError:
                pass
        elif key == 'cohere_chat':
            try:
                import cohere
                cohere.Client.chat = original_method
            except ImportError:
                pass
        elif key == 'langchain_llm_invoke':
            try:
                from langchain.llms.base import LLM
                LLM.invoke = original_method
            except ImportError:
                pass
        elif key == 'langchain_chat_invoke':
            try:
                from langchain.chat_models.base import BaseChatModel
                BaseChatModel.invoke = original_method
            except ImportError:
                pass
        elif key == 'langchain_chain_invoke':
            try:
                from langchain.chains.base import Chain
                Chain.invoke = original_method
            except ImportError:
                pass

# Global interceptor instance
interceptor = APIInterceptor()

def extract_prompt_from_messages_runtime(func: Callable, *args, **kwargs) -> Optional[str]:
    """Extract prompt from intercepted API calls."""
    context = _trace_context.get()
    
    if context and 'api_calls' in context:
        # Get the most recent API call
        api_calls = context['api_calls']
        
        if api_calls:
            latest_call = api_calls[-1]
            
            # Combine system and user prompts
            system_prompt = latest_call.get('system_prompt', '')
            user_prompt = latest_call.get('prompt', '')
            
            if system_prompt and user_prompt:
                return f"System: {system_prompt}\n\nUser: {user_prompt}"
            elif user_prompt:
                return user_prompt
            elif system_prompt:
                return system_prompt
    
    return None

