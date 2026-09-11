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
        # ADB shell input text doesn't like spaces, so we quote it or use keyevents
        escaped_text = text.replace(" ", "%s").replace("&", "\&")
        self._run_adb(f"shell input text {escaped_text}")

    def _tap(self, x: int, y: int):
        """Tap a specific coordinate on screen"""
        self._run_adb(f"shell input tap {x} {y}")

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

    def create_instagram_account(self, account_data: Dict, otp_code: str, twofa_enabled: bool = True) -> Dict:
        """
        The master workflow for creating an Instagram account via LDPlayer.
        Calibrated for 1080x1920 resolution (480 dpi).
        """
        print(f"Starting Instagram automation for {account_data['username']}...")
        
        if not self.ensure_device_connected():
            return {'success': False, 'error': 'LDPlayer not connected. Is it running?'}

        try:
            # 1. Force close and restart Instagram using robust launcher
            print("Launching Instagram...")
            self._run_adb("shell am force-stop com.instagram.android")
            time.sleep(2)
            self.launch_instagram()
            time.sleep(10) # Wait for app to load

            # 2. Click "Sign up with email or phone number"
            # On 1080x1920, the bottom buttons are usually around Y=1600-1700
            print("Clicking Sign Up...")
            self._tap(540, 1650)  
            time.sleep(3)

            # 3. Enter Email
            print("Entering email...")
            self._type_text(account_data['email'])
            time.sleep(1)
            # 'Next' button is usually a wide blue button in the middle
            self._tap(540, 1000) 
            time.sleep(5)

            # 4. Enter OTP Code (from EasyEarn)
            print(f"Entering OTP: {otp_code}")
            self._type_text(otp_code)
            time.sleep(1)
            self._tap(540, 1000) # Tap 'Next'
            time.sleep(8)

            # 5. Full Name & Password
            print("Entering name and password...")
            self._type_text(account_data['full_name'])
            time.sleep(1)
            # Tap Password field (usually right below name)
            self._tap(540, 800) 
            time.sleep(1)
            self._type_text(account_data['password'])
            time.sleep(1)
            # Tap 'Continue without syncing contacts' (bottom button)
            self._tap(540, 1000) 
            time.sleep(5)

            # 6. Date of Birth (Skip/Accept default if possible, or scroll)
            print("Setting Birthday...")
            self._tap(540, 1200) # Tap 'Next'
            time.sleep(5)

            # 7. Username (Instagram usually auto-generates, we might need to clear and type ours)
            print("Setting Username...")
            self._tap(540, 1000) # Tap 'Next'
            time.sleep(8)

            # 8. Skip PFP / Skip connecting to FB
            print("Skipping profile setup...")
            self._tap(540, 1600) # Tap 'Skip'
            time.sleep(3)
            self._tap(540, 1600) # Tap 'Skip' again
            time.sleep(3)

            twofa_key = ""
            if twofa_enabled:
                print("Setting up 2FA...")
                # Profile tab (bottom right corner on 1080x1920)
                self._tap(980, 1800) 
                time.sleep(3)
                # Hamburger menu (top right)
                self._tap(980, 150)  
                time.sleep(2)
                # Settings (usually first option)
                self._tap(540, 400) 
                time.sleep(2)
                
                twofa_key = self._generate_2fa_secret()
                print(f"Generated 2FA Secret: {twofa_key}")

            return {
                'success': True,
                'username': account_data['username'],
                'twofa_key': twofa_key
            }

        except Exception as e:
            print(f"LDPlayer Automation Error: {e}")
            return {'success': False, 'error': str(e)}

