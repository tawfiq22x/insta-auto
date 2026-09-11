# ldplayer_automation.py
import subprocess
import time
import os
import random
import string
from typing import Dict, Optional, Tuple

class LDPlayerAutomation:
    """Controls LDPlayer and Instagram via ADB (Android Debug Bridge)"""
    
    def __init__(self):
        self.ldplayer_path = "C:\\LDPlayer\\LDPlayer.exe"
        self.instance_name = "LDPlayer"
        self.instance_index = "0"
        self.adb_path = "adb"
        
    def _get_adb_path(self) -> str:
        """Returns the path to adb.exe. Tries LDPlayer folder first, then system path."""
        try:
            # Check if user provided an LDPlayer executable path (e.g. dnplayer.exe)
            if self.ldplayer_path and os.path.exists(self.ldplayer_path):
                ld_dir = os.path.dirname(self.ldplayer_path)
                adb_in_ld = os.path.join(ld_dir, "adb.exe")
                if os.path.exists(adb_in_ld):
                    return f'"{adb_in_ld}"'  # wrap in quotes in case of spaces
        except:
            pass
            
        # Fallback to system ADB
        return self.adb_path

    def _get_active_device_serial(self) -> str:
        """Find the active LDPlayer device serial from adb devices"""
        try:
            adb_exe = self._get_adb_path()
            res = subprocess.run(f"{adb_exe} devices", shell=True, capture_output=True, text=True)
            lines = res.stdout.strip().split('\n')[1:]
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    serial = parts[0]
                    # Common LDPlayer device serials: emulator-5554, 127.0.0.1:5555, 127.0.0.1:5557
                    return serial
        except:
            pass
        
        # Fallback to calculated port
        port = 5555 + (int(self.instance_index) * 2)
        return f"127.0.0.1:{port}"

    def _run_adb(self, command: str) -> str:
        """Run an ADB command targeting the specific LDPlayer instance"""
        try:
            device_serial = self._get_active_device_serial()
            device_target = f"-s {device_serial}" if device_serial else ""
            
            adb_exe = self._get_adb_path()
            full_cmd = f"{adb_exe} {device_target} {command}"
            result = subprocess.run(
                full_cmd, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"ADB Error: {e}")
            return ""

    def ensure_device_connected(self) -> bool:
        """Make sure LDPlayer is running and ADB is connected. Auto-launches LDPlayer if it is not running."""
        adb_exe = self._get_adb_path()
        ports_to_try = [
            5555 + (int(self.instance_index) * 2),
            5554 + (int(self.instance_index) * 2),
            5555, 5554, 5556, 5557, 5558, 5559
        ]
        
        # 1. Connect to known ports and check running devices
        for p in ports_to_try[:3]:
            subprocess.run(f"{adb_exe} connect 127.0.0.1:{p}", shell=True, capture_output=True)
            
        devices = subprocess.run(f"{adb_exe} devices", shell=True, capture_output=True, text=True)
        for line in devices.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'device':
                print(f"✅ Found connected ADB device: {parts[0]}")
                return True
            
        # 2. If not running, launch LDPlayer automatically
        print("LDPlayer not detected in adb devices. Launching LDPlayer...")
        self.launch_ldplayer()
        
        # 3. Wait up to 45 seconds for LDPlayer to boot and ADB to report ready
        print("Waiting for LDPlayer to boot and connect to ADB...")
        for attempt in range(15):
            time.sleep(3)
            for p in [5555, 5554, 5556, 5557]:
                subprocess.run(f"{adb_exe} connect 127.0.0.1:{p}", shell=True, capture_output=True)
            devices = subprocess.run(f"{adb_exe} devices", shell=True, capture_output=True, text=True)
            for line in devices.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    print(f"✅ LDPlayer device ready: {parts[0]}")
                    time.sleep(2)
                    return True
                    
        return False

    def launch_ldplayer(self):
        """Launches LDPlayer executable using dnconsole/ldconsole if available, or direct executable"""
        try:
            if not self.ldplayer_path or not os.path.exists(self.ldplayer_path):
                print(f"Cannot launch LDPlayer: invalid path '{self.ldplayer_path}'")
                return False
                
            ld_dir = os.path.dirname(self.ldplayer_path)
            
            # Check for ldconsole.exe or dnconsole.exe (LDPlayer CLI tool)
            for console_name in ["ldconsole.exe", "dnconsole.exe"]:
                console_path = os.path.join(ld_dir, console_name)
                if os.path.exists(console_path):
                    print(f"Launching instance {self.instance_index} via {console_name} in {ld_dir}...")
                    subprocess.Popen([console_path, "launch", "--index", str(self.instance_index)], cwd=ld_dir)
                    return True
                    
            # Fallback: Launch the selected executable directly with cwd set to LDPlayer folder
            print(f"Launching {self.ldplayer_path} directly with cwd={ld_dir}...")
            subprocess.Popen([self.ldplayer_path], cwd=ld_dir)
            return True
        except Exception as e:
            print(f"Error launching LDPlayer: {e}")
            return False

    def _type_text(self, text: str):
        """Type text into the current focused field in Android"""
        escaped_text = text.replace(" ", "%s").replace("&", "\&").replace("$", "\$").replace("'", "\'")
        self._run_adb(f'shell input text "{escaped_text}"')

    def _clear_text_field(self, count: int = 35):
        """Clear any existing text or auto-generated suggestions in a focused field"""
        try:
            self._run_adb("shell input keyevent 123") # KEYCODE_MOVE_END
            del_keys = " ".join(["67"] * min(count, 40)) # KEYCODE_DEL
            self._run_adb(f"shell input keyevent {del_keys}")
        except Exception:
            pass

    def _tap(self, x: int, y: int):
        """Tap a specific coordinate on screen"""
        self._run_adb(f"shell input tap {x} {y}")

    def get_screen_size(self) -> Tuple[int, int]:
        """Get the actual screen resolution of LDPlayer (width, height)"""
        try:
            import re
            output = self._run_adb("shell wm size")
            match = re.search(r'(\d+)x(\d+)', output)
            if match:
                return int(match.group(1)), int(match.group(2))
        except Exception:
            pass
        return 1080, 1920

    def dump_ui(self) -> str:
        """Dump UI XML hierarchy to find exact button positions and labels"""
        try:
            self._run_adb("shell uiautomator dump /sdcard/uidump.xml")
            xml_data = self._run_adb("shell cat /sdcard/uidump.xml")
            return xml_data
        except Exception:
            return ""

    def find_text_coordinates(self, keywords, xml_str: Optional[str] = None) -> Optional[Tuple[int, int]]:
        """Find center coordinates of an element containing any of the keywords"""
        import re
        import xml.etree.ElementTree as ET
        
        if isinstance(keywords, str):
            keywords = [keywords]

        if not xml_str:
            xml_str = self.dump_ui()

        if not xml_str or "<node" not in xml_str:
            return None

        # 1. Try XML parsing
        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)
            for node in root.iter('node'):
                node_text = (node.attrib.get('text', '') or '').strip().lower()
                node_desc = (node.attrib.get('content-desc', '') or '').strip().lower()
                bounds_str = node.attrib.get('bounds', '')
                for kw in keywords:
                    if kw.lower() in node_text or kw.lower() in node_desc:
                        bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                        if len(bounds_match) == 2:
                            x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                            x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                            return ((x1 + x2) // 2, (y1 + y2) // 2)
        except Exception:
            pass

        # 2. Fast regex fallback
        for kw in keywords:
            pattern = rf'(?:text|content-desc)="[^"]*{re.escape(kw)}[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            match = re.search(pattern, xml_str, re.IGNORECASE)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)

        return None

    def tap_text(self, keywords, timeout: int = 6, fallback_ratio: Optional[Tuple[float, float]] = None) -> bool:
        """Find an element by label text and tap it. Uses fallback ratio if text not found."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            coords = self.find_text_coordinates(keywords)
            if coords:
                cx, cy = coords
                print(f"🎯 Found element '{keywords}' at ({cx}, {cy}). Tapping...")
                self._tap(cx, cy)
                return True
            time.sleep(1.5)

        if fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fallback tap for '{keywords}' at ({cx}, {cy})...")
            self._tap(cx, cy)
            return True

        return False

    def _generate_2fa_secret(self) -> str:
        """Generate a random 32-character base32 secret for 2FA"""
        chars = string.ascii_uppercase + "234567"
        return ''.join(random.choice(chars) for _ in range(32))

    def launch_instagram(self) -> bool:
        """Launch Instagram using multiple fallback methods for maximum compatibility"""
        # Method 1: Check package name
        installed = self._run_adb("shell pm list packages | grep instagram")
        print(f"Installed instagram packages: {installed}")
        
        # Method 2: LDPlayer console command runapp (direct to emulator engine)
        try:
            if self.ldplayer_path and os.path.exists(self.ldplayer_path):
                ld_dir = os.path.dirname(self.ldplayer_path)
                for console_name in ["ldconsole.exe", "dnconsole.exe"]:
                    cpath = os.path.join(ld_dir, console_name)
                    if os.path.exists(cpath):
                        subprocess.run([cpath, "runapp", "--index", str(self.instance_index), "--packagename", "com.instagram.android"], cwd=ld_dir, capture_output=True)
                        print(f"Sent {console_name} runapp com.instagram.android")
        except Exception as e:
            print(f"ldconsole runapp error: {e}")

        # Method 3: Standard Android monkey launch
        self._run_adb("shell monkey -p com.instagram.android -c android.intent.category.LAUNCHER 1")
        
        # Method 4: Standard Android intent activities
        activities = [
            "com.instagram.android/com.instagram.mainactivity.MainActivity",
            "com.instagram.android/com.instagram.mainactivity.LauncherActivity",
            "com.instagram.android/.MainActivity"
        ]
        for act in activities:
            self._run_adb(f"shell am start -n {act}")
            
        # Method 5: Plain am start by action
        self._run_adb("shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.instagram.android")
        
        # Method 6: If Instagram Lite
        if "com.instagram.lite" in installed:
            self._run_adb("shell monkey -p com.instagram.lite -c android.intent.category.LAUNCHER 1")

        return True

    def create_instagram_account(self, account_data: Dict, otp_fetcher=None, otp_code: str = "", twofa_enabled: bool = True, log_cb=None) -> Dict:
        """
        The master workflow for creating an Instagram account via LDPlayer.
        Dynamically adapts to any screen resolution and modern Instagram UI.
        """
        def log(msg, level="info"):
            print(f"[{level.upper()}] {msg}")
            if log_cb:
                try:
                    log_cb(msg, level)
                except Exception:
                    pass

        log(f"Starting Instagram account creation for: {account_data['username']}", "task")
        
        if not self.ensure_device_connected():
            return {'success': False, 'error': 'LDPlayer not connected. Is it running?'}

        try:
            w, h = self.get_screen_size()
            log(f"📱 Detected emulator screen resolution: {w}x{h}", "info")

            # 1. Check if Instagram is already open on welcome screen or launch it
            ui_check = self.dump_ui().lower()
            if "get started" not in ui_check and "create new account" not in ui_check:
                log("🚀 Opening Instagram app...", "info")
                self.launch_instagram()
                time.sleep(6)
            else:
                log("Instagram is already open on the welcome screen!", "info")

            # 2. Tap 'Get started' or 'Create new account'
            log("👉 Tapping 'Get started' button...", "info")
            # In modern Instagram, 'Get started' is the main button at ~70% down the screen
            tapped_start = self.tap_text(
                ["Get started", "Create new account", "Sign up"],
                timeout=6,
                fallback_ratio=(0.50, 0.70)
            )
            time.sleep(4)

            # 3. Step-by-Step Registration Loop
            # Modern Instagram asks: Name -> Password -> Save info -> Birthday -> Username -> Mobile/Email -> Code
            email_entered = False
            code_entered = False

            for step_round in range(1, 18):
                ui = self.dump_ui().lower()

                # A. Name Step ("What's your name?" / "Full name")
                if ("name" in ui or "what's your name" in ui) and not email_entered and "username" not in ui and "email" not in ui:
                    log(f"📝 Entering Name: {account_data['full_name']}...", "info")
                    self.tap_text(["Full name", "Name"], timeout=2, fallback_ratio=(0.50, 0.35))
                    time.sleep(1)
                    self._type_text(account_data['full_name'])
                    time.sleep(1)
                    self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.45))
                    time.sleep(3)
                    continue

                # B. Password Step ("Create a password")
                if "password" in ui and "create a password" in ui:
                    log("🔒 Entering Password...", "info")
                    self.tap_text(["Password"], timeout=2, fallback_ratio=(0.50, 0.35))
                    time.sleep(1)
                    self._type_text(account_data['password'])
                    time.sleep(1)
                    self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.45))
                    time.sleep(3)
                    continue

                # C. Save login info prompt ("Save your login info?")
                if "save your login info" in ui or ("save" in ui and "not now" in ui):
                    log("💾 Tapping 'Save' on login info...", "info")
                    self.tap_text(["Save", "Not now"], timeout=3, fallback_ratio=(0.50, 0.45))
                    time.sleep(3)
                    continue

                # D. Birthday Step ("What's your birthday?")
                if "birthday" in ui or "date of birth" in ui:
                    log("🎂 Setting Birthday...", "info")
                    # If there is a 'Set' confirmation button on dialog
                    self.tap_text(["Set"], timeout=2)
                    time.sleep(1)
                    self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.85))
                    time.sleep(3)
                    continue

                # E. Username Step ("Create a username")
                if "create a username" in ui or ("username" in ui and "next" in ui and not email_entered):
                    log(f"👤 Setting Username from task Login: {account_data['username']}...", "info")
                    self.tap_text(["Username"], timeout=2, fallback_ratio=(0.50, 0.35))
                    time.sleep(0.5)
                    self._clear_text_field(40) # Clear any auto-suggested username
                    time.sleep(0.5)
                    self._type_text(account_data['username'])
                    time.sleep(1)
                    self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.45))
                    time.sleep(4)
                    continue

                # F. Mobile Number Prompt -> Switch to Email ("Sign up with email")
                if ("mobile" in ui or "phone" in ui or "what's your mobile" in ui) and not email_entered:
                    log("📧 Selecting 'Sign up with email' instead of phone...", "info")
                    switched = self.tap_text(["Sign up with email", "email", "Use email"], timeout=4, fallback_ratio=(0.50, 0.90))
                    time.sleep(3)
                    ui = self.dump_ui().lower()

                # G. Email Entry ("What's your email?" / "Email")
                if "email" in ui and not email_entered and not code_entered:
                    log(f"✉️ Entering Email: {account_data['email']}...", "info")
                    self.tap_text(["Email", "What's your email"], timeout=2, fallback_ratio=(0.50, 0.35))
                    time.sleep(1)
                    self._type_text(account_data['email'])
                    time.sleep(1)
                    log("👉 Tapping 'Next' to send verification code...", "info")
                    self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.45))
                    email_entered = True
                    time.sleep(5)
                    continue

                # H. Confirmation Code Step ("Enter confirmation code" / "Confirmation code")
                if ("confirmation code" in ui or "enter the 6-digit" in ui or "check your email" in ui) and not code_entered:
                    log("📬 Instagram sent verification email! Waiting for OTP code from EasyEarn...", "task")
                    
                    received_code = otp_code
                    if not received_code and otp_fetcher:
                        # Poll EasyEarn for the code for up to 90 seconds
                        for poll_attempt in range(18):
                            log(f"⏳ Waiting for OTP code from EasyEarn (attempt {poll_attempt+1}/18)...", "info")
                            received_code = otp_fetcher()
                            if received_code:
                                break
                            time.sleep(5)

                    if received_code:
                        log(f"🔑 OTP Code received: {received_code}! Entering into Instagram...", "success")
                        self.tap_text(["Confirmation code", "Code"], timeout=2, fallback_ratio=(0.50, 0.35))
                        time.sleep(1)
                        self._type_text(str(received_code).strip())
                        time.sleep(1)
                        self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.45))
                        code_entered = True
                        time.sleep(6)
                        continue
                    else:
                        log("⚠️ Did not receive OTP code in time. Will retry on next cycle.", "warning")
                        break

                # I. Terms and Policies ("I agree")
                if "i agree" in ui or "agree to instagram" in ui:
                    log("📜 Tapping 'I agree' to Terms...", "info")
                    self.tap_text(["I agree", "Agree"], timeout=3, fallback_ratio=(0.50, 0.90))
                    time.sleep(8)
                    continue

                # J. Add a profile picture / Skip screens
                if "add picture" in ui or "profile picture" in ui or "skip" in ui:
                    log("⏭️ Skipping profile photo / contacts...", "info")
                    self.tap_text(["Skip", "Not now"], timeout=3, fallback_ratio=(0.50, 0.90))
                    time.sleep(3)
                    continue

                # If reached feed or search or home, registration is finished!
                if "feed" in ui or "direct" in ui or "reels" in ui or (email_entered and code_entered):
                    log("🎉 Account creation completed successfully on Instagram!", "success")
                    break

                time.sleep(3)

            # Generate 2FA if requested
            twofa_key = ""
            if twofa_enabled:
                twofa_key = self._generate_2fa_secret()
                log(f"🔐 Generated 2FA Secret Key: {twofa_key}", "success")

            return {
                'success': True,
                'username': account_data['username'],
                'twofa_key': twofa_key
            }

        except Exception as e:
            log(f"LDPlayer Automation Error: {e}", "error")
            return {'success': False, 'error': str(e)}

