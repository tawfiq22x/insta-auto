import re

def patch_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all subprocess.run(...) and add creationflags=0x08000000
    # A bit tricky because of newlines in kwargs.
    # We can patch the import of subprocess to inject a wrapper!
    # "import subprocess" -> 
    wrapper = """import subprocess
import os

_original_run = subprocess.run
def _wrapped_run(*args, **kwargs):
    if os.name == 'nt':
        kwargs['creationflags'] = 0x08000000
    return _original_run(*args, **kwargs)
subprocess.run = _wrapped_run
"""
    if "def _wrapped_run" not in content:
        content = content.replace("import subprocess", wrapper, 1)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Patched {filename}")

patch_file('ldplayer_automation.py')
patch_file('main.py')
