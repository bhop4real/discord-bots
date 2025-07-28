from openai import OpenAI
from .base_provider import BaseProvider

class DeepSeekProvider(BaseProvider):
    def __init__(self, api_key):
        if not api_key or 'your_deepseek_api_key' in api_key:
            raise ValueError("DeepSeek API key is missing or is a placeholder. Please check your config.py file.")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )

    def get_response(self, messages, model, max_tokens):
        """
        Gets a response from the DeepSeek API.

        Returns the entire response object to allow access to metadata
        like reasoning (Chain of Thought).
        """
        return self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens
        )