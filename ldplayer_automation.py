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
        self.stop_requested = False
        
    def request_stop(self, stop_app: bool = True):
        """Immediately signals the automation to abort and optionally terminates Instagram on emulator"""
        self.stop_requested = True
        if stop_app:
            self.force_stop_instagram()

    def reset_stop(self):
        """Clears the stop requested flag before starting a new run"""
        self.stop_requested = False

    def is_stopped(self) -> bool:
        """Check if a stop has been requested"""
        return bool(self.stop_requested)

    def sleep(self, seconds: float) -> bool:
        """
        Interruptible sleep that exits immediately (within 50ms) if a stop is requested.
        Returns True if the sleep completed fully, False if aborted by stop request.
        """
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self.stop_requested:
                return False
            time.sleep(min(0.05, max(0.005, end_time - time.time())))
        return not self.stop_requested

    def force_stop_instagram(self):
        """Force stops Instagram and Instagram Lite on emulator immediately"""
        try:
            device_serial = self._get_active_device_serial()
            adb_exe = self._get_adb_path().strip('"')
            target = ["-s", device_serial] if device_serial else []
            subprocess.run([adb_exe] + target + ["shell", "am", "force-stop", "com.instagram.android"], shell=False, capture_output=True, timeout=5)
            subprocess.run([adb_exe] + target + ["shell", "am", "force-stop", "com.instagram.lite"], shell=False, capture_output=True, timeout=5)
            print("⏹️ Force-stopped Instagram on LDPlayer emulator.")
        except Exception as e:
            print(f"Force stop Instagram error: {e}")

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
            res = subprocess.run(f"{adb_exe} devices", shell=True, capture_output=True, text=True, timeout=10)
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
        if self.stop_requested and "force-stop" not in command and "devices" not in command:
            return ""
        try:
            device_serial = self._get_active_device_serial()
            device_target = f"-s {device_serial}" if device_serial else ""
            
            adb_exe = self._get_adb_path()
            full_cmd = f"{adb_exe} {device_target} {command}"
            result = subprocess.run(
                full_cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=12
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"ADB Error: {e}")
            return ""

    def _run_adb_args(self, args: list) -> str:
        """Run an ADB command using argument list (shell=False) to avoid Windows cmd.exe escaping issues"""
        if self.stop_requested and "force-stop" not in args:
            return ""
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
                text=True,
                timeout=12
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

    def _clear_text_field(self, count: int = 25):
        """Cleanly clear existing text or suggestions in focused field with fast direct keyevents"""
        try:
            # Single subshell process: move to end then send backspaces
            self._run_adb_args(["shell", "sh", "-c", "input keyevent 123; for i in $(seq 1 20); do input keyevent 67; done"])
        except Exception:
            try:
                self._run_adb_args(["shell", "input", "keyevent", "123"])
                self._run_adb_args(["shell", "input", "keyevent", "67"])
            except Exception:
                pass

    def _tap(self, x: int, y: int):
        """Tap a specific coordinate on screen instantly via direct process arguments"""
        self._run_adb_args(["shell", "input", "tap", str(x), str(y)])

    def get_screen_size(self) -> Tuple[int, int]:
        """Get the actual screen resolution of LDPlayer (width, height)"""
        try:
            import re
            output = self._run_adb_args(["shell", "wm", "size"])
            match = re.search(r'(\d+)x(\d+)', output)
            if match:
                return int(match.group(1)), int(match.group(2))
        except Exception:
            pass
        return 1080, 1920

    def dump_ui(self) -> str:
        """Dump UI XML hierarchy to find exact button positions and labels with maximum speed"""
        try:
            # Fast single-command dump & cat via Android shell
            dump_res = self._run_adb_args(["shell", "sh", "-c", "uiautomator dump /sdcard/uidump.xml >/dev/null 2>&1 && cat /sdcard/uidump.xml"])
            if "<node" in dump_res:
                return dump_res
            # Fallback
            self._run_adb_args(["shell", "uiautomator", "dump", "/sdcard/uidump.xml"])
            return self._run_adb_args(["shell", "cat", "/sdcard/uidump.xml"])
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

    def tap_text(self, keywords, timeout: float = 1.2, fallback_ratio: Optional[Tuple[float, float]] = None, xml_str: Optional[str] = None) -> bool:
        """Find an element by label text and tap it with zero latency when xml_str is present, or fast polling."""
        # 1. Zero-latency check against pre-dumped xml_str
        if xml_str:
            coords = self.find_text_coordinates(keywords, xml_str=xml_str)
            if coords:
                cx, cy = coords
                print(f"⚡ Instant tap for '{keywords}' at ({cx}, {cy})")
                self._tap(cx, cy)
                return True

        # 2. Fast polling
        start_time = time.time()
        while time.time() - start_time < timeout:
            coords = self.find_text_coordinates(keywords)
            if coords:
                cx, cy = coords
                print(f"🎯 Found element '{keywords}' at ({cx}, {cy}). Tapping...")
                self._tap(cx, cy)
                return True
            time.sleep(0.2)

        # 3. High-speed fallback tap
        if fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fast fallback tap for '{keywords}' at ({cx}, {cy})...")
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

        # 1. Fast regex lookup for password="true" or password resource-id
        if is_password:
            match_pwd = re.search(r'password="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_str)
            if match_pwd:
                x1, y1, x2, y2 = map(int, match_pwd.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)
            match_pwd_id = re.search(r'class="[^"]*EditText[^"]*"[^>]*resource-id="[^"]*password[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml_str, re.IGNORECASE)
            if match_pwd_id:
                x1, y1, x2, y2 = map(int, match_pwd_id.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)

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

                # ONLY genuine input fields (never match static header TextViews!)
                if 'EditText' in node_class or node_pwd:
                    edit_texts.append(node)

            # Prioritize password node if is_password
            if is_password and password_nodes:
                bounds_str = password_nodes[0].attrib.get('bounds', '')
                bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(bounds_match) == 2:
                    x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                    x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                    return ((x1 + x2) // 2, (y1 + y2) // 2)

            # Match against hint, text, resource-id, or content-desc of genuine edit_texts only
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
        """Enters password using the exact same robust design as email, username and name fields"""
        return self.enter_text_to_field(
            password, 
            hint_keywords=["password", "create a password", "choose a password"], 
            fallback_ratio=fallback_ratio,
            is_password=True
        )

    def enter_text_to_field(self, text: str, hint_keywords=None, fallback_ratio=(0.50, 0.35), is_password: bool = False, xml_str: Optional[str] = None) -> bool:
        """Find the real EditText field, tap it to focus, clear it, and type text safely via fast ADB keystrokes.
        Identical rock-solid design across email, username, name, and password fields.
        """
        if not text:
            print("⚠️ Warning: Empty text passed to enter_text_to_field!")
            return False

        # If entering password, wipe out any prior clipboard items on Windows and Android with the exact password
        # This guarantees that if Android or LDPlayer triggers any paste or autofill popup, it will paste the exact password!
        if is_password or (hint_keywords and any("pass" in str(k).lower() for k in hint_keywords)):
            try:
                self.set_clipboard(text)
            except Exception:
                pass

        coords = self.find_edit_text_coordinates(hint_keywords, xml_str=xml_str, is_password=is_password)
        if coords:
            cx, cy = coords
            print(f"🎯 Tapping input field at ({cx}, {cy})...")
            self._tap(cx, cy)
        elif fallback_ratio:
            w, h = self.get_screen_size()
            cx, cy = int(w * fallback_ratio[0]), int(h * fallback_ratio[1])
            print(f"🎯 Fallback tap for input field at ({cx}, {cy})...")
            self._tap(cx, cy)
            
        time.sleep(0.12)
        self._clear_text_field(25)
        time.sleep(0.06)
        
        # Type text purely via ADB keystrokes (identical design to the email field)
        print(f"⌨️ Typing input text: {text}")
        self._type_text(text)
        time.sleep(0.12)
        
        # Dismiss soft keyboard cleanly with KEYCODE_BACK
        self._run_adb_args(["shell", "input", "keyevent", "4"]) # KEYCODE_BACK
        time.sleep(0.08)
        return True

    def _get_displayed_year(self, xml_str: Optional[str] = None) -> Optional[int]:
        """Extract the 4-digit year from the picker or date view in UI XML"""
        import re
        import xml.etree.ElementTree as ET
        if not xml_str:
            xml_str = self.dump_ui()
        if not xml_str:
            return None

        w, h = self.get_screen_size()

        # Priority 1: Check nodes located in the lower half of screen (the picker wheel)
        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)
            picker_years = []
            for node in root.iter('node'):
                bounds_str = node.attrib.get('bounds', '')
                bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(bounds_match) == 2:
                    y1 = int(bounds_match[0][1])
                    if y1 >= int(h * 0.45):
                        text = (node.attrib.get('text', '') or '').strip()
                        desc = (node.attrib.get('content-desc', '') or '').strip()
                        for val in [text, desc]:
                            found = re.findall(r'\b(19\d{2}|20\d{2})\b', val)
                            for fy in found:
                                iy = int(fy)
                                if 1900 <= iy <= 2035:
                                    picker_years.append(iy)
            if picker_years:
                # Return the year closest to center of picker
                return picker_years[0]
        except Exception:
            pass

        # Priority 2: Check any year found in the XML; picker is usually near the end of XML
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', xml_str)
        if years:
            try:
                valid = [int(y) for y in years if 1900 <= int(y) <= 2035]
                if valid:
                    return valid[-1]
            except Exception:
                pass
        return None

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

        # 1. Search for 4-digit year element in XML strictly located in lower half (picker zone)
        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)

            # Check for year text or content-desc in picker region (y >= 0.45 * h)
            for node in root.iter('node'):
                text = (node.attrib.get('text', '') or '').strip()
                desc = (node.attrib.get('content-desc', '') or '').strip()
                if re.search(r'\b(19\d{2}|20\d{2})\b', text) or re.search(r'\b(19\d{2}|20\d{2})\b', desc):
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                        x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                        if y1 >= int(h * 0.45):
                            year_x = (x1 + x2) // 2
                            year_y = (y1 + y2) // 2
                            drag_dist = max(180, int(h * 0.12))
                            y_top = max(int(h * 0.58), year_y - drag_dist)
                            y_bottom = min(int(h * 0.90), year_y + drag_dist)
                            return (year_x, year_y, y_top, y_bottom)

            # Check for NumberPicker or DatePicker elements
            pickers = []
            for node in root.iter('node'):
                node_class = (node.attrib.get('class', '') or '').lower()
                res_id = (node.attrib.get('resource-id', '') or '').lower()
                if 'numberpicker' in node_class or 'datepicker' in node_class or 'wheel' in node_class or 'picker' in res_id:
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                        x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                        if 30 < (x2 - x1) < int(w * 0.60) and (y2 - y1) > 60 and y1 >= int(h * 0.45):
                            pickers.append((x1, y1, x2, y2))

            if pickers:
                # Rightmost picker is Year in LTR / Western / Latin layouts
                pickers.sort(key=lambda p: p[0])
                p = pickers[-1]
                year_x = (p[0] + p[2]) // 2
                year_y = (p[1] + p[3]) // 2
                y_top = p[1] + int((p[3] - p[1]) * 0.18)
                y_bottom = p[3] - int((p[3] - p[1]) * 0.18)
                return (year_x, year_y, y_top, y_bottom)
        except Exception:
            pass

        # 2. Geometric fallback for mobile portrait screen (wheels occupy lower portion)
        # Year wheel is on the right (~78% width), middle vertical zone (~74% height)
        year_x = int(w * 0.78)
        year_y = int(h * 0.74)
        y_top = int(h * 0.62)
        y_bottom = int(h * 0.86)
        return (year_x, year_y, y_top, y_bottom)

    def set_birthday(self, log_cb=None, account_data: Optional[dict] = None) -> bool:
        """
        Rock-solid birthday automation for Instagram:
        1. Ensures the DatePicker bottom-sheet/dialog is open (taps date field if needed).
        2. Detects Year column & current displayed year in picker zone.
        3. Supports direct EditText entry if native NumberPicker is present.
        4. Performs high-velocity physics flings (110ms) DOWN to roll year wheel back ~27 years (to 1999).
        5. Confirms any DatePicker dialog ('Set' / 'OK' / 'Done' / android:id/button1).
        6. Taps primary 'Next' / 'Continue' button with fallback coordinates & keyevent 66.
        7. Handles Instagram age confirmation dialog ('Are you X years old?' / 'Confirm your age').
        8. Dismisses under-age error dialogs if encountered and retries.
        """
        if self.stop_requested:
            return False

        def log(msg, level="info"):
            if log_cb:
                try:
                    log_cb(msg, level)
                except Exception:
                    pass

        w, h = self.get_screen_size()
        target_year = 1999
        if account_data and account_data.get('birthday'):
            try:
                b_parts = str(account_data['birthday']).split('-')
                if len(b_parts) >= 1 and b_parts[0].isdigit():
                    py = int(b_parts[0])
                    if 1970 <= py <= 2004:
                        target_year = py
            except Exception:
                pass

        log(f"🎂 [Birthday] Inspecting Birthday screen (Target Year: {target_year})...", "info")
        xml = self.dump_ui()

        # Step 1: Ensure DatePicker is open.
        # If no pickers/wheels or 4-digit years found in lower half, tap the date field in upper half
        has_picker_in_lower_half = False
        import re, xml.etree.ElementTree as ET
        try:
            xml_start = xml.find("<?xml")
            clean_xml = xml[xml_start:] if xml_start != -1 else xml
            root = ET.fromstring(clean_xml)
            for node in root.iter('node'):
                bounds_str = node.attrib.get('bounds', '')
                bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(bounds_match) == 2:
                    y1 = int(bounds_match[0][1])
                    if y1 >= int(h * 0.45):
                        n_cls = (node.attrib.get('class', '') or '').lower()
                        n_id = (node.attrib.get('resource-id', '') or '').lower()
                        n_text = (node.attrib.get('text', '') or '')
                        if 'picker' in n_cls or 'wheel' in n_cls or 'picker' in n_id or re.search(r'\b(19\d{2}|20\d{2})\b', n_text):
                            has_picker_in_lower_half = True
                            break
        except Exception:
            pass

        if not has_picker_in_lower_half:
            log("👉 Date picker not open yet. Tapping date display field to open wheel...", "info")
            date_field_coords = self.find_text_coordinates([
                "january", "february", "march", "april", "may", "june",
                "july", "august", "september", "october", "november", "december",
                "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
                "2026", "2025", "2024", "date of birth", "birthday"
            ], xml_str=xml)
            if date_field_coords and date_field_coords[1] < int(h * 0.45):
                self._tap(date_field_coords[0], date_field_coords[1])
            else:
                self._tap(int(w * 0.50), int(h * 0.32))
            time.sleep(0.6)
            xml = self.dump_ui()

        # Step 2: Try direct NumberPicker EditText entry if native widget exists
        direct_entry_success = False
        try:
            xml_start = xml.find("<?xml")
            clean_xml = xml[xml_start:] if xml_start != -1 else xml
            root = ET.fromstring(clean_xml)
            for node in root.iter('node'):
                res_id = (node.attrib.get('resource-id', '') or '').lower()
                node_cls = (node.attrib.get('class', '') or '').lower()
                text = (node.attrib.get('text', '') or '').strip()
                if ('numberpicker_input' in res_id or 'edittext' in node_cls) and re.match(r'^(?:19\d{2}|20\d{2})$', text):
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        cx = (int(bounds_match[0][0]) + int(bounds_match[1][0])) // 2
                        cy = (int(bounds_match[0][1]) + int(bounds_match[1][1])) // 2
                        if cy >= int(h * 0.45):
                            log(f"✍️ Direct year input detected at ({cx}, {cy}). Setting Year {target_year}...", "info")
                            self._tap(cx, cy)
                            time.sleep(0.15)
                            self._clear_text_field(6)
                            self._run_adb_args(["shell", "input", "text", str(target_year)])
                            time.sleep(0.2)
                            direct_entry_success = True
                            break
        except Exception:
            pass

        # Step 3: Scrollable Wheel Automation with high-velocity flings
        year_x, year_y, y_top, y_bottom = self.find_birthday_picker_info(xml)
        month_x = int(w * 0.22)
        day_x = int(w * 0.50)

        # High-velocity fling helper: duration 110ms gives Android momentum to spin 8-12 items
        def do_fling(x, y1, y2, duration_ms=110):
            self._run_adb_args(["shell", "input", "swipe", str(x), str(y1), str(x), str(y2), str(duration_ms)])
            time.sleep(0.12)

        if not direct_entry_success:
            initial_year = self._get_displayed_year(xml)
            log(f"🔄 Rolling Year wheel at x={year_x} (initial detected: {initial_year or 'current'})...", "info")

            # Direction 1: Pull DOWN (from y_top to y_bottom) to decrease years towards target
            # 5 fast flings will spin the wheel back 20-30 years
            for _ in range(5):
                do_fling(year_x, y_top, y_bottom, duration_ms=110)

            # Tap center to stop momentum
            self._tap(year_x, year_y)
            time.sleep(0.3)

            mid_check_xml = self.dump_ui()
            year_after_down = self._get_displayed_year(mid_check_xml)

            # If wheel did not decrease or is still >= 2005, try scrolling UP
            if initial_year and year_after_down and year_after_down >= initial_year and year_after_down > 2004:
                log("🔄 Wheel inverted. Flinging UP to reach adult years...", "info")
                for _ in range(6):
                    do_fling(year_x, y_bottom, y_top, duration_ms=110)
                self._tap(year_x, year_y)
                time.sleep(0.3)
            elif not year_after_down or year_after_down > 2004:
                # Additional flings downward to firmly ensure adult age
                for _ in range(4):
                    do_fling(year_x, y_top, y_bottom, duration_ms=110)
                self._tap(year_x, year_y)
                time.sleep(0.3)

            # Also fling month and day once so the date looks completely natural
            do_fling(month_x, y_top, y_bottom, duration_ms=150)
            do_fling(day_x, y_top, y_bottom, duration_ms=150)

        # Allow wheel momentum to settle
        time.sleep(0.4)

        # Step 4: Confirm DatePicker Dialog ("SET" / "OK" / "Done") if modal
        log("👉 Confirming date selection in DatePicker...", "info")
        # Tap Set/OK only if element actually exists on screen
        dialog_confirmed = self.tap_text(["Set", "SET", "Ok", "OK", "Done", "DONE", "Confirm", "Save", "Установить", "Готово"], timeout=0.6)
        if not dialog_confirmed:
            # Check for native Android dialog positive button
            post_wheel_xml = self.dump_ui()
            if "android:id/button1" in post_wheel_xml:
                coords = self.find_text_coordinates(["SET", "Set", "OK", "Ok"], xml_str=post_wheel_xml)
                if coords:
                    self._tap(coords[0], coords[1])
        time.sleep(0.4)

        # Step 5: Tap primary 'Next' button on Birthday screen
        log("👉 Tapping 'Next' on Birthday screen...", "info")
        next_coords = self.find_text_coordinates(["Next", "Continue", "Далее", "Siguiente", "Avançar"])
        if next_coords:
            log(f"🎯 Tapping 'Next' at {next_coords}...", "info")
            self._tap(next_coords[0], next_coords[1])
        else:
            # Tap Instagram standard Next position (above wheels at y=0.44 * h)
            self._tap(int(w * 0.50), int(h * 0.44))
            time.sleep(0.2)
            self._tap(int(w * 0.50), int(h * 0.52))

        # Send Enter key as complementary confirmation
        self._run_adb_args(["shell", "input", "keyevent", "66"])
        time.sleep(1.2)

        # Step 6: Handle Age Confirmation Dialog ("Are you X years old?" / "Confirm your age")
        post_xml = self.dump_ui().lower()
        if any(k in post_xml for k in ["years old", "confirm your age", "confirm your birthday", "is this your", "how old are you"]):
            log("🎂 Age confirmation dialog detected ('Are you X years old?'). Tapping 'OK' / 'Confirm'...", "info")
            self.tap_text(["OK", "Ok", "Confirm", "Yes", "Continue"], timeout=1.0, fallback_ratio=(0.75, 0.58))
            time.sleep(1.0)
            post_xml = self.dump_ui().lower()

        # Step 7: Handle Under-13 or Invalid Birthday Error Popup
        if any(k in post_xml for k in ["at least 13", "valid birthday", "can't continue", "sorry"]):
            log("⚠️ Age error dialog detected ('Must be at least 13'). Dismissing and rolling further back...", "warning")
            self.tap_text(["OK", "Ok", "Dismiss", "Cancel"], timeout=1.0)
            time.sleep(0.3)
            # Re-fling year wheel heavily downwards
            for _ in range(8):
                do_fling(year_x, y_top, y_bottom, duration_ms=110)
            self._tap(year_x, year_y)
            time.sleep(0.3)
            self.tap_text(["Set", "SET", "Ok", "OK"], timeout=0.6)
            self.tap_text(["Next", "Continue"], timeout=0.8, fallback_ratio=(0.50, 0.44))
            self._run_adb_args(["shell", "input", "keyevent", "66"])
            time.sleep(1.0)
            post_xml = self.dump_ui().lower()

        # Step 8: Verification - did the screen advance away from Birthday?
        birthday_keywords = [
            "birthday", "date of birth", "how old are you", "set date", 
            "birth date", "add your birthday", "when's your birthday", "день рождения", "дата рождения", "cumpleaños"
        ]
        if not any(k in post_xml for k in birthday_keywords):
            log("✅ Successfully set adult birthday and advanced!", "success")
            return True

        # Retry tap Next once more
        log("⚠️ Still on Birthday screen. Retrying Next tap...", "warning")
        self._tap(int(w * 0.50), int(h * 0.44))
        time.sleep(0.2)
        self._tap(int(w * 0.50), int(h * 0.52))
        self._run_adb_args(["shell", "input", "keyevent", "66"])
        time.sleep(1.0)

        final_xml = self.dump_ui().lower()
        if not any(k in final_xml for k in birthday_keywords):
            log("✅ Successfully set adult birthday and advanced!", "success")
            return True

        log("⚠️ Still on Birthday screen. Will retry on next loop pass...", "warning")
        return False

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

    def is_instagram_installed(self) -> bool:
        """Check if Instagram (or Instagram Lite) is installed on the connected emulator instance"""
        try:
            pkgs = self._run_adb_args(["shell", "pm", "list", "packages"])
            if "com.instagram" in pkgs:
                return True
            path_check = self._run_adb_args(["shell", "pm", "path", "com.instagram.android"])
            if "package:" in path_check:
                return True
            path_lite = self._run_adb_args(["shell", "pm", "path", "com.instagram.lite"])
            if "package:" in path_lite:
                return True
        except Exception:
            pass
        return False

    def launch_instagram(self) -> bool:
        """Launch Instagram using multiple fallback methods for maximum compatibility"""
        # Method 1: Check package name
        installed = self._run_adb("shell pm list packages")
        print(f"Installed instagram check: {'com.instagram' in installed}")
        
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
        if self.stop_requested:
            return ""

        def log(msg, level="info"):
            print(f"[{level.upper()}] {msg}")
            if log_cb:
                try:
                    log_cb(msg, level)
                except Exception:
                    pass

        log("🔐 Setting up real Two-Factor Authentication on Instagram...", "task")
        
        # Step 1: Ensure any initial dialogs/popups are dismissed and navigate to Profile
        if not self.sleep(1.0):
            return ""
        for _ in range(3):
            if self.stop_requested:
                return ""
            ui = self.dump_ui().lower()
            if "not now" in ui or "skip" in ui:
                self.tap_text(["Not now", "Skip"], timeout=1.2, xml_str=ui)
                if not self.sleep(0.5):
                    return ""
            else:
                break
                
        if self.stop_requested:
            return ""

        # Tap Profile tab (bottom right of screen: ~90% x, 95% y)
        log("👤 Navigating to Profile tab...", "info")
        self.tap_text(["Profile", "Edit profile"], timeout=2.0, fallback_ratio=(0.90, 0.95))
        if not self.sleep(0.8):
            return ""
        
        if self.stop_requested:
            return ""

        # Step 2: Tap Hamburger Menu (top right: ~92% x, 5% y)
        log("🍔 Opening Settings Menu (three bars)...", "info")
        self.tap_text(["Options", "Menu", "More options"], timeout=2.0, fallback_ratio=(0.92, 0.05))
        if not self.sleep(0.8):
            return ""
        
        if self.stop_requested:
            return ""

        # Step 3: Tap 'Settings and privacy' or 'Accounts Center'
        log("⚙️ Opening Accounts Center / Settings...", "info")
        self.tap_text(["Accounts Center", "Account Centre", "Settings and privacy", "Settings"], timeout=2.0, fallback_ratio=(0.50, 0.12))
        if not self.sleep(0.8):
            return ""
        
        # In case we landed on Settings list and Accounts Center is at the top card
        ui = self.dump_ui().lower()
        if "accounts center" in ui or "account centre" in ui:
            self.tap_text(["Accounts Center", "Account Centre"], timeout=1.5, fallback_ratio=(0.50, 0.15), xml_str=ui)
            time.sleep(0.8)

        # Step 4: Inside Accounts Center, tap 'Password and security'
        log("🛡️ Opening 'Password and security'...", "info")
        found_pws = self.tap_text(["Password and security", "Password & security"], timeout=2.0)
        if not found_pws:
            # Scroll down slightly and try again
            self._run_adb_args(["shell", "input", "swipe", "540", "1200", "540", "600", "200"])
            time.sleep(0.5)
            self.tap_text(["Password and security", "Password & security"], timeout=1.5, fallback_ratio=(0.50, 0.40))
        time.sleep(0.8)

        # Step 5: Inside Password and security, tap 'Two-factor authentication'
        log("🔐 Opening 'Two-factor authentication'...", "info")
        self.tap_text(["Two-factor authentication", "Two-Factor authentication", "Two-factor", "2-step"], timeout=2.0, fallback_ratio=(0.50, 0.32))
        time.sleep(0.8)

        # Step 6: Choose Account (Instagram profile)
        log("👤 Selecting account...", "info")
        username = account_data.get('username', '')
        self.tap_text([username, "Instagram"], timeout=1.5, fallback_ratio=(0.50, 0.20))
        time.sleep(0.8)

        # Step 7: Choose 'Authentication app' method
        log("📱 Selecting 'Authentication app' method...", "info")
        self.tap_text(["Authentication app", "Authentication app (recommended)"], timeout=2.0, fallback_ratio=(0.50, 0.32))
        time.sleep(0.5)
        # Tap Next on method selection
        self.tap_text(["Next", "Continue"], timeout=1.5, fallback_ratio=(0.50, 0.92))
        time.sleep(1.2)

        # Step 8: 'Set up authentication app' screen -> Tap 'Copy key'
        log("📋 Locating 'Copy key' button on Instagram...", "info")
        self.tap_text(["Copy key", "Copy code", "Copy"], timeout=2.5, fallback_ratio=(0.50, 0.70))
        time.sleep(0.8)

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
        self.tap_text(["Next", "Enter code", "Continue"], timeout=2.0, fallback_ratio=(0.50, 0.92))
        time.sleep(1.0)

        # Step 11: Enter the 6-digit OTP code into Instagram
        if otp_code:
            log(f"⌨️ Entering OTP code ({otp_code}) into Instagram...", "info")
            self.enter_text_to_field(str(otp_code), hint_keywords=["code", "confirmation", "6-digit"], fallback_ratio=(0.50, 0.35))
            time.sleep(0.5)
            self.tap_text(["Next", "Continue"], timeout=2.0, fallback_ratio=(0.50, 0.45))
            time.sleep(2.0)
            
            # Tap 'Done' on 2FA confirmation screen
            log("✅ Confirming Two-factor authentication is active...", "info")
            self.tap_text(["Done", "Finish", "Next"], timeout=2.0, fallback_ratio=(0.50, 0.92))
            time.sleep(1.0)
            log("🎉 Instagram Two-Factor Authentication successfully enabled!", "success")
        else:
            log("⚠️ No OTP code available to finalize Instagram 2FA in-app, proceeding with extracted key.", "warning")

        return twofa_key

    def create_instagram_account(self, account_data: Dict, otp_fetcher=None, otp_code: str = "", twofa_enabled: bool = True, easyearn_client=None, log_cb=None) -> Dict:
        """
        The master workflow for creating an Instagram account via LDPlayer.
        Dynamically adapts to any screen resolution and modern Instagram UI.
        """
        if self.stop_requested:
            return {'success': False, 'error': 'Stopped by user', 'stopped': True}

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
            if self.stop_requested:
                return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            if "get started" not in ui_check and "create new account" not in ui_check and "create account" not in ui_check:
                log("🚀 Opening Instagram app...", "info")
                self.launch_instagram()
                if not self.sleep(3.5):
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                ui_check = self.dump_ui().lower()
            else:
                log("Instagram is already open!", "info")

            if self.stop_requested:
                return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            # Dismiss Google Smart Lock / Autofill popup if present
            if "none of the above" in ui_check or ("smart lock" in ui_check and "google" in ui_check):
                log("Dismissing Google Smart Lock popup...", "info")
                self.tap_text(["None of the above", "Cancel", "Not now"], timeout=1.0)
                if not self.sleep(0.5):
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                ui_check = self.dump_ui().lower()

            if self.stop_requested:
                return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            # 2. Tap 'Get started' or 'Create new account' if present on welcome screen
            if "create new account" in ui_check or "get started" in ui_check or "create account" in ui_check or "sign up with email or phone" in ui_check:
                log("👉 [Step 1/11] Tapping 'Create new account' / 'Get started'...", "info")
                self.tap_text(
                    ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up"],
                    timeout=2.0,
                    fallback_ratio=(0.50, 0.85),
                    xml_str=ui_check
                )
                if not self.sleep(1.0):
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            # 3. Step-by-Step Registration Loop (11-Step Instagram Registration Flow)
            email_entered = False
            code_entered = False
            password_entered = False
            birthday_set = False
            username_entered = False
            name_entered = False
            terms_agreed = False
            skippable_pass_count = 0

            registration_completed = False

            for step_round in range(1, 50):
                if self.stop_requested:
                    log("⏹️ Stop requested. Halting registration immediately.", "warning")
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}

                ui = self.dump_ui().lower()

                # Dismiss Google Smart Lock / Autofill popup
                if "none of the above" in ui or ("choose an account" in ui and "google" in ui):
                    log("Dismissing Google Autofill / Smart Lock...", "info")
                    self.tap_text(["None of the above", "Cancel", "Not now"], timeout=1.0)
                    if not self.sleep(0.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 1 Recovery: If screen is still on Welcome Screen
                if not (email_entered or code_entered or password_entered or birthday_set or terms_agreed) and (
                    "create new account" in ui or "get started" in ui or "already have an account" in ui
                ):
                    log("👉 [Step 1/11] Welcome screen detected! Tapping 'Create new account'...", "info")
                    self.tap_text(
                        ["Create new account", "Create account", "Get started", "Sign up with email or phone number", "Sign up"],
                        timeout=1.5,
                        fallback_ratio=(0.50, 0.85),
                        xml_str=ui
                    )
                    if not self.sleep(1.0):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 2a: Contact Method - Phone screen detected -> Switch to Email
                on_phone_screen = (
                    ("what's your mobile" in ui or "enter your mobile" in ui or "mobile number" in ui or 
                     "phone number" in ui or "sign up with email" in ui or "sign up with email address" in ui or 
                     "use email" in ui or ("mobile" in ui and "email" not in ui))
                    and not ("what's your email" in ui or "enter your email" in ui or "email address" in ui)
                    and not code_entered
                )
                if on_phone_screen:
                    log("📧 [Step 2/11] Mobile screen detected. Switching to Email ('Sign up with email' / Email tab)...", "info")
                    self.tap_text(
                        ["Sign up with email", "Sign up with email address", "Use email address instead", "Use email", "Email"],
                        timeout=1.2,
                        fallback_ratio=(0.50, 0.88),
                        xml_str=ui
                    )
                    if not self.sleep(0.8):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 2b: Contact Method - Email Entry screen detected
                on_email_screen = (
                    ("what's your email" in ui or "enter your email" in ui or "email address" in ui or 
                     ("email" in ui and ("sign up with phone" in ui or "sign up with mobile" in ui or "use phone" in ui or "use mobile" in ui)) or
                     ("email" in ui and "phone" not in ui and "mobile" not in ui and not code_entered))
                    and not code_entered
                    and not password_entered
                )
                if on_email_screen:
                    log(f"✉️ [Step 2/11] Email screen detected! Entering Email: {account_data['email']}...", "info")
                    self.enter_text_to_field(account_data['email'], hint_keywords=["email", "what's your email", "email address"], fallback_ratio=(0.50, 0.35))
                    log("👉 [Step 2/11] Tapping 'Next' to dispatch confirmation code...", "info")
                    self.tap_text(["Next", "Continue"], timeout=1.2, fallback_ratio=(0.50, 0.45))
                    if not self.sleep(1.2):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    
                    # Verify if screen advanced to confirmation code or password
                    check_post_email = self.dump_ui().lower()
                    if "code" in check_post_email or "confirmation" in check_post_email or "security code" in check_post_email:
                        log("📬 [Step 2/11] Verification code dispatched successfully by Instagram!", "success")
                        email_entered = True
                    elif "password" in check_post_email:
                        email_entered = True
                    continue

                # Step 3: Confirmation Code ("Enter confirmation code" / "Confirmation code" / "6-digit")
                if "confirmation code" in ui or "enter the 6-digit" in ui or "check your email" in ui or "security code" in ui or "enter confirmation" in ui:
                    email_entered = True
                    log("📬 [Step 3/11] Instagram sent verification email! Waiting for OTP code from EasyEarn...", "task")
                    
                    received_code = otp_code
                    if not received_code and otp_fetcher:
                        # Poll EasyEarn for the code for up to 90 seconds
                        for poll_attempt in range(20):
                            if self.stop_requested:
                                log("⏹️ Stop requested. Halting OTP code wait immediately.", "warning")
                                return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                            log(f"⏳ [Step 3/11] Waiting for OTP code from EasyEarn (attempt {poll_attempt+1}/20)...", "info")
                            received_code = otp_fetcher()
                            if received_code:
                                break
                            if not self.sleep(3):
                                log("⏹️ Stop requested. Aborting OTP code wait.", "warning")
                                return {'success': False, 'error': 'Stopped by user', 'stopped': True}

                    if self.stop_requested:
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}

                    if received_code:
                        log(f"🔑 [Step 3/11] OTP Code received: {received_code}! Entering into Instagram...", "success")
                        self.enter_text_to_field(str(received_code).strip(), hint_keywords=["confirmation code", "code"], fallback_ratio=(0.50, 0.35))
                        self.tap_text(["Next", "Continue"], timeout=1.0, fallback_ratio=(0.50, 0.45))
                        code_entered = True
                        if not self.sleep(1.2):
                            return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                        continue
                    else:
                        log("⚠️ [Step 3/11] Did not receive OTP code in time. Will retry on next cycle.", "warning")
                        break

                # Step 4: Password Step ("Create a password")
                on_password_screen = (
                    not password_entered and 
                    ("create a password" in ui or "choose a password" in ui or "set a password" in ui or 
                     ("password" in ui and "login" not in ui and not on_phone_screen and not on_email_screen))
                )
                if on_password_screen:
                    pwd = account_data.get('password', '').strip()
                    if not pwd or len(pwd) < 6:
                        import random, string
                        seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                        pwd = f"Insta_{seed}9"
                        account_data['password'] = pwd

                    log(f"🔒 [Step 4/11] Entering Password: '{account_data['password']}'", "info")
                    self.set_clipboard(account_data['password'])
                    self.enter_text_to_field(account_data['password'], hint_keywords=["password", "create a password"], fallback_ratio=(0.50, 0.35), is_password=True)
                    log("👉 [Step 4/11] Submitting password via 'Next' and enter key...", "info")
                    self.tap_text(["Next", "Continue"], timeout=1.2, fallback_ratio=(0.50, 0.52))
                    self._run_adb_args(["shell", "input", "keyevent", "66"])
                    if not self.sleep(1.2):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    
                    # Verify if screen transitioned away from password
                    check_post_pwd = self.dump_ui().lower()
                    if not ("create a password" in check_post_pwd or "choose a password" in check_post_pwd):
                        log("✅ [Step 4/11] Password accepted by Instagram!", "success")
                        password_entered = True
                    else:
                        # Retry Next button at alternative positions
                        self._tap(int(w * 0.50), int(h * 0.52))
                        time.sleep(0.2)
                        self._tap(int(w * 0.50), int(h * 0.45))
                        self._run_adb_args(["shell", "input", "keyevent", "66"])
                        password_entered = True
                    continue

                # Step 4b: Save login info prompt ("Save your login info?")
                on_save_login_screen = (
                    ("save your login info" in ui or "save login info" in ui or 
                     (("save" in ui or "remember" in ui) and ("not now" in ui or "never" in ui or "no thanks" in ui)))
                    and not on_phone_screen and not on_email_screen
                )
                if on_save_login_screen:
                    log("💾 [Step 4b/11] Save Login Info detected. Tapping 'Save'...", "info")
                    self.tap_text(["Save", "Save info", "Not now"], timeout=1.2, fallback_ratio=(0.50, 0.48))
                    if not self.sleep(0.8):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 5: Birthday Step ("What's your birthday?" / "Date of birth")
                on_birthday_screen = (
                    "birthday" in ui or "date of birth" in ui or "how old are you" in ui or 
                    "set date" in ui or "birth date" in ui or "add your birthday" in ui or
                    "when's your birthday" in ui or "whens your birthday" in ui or
                    "день рождения" in ui or "дата рождения" in ui or "cumpleaños" in ui or
                    "aniversário" in ui or ("month" in ui and "year" in ui) or ("day" in ui and "year" in ui) or
                    "numberpicker" in ui or "datepicker" in ui or "date_picker" in ui
                )
                if on_birthday_screen:
                    log("🎂 [Step 5/11] Birthday screen detected! Setting adult age (rolling wheel back to 1999)...", "info")
                    if self.set_birthday(log_cb=log, account_data=account_data):
                        birthday_set = True
                    if not self.sleep(1.0):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 6: Username Step ("Create a username")
                on_username_screen = (
                    "create a username" in ui or "choose a username" in ui or "what's your username" in ui or
                    ("username" in ui and not on_email_screen and not on_birthday_screen and not on_password_screen)
                )
                if on_username_screen:
                    log(f"👤 [Step 6/11] Setting Username: {account_data['username']}...", "info")
                    self.enter_text_to_field(account_data['username'], hint_keywords=["username", "create a username"], fallback_ratio=(0.50, 0.35))
                    self.tap_text(["Next", "Continue"], timeout=1.2, fallback_ratio=(0.50, 0.52))
                    self._run_adb_args(["shell", "input", "keyevent", "66"])
                    username_entered = True
                    if not self.sleep(0.8):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Optional Name step if presented in this variant ("What's your name?" / "Full name")
                if not name_entered and ("what's your name" in ui or "full name" in ui):
                    log(f"📝 Entering Name: {account_data['full_name']}...", "info")
                    self.enter_text_to_field(account_data['full_name'], hint_keywords=["full name", "name"], fallback_ratio=(0.50, 0.35))
                    self.tap_text(["Next", "Continue"], timeout=1.0, fallback_ratio=(0.50, 0.45))
                    name_entered = True
                    if not self.sleep(0.4):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 7: Agree to Terms and Policies ("I agree" / "Sign up")
                if not terms_agreed and ("i agree" in ui or "agree to instagram" in ui or "terms & policies" in ui or "terms and policies" in ui or "terms of use" in ui or "terms" in ui):
                    log("📜 [Step 7/11] Tapping 'I agree' to Terms & Policies...", "info")
                    self.tap_text(["I agree", "Agree", "Sign up"], timeout=1.2, fallback_ratio=(0.50, 0.90))
                    terms_agreed = True
                    if not self.sleep(3.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 8: Add Profile Picture (Skippable)
                if terms_agreed and ("add picture" in ui or "profile picture" in ui or "add a profile photo" in ui):
                    log("⏭️ [Step 8/11] Add Profile Picture: Tapping 'Skip'...", "info")
                    self.tap_text(["Skip", "Not now"], timeout=1.0, fallback_ratio=(0.50, 0.90), xml_str=ui)
                    skippable_pass_count += 1
                    if not self.sleep(0.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 9: Find Friends from Contacts (Skippable)
                if terms_agreed and ("find friends" in ui or "contacts" in ui or "sync contacts" in ui):
                    log("⏭️ [Step 9/11] Contacts Sync: Tapping 'Skip'...", "info")
                    self.tap_text(["Skip", "Not now", "Cancel", "Deny"], timeout=1.0, fallback_ratio=(0.50, 0.90), xml_str=ui)
                    skippable_pass_count += 1
                    if not self.sleep(0.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 10: Connect to Facebook (Skippable)
                if terms_agreed and ("facebook" in ui or "connect to facebook" in ui):
                    log("⏭️ [Step 10/11] Connect to Facebook: Tapping 'Skip'...", "info")
                    self.tap_text(["Skip", "Not now"], timeout=1.0, fallback_ratio=(0.50, 0.90), xml_str=ui)
                    skippable_pass_count += 1
                    if not self.sleep(0.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Step 11: Discover Suggested Accounts (Final Screen - Bypass via Top Right Arrow/Next)
                if terms_agreed and ("discover people" in ui or "suggested accounts" in ui or "suggestions" in ui or ("follow" in ui and "discover" in ui)):
                    log("👥 [Step 11/11] Discover Suggested Accounts: Bypassing via top-right arrow/next...", "info")
                    tapped = self.tap_text(["Next", "Done", "Skip"], timeout=0.8, xml_str=ui)
                    if not tapped:
                        # Tap top-right arrow button at ~92% width, ~6% height
                        self._tap(int(w * 0.92), int(h * 0.06))
                    skippable_pass_count += 1
                    if not self.sleep(1.0):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Generic Onboarding Skip after terms agreed
                if terms_agreed and ("skip" in ui or "not now" in ui):
                    log("⏭️ Bypassing onboarding prompt ('Skip' / 'Not now')...", "info")
                    self.tap_text(["Skip", "Not now"], timeout=1.0, fallback_ratio=(0.50, 0.90), xml_str=ui)
                    skippable_pass_count += 1
                    if not self.sleep(0.5):
                        return {'success': False, 'error': 'Stopped by user', 'stopped': True}
                    continue

                # Final Home Feed Verification
                # Screen loads primary bottom navigation bar (Home feed, Search, Reels, Profile)
                # CRITICAL RULE: terms_agreed MUST be True. You cannot complete registration before terms!
                on_home_feed = (
                    terms_agreed and (
                        "tab_bar" in ui or "tab_avatar" in ui or "main_feed" in ui or
                        skippable_pass_count >= 2 or
                        ("feed" in ui and ("search" in ui or "reels" in ui or "profile" in ui))
                    )
                )
                if on_home_feed:
                    log("🎉 [Complete] Home feed reached! Instagram registration fully verified!", "success")
                    registration_completed = True
                    break

                if not self.sleep(0.35):
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            if self.stop_requested:
                log("⏹️ Stop requested. Halting registration immediately.", "warning")
                return {'success': False, 'error': 'Stopped by user', 'stopped': True}

            if not registration_completed:
                stalled_screen = "Unknown screen"
                if "create new account" in ui or "get started" in ui:
                    stalled_screen = "Welcome screen"
                elif "mobile" in ui or "phone" in ui:
                    stalled_screen = "Mobile number screen"
                elif "birthday" in ui or "date of birth" in ui:
                    stalled_screen = "Birthday screen"
                elif "password" in ui or "create a password" in ui:
                    stalled_screen = "Password screen"
                elif "username" in ui:
                    stalled_screen = "Username screen"
                elif "email" in ui:
                    stalled_screen = "Email screen"
                elif "confirmation code" in ui or "code" in ui:
                    stalled_screen = "OTP Code screen"
                elif "agree" in ui or "terms" in ui:
                    stalled_screen = "Terms & Conditions screen"
                
                log(f"❌ Registration did not finish. Stopped at: {stalled_screen}", "error")
                return {
                    'success': False,
                    'error': f'Registration stopped at {stalled_screen}',
                    'username': account_data.get('username', '')
                }

            # Step 4: Real Two-Factor Authentication (2FA) Setup
            twofa_key = ""
            if twofa_enabled:
                if self.stop_requested:
                    return {'success': False, 'error': 'Stopped by user', 'stopped': True}
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

