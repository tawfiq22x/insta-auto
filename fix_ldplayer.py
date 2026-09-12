with open('ldplayer_automation.py', 'r', encoding='utf-8') as f:
    content = f.read()

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

if "_run_patched" not in content:
    content = new_wrapper + "\n" + content

with open('ldplayer_automation.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ldplayer!")
