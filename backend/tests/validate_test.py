"""Direct test of config validation."""
import os
import sys
from pathlib import Path

# Ensure backend/ is on sys.path so app module resolves
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set up environment with missing FEATHERLESS_API_KEY
os.environ['LLM_PROVIDER'] = 'featherless'
os.environ.pop('FEATHERLESS_API_KEY', None)
os.environ.pop('MODEL', None)

# Now try to import config
print("Environment setup:")
print(f"  LLM_PROVIDER: {os.environ.get('LLM_PROVIDER')}")
print(f"  FEATHERLESS_API_KEY: '{os.environ.get('FEATHERLESS_API_KEY')}'")
print(f"  MODEL: '{os.environ.get('MODEL')}'")

# Try to import config
try:
    import app.config
    print(f"\n✗ Imported successfully (should have failed!)")
    print(f"  LLM_PROVIDER: {app.config.LLM_PROVIDER}")
    print(f"  FEATHERLESS_API_KEY: '{app.config.FEATHERLESS_API_KEY}'")
    print(f"  MODEL: '{app.config.MODEL}'")
except RuntimeError as e:
    print(f"\n✓ RuntimeError raised as expected: {e}")

print("\n" + "="*60 + "\n")

# Test with valid Featherless config
for var in ['FEATHERLESS_API_KEY', 'MODEL']:
    os.environ.pop(var, None)

os.environ['LLM_PROVIDER'] = 'featherless'
os.environ['FEATHERLESS_API_KEY'] = 'test-key-123'
os.environ['MODEL'] = 'test/model'

# Clear modules
for mod in list(sys.modules.keys()):
    if mod.startswith('app.'):
        del sys.modules[mod]

print("Environment setup (valid Featherless):")
print(f"  LLM_PROVIDER: {os.environ.get('LLM_PROVIDER')}")
print(f"  FEATHERLESS_API_KEY: '{os.environ.get('FEATHERLESS_API_KEY')}'")
print(f"  MODEL: '{os.environ.get('MODEL')}'")

# Import config
try:
    import app.config
    print(f"\n✓ Imported successfully:")
    print(f"  LLM_PROVIDER: {app.config.LLM_PROVIDER}")
    print(f"  FEATHERLESS_API_KEY: '{app.config.FEATHERLESS_API_KEY}'")
    print(f"  MODEL: '{app.config.MODEL}'")
except RuntimeError as e:
    print(f"\n✗ Unexpected RuntimeError: {e}")
