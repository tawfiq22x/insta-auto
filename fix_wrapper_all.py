def fix_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    # Remove old new_wrapper logic
    content = re.sub(r'import os\nimport subprocess\nif not hasattr\(subprocess, \'_run_patched\'\):.*?\n\s+subprocess\._run_patched = True\n', '', content, flags=re.DOTALL)

    new_wrapper = """import os
import subprocess
if not hasattr(subprocess, '_run_patched'):
    _original_run = subprocess.run
    def _wrapped_run(*args, **kwargs):
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000
        return _original_run(*args, **kwargs)
    subprocess.run = _wrapped_run
    
    _original_popen = subprocess.Popen
    class _WrappedPopen(_original_popen):
        def __init__(self, *args, **kwargs):
            if os.name == 'nt':
                kwargs['creationflags'] = kwargs.get('creationflags', 0) | 0x08000000
            super().__init__(*args, **kwargs)
    subprocess.Popen = _WrappedPopen
    
    subprocess._run_patched = True
"""

    if filename == 'main.py':
        content = content.replace("import sys", "import sys\n" + new_wrapper, 1)
    else:
        content = new_wrapper + "\n" + content

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

fix_file('main.py')
fix_file('ldplayer_automation.py')
print("Patched both Popen and run!")
