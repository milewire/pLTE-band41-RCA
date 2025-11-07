#!/usr/bin/env python3
"""
Test script to verify OpenAI API connection for Ask AI feature.
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env file from: {env_path}")
else:
    print(f"[ERROR] No .env file found at: {env_path}")
    print(f"  Create one with: ALLOW_CLOUD=1 and OPENAI_API_KEY=your-key")

# Check configuration
allow_cloud = os.getenv("ALLOW_CLOUD", "0")
api_key = os.getenv("OPENAI_API_KEY", "")

print("\n" + "="*60)
print("Ask AI Configuration Check")
print("="*60)
print(f"ALLOW_CLOUD: {allow_cloud}")
print(f"OPENAI_API_KEY: {'[OK] Set (' + str(len(api_key)) + ' chars)' if api_key else '[ERROR] Not set'}")

if allow_cloud != "1":
    print("\n[WARNING] LLM mode is DISABLED")
    print("  Set ALLOW_CLOUD=1 in backend/.env to enable")
    sys.exit(1)

if not api_key:
    print("\n[ERROR] API key is missing")
    print("  Set OPENAI_API_KEY in backend/.env")
    sys.exit(1)

# Test OpenAI connection
print("\n" + "="*60)
print("Testing OpenAI API Connection...")
print("="*60)

try:
    from openai import OpenAI
    
    # Check for proxy environment variables that might interfere
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    has_proxy = any(os.getenv(var) for var in proxy_vars)
    if has_proxy:
        print(f"[INFO] Proxy environment variables detected")
    
    # Initialize client with just the API key
    print(f"Initializing OpenAI client...")
    client = OpenAI(api_key=api_key.strip())
    
    # Make a simple test call
    print("Making test API call...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, Ask AI is working!' in one sentence."}
        ],
        max_tokens=50
    )
    
    answer = response.choices[0].message.content.strip()
    print(f"\n[SUCCESS] OpenAI API Connection: WORKING")
    print(f"  Response: {answer}")
    print(f"\n[SUCCESS] Ask AI is configured and ready to use GPT-4o!")
    
except ImportError:
    print("\n[ERROR] OpenAI library not installed")
    print("  Install with: pip install openai")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] OpenAI API Connection: FAILED")
    print(f"  Error: {str(e)}")
    print(f"\n  Check:")
    print(f"  1. Your API key is valid")
    print(f"  2. You have API credits/quota")
    print(f"  3. Your network can reach OpenAI servers")
    sys.exit(1)

