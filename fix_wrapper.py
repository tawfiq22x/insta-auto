def fix_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove the bad wrapper
    wrapper_code = """import subprocess
import os

_original_run = subprocess.run
def _wrapped_run(*args, **kwargs):
    if os.name == 'nt':
        kwargs['creationflags'] = 0x08000000
    return _original_run(*args, **kwargs)
subprocess.run = _wrapped_run
"""
    content = content.replace(wrapper_code, "import subprocess")

    # Now add it cleanly at the top of the file, right after the first imports
    new_wrapper = """import os
import subprocess
if not hasattr(subprocess, '_run_patched'):
    _original_run = subprocess.run
    def _wrapped_run(*args, **kwargs):
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000
        return _original_run(*args, **kwargs)
    subprocess.run = _wrapped_run
    subprocess._run_patched = True
"""
    
    if "import sys" in content:
        content = content.replace("import sys", "import sys\n" + new_wrapper, 1)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

fix_file('main.py')
fix_file('ldplayer_automation.py')
print("Fixed wrappers!")
