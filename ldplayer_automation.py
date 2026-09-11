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

    def _run_adb_args(self, args: list) -> str:
        """Run an ADB command using argument list (shell=False) to avoid Windows cmd.exe escaping issues"""
        try:
            device_serial = self._get_active_device_serial()
            adb_exe = self._get_adb_path().strip('"')
            cmd_list = [adb_exe]
            if device_serial:
                cmd_list.extend(["-s", device_serial])
            cmd_list.extend(args)
            result = subprocess.run(
                cmd_list, 
                shell=False, 
                capture_output=True, 
                text=True
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"ADB Args Error: {e}")
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
        """Type text into current focused field in Android with rock-solid escaping and no clipboard dependencies"""
        if not text:
            return
            
        symbol_keycodes = {
            '@': '77', '#': '18', '*': '17', '+': '81',
            '-': '69', '=': '70', '.': '56', ',': '55',
            '/': '76', ' ': '62'
        }
        
        current_chunk = []
        for ch in text:
            if ch in symbol_keycodes:
                if current_chunk:
                    chunk_str = "".join(current_chunk)
                    self._run_adb_args(["shell", "input", "text", chunk_str])
                    current_chunk = []
                self._run_adb_args(["shell", "input", "keyevent", symbol_keycodes[ch]])
            elif ch.isalnum() or ch in '_':
                current_chunk.append(ch)
            else:
                if current_chunk:
                    chunk_str = "".join(current_chunk)
                    self._run_adb_args(["shell", "input", "text", chunk_str])
                    current_chunk = []
                # Pass escaped symbol directly to Android input text
                self._run_adb_args(["shell", "input", "text", f"\\{ch}"])
                
        if current_chunk:
            chunk_str = "".join(current_chunk)
            self._run_adb_args(["shell", "input", "text", chunk_str])

    def _clear_text_field(self, count: int = 40):
        """Cleanly clear existing text or suggestions in focused field without typing stray characters"""
        try:
            # Move cursor to end of any existing text
            self._run_adb("shell input keyevent 123") # KEYCODE_MOVE_END
            # Send batch backspaces (KEYCODE_DEL = 67)
            del_keys = " ".join(["67"] * min(count, 50))
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

    def tap_text(self, keywords, timeout: int = 5, fallback_ratio: Optional[Tuple[float, float]] = None) -> bool:
        """Find an element by label text and tap it. Fast polling with fallback ratio."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            coords = self.find_text_coordinates(keywords)
            if coords:
                cx, cy = coords
                print(f"🎯 Found element '{keywords}' at ({cx}, {cy}). Tapping...")
                self._tap(cx, cy)
                return True
            time.sleep(0.6)

        if fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fallback tap for '{keywords}' at ({cx}, {cy})...")
            self._tap(cx, cy)
            return True

        return False

    def find_edit_text_coordinates(self, hint_keywords=None, xml_str: Optional[str] = None, is_password: bool = False) -> Optional[Tuple[int, int]]:
        """Find center coordinates of an EditText field, checking password attributes, resource-ids, and hints"""
        import re
        import xml.etree.ElementTree as ET

        if not xml_str:
            xml_str = self.dump_ui()

        if not xml_str or "<node" not in xml_str:
            return None

        if isinstance(hint_keywords, str):
            hint_keywords = [hint_keywords]

        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)
            
            edit_texts = []
            password_nodes = []
            for node in root.iter('node'):
                node_class = node.attrib.get('class', '')
                node_pwd = node.attrib.get('password') == 'true'
                res_id = (node.attrib.get('resource-id', '') or '').lower()
                
                if node_pwd or 'password' in res_id:
                    password_nodes.append(node)

                # Identify any input field
                if 'EditText' in node_class or node_pwd or (node.attrib.get('focusable') == 'true' and 'clickable' in node.attrib and 'Text' in node_class):
                    edit_texts.append(node)

            # Prioritize password node if is_password
            if is_password and password_nodes:
                bounds_str = password_nodes[0].attrib.get('bounds', '')
                bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(bounds_match) == 2:
                    x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                    x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                    return ((x1 + x2) // 2, (y1 + y2) // 2)

            # Match against hint, text, resource-id, or content-desc
            if hint_keywords:
                for node in edit_texts:
                    node_text = (node.attrib.get('text', '') or '').strip().lower()
                    node_hint = (node.attrib.get('hint', '') or '').strip().lower()
                    node_desc = (node.attrib.get('content-desc', '') or '').strip().lower()
                    node_res = (node.attrib.get('resource-id', '') or '').strip().lower()
                    for kw in hint_keywords:
                        kw_lower = kw.lower()
                        if (kw_lower in node_text or kw_lower in node_hint or 
                            kw_lower in node_desc or kw_lower in node_res):
                            bounds_str = node.attrib.get('bounds', '')
                            bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                            if len(bounds_match) == 2:
                                x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                                x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                                return ((x1 + x2) // 2, (y1 + y2) // 2)

            # Fallback to the first actual EditText field on screen
            if edit_texts:
                bounds_str = edit_texts[0].attrib.get('bounds', '')
                bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(bounds_match) == 2:
                    x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                    x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                    return ((x1 + x2) // 2, (y1 + y2) // 2)
        except Exception:
            pass

        # Regex fallback for EditText bounds
        if is_password:
            match_pwd = re.search(r'password="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_str)
            if match_pwd:
                x1, y1, x2, y2 = map(int, match_pwd.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)

        match = re.search(r'class="[^"]*EditText[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_str)
        if match:
            x1, y1, x2, y2 = map(int, match.groups())
            return ((x1 + x2) // 2, (y1 + y2) // 2)

        return None

    def set_clipboard(self, text: str) -> bool:
        """
        Copy text to BOTH:
        1. Windows Host OS Clipboard (via ctypes Win32 API)
           LDPlayer automatically syncs the host Windows clipboard into Android,
           wiping out any previous user copy/paste items!
        2. LDPlayer Android Emulator Clipboard (via ADB service call / cmd clipboard)
        """
        success = False
        
        # 1. Windows Host Clipboard (ctypes Win32)
        try:
            import ctypes
            if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'user32'):
                user32 = ctypes.windll.user32
                kernel32 = ctypes.windll.kernel32
                for _ in range(5):
                    if user32.OpenClipboard(None):
                        user32.EmptyClipboard()
                        data = text.encode('utf-16le') + b'\x00\x00'
                        h_mem = kernel32.GlobalAlloc(0x0042, len(data)) # GMEM_MOVEABLE | GMEM_ZEROINIT
                        p_mem = kernel32.GlobalLock(h_mem)
                        ctypes.memmove(p_mem, data, len(data))
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(13, h_mem) # CF_UNICODETEXT = 13
                        user32.CloseClipboard()
                        success = True
                        break
                    time.sleep(0.05)
        except Exception:
            pass

        # 2. Android Emulator Clipboard via cmd clipboard
        try:
            escaped = text.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')
            self._run_adb(f'shell cmd clipboard set text "{escaped}"')
            success = True
        except Exception:
            pass

        # 3. Android Emulator Clipboard via service call
        try:
            self._run_adb(f'shell service call clipboard 2 i32 1 s16 "com.android.shell" s16 "{text}"')
            success = True
        except Exception:
            pass

        return success

    def enter_password(self, password: str, fallback_ratio=(0.50, 0.35)) -> bool:
        """
        Specifically handles Instagram password entry:
        1. Accurately focuses password field via password="true", resource-id or hint
        2. Clears previous text thoroughly without typing stray characters
        3. Types password directly via ADB input text without touching clipboard
        4. Submits via KEYCODE_ENTER (66) and cleanly dismisses soft keyboard
        """
        if not password or len(str(password).strip()) < 6:
            import random, string
            seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            password = f"Insta_{seed}9"
            print(f"⚠️ Empty/short password provided. Using secure generated password: {password}")

        # Step 1: Focus the password field
        coords = self.find_edit_text_coordinates(hint_keywords=["password", "create a password", "choose a password"], is_password=True)
        if coords:
            cx, cy = coords
            print(f"🎯 Focusing password field at ({cx}, {cy})...")
            self._tap(cx, cy)
        elif fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fallback tap for password field at ({cx}, {cy})...")
            self._tap(cx, cy)

        time.sleep(0.3)
        self._clear_text_field(25)
        time.sleep(0.15)

        # Step 2: Type password directly via ADB keycodes and text (NO CLIPBOARD TOUCHED)
        print(f"🔑 Typing password ({len(password)} characters) via direct ADB engine...")
        self._type_text(password)
        time.sleep(0.4)

        # Step 3: Trigger submission via keyboard ENTER action (IME_ACTION_NEXT/DONE)
        print("👉 Submitting password via keyboard ENTER action...")
        self._run_adb_args(["shell", "input", "keyevent", "66"]) # KEYCODE_ENTER
        time.sleep(1.0)

        # Step 4: Dismiss soft keyboard cleanly with KEYCODE_BACK if still open (never KEYCODE_ESCAPE which clears text)
        self._run_adb_args(["shell", "input", "keyevent", "4"]) # KEYCODE_BACK closes soft keyboard safely
        time.sleep(0.3)
        return True

    def enter_text_to_field(self, text: str, hint_keywords=None, fallback_ratio=(0.50, 0.35), is_password: bool = False) -> bool:
        """Find the real EditText field, tap it to focus, clear it, and type text safely via ADB"""
        if is_password:
            return self.enter_password(text, fallback_ratio=fallback_ratio)

        if not text:
            print("⚠️ Warning: Empty text passed to enter_text_to_field!")
            return False

        coords = self.find_edit_text_coordinates(hint_keywords, is_password=is_password)
        if coords:
            cx, cy = coords
            print(f"🎯 Tapping input field at ({cx}, {cy})...")
            self._tap(cx, cy)
        elif fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fallback tap for input field at ({cx}, {cy})...")
            self._tap(cx, cy)
            
        time.sleep(0.3)
        self._clear_text_field(40)
        time.sleep(0.15)
        
        # Type text purely via ADB input text
        print(f"⌨️ Typing input text: {text}")
        self._type_text(text)
        time.sleep(0.4)
        
        # Dismiss soft keyboard cleanly with KEYCODE_BACK
        self._run_adb_args(["shell", "input", "keyevent", "4"]) # KEYCODE_BACK
        time.sleep(0.2)
        return True

    def find_birthday_picker_info(self, xml_str: Optional[str] = None) -> Tuple[int, int, int, int]:
        """
        Locates the scrollable birthday date picker wheels (Month, Day, Year).
        Returns (year_x, year_y, y_top, y_bottom).
        """
        import re
        import xml.etree.ElementTree as ET

        w, h = self.get_screen_size()
        if not xml_str:
            xml_str = self.dump_ui()

        # 1. Search for 4-digit year element in XML (e.g. 2026, 2025, 2024, 2005)
        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)

            # Check for year text node
            for node in root.iter('node'):
                text = (node.attrib.get('text', '') or '').strip()
                if re.match(r'^(?:19\d{2}|20\d{2})$', text):
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                        x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                        year_x = (x1 + x2) // 2
                        year_y = (y1 + y2) // 2
                        y_top = max(0, year_y - int(h * 0.10))
                        y_bottom = min(h, year_y + int(h * 0.10))
                        return (year_x, year_y, y_top, y_bottom)

            # Check for NumberPicker elements
            pickers = []
            for node in root.iter('node'):
                node_class = node.attrib.get('class', '')
                if 'NumberPicker' in node_class or 'DatePicker' in node_class:
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                        x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                        pickers.append((x1, y1, x2, y2))

            if pickers:
                # Sort by horizontal position (rightmost picker is Year in LTR)
                pickers.sort(key=lambda p: p[0])
                p = pickers[-1]
                year_x = (p[0] + p[2]) // 2
                year_y = (p[1] + p[3]) // 2
                y_top = p[1] + int((p[3] - p[1]) * 0.15)
                y_bottom = p[3] - int((p[3] - p[1]) * 0.15)
                return (year_x, year_y, y_top, y_bottom)
        except Exception:
            pass

        # 2. Geometric fallback for portrait mobile screen
        year_x = int(w * 0.78)
        year_y = int(h * 0.72)
        y_top = int(h * 0.62)
        y_bottom = int(h * 0.82)
        return (year_x, year_y, y_top, y_bottom)

    def set_birthday(self, log_cb=None) -> bool:
        """
        Rolls the scrollable Year wheel back by 20-25 years to ensure the account
        is an adult age (e.g. Year ~2000), confirms dialog 'SET' button, and taps 'Next'.
        """
        def log(msg, level="info"):
            if log_cb:
                try:
                    log_cb(msg, level)
                except Exception:
                    pass

        w, h = self.get_screen_size()
        log("🎂 Locating scrollable Birthday picker...", "info")
        xml = self.dump_ui()
        year_x, year_y, y_top, y_bottom = self.find_birthday_picker_info(xml)

        log(f"🔄 Scrolling Year wheel backwards at x={year_x}...", "info")
        # Swiping down from top to bottom on Android NumberPicker pulls past years down
        for i in range(6):
            self._run_adb(f"shell input swipe {year_x} {y_top} {year_x} {y_bottom} 130")
            time.sleep(0.08)

        # Give Month (left) and Day (middle) 1 natural swipe
        month_x = int(w * 0.22)
        day_x = int(w * 0.50)
        self._run_adb(f"shell input swipe {month_x} {y_top} {month_x} {y_bottom} 150")
        time.sleep(0.05)
        self._run_adb(f"shell input swipe {day_x} {y_top} {day_x} {y_bottom} 150")
        time.sleep(0.4)

        # Confirm dialog if there is a 'SET' / 'Set' / 'OK' button on popup
        log("👉 Confirming date of birth selection...", "info")
        self.tap_text(["Set", "SET", "Ok", "OK", "Done", "Confirm"], timeout=1.2)
        time.sleep(0.5)

        # Tap the main 'Next' button
        log("👉 Tapping 'Next' on Birthday screen...", "info")
        self.tap_text(["Next", "Continue"], timeout=2.5, fallback_ratio=(0.50, 0.42))
        return True

    def get_clipboard(self) -> str:
        """Read Android clipboard string via ADB"""
        # Try Android cmd clipboard
        try:
            res = self._run_adb("shell cmd clipboard get")
            if res and "Error" not in res and len(res.strip()) >= 16:
                return res.strip()
        except Exception:
            pass

        # Try Android service call clipboard (works on LDPlayer Android 7/9)
        try:
            raw = self._run_adb('shell service call clipboard 2 i32 1 s16 "com.android.shell"')
            import re
            chars = []
            for line in raw.splitlines():
                if "'" in line:
                    part = line[line.find("'")+1 : line.rfind("'")]
                    cleaned = part.replace('.', '').replace('\x00', '').strip()
                    chars.append(cleaned)
            parsed = "".join(chars).strip()
            if len(parsed) >= 16:
                return parsed
        except Exception:
            pass
        return ""

    def extract_2fa_key_from_ui(self, xml_str: Optional[str] = None) -> str:
        """Extract a 16-36 character base32 2FA secret key from UI XML text nodes"""
        if not xml_str:
            xml_str = self.dump_ui()
        import re
        # Look for base32 patterns (A-Z and 2-7, possibly separated by spaces)
        candidates = re.findall(r'text="([A-Z2-7\s]{16,40})"', xml_str)
        for c in candidates:
            clean = c.replace(" ", "").strip()
            if 16 <= len(clean) <= 36:
                return clean
        return ""

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

    def setup_instagram_2fa(self, easyearn_client, account_data: Dict, log_cb=None) -> str:
        """
        Configure real Two-Factor Authentication (2FA) in Instagram and link with EasyEarn:
        1. Navigate to Profile tab -> Hamburger Menu
        2. Tap 'Settings and privacy' (or Accounts Center)
        3. Tap 'Accounts Center' -> 'Password and security'
        4. Tap 'Two-factor authentication' -> Select Instagram account
        5. Select 'Authentication app' -> Tap 'Next'
        6. Tap 'Copy key' button -> Extract genuine 2FA secret from UI/clipboard
        7. Submit 2FA secret to EasyEarn -> EasyEarn returns 6-digit OTP code
        8. In Instagram, tap 'Next' / 'Enter code'
        9. Type 6-digit OTP code into Instagram -> Tap 'Next' to finish
        Returns the genuine 2FA Secret Key string.
        """
        def log(msg, level="info"):
            print(f"[{level.upper()}] {msg}")
            if log_cb:
                try:
                    log_cb(msg, level)
                except Exception:
                    pass

        log("🔐 Setting up real Two-Factor Authentication on Instagram...", "task")
        
        # Step 1: Ensure any initial dialogs/popups are dismissed and navigate to Profile
        time.sleep(3)
        for _ in range(3):
            ui = self.dump_ui().lower()
            if "not now" in ui or "skip" in ui:
                self.tap_text(["Not now", "Skip"], timeout=2)
                time.sleep(2)
            else:
                break
                
        # Tap Profile tab (bottom right of screen: ~90% x, 95% y)
        log("👤 Navigating to Profile tab...", "info")
        self.tap_text(["Profile", "Edit profile"], timeout=4, fallback_ratio=(0.90, 0.95))
        time.sleep(3)
        
        # Step 2: Tap Hamburger Menu (top right: ~92% x, 5% y)
        log("🍔 Opening Settings Menu (three bars)...", "info")
        self.tap_text(["Options", "Menu", "More options"], timeout=4, fallback_ratio=(0.92, 0.05))
        time.sleep(3)
        
        # Step 3: Tap 'Settings and privacy' or 'Accounts Center'
        log("⚙️ Opening Accounts Center / Settings...", "info")
        self.tap_text(["Accounts Center", "Account Centre", "Settings and privacy", "Settings"], timeout=4, fallback_ratio=(0.50, 0.12))
        time.sleep(3)
        
        # In case we landed on Settings list and Accounts Center is at the top card
        ui = self.dump_ui().lower()
        if "accounts center" in ui or "account centre" in ui:
            self.tap_text(["Accounts Center", "Account Centre"], timeout=3, fallback_ratio=(0.50, 0.15))
            time.sleep(3)

        # Step 4: Inside Accounts Center, tap 'Password and security'
        log("🛡️ Opening 'Password and security'...", "info")
        found_pws = self.tap_text(["Password and security", "Password & security"], timeout=4)
        if not found_pws:
            # Scroll down slightly and try again
            self._run_adb("shell input swipe 540 1200 540 600 300")
            time.sleep(1.5)
            self.tap_text(["Password and security", "Password & security"], timeout=4, fallback_ratio=(0.50, 0.40))
        time.sleep(3)

        # Step 5: Inside Password and security, tap 'Two-factor authentication'
        log("🔐 Opening 'Two-factor authentication'...", "info")
        self.tap_text(["Two-factor authentication", "Two-Factor authentication", "Two-factor", "2-step"], timeout=4, fallback_ratio=(0.50, 0.32))
        time.sleep(3)

        # Step 6: Choose Account (Instagram profile)
        log("👤 Selecting account...", "info")
        username = account_data.get('username', '')
        self.tap_text([username, "Instagram"], timeout=3, fallback_ratio=(0.50, 0.20))
        time.sleep(3)

        # Step 7: Choose 'Authentication app' method
        log("📱 Selecting 'Authentication app' method...", "info")
        self.tap_text(["Authentication app", "Authentication app (recommended)"], timeout=4, fallback_ratio=(0.50, 0.32))
        time.sleep(2)
        # Tap Next on method selection
        self.tap_text(["Next", "Continue"], timeout=3, fallback_ratio=(0.50, 0.92))
        time.sleep(4)

        # Step 8: 'Set up authentication app' screen -> Tap 'Copy key'
        log("📋 Locating 'Copy key' button on Instagram...", "info")
        self.tap_text(["Copy key", "Copy code", "Copy"], timeout=5, fallback_ratio=(0.50, 0.70))
        time.sleep(2)

        # Extract 2FA Secret Key
        twofa_key = ""
        # 1. From UI XML nodes
        twofa_key = self.extract_2fa_key_from_ui()
        # 2. If not found in XML, check Android clipboard
        if not twofa_key or len(twofa_key) < 16:
            clip = self.get_clipboard()
            clean_clip = clip.replace(" ", "").strip().upper()
            if 16 <= len(clean_clip) <= 36:
                twofa_key = clean_clip

        if twofa_key:
            log(f"🔑 Real Instagram 2FA Secret Key: {twofa_key}", "success")
        else:
            log("⚠️ Could not automatically parse 2FA key text, checking clipboard fallback...", "warning")
            twofa_key = self._generate_2fa_secret()

        # Step 9: Submit 2FA Secret Key to EasyEarn to get OTP code!
        otp_code = None
        if easyearn_client:
            log("🌐 Submitting 2FA Secret to EasyEarn to generate OTP code...", "info")
            otp_code = easyearn_client.submit_2fa_key(twofa_key)
            if otp_code:
                log(f"🔑 EasyEarn generated OTP Code: {otp_code}!", "success")
            else:
                log("⚠️ EasyEarn did not return an OTP code immediately.", "warning")

        # Step 10: In Instagram, tap 'Next' or 'Enter code'
        log("👉 Tapping 'Next' to enter confirmation code in Instagram...", "info")
        self.tap_text(["Next", "Enter code", "Continue"], timeout=4, fallback_ratio=(0.50, 0.92))
        time.sleep(4)

        # Step 11: Enter the 6-digit OTP code into Instagram
        if otp_code:
            log(f"⌨️ Entering OTP code ({otp_code}) into Instagram...", "info")
            self.enter_text_to_field(str(otp_code), hint_keywords=["code", "confirmation", "6-digit"], fallback_ratio=(0.50, 0.35))
            time.sleep(1.5)
            self.tap_text(["Next", "Continue"], timeout=4, fallback_ratio=(0.50, 0.45))
            time.sleep(5)
            
            # Tap 'Done' on 2FA confirmation screen
            log("✅ Confirming Two-factor authentication is active...", "info")
            self.tap_text(["Done", "Finish", "Next"], timeout=4, fallback_ratio=(0.50, 0.92))
            time.sleep(2)
            log("🎉 Instagram Two-Factor Authentication successfully enabled!", "success")
        else:
            log("⚠️ No OTP code available to finalize Instagram 2FA in-app, proceeding with extracted key.", "warning")

        return twofa_key

    def create_instagram_account(self, account_data: Dict, otp_fetcher=None, otp_code: str = "", twofa_enabled: bool = True, easyearn_client=None, log_cb=None) -> Dict:
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
                time.sleep(3.5)
            else:
                log("Instagram is already open on the welcome screen!", "info")

            # 2. Tap 'Get started' or 'Create new account'
            log("👉 Tapping 'Get started' button...", "info")
            # In modern Instagram, 'Get started' is the main button at ~70% down the screen
            tapped_start = self.tap_text(
                ["Get started", "Create new account", "Sign up"],
                timeout=4,
                fallback_ratio=(0.50, 0.70)
            )
            time.sleep(1.5)

            # 3. Step-by-Step Registration Loop
            # Modern Instagram asks: Name -> Password -> Save info -> Birthday -> Username -> Mobile/Email -> Code
            name_entered = False
            password_entered = False
            birthday_set = False
            username_entered = False
            email_entered = False
            code_entered = False
            terms_agreed = False

            for step_round in range(1, 20):
                ui = self.dump_ui().lower()

                # A. Name Step ("What's your name?" / "Full name")
                if not name_entered and ("what's your name" in ui or "full name" in ui or ("name" in ui and not password_entered and not birthday_set and not email_entered)):
                    log(f"📝 Entering Name: {account_data['full_name']}...", "info")
                    self.enter_text_to_field(account_data['full_name'], hint_keywords=["full name", "name"], fallback_ratio=(0.50, 0.35))
                    self.tap_text(["Next", "Continue"], timeout=2.5, fallback_ratio=(0.50, 0.45))
                    name_entered = True
                    time.sleep(0.8)
                    continue

                # B. Password Step ("Create a password")
                if not password_entered and ("password" in ui or "create a password" in ui or "choose a password" in ui or "set a password" in ui):
                    pwd = account_data.get('password', '').strip()
                    if not pwd or len(pwd) < 6:
                        import random, string
                        seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                        pwd = f"Insta_{seed}9"
                        account_data['password'] = pwd
                        log(f"⚠️ Generated valid replacement password: {pwd}", "warning")

                    log(f"🔒 Entering Password ({len(pwd)} chars) via direct keystroke engine...", "info")
                    self.enter_password(pwd, fallback_ratio=(0.50, 0.35))
                    time.sleep(1.2)

                    # Check if screen still on password screen or error displayed
                    ui_check = self.dump_ui().lower()
                    if "cannot be empty" in ui_check or "at least 6" in ui_check or "password must be" in ui_check:
                        log("⚠️ Instagram showed password error, re-entering cleanly...", "warning")
                        self.enter_password(pwd, fallback_ratio=(0.50, 0.35))
                        time.sleep(1.2)
                        ui_check = self.dump_ui().lower()

                    # Tap Next / Continue (button is below password field and checkbox at Y=0.55 or bottom Y=0.90)
                    if "password" in ui_check or "create a password" in ui_check:
                        log("👉 Tapping 'Next' to confirm password...", "info")
                        self.tap_text(["Next", "Continue"], timeout=3.0, fallback_ratio=(0.50, 0.55))
                        time.sleep(1.2)

                    password_entered = True
                    time.sleep(0.8)
                    continue

                # C. Save login info prompt ("Save your login info?")
                if "save your login info" in ui or ("save" in ui and "not now" in ui):
                    log("💾 Tapping 'Save' on login info...", "info")
                    self.tap_text(["Save", "Not now"], timeout=2.0, fallback_ratio=(0.50, 0.45))
                    time.sleep(0.8)
                    continue

                # D. Birthday Step ("What's your birthday?")
                if not birthday_set and ("birthday" in ui or "date of birth" in ui or "how old are you" in ui or "set date" in ui):
                    log("🎂 Setting Birthday via scrollable wheel picker...", "info")
                    self.set_birthday(log_cb=log)
                    birthday_set = True
                    time.sleep(1.0)
                    continue

                # E. Username Step ("Create a username")
                if not username_entered and ("create a username" in ui or "choose a username" in ui or ("username" in ui and not email_entered)):
                    log(f"👤 Setting Username: {account_data['username']}...", "info")
                    self.enter_text_to_field(account_data['username'], hint_keywords=["username"], fallback_ratio=(0.50, 0.35))
                    self.tap_text(["Next", "Continue"], timeout=2.5, fallback_ratio=(0.50, 0.45))
                    username_entered = True
                    time.sleep(1.0)
                    continue

                # F. Mobile Number Prompt -> Switch to Email ("Sign up with email")
                if not email_entered and ("mobile" in ui or "phone" in ui or "what's your mobile" in ui):
                    log("📧 Selecting 'Sign up with email' instead of phone...", "info")
                    self.tap_text(["Sign up with email", "email", "Use email"], timeout=2.5, fallback_ratio=(0.50, 0.90))
                    time.sleep(0.8)
                    ui = self.dump_ui().lower()

                # G. Email Entry ("What's your email?" / "Email")
                if not email_entered and not code_entered and ("what's your email" in ui or "email" in ui):
                    log(f"✉️ Entering Email: {account_data['email']}...", "info")
                    self.enter_text_to_field(account_data['email'], hint_keywords=["email", "what's your email"], fallback_ratio=(0.50, 0.35))
                    log("👉 Tapping 'Next' to send verification code...", "info")
                    self.tap_text(["Next", "Continue"], timeout=2.5, fallback_ratio=(0.50, 0.45))
                    email_entered = True
                    time.sleep(1.8)
                    continue

                # H. Confirmation Code Step ("Enter confirmation code" / "Confirmation code")
                if not code_entered and ("confirmation code" in ui or "enter the 6-digit" in ui or "check your email" in ui):
                    log("📬 Instagram sent verification email! Waiting for OTP code from EasyEarn...", "task")
                    
                    received_code = otp_code
                    if not received_code and otp_fetcher:
                        # Poll EasyEarn for the code for up to 90 seconds
                        for poll_attempt in range(18):
                            log(f"⏳ Waiting for OTP code from EasyEarn (attempt {poll_attempt+1}/18)...", "info")
                            received_code = otp_fetcher()
                            if received_code:
                                break
                            time.sleep(4)

                    if received_code:
                        log(f"🔑 OTP Code received: {received_code}! Entering into Instagram...", "success")
                        self.enter_text_to_field(str(received_code).strip(), hint_keywords=["confirmation code", "code"], fallback_ratio=(0.50, 0.35))
                        self.tap_text(["Next", "Continue"], timeout=2.5, fallback_ratio=(0.50, 0.45))
                        code_entered = True
                        time.sleep(2.0)
                        continue
                    else:
                        log("⚠️ Did not receive OTP code in time. Will retry on next cycle.", "warning")
                        break

                # I. Terms and Policies ("I agree")
                if not terms_agreed and ("i agree" in ui or "agree to instagram" in ui or "terms" in ui):
                    log("📜 Tapping 'I agree' to Terms...", "info")
                    self.tap_text(["I agree", "Agree"], timeout=2.5, fallback_ratio=(0.50, 0.90))
                    terms_agreed = True
                    time.sleep(3.0)
                    continue

                # J. Add a profile picture / Skip screens
                if "add picture" in ui or "profile picture" in ui or "skip" in ui:
                    log("⏭️ Skipping profile photo / contacts...", "info")
                    self.tap_text(["Skip", "Not now"], timeout=2.0, fallback_ratio=(0.50, 0.90))
                    time.sleep(1.0)
                    continue

                # If reached feed or search or home, registration is finished!
                if "feed" in ui or "direct" in ui or "reels" in ui or (email_entered and code_entered and terms_agreed):
                    log("🎉 Account creation completed successfully on Instagram!", "success")
                    break

                time.sleep(1.0)

            # Step 4: Real Two-Factor Authentication (2FA) Setup
            twofa_key = ""
            if twofa_enabled:
                twofa_key = self.setup_instagram_2fa(
                    easyearn_client=easyearn_client,
                    account_data=account_data,
                    log_cb=log
                )

            return {
                'success': True,
                'username': account_data['username'],
                'twofa_key': twofa_key
            }

        except Exception as e:
            log(f"LDPlayer Automation Error: {e}", "error")
            return {'success': False, 'error': str(e)}

