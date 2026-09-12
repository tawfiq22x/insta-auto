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

    def find_text_coordinates(
        self,
        keywords,
        xml_str: Optional[str] = None,
        exact: bool = False,
        min_y: int = 0,
        max_y: Optional[int] = None,
        exclude_ids: Optional[list] = None,
        prefer_clickable: bool = False
    ) -> Optional[Tuple[int, int]]:
        """Find center coordinates of an element containing or matching any of the keywords with optional ID filtering"""
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
            candidates = []
            for node in root.iter('node'):
                node_text = (node.attrib.get('text', '') or '').strip().lower()
                node_desc = (node.attrib.get('content-desc', '') or '').strip().lower()
                res_id = (node.attrib.get('resource-id', '') or '').lower()
                clickable = (node.attrib.get('clickable') == 'true') or ('button' in (node.attrib.get('class', '') or '').lower())

                # Skip nodes matching exclude_ids (e.g. ['title', 'alerttitle', 'header'])
                if exclude_ids and any(ex.lower() in res_id for ex in exclude_ids):
                    continue

                bounds_str = node.attrib.get('bounds', '')
                for kw in keywords:
                    kw_lower = kw.lower().strip()
                    matched = False
                    if exact:
                        matched = (node_text == kw_lower or node_desc == kw_lower)
                    else:
                        matched = (kw_lower in node_text or kw_lower in node_desc)

                    if matched:
                        bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                        if len(bounds_match) == 2:
                            x1, y1 = int(bounds_match[0][0]), int(bounds_match[0][1])
                            x2, y2 = int(bounds_match[1][0]), int(bounds_match[1][1])
                            cx = (x1 + x2) // 2
                            cy = (y1 + y2) // 2
                            if cy >= min_y and (max_y is None or cy <= max_y):
                                candidates.append((cx, cy, clickable))
                                break

            if candidates:
                if prefer_clickable:
                    clickables = [c for c in candidates if c[2]]
                    if clickables:
                        return (clickables[0][0], clickables[0][1])
                return (candidates[0][0], candidates[0][1])
        except Exception:
            pass

        # 2. Fast regex fallback
        for kw in keywords:
            if exact:
                pattern = rf'(?:text|content-desc)="{re.escape(kw)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            else:
                pattern = rf'(?:text|content-desc)="[^"]*{re.escape(kw)}[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
            match = re.search(pattern, xml_str, re.IGNORECASE)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                cy = (y1 + y2) // 2
                if cy >= min_y and (max_y is None or cy <= max_y):
                    return ((x1 + x2) // 2, cy)

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
        
        # Type text cleanly: pure ASCII uses direct keyevents, Unicode/Arabic uses clipboard paste
        is_pure_ascii = all(ord(c) < 128 for c in text)
        if is_pure_ascii:
            print(f"⌨️ Typing input text: {text}")
            self._type_text(text)
        else:
            print(f"📋 Pasting Unicode/Arabic text: {text}")
            self.set_clipboard(text)
            time.sleep(0.08)
            # KEYCODE_PASTE (279)
            self._run_adb_args(["shell", "input", "keyevent", "279"])
            time.sleep(0.06)
            # Ctrl+V fallback
            self._run_adb_args(["shell", "input", "keyevent", "--meta", "113", "29"])
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

        # Priority 1: Check nodes located in picker zone (y >= 0.25 * h)
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
                    if y1 >= int(h * 0.25):
                        text = (node.attrib.get('text', '') or '').strip()
                        desc = (node.attrib.get('content-desc', '') or '').strip()
                        for val in [text, desc]:
                            found = re.findall(r'\b(19\d{2}|20\d{2})\b', val)
                            for fy in found:
                                iy = int(fy)
                                if 1900 <= iy <= 2035:
                                    picker_years.append(iy)
            if picker_years:
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

        # 1. Search for NumberPicker or DatePicker elements in XML
        try:
            xml_start = xml_str.find("<?xml")
            clean_xml = xml_str[xml_start:] if xml_start != -1 else xml_str
            root = ET.fromstring(clean_xml)

            # Look for 4-digit year element in XML to locate exact year column
            year_node_bounds = None
            for node in root.iter('node'):
                text = (node.attrib.get('text', '') or '').strip()
                desc = (node.attrib.get('content-desc', '') or '').strip()
                if re.search(r'\b(19\d{2}|20\d{2})\b', text) or re.search(r'\b(19\d{2}|20\d{2})\b', desc):
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        y1 = int(bounds_match[0][1])
                        if y1 >= int(h * 0.25):
                            year_node_bounds = (int(bounds_match[0][0]), int(bounds_match[0][1]), int(bounds_match[1][0]), int(bounds_match[1][1]))
                            break

            # Find all NumberPicker columns
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
                        if 30 < (x2 - x1) < int(w * 0.60) and (y2 - y1) > 60 and y1 >= int(h * 0.25):
                            pickers.append((x1, y1, x2, y2))

            if pickers:
                # Deduplicate pickers with overlapping x coordinates
                unique_pickers = []
                for p in sorted(pickers, key=lambda p: p[0]):
                    if not unique_pickers or abs(p[0] - unique_pickers[-1][0]) > 40:
                        unique_pickers.append(p)

                # If we found year_node_bounds, find which picker contains its X center
                target_picker = None
                if year_node_bounds:
                    yn_cx = (year_node_bounds[0] + year_node_bounds[2]) // 2
                    for p in unique_pickers:
                        if p[0] <= yn_cx <= p[2]:
                            target_picker = p
                            break

                # Otherwise default to the rightmost picker (Western/Android standard)
                if not target_picker:
                    target_picker = unique_pickers[-1]

                year_x = (target_picker[0] + target_picker[2]) // 2
                year_y = (target_picker[1] + target_picker[3]) // 2
                drag_dist = max(140, int((target_picker[3] - target_picker[1]) * 0.25))
                y_top = max(target_picker[1] + 30, year_y - drag_dist)
                y_bottom = min(target_picker[3] - 30, year_y + drag_dist)
                return (year_x, year_y, y_top, y_bottom)

            # If no pickers found but year node exists
            if year_node_bounds:
                year_x = (year_node_bounds[0] + year_node_bounds[2]) // 2
                year_y = (year_node_bounds[1] + year_node_bounds[3]) // 2
                drag_dist = max(180, int(h * 0.12))
                y_top = max(int(h * 0.35), year_y - drag_dist)
                y_bottom = min(int(h * 0.90), year_y + drag_dist)
                return (year_x, year_y, y_top, y_bottom)
        except Exception:
            pass

        # Geometric fallback: year wheel is in the right third of the dialog/picker area
        year_x = int(w * 0.78)
        year_y = int(h * 0.58)
        y_top = int(h * 0.45)
        y_bottom = int(h * 0.70)
        return (year_x, year_y, y_top, y_bottom)

    def confirm_date_picker(self, log_cb=None) -> bool:
        """
        Confirms the DatePicker dialog or bottom sheet ('SET' / 'Set' / 'Set date' / 'android:id/button1').
        Guarantees that the positive confirmation button is clicked rather than dialog title headers.
        """
        def log(msg, level="info"):
            if log_cb:
                try: log_cb(msg, level)
                except Exception: pass

        w, h = self.get_screen_size()
        xml = self.dump_ui()
        import re, xml.etree.ElementTree as ET

        # 1. Primary Check: android:id/button1 (The official positive button of any Android AlertDialog/DatePickerDialog)
        try:
            xml_start = xml.find("<?xml")
            clean_xml = xml[xml_start:] if xml_start != -1 else xml
            root = ET.fromstring(clean_xml)
            for node in root.iter('node'):
                res_id = (node.attrib.get('resource-id', '') or '').lower()
                if 'button1' in res_id:
                    bounds_str = node.attrib.get('bounds', '')
                    bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                    if len(bounds_match) == 2:
                        cx = (int(bounds_match[0][0]) + int(bounds_match[1][0])) // 2
                        cy = (int(bounds_match[0][1]) + int(bounds_match[1][1])) // 2
                        log(f"🎯 Tapped DatePicker confirm button (android:id/button1) at ({cx}, {cy})", "info")
                        self._tap(cx, cy)
                        time.sleep(0.4)
                        return True
        except Exception:
            pass

        # 2. Check for button with text "SET", "Set", "Set date", "Done", "OK" that is NOT a title/header
        try:
            xml_start = xml.find("<?xml")
            clean_xml = xml[xml_start:] if xml_start != -1 else xml
            root = ET.fromstring(clean_xml)
            for node in root.iter('node'):
                text = (node.attrib.get('text', '') or '').strip()
                desc = (node.attrib.get('content-desc', '') or '').strip()
                res_id = (node.attrib.get('resource-id', '') or '').lower()

                # STRICTLY skip dialog titles or header text
                if 'title' in res_id or 'header' in res_id or 'alerttitle' in res_id:
                    continue

                for label in [text, desc]:
                    if label.upper() in ["SET", "SET DATE", "DONE", "OK", "CONFIRM", "SAVE", "ГОТОВО", "УСТАНОВИТЬ"]:
                        bounds_str = node.attrib.get('bounds', '')
                        bounds_match = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                        if len(bounds_match) == 2:
                            cx = (int(bounds_match[0][0]) + int(bounds_match[1][0])) // 2
                            cy = (int(bounds_match[0][1]) + int(bounds_match[1][1])) // 2
                            # Must be below the top third of screen
                            if cy >= int(h * 0.35):
                                log(f"🎯 Tapped DatePicker confirmation button '{label}' at ({cx}, {cy})", "info")
                                self._tap(cx, cy)
                                time.sleep(0.4)
                                return True
        except Exception:
            pass

        # 3. Fast regex check for exact button text="SET" or text="Set"
        match_btn = re.search(r'text="(?i:set|set date|done|ok)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)
        if match_btn:
            x1, y1, x2, y2 = map(int, match_btn.groups())
            cy = (y1 + y2) // 2
            if cy >= int(h * 0.35):
                cx = (x1 + x2) // 2
                log(f"🎯 Regex matched DatePicker confirm button at ({cx}, {cy})", "info")
                self._tap(cx, cy)
                time.sleep(0.4)
                return True

        # 4. Fallback: Standard Android dialog positive button location (~78% width, dialog button area)
        log("👉 Trying standard DatePicker positive button fallback...", "info")
        self._tap(int(w * 0.78), int(h * 0.65))
        time.sleep(0.2)
        self._run_adb_args(["shell", "input", "keyevent", "66"]) # KEYCODE_ENTER
        time.sleep(0.4)
        return False

    def set_birthday(self, log_cb=None, account_data: Optional[dict] = None) -> bool:
        """
        Ultra-efficient, simplified birthday setter.
        Swipes down forcefully on the year column and proceeds.
        """
        if self.stop_requested:
            return False

        def log(msg, level="info"):
            if log_cb:
                try: log_cb(msg, level)
                except Exception: pass

        w, h = self.get_screen_size()
        log("🎂 [Birthday] Setting adult age aggressively...", "info")

        # 1. Bring up the date picker if it isn't visible yet
        xml = self.dump_ui().lower()
        if "numberpicker" not in xml and "datepicker" not in xml and "button1" not in xml:
            log("👉 Opening Date Picker...", "info")
            coords = self.find_text_coordinates(["set date", "birthday", "january", "february", "march", "date of birth", "add your birthday", "year"], max_y=int(h * 0.60))
            if coords: self._tap(coords[0], coords[1])
            else: self._tap(int(w * 0.50), int(h * 0.35))
            time.sleep(1.0)
        
        # 2. Forceful Swipes DOWN on the right side of the screen (where the Year wheel sits)
        log("🔄 Spinning the year wheel back...", "info")
        year_x = int(w * 0.80)
        y_top = int(h * 0.40)
        y_bottom = int(h * 0.70)
        
        for _ in range(6):
            self._run_adb_args(["shell", "input", "swipe", str(year_x), str(y_top), str(year_x), str(y_bottom), "100"])
            time.sleep(0.2)
        
        self._tap(year_x, (y_top + y_bottom) // 2)
        time.sleep(0.5)

        # 3. Confirm the date picker
        self.confirm_date_picker(log_cb=log)
        time.sleep(1.0)
        check_xml = self.dump_ui().lower()
        if "button1" in check_xml or "numberpicker" in check_xml:
            self.confirm_date_picker(log_cb=log)
            time.sleep(1.0)

        # 4. Tap the 'Next' button on the main birthday screen
        log("👉 Tapping 'Next' to proceed...", "info")
        next_coords = self.find_text_coordinates(["Next", "Continue", "Далее", "Siguiente"], min_y=int(h * 0.40))
        if next_coords:
            self._tap(next_coords[0], next_coords[1])
        else:
            self._tap(int(w * 0.50), int(h * 0.45))
            time.sleep(0.3)
            self._tap(int(w * 0.50), int(h * 0.52))

        self._run_adb_args(["shell", "input", "keyevent", "66"])
        time.sleep(1.5)

        # 5. Handle confirmations or errors
        post_xml = self.dump_ui().lower()
        if any(k in post_xml for k in ["years old", "confirm your age", "confirm your birthday", "is this your", "how old are you"]):
            log("🎂 Confirming age dialog...", "info")
            self.tap_text(["OK", "Ok", "Confirm", "Yes", "Continue"], timeout=1.0)
            time.sleep(1.5)
            post_xml = self.dump_ui().lower()

        if any(k in post_xml for k in ["at least 13", "valid birthday", "can't continue", "sorry"]):
            log("⚠️ Age error detected. Swiping again...", "warning")
            self.tap_text(["OK", "Ok", "Dismiss", "Close", "Cancel"], timeout=1.0)
            time.sleep(0.5)
            for _ in range(8):
                self._run_adb_args(["shell", "input", "swipe", str(year_x), str(y_top), str(year_x), str(y_bottom), "100"])
            self._tap(year_x, (y_top + y_bottom) // 2)
            time.sleep(0.5)
            self.confirm_date_picker(log_cb=log)
            time.sleep(1.0)
            next_coords = self.find_text_coordinates(["Next", "Continue"], min_y=int(h * 0.40))
            if next_coords: self._tap(next_coords[0], next_coords[1])
            else: self._tap(int(w * 0.50), int(h * 0.45))
            self._run_adb_args(["shell", "input", "keyevent", "66"])
            time.sleep(1.5)
        
        return True
