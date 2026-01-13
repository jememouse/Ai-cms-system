import requests
import sys
import os
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config

def call_llm(prompt: str, system_prompt: str = None, model: str = None, temperature: float = 1.0) -> str:
    """
    统一的 LLM 调用工具
    """
    api_key = config.LLM_API_KEY
    api_url = config.LLM_API_URL
    model = model or config.LLM_MODEL
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 针对 OpenRouter/DeepSeek 的特殊头
    if "openrouter" in api_url or "deepseek" in api_url:
        headers["HTTP-Referer"] = "https://github.com/jememouse/deepseek-feisu-cms"
        headers["X-Title"] = "DeepSeek CMS Agent"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            if 'choices' in data:
                return data['choices'][0]['message']['content']
            else:
                print(f"   ❌ LLM Unexpected Response: {data}")
                return ""
        else:
            print(f"   ❌ LLM Error: {resp.status_code} - {resp.text}")
            return ""
    except Exception as e:
        print(f"   ❌ Request Error: {e}")
        return ""
