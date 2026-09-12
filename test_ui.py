import sys
from ldplayer_automation import LDPlayerAutomation
ld = LDPlayerAutomation()
print(ld.dump_ui().lower())
