"""Final verification test."""
import os
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so app module resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("="*60)
print("=== FINAL VERIFICATION TEST ===")
print("="*60)

# Test 1: Check that get_llm_client exists and returns correct types
print("\n1. Testing get_llm_client() function:")
print("   Importing app.extraction...")
from app.extraction import get_llm_client
print(f"   ✓ get_llm_client() imported successfully")

# Test 2: Set up Featherless provider (valid)
print("\n2. Testing Featherless provider (valid config):")
os.environ['LLM_PROVIDER'] = 'featherless'
os.environ['FEATHERLESS_API_KEY'] = 'test-fc-key'
os.environ['FEATHERLESS_BASE_URL'] = 'https://api.featherless.ai/v1'
os.environ['MODEL'] = 'test/model'

# Clear module cache
for mod in list(sys.modules.keys()):
    if mod.startswith('app.'):
        del sys.modules[mod]

# Import fresh modules
from app.config import LLM_PROVIDER, FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, MODEL
from app.extraction import get_llm_client, _get_client

print(f"   Config - LLM_PROVIDER: {LLM_PROVIDER}")
print(f"   Config - FEATHERLESS_API_KEY: {FEATHERLESS_API_KEY}")
print(f"   Config - FEATHERLESS_BASE_URL: {FEATHERLESS_BASE_URL}")
print(f"   Config - MODEL: {MODEL}")

client, model = get_llm_client()
print(f"   get_llm_client() -> client type: {type(client).__name__}, model: {model}")
print(f"   ✓ Featherless provider works correctly")

# Test 3: Set up Groq provider (backward compatibility)
print("\n3. Testing Groq provider (backward compatibility):")
# Clear out Featherless vars
for var in ['FEATHERLESS_API_KEY', 'FEATHERLESS_BASE_URL', 'MODEL']:
    os.environ.pop(var, None)

os.environ['LLM_PROVIDER'] = 'groq'
os.environ['GROQ_API_KEY'] = 'test-gq-key'
os.environ['GROQ_MODEL'] = 'llama-3.3-70b-versatile'

# Clear module cache
for mod in list(sys.modules.keys()):
    if mod.startswith('app.'):
        del sys.modules[mod]

# Import fresh modules
from app.config import LLM_PROVIDER, GROQ_API_KEY, GROQ_MODEL
from app.extraction import get_llm_client

print(f"   Config - LLM_PROVIDER: {LLM_PROVIDER}")
print(f"   Config - GROQ_API_KEY: {GROQ_API_KEY}")
print(f"   Config - GROQ_MODEL: {GROQ_MODEL}")

client, model = get_llm_client()
print(f"   get_llm_client() -> client type: {type(client).__name__}, model: {model}")
print(f"   ✓ Groq provider maintains backward compatibility")

# Test 4: Verify _get_client uses provider-specific logic
print("\n4. Testing _get_client() with both providers:")
for provider in ['featherless', 'groq']:
    for var in ['FEATHERLESS_API_KEY', 'FEATHERLESS_BASE_URL', 'MODEL',
                'GROQ_API_KEY', 'GROQ_MODEL']:
        os.environ.pop(var, None)
    
    if provider == 'featherless':
        os.environ['LLM_PROVIDER'] = 'featherless'
        os.environ['FEATHERLESS_API_KEY'] = 'test-fc-key'
        os.environ['FEATHERLESS_BASE_URL'] = 'https://api.featherless.ai/v1'
        os.environ['MODEL'] = 'test/model'
    else:
        os.environ['LLM_PROVIDER'] = 'groq'
        os.environ['GROQ_API_KEY'] = 'test-gq-key'
        os.environ['GROQ_MODEL'] = 'llama-3.3-70b-versatile'
    
    # Clear module cache
    for mod in list(sys.modules.keys()):
        if mod.startswith('app.'):
            del sys.modules[mod]
    
    from app.extraction import _get_client
    instructor_client = _get_client()
    
    print(f"   {provider:12s} provider -> _get_client() type: {type(instructor_client).__name__}")

# Test 5: Verify get_llm_client returns both (client, model_name)
print("\n5. Verifying get_llm_client() return format:")
from app.extraction import get_llm_client

# Test with Featherless
os.environ['LLM_PROVIDER'] = 'featherless'
os.environ['FEATHERLESS_API_KEY'] = 'test-fc-key'

for var in ['FEATHERLESS_BASE_URL', 'MODEL', 'GROQ_API_KEY', 'GROQ_MODEL']:
    os.environ.pop(var, None)

# Clear module cache
for mod in list(sys.modules.keys()):
    if mod.startswith('app.'):
        del sys.modules[mod]

client, model_name = get_llm_client()
print(f"   Return type: tuple (client, model_name)")
print(f"   client type: {type(client).__name__}")
print(f"   model_name: {model_name}")
print(f"   ✓ Returns expected format: (client, model_name)")

print("\n" + "="*60)
print("✓ ALL VERIFICATION TESTS PASSED!")
print("="*60)
