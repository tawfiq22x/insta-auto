with open('ldplayer_automation.py', 'r') as f:
    content = f.read()

import re

target = """                    log("👉 [Step 1/11] Welcome screen detected! Tapping 'Create new account' / 'Get started'...", "info")
                    self.tap_text(
                        ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up", "GET STARTED"],
                        timeout=1.5,
                        fallback_ratio=(0.50, 0.85),
                        xml_str=ui
                    )
                    if not self.sleep(1.0):"""

replacement = """                    log("👉 [Step 1/11] Welcome screen detected! Tapping 'Create new account' / 'Get started'...", "info")
                    found = self.tap_text(
                        ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up", "GET STARTED"],
                        timeout=1.5,
                        fallback_ratio=None,
                        xml_str=ui
                    )
                    if not found:
                        log("⚠️ Text not found! Using aggressive fallback taps...", "warning")
                        w, h = self.get_screen_size()
                        self._tap(int(w * 0.50), int(h * 0.85))
                        time.sleep(0.3)
                        self._tap(int(w * 0.50), int(h * 0.90))
                        time.sleep(0.3)
                        self._tap(int(w * 0.50), int(h * 0.75))
                        time.sleep(0.3)
                        self._tap(int(w * 0.50), int(h * 0.80))
                    
                    if not self.sleep(1.5):"""

content = content.replace(target, replacement)

# Let's also do it for the pre-loop check!
target2 = """            if "create new account" in ui_check or "get started" in ui_check or "create account" in ui_check or "sign up with email or phone" in ui_check:
                log("👉 [Step 1/11] Tapping 'Create new account' / 'Get started'...", "info")
                self.tap_text(
                    ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up"],
                    timeout=2.0,
                    fallback_ratio=(0.50, 0.85),
                    xml_str=ui_check
                )
                if not self.sleep(1.0):"""

replacement2 = """            if "create new account" in ui_check or "get started" in ui_check or "create account" in ui_check or "sign up with email or phone" in ui_check:
                log("👉 [Step 1/11] Tapping 'Create new account' / 'Get started'...", "info")
                found = self.tap_text(
                    ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up"],
                    timeout=2.0,
                    fallback_ratio=None,
                    xml_str=ui_check
                )
                if not found:
                    w, h = self.get_screen_size()
                    self._tap(int(w * 0.50), int(h * 0.85))
                    self._tap(int(w * 0.50), int(h * 0.90))
                    self._tap(int(w * 0.50), int(h * 0.75))
                if not self.sleep(1.5):"""

content = content.replace(target2, replacement2)

with open('ldplayer_automation.py', 'w') as f:
    f.write(content)
print("Patched welcome screen!")
