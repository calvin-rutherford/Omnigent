import os
from django.conf import settings
import litellm

class UniversalProvider:
    def __init__(self):
        # Allow user to specify which model they want via env var (e.g., 'gpt-4o', 'claude-3-opus-20240229', 'gemini/gemini-1.5-pro')
        self.model = getattr(settings, 'DEFAULT_LLM_MODEL', os.getenv('DEFAULT_LLM_MODEL', 'gemini/gemini-1.5-pro'))
        
        # litellm automatically picks up OPENAI_API_KEY, GEMINI_API_KEY, ANTHROPIC_API_KEY from os.environ
        
    def generate_content(self, system_prompt: str, user_prompt: str = "") -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
            
        try:
            response = litellm.completion(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with LLM Provider ({self.model}): {str(e)}"
