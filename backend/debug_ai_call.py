import os
import sys
from app.core.config import settings

try:
    from openai import OpenAI
    print("OpenAI module available: Yes")
except ImportError:
    print("OpenAI module available: No")

print(f"SILICONFLOW_API_KEY configured: {'Yes' if settings.SILICONFLOW_API_KEY else 'No'}")
print(f"SILICONFLOW_MODEL: {settings.SILICONFLOW_MODEL}")

if settings.SILICONFLOW_API_KEY:
    try:
        client = OpenAI(base_url="https://api.siliconflow.cn/v1", api_key=settings.SILICONFLOW_API_KEY)
        print("Testing API connection...")
        response = client.chat.completions.create(
            model=settings.SILICONFLOW_MODEL or "Qwen/Qwen2.5-7B-Instruct",
            messages=[
                {"role": "user", "content": "Hello, say something in Chinese."}
            ],
            max_tokens=50
        )
        print("API Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"API Call Failed: {e}")
else:
    print("Skipping API test because API Key is missing.")
