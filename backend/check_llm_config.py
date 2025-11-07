#!/usr/bin/env python3
"""
Helper script to check if LLM configuration is set up correctly.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded .env file from: {env_path}")
else:
    print(f"✗ No .env file found at: {env_path}")
    print(f"  Create one by copying .env.example to .env")

# Check environment variables
allow_cloud = os.getenv("ALLOW_CLOUD", "0")
api_key = os.getenv("OPENAI_API_KEY", "")

print("\nConfiguration Status:")
print(f"  ALLOW_CLOUD: {allow_cloud}")
print(f"  OPENAI_API_KEY: {'✓ Set' if api_key else '✗ Not set'}")

if allow_cloud == "1" and api_key:
    print("\n✓ LLM mode is ENABLED - Ask AI will use GPT-4o")
elif allow_cloud == "1" and not api_key:
    print("\n✗ LLM mode requested but API key missing")
    print("  Set OPENAI_API_KEY in your .env file")
elif allow_cloud != "1":
    print("\n⚠ LLM mode is DISABLED - Ask AI will use local rule-based responses")
    print("  Set ALLOW_CLOUD=1 in your .env file to enable")
else:
    print("\n✗ Configuration incomplete")

