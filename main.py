# main.py
import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from typing import Dict, Optional

# --- Error Logging Setup ---
class Logger(object):
    def __init__(self, filename="error_log.txt"):
        self.terminal = sys.stdout
        self.log_file = open(filename, "a", encoding="utf-8")

    def write(self, message):
        if self.terminal:
            try:
                self.terminal.write(message)
            except:
                pass
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        if self.terminal:
            try:
                self.terminal.flush()
            except:
                pass
        self.log_file.flush()

# Redirect stdout and stderr to our logger file
sys.stdout = Logger("error_log.txt")
sys.stderr = sys.stdout
# ---------------------------

# Import our modules
from easyearn_client import EasyEarnClient
from ldplayer_automation import LDPlayerAutomation

class InstagramAutomationController:
    """Master controller for the entire automation workflow"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 Instagram Automation Suite v5.0")
        self.root.geometry("1100x750")
        self.root.resizable(False, False)
        
        # State
        self.is_running = False
        self.current_task = None
        self.accounts_created = 0
        self.failed_accounts = 0
        
        # Load version info
        self.version_info = self.get_version_info()
        curr_ver = self.version_info.get("version", "1.4.5")
        self.root.title(f"🤖 Instagram Automation Suite - v{curr_ver}")
        self.root.geometry("1120x800")
        self.root.minsize(1000, 720)
        self.root.resizable(True, True)
        
        # Initialize clients
        self.easyearn = EasyEarnClient(log_callback=self.log)
        self.ldplayer = LDPlayerAutomation()
        
        # UI Variables
        self.ldplayer_path = tk.StringVar(value="C:\\LDPlayer\\LDPlayer9\\dnplayer.exe")
        self.instance_name = tk.StringVar(value="LDPlayer")
        self.instance_index = tk.StringVar(value="0")
        self.auto_mode = tk.BooleanVar(value=True)
        self.headless_mode = tk.BooleanVar(value=False)
        self._config_loaded = False
        
        self.setup_ui()
        self.load_config()
        self._config_loaded = True
        
        # Attach automatic saving to all configuration variables
        self._bind_auto_save(self.ldplayer_path)
        self._bind_auto_save(self.instance_name)
        self._bind_auto_save(self.instance_index)
        self._bind_auto_save(self.auto_mode)
        self._bind_auto_save(self.headless_mode)
        
    def get_version_info(self) -> dict:
        """Load version and release details from version.json"""
        default_info = {
            "version": "1.4.9",
            "release_date": "2026-09-11 19:15",
            "build_id": "v1.4.9-rel",
            "features": [
                "Unified Email & Password Keystroke Engine: Password entry strictly uses the identical direct ADB typing design as the email field (zero clipboard paste dependencies)",
                "Clipboard Sanitization: Both Windows and Android clipboards are explicitly synchronized with the active password, preventing any stale clipboard text from ever being pasted",
                "Accurate Password Field Targeting: Prioritizes genuine EditText nodes with password='true' and ignores static header TextViews",
                "Single-Process Subshell Clear: Clearing fields runs via device-native subshell loop for instant clearing without lag",
                "High-Speed Button Presses: Direct process argument invocation eliminates process spawn overhead on taps",
                "Zero-Latency Pre-dumped XML Lookup: Reuses already-dumped UI XML hierarchy so buttons like 'Next' and 'Save' tap in milliseconds without re-dumping"
            ]
        }
        if os.path.exists("version.json"):
            try:
                with open("version.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**default_info, **data}
            except Exception:
                pass
        return default_info

    def setup_ui(self):
        """Build the user interface with tabs"""
        curr_ver = self.version_info.get("version", "1.4.2")
        
        # Notebook for navigation tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Tab 1: Dashboard Frame
        dashboard_tab = ttk.Frame(self.notebook, padding="8")
        self.notebook.add(dashboard_tab, text=" ⚡ Dashboard & Automation ")
        
        # Tab 2: Version & Updates Frame
        version_tab = ttk.Frame(self.notebook, padding="12")
        self.notebook.add(version_tab, text=f" ℹ️ Version & Updates (v{curr_ver}) ")
        
        # Setup Tab 2 contents
        self.setup_version_tab(version_tab)
        
        # Trigger integrity refresh when switching tabs
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        # === Title inside Dashboard ===
        title = ttk.Label(dashboard_tab, text=f"🤖 Instagram Automation Suite   •   v{curr_ver}", 
                         font=('Arial', 17, 'bold'))
        title.grid(row=0, column=0, columnspan=5, pady=8)
        
        # === Stats Bar ===
        stats_frame = ttk.LabelFrame(dashboard_tab, text="📊 Statistics", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=4)
        
        self.stats_labels = {}
        stats = [
            ("🔄 Accounts Created:", "0", "accounts_created"),
            ("❌ Failed:", "0", "failed_accounts"),
            ("💰 Earnings:", "$0.00", "earnings"),
            ("⏱️ Runtime:", "00:00:00", "runtime")
        ]
        
        for i, (label, value, key) in enumerate(stats):
            ttk.Label(stats_frame, text=label).grid(row=0, column=i*2, sticky=tk.W, padx=5)
            self.stats_labels[key] = ttk.Label(stats_frame, text=value, font=('Arial', 12, 'bold'))
            self.stats_labels[key].grid(row=0, column=i*2+1, sticky=tk.W, padx=5)
            if i < len(stats)-1:
                ttk.Separator(stats_frame, orient=tk.VERTICAL).grid(row=0, column=i*2+2, sticky=tk.NS, padx=10)
        
        # === Settings ===
        settings_frame = ttk.LabelFrame(dashboard_tab, text="⚙️ Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=4)
        
        # EasyEarn Account
        ttk.Label(settings_frame, text="Chrome Connection:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="Bot will launch an isolated Stealth Browser. Please click the Cloudflare box manually if it appears.", foreground="#4ec9b0").grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5)
        
        # LDPlayer
        ttk.Label(settings_frame, text="LDPlayer Path:").grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.ldplayer_path, width=40).grid(row=1, column=1, columnspan=2, padx=5)
        ttk.Button(settings_frame, text="Browse", command=self.browse_ldplayer).grid(row=1, column=3, padx=5)
        
        ttk.Label(settings_frame, text="Instance:").grid(row=2, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.instance_name, width=20).grid(row=2, column=1, padx=5, sticky=tk.W)
        ttk.Label(settings_frame, text="Index:").grid(row=2, column=2, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.instance_index, width=10).grid(row=2, column=3, padx=5, sticky=tk.W)
        
        # Options
        ttk.Checkbutton(settings_frame, text="🤖 Auto Mode", variable=self.auto_mode).grid(row=3, column=0, padx=5)
        ttk.Checkbutton(settings_frame, text="🖥️ Headless Mode", variable=self.headless_mode).grid(row=3, column=1, padx=5)
        
        # === Controls ===
        control_frame = ttk.Frame(dashboard_tab)
        control_frame.grid(row=3, column=0, columnspan=5, pady=8)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Automation", 
                                    command=self.start_automation, width=18)
        self.start_btn.grid(row=0, column=0, padx=4)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", 
                                   command=self.stop_automation, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=4)
        
        ttk.Button(control_frame, text="🧹 Clear Log", command=self.clear_log, width=13).grid(row=0, column=2, padx=4)
        ttk.Button(control_frame, text="💾 Save Config", command=self.save_config, width=13).grid(row=0, column=3, padx=4)
        ttk.Button(control_frame, text="📊 Test Connection", command=self.test_connection, width=15).grid(row=0, column=4, padx=4)
        ttk.Button(control_frame, text="🚀 Launch LDPlayer", command=self.manual_launch_ldplayer, width=16).grid(row=0, column=5, padx=4)
        ttk.Button(control_frame, text="📸 Open Instagram", command=self.manual_launch_instagram, width=16).grid(row=0, column=6, padx=4)
        ttk.Button(control_frame, text="🌐 Open Browser", command=self.manual_open_browser, width=15).grid(row=0, column=7, padx=4)
        
        # === Current Task ===
        task_frame = ttk.LabelFrame(dashboard_tab, text="📋 Current Task", padding="8")
        task_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=4)
        
        self.task_info = ttk.Label(task_frame, text="No active task", font=('Arial', 11))
        self.task_info.grid(row=0, column=0, sticky=tk.W)
        
        # === Log ===
        log_frame = ttk.LabelFrame(dashboard_tab, text="📝 Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=4)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=120, height=18, 
                                                  font=('Consolas', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log colors
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('warning', foreground='#d7ba7d')
        self.log_text.tag_config('info', foreground='#9cdcfe')
        self.log_text.tag_config('task', foreground='#ce9178')
        
        # === Status Bar ===
        self.status_var = tk.StringVar(value=f"Ready  •  Version: v{curr_ver}  •  Press Start to begin")
        status_bar = ttk.Label(dashboard_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=4)
        
        # Grid weights
        dashboard_tab.columnconfigure(0, weight=1)
        dashboard_tab.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def _on_tab_changed(self, event):
        """Called when user changes tabs in the notebook"""
        try:
            selected_tab = self.notebook.tab(self.notebook.select(), "text")
            if "Version" in selected_tab:
                self.refresh_file_integrity()
        except Exception:
            pass

    def setup_version_tab(self, parent):
        """Construct the Version & Updates inspection tab"""
        curr_ver = self.version_info.get("version", "1.4.2")
        rel_date = self.version_info.get("release_date", "2026-09-11")
        build_id = self.version_info.get("build_id", "v1.4.2-rel")
        
        # --- Top Info Card ---
        header_frame = ttk.LabelFrame(parent, text="📌 Installed Version & Build Info", padding="12")
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        row1 = ttk.Frame(header_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ver_badge = ttk.Label(row1, text=f"Installed Version: v{curr_ver}", 
                              font=('Arial', 14, 'bold'), foreground="#22863a")
        ver_badge.pack(side=tk.LEFT, padx=5)
        
        state_badge = ttk.Label(row1, text="  ✅ Up to Date with Workspace", 
                                font=('Arial', 11, 'bold'), foreground="#0366d6")
        state_badge.pack(side=tk.LEFT, padx=10)
        
        row2 = ttk.Frame(header_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text=f"📅 Release Timestamp: {rel_date}    |    🏷️ Build ID: {build_id}", 
                  font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
                  
        # Repo & Token Check
        row3 = ttk.Frame(header_frame)
        row3.pack(fill=tk.X, pady=(4, 0))
        
        token_status = "❌ Not found"
        for tname in ["token.txt", ".github_token"]:
            if os.path.exists(tname):
                try:
                    with open(tname, "r", encoding="utf-8") as tf:
                        txt = tf.read().strip()
                        if txt:
                            token_status = f"✅ Active ({tname} - {len(txt)} chars)"
                            break
                except Exception:
                    pass
                    
        repo_url = "Not configured"
        for rname in [".github_repo", "github_repo.txt"]:
            if os.path.exists(rname):
                try:
                    with open(rname, "r", encoding="utf-8") as rf:
                        rval = rf.read().strip()
                        if rval:
                            repo_url = rval
                            break
                except Exception:
                    pass
                    
        ttk.Label(row3, text=f"🔒 Private Repo Token: {token_status}    |    🌐 Repository: {repo_url}", 
                  font=('Arial', 10), foreground="#555555").pack(side=tk.LEFT, padx=5)
        
        # --- Action Buttons ---
        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Button(btn_bar, text="🔄 Run UPDATE.bat (Sync Latest)", 
                   command=self.run_update_utility, width=28).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="🔍 Refresh File Integrity", 
                   command=self.refresh_file_integrity, width=22).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_bar, text="📂 Open Bot Folder", 
                   command=self.open_bot_directory, width=18).pack(side=tk.LEFT, padx=4)
        
        # --- File Verification Table (Treeview) ---
        table_frame = ttk.LabelFrame(parent, text="📂 Local Files & Update Verification (Check modification times)", padding="8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        columns = ("file", "status", "size", "mtime", "desc")
        self.file_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        self.file_tree.heading("file", text="File Name")
        self.file_tree.heading("status", text="Status")
        self.file_tree.heading("size", text="File Size")
        self.file_tree.heading("mtime", text="Last Modified (Date & Time)")
        self.file_tree.heading("desc", text="Role & Purpose")
        
        self.file_tree.column("file", width=180, anchor=tk.W)
        self.file_tree.column("status", width=110, anchor=tk.CENTER)
        self.file_tree.column("size", width=100, anchor=tk.E)
        self.file_tree.column("mtime", width=180, anchor=tk.CENTER)
        self.file_tree.column("desc", width=280, anchor=tk.W)
        
        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Changelog / What's New Frame ---
        notes_frame = ttk.LabelFrame(parent, text=f"✨ What's New in Version {curr_ver}", padding="8")
        notes_frame.pack(fill=tk.X)
        
        features = self.version_info.get("features", [])
        for feat in features:
            f_row = ttk.Frame(notes_frame)
            f_row.pack(fill=tk.X, pady=1)
            ttk.Label(f_row, text="• ", font=('Arial', 10, 'bold'), foreground="#22863a").pack(side=tk.LEFT)
            ttk.Label(f_row, text=feat, font=('Arial', 10)).pack(side=tk.LEFT, fill=tk.X)
            
        self.refresh_file_integrity()

    def refresh_file_integrity(self):
        """Scans local workspace files to display exact sizes and modification timestamps"""
        if not hasattr(self, 'file_tree'):
            return
            
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
            
        files_to_check = [
            ("main.py", "Core Controller & GUI"),
            ("ldplayer_automation.py", "LDPlayer ADB Automation Engine"),
            ("easyearn_client.py", "EasyEarn API & Stealth Browser"),
            ("version.json", "Version & Release Manifest"),
            ("updater.py", "GitHub & ZIP Updater Engine"),
            ("UPDATE.bat", "Windows 1-Click Update Script"),
            ("run.bat", "Bot Launcher Script"),
            ("config.json", "Saved Configuration (LDPlayer Path)"),
            ("token.txt", "Private GitHub Access Token"),
        ]
        
        for filename, desc in files_to_check:
            if os.path.exists(filename):
                status = "✅ Present"
                try:
                    bytes_size = os.path.getsize(filename)
                    if bytes_size >= 1024:
                        size_str = f"{bytes_size / 1024:.1f} KB"
                    else:
                        size_str = f"{bytes_size} B"
                except Exception:
                    size_str = "Unknown"
                    
                try:
                    mtime = os.path.getmtime(filename)
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    mtime_str = "Unknown"
            else:
                if filename in ("token.txt", "config.json"):
                    status = "ℹ️ Optional"
                else:
                    status = "⚠️ Missing"
                size_str = "-"
                mtime_str = "-"
                
            self.file_tree.insert("", tk.END, values=(filename, status, size_str, mtime_str, desc))

    def run_update_utility(self):
        """Launch the update utility in an external CMD window"""
        try:
            import subprocess
            if os.path.exists("UPDATE.bat"):
                subprocess.Popen(["cmd.exe", "/c", "start", "UPDATE.bat"])
                self.log("🚀 Launched UPDATE.bat in a new command window.", 'info')
            elif os.path.exists("updater.py"):
                subprocess.Popen(["cmd.exe", "/c", "start", "python", "updater.py"])
                self.log("🚀 Launched updater.py in a new command window.", 'info')
            else:
                messagebox.showerror("Error", "Neither UPDATE.bat nor updater.py was found.")
        except Exception as e:
            messagebox.showerror("Launch Error", f"Could not launch updater: {e}")

    def open_bot_directory(self):
        """Open the local folder containing the bot files"""
        try:
            cur_dir = os.getcwd()
            if sys.platform == 'win32':
                os.startfile(cur_dir)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', cur_dir])
        except Exception as e:
            messagebox.showinfo("Bot Folder", f"Bot directory:\n{os.getcwd()}")
    
    # ============================================
    # UI Methods
    # ============================================
    
    def log(self, message, level='info'):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] ", 'info')
        self.log_text.insert(tk.END, f"{message}\n", level)
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_stats(self, key, value):
        """Update a statistic"""
        if key in self.stats_labels:
            self.stats_labels[key].config(text=str(value))
    
    def _bind_auto_save(self, var):
        """Automatically save config whenever a Tk variable changes"""
        def _on_change(*args):
            if hasattr(self, '_config_loaded') and self._config_loaded:
                self.save_config(show_alert=False)
        if hasattr(var, "trace_add"):
            var.trace_add("write", _on_change)
        elif hasattr(var, "trace"):
            var.trace("w", _on_change)

    def detect_ldplayer_path(self) -> str:
        """Auto-detect common LDPlayer 9 / 4 installation paths on Windows"""
        candidates = [
            r"C:\LDPlayer\LDPlayer9\dnplayer.exe",
            r"D:\LDPlayer\LDPlayer9\dnplayer.exe",
            r"E:\LDPlayer\LDPlayer9\dnplayer.exe",
            r"C:\leidian\LDPlayer9\dnplayer.exe",
            r"D:\leidian\LDPlayer9\dnplayer.exe",
            r"E:\leidian\LDPlayer9\dnplayer.exe",
            r"C:\leidian\LDPlayer4.0\dnplayer.exe",
            r"D:\leidian\LDPlayer4.0\dnplayer.exe",
            r"C:\LDPlayer\LDPlayer.exe",
            r"D:\LDPlayer\LDPlayer.exe",
            r"C:\Program Files\LDPlayer\LDPlayer.exe",
            r"C:\Program Files (x86)\LDPlayer\LDPlayer.exe",
        ]
        for p in candidates:
            if os.path.exists(p):
                return p
        return r"C:\LDPlayer\LDPlayer9\dnplayer.exe"

    def browse_ldplayer(self):
        """Browse for LDPlayer executable and instantly persist choice"""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select LDPlayer or dnplayer executable",
            filetypes=[
                ("LDPlayer Executable", "*.exe"),
                ("All Files", "*.*")
            ]
        )
        if path:
            normalized = os.path.normpath(path)
            self.ldplayer_path.set(normalized)
            self.ldplayer.ldplayer_path = normalized
            self.save_config(show_alert=False)
            self.log(f"💾 LDPlayer path saved: {normalized}", 'success')
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def load_config(self):
        """Load configuration from config.json or detect default LDPlayer installation"""
        loaded = False
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    saved_path = config.get('ldplayer_path')
                    if saved_path:
                        self.ldplayer_path.set(os.path.normpath(saved_path))
                    self.instance_name.set(config.get('instance_name', 'LDPlayer'))
                    self.instance_index.set(config.get('instance_index', '0'))
                    self.auto_mode.set(config.get('auto_mode', True))
                    self.headless_mode.set(config.get('headless_mode', False))
                    loaded = True
                self.log(f"Configuration loaded (LDPlayer: {self.ldplayer_path.get()})", 'info')
        except Exception as e:
            self.log(f"Config load error: {e}", 'error')

        if not loaded:
            detected = self.detect_ldplayer_path()
            if detected:
                self.ldplayer_path.set(detected)
            # Save the initial configuration so config.json is created right away
            self.save_config(show_alert=False)
            
        # Update ldplayer instance with loaded path
        self.ldplayer.ldplayer_path = self.ldplayer_path.get()
    
    def save_config(self, show_alert: bool = True):
        """Save configuration to config.json"""
        try:
            config = {
                'ldplayer_path': self.ldplayer_path.get(),
                'instance_name': self.instance_name.get(),
                'instance_index': self.instance_index.get(),
                'auto_mode': self.auto_mode.get(),
                'headless_mode': self.headless_mode.get()
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            if show_alert:
                self.log("Configuration saved", 'success')
                messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            if show_alert:
                self.log(f"Save error: {e}", 'error')
    
    def test_connection(self):
        """Test connections to EasyEarn and LDPlayer"""
        self.log("🔍 Testing connections...", 'info')
        
        # Test EasyEarn
        try:
            import requests
            response = requests.get("https://easyearn.cash", timeout=5)
            if response.status_code == 200:
                self.log("✅ EasyEarn: Connected", 'success')
            else:
                self.log(f"⚠️ EasyEarn: Status {response.status_code}", 'warning')
        except Exception as e:
            self.log(f"❌ EasyEarn: {e}", 'error')
        
        # Test LDPlayer
        if os.path.exists(self.ldplayer_path.get()):
            self.log(f"✅ LDPlayer: Found at {self.ldplayer_path.get()}", 'success')
        else:
            self.log(f"❌ LDPlayer: Not found at {self.ldplayer_path.get()}", 'error')
        
        # Test ADB
        try:
            import subprocess
            # Look in LDPlayer folder first
            adb_test_cmd = ['adb', 'version']
            if os.path.exists(self.ldplayer_path.get()):
                ld_dir = os.path.dirname(self.ldplayer_path.get())
                ld_adb = os.path.join(ld_dir, 'adb.exe')
                if os.path.exists(ld_adb):
                    adb_test_cmd = [ld_adb, 'version']
                    
            result = subprocess.run(adb_test_cmd, capture_output=True, text=True)
            if 'Android Debug Bridge' in result.stdout:
                self.log("✅ ADB: Available", 'success')
                # Check connected devices
                adb_cmd = adb_test_cmd[0]
                dev_res = subprocess.run(f'"{adb_cmd}" devices', shell=True, capture_output=True, text=True)
                dev_lines = [l for l in dev_res.stdout.strip().splitlines()[1:] if l.strip()]
                if dev_lines:
                    self.log(f"📱 Connected ADB Devices: {', '.join(dev_lines)}", 'info')
                    # Check if Instagram is installed on the emulator
                    inst_check = subprocess.run(f'"{adb_cmd}" shell pm list packages com.instagram', shell=True, capture_output=True, text=True)
                    if "com.instagram" in inst_check.stdout:
                        self.log("✅ Instagram App: Detected inside LDPlayer!", 'success')
                    else:
                        self.log("⚠️ Instagram App: NOT detected in LDPlayer. Please install Instagram inside LDPlayer!", 'warning')
                else:
                    self.log("ℹ️ No active ADB devices currently connected (start LDPlayer to connect)", 'warning')
            else:
                self.log("❌ ADB: Not available", 'error')
        except:
            self.log("❌ ADB: Not in PATH (and not found in LDPlayer folder)", 'error')

    def manual_launch_ldplayer(self):
        """Manually trigger LDPlayer launch from UI"""
        self.ldplayer.ldplayer_path = self.ldplayer_path.get()
        self.ldplayer.instance_index = self.instance_index.get()
        self.log(f"🚀 Launching LDPlayer from: {self.ldplayer.ldplayer_path}...", 'info')
        success = self.ldplayer.launch_ldplayer()
        if success:
            self.log("✅ LDPlayer launch command sent successfully!", 'success')
        else:
            self.log(f"❌ Failed to launch LDPlayer. Please verify file path: {self.ldplayer.ldplayer_path}", 'error')

    def manual_launch_instagram(self):
        """Manually trigger Instagram launch in LDPlayer to test opening it"""
        self.ldplayer.ldplayer_path = self.ldplayer_path.get()
        self.ldplayer.instance_index = self.instance_index.get()
        self.log("📸 Attempting to launch Instagram in LDPlayer...", 'info')
        if not self.ldplayer.ensure_device_connected():
            self.log("❌ Cannot launch Instagram: LDPlayer is not connected to ADB yet!", 'error')
            return
        
        opened = self.ldplayer.launch_instagram()
        if opened:
            self.log("✅ Instagram launch commands sent to LDPlayer!", 'success')
        else:
            self.log("❌ Could not open Instagram. Check LDPlayer screen.", 'error')
            
    def manual_open_browser(self):
        """Manually trigger browser launch to test EasyEarn connection or login"""
        self.log("🌐 Attempting to launch browser for EasyEarn...", 'info')
        def _launch():
            try:
                self.easyearn.start_browser()
                self.easyearn.driver.get(f"{self.easyearn.base_url}/dashboard")
                self.log("✅ Browser launched and navigated to EasyEarn dashboard!", 'success')
            except Exception as e:
                self.log(f"❌ Failed to launch browser: {e}", 'error')
        threading.Thread(target=_launch, daemon=True).start()
    
    # ============================================
    # Core Automation
    # ============================================
    
    def start_automation(self):
        """Start the automation process"""
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running...")
        
        # Start in background thread
        thread = threading.Thread(target=self.run_automation_loop)
        thread.daemon = True
        thread.start()
        
        self.log("🚀 Automation started!", 'success')
    
    def run_automation_loop(self):
        """Main automation loop"""
        try:
            # Apply user's headless preference to the browser
            self.easyearn.headless = self.headless_mode.get()
            
            # Configure LDPlayer instance settings immediately
            self.ldplayer.ldplayer_path = self.ldplayer_path.get()
            self.ldplayer.instance_name = self.instance_name.get()
            self.ldplayer.instance_index = self.instance_index.get()
            
            # Launch LDPlayer in background right away if it's not already running
            self.log("🤖 Ensuring LDPlayer emulator is started...", 'info')
            threading.Thread(target=self.ldplayer.ensure_device_connected, daemon=True).start()
            
            while self.is_running:
                # Step 1: Wait for login
                self.log("🌐 Opening browser. Please log in manually if prompted...", 'info')
                if not self.easyearn.wait_for_login():
                    self.log("❌ Failed to detect login state.", 'error')
                    break
                
                # Step 2: Get task - fetch and verify ALL info from EasyEarn first
                self.log("📋 Fetching all task details from EasyEarn first...", 'info')
                task = self.easyearn.get_task()
                if not task or not task.get('login'):
                    self.log("⚠️ No active tasks available, waiting...", 'warning')
                    time.sleep(20)
                    continue
                
                self.current_task = task
                pwd_raw = str(task.get('password', '')).strip()
                if not pwd_raw or len(pwd_raw) < 6:
                    import random, string
                    seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    pwd_raw = f"Insta_{seed}9"
                    task['password'] = pwd_raw

                pwd_masked = (pwd_raw[:2] + "****" + pwd_raw[-1:]) if len(pwd_raw) > 3 else "***"
                
                self.task_info.config(text=f"Task: {task.get('login', '')} | Email: {task.get('email', '')}")
                self.log(f"📦 Successfully collected all task info from EasyEarn FIRST:", 'success')
                self.log(f"   👤 Username : {task.get('login', '')}", 'info')
                self.log(f"   🔒 Password : {pwd_masked} ({len(pwd_raw)} chars - direct keystroke engine)", 'info')
                self.log(f"   ✉️ Email    : {task.get('email', '')}", 'info')
                self.log(f"   📝 Full Name: {task.get('first_name', task.get('login', ''))}", 'info')
                
                # Step 3: Ensure LDPlayer is ready before proceeding
                self.log("📱 Connecting to LDPlayer emulator...", 'info')
                if not self.ldplayer.ensure_device_connected():
                    self.log(f"❌ Could not connect to LDPlayer at {self.ldplayer.ldplayer_path}. Please make sure LDPlayer is open!", 'error')
                    time.sleep(10)
                    continue
                self.log("✅ LDPlayer connected and ready!", 'success')

                # Step 4: Feed pre-collected EasyEarn data to Instagram
                self.log("🚀 Feeding verified EasyEarn credentials into Instagram registration...", 'task')
                
                account_data = {
                    'email': task.get('email', ''),
                    'username': task.get('login', ''),
                    'password': task.get('password', ''),
                    'full_name': task.get('first_name', task.get('login', ''))
                }
                
                # Step 4: Launch registration workflow on LDPlayer
                # OTP code will be fetched in real-time when Instagram reaches the verification screen
                result = self.ldplayer.create_instagram_account(
                    account_data=account_data,
                    otp_fetcher=self.easyearn.get_email_code,
                    twofa_enabled=True,
                    easyearn_client=self.easyearn,
                    log_cb=self.log
                )
                
                if result['success']:
                    self.accounts_created += 1
                    self.update_stats('accounts_created', self.accounts_created)
                    self.log(f"✅ Account created: {result['username']}", 'success')
                    
                    # Generate and submit final report on EasyEarn
                    self.log("📤 Submitting final completion report to EasyEarn...", 'info')
                    if self.easyearn.submit_report():
                        self.log("✅ Task completed successfully!", 'success')
                        self.update_stats('earnings', f"${self.accounts_created * 0.025:.3f}")
                    else:
                        self.log("⚠️ Report submission failed", 'warning')
                else:
                    self.failed_accounts += 1
                    self.update_stats('failed_accounts', self.failed_accounts)
                    self.log(f"❌ Account creation failed: {result.get('error', 'Unknown error')}", 'error')
                
                # Clean up and wait
                self.log("🔄 Cycle complete, waiting for next task...", 'info')
                time.sleep(5)
                
        except Exception as e:
            import traceback
            full_error = traceback.format_exc()
            self.log(f"❌ Automation CRITICAL ERROR:\n{full_error}", 'error')
        finally:
            self.stop_automation()
    
    def stop_automation(self):
        """Stop the automation loop"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")
        self.log("⏹️ Automation stopped.", 'warning')
    
    def on_closing(self):
        """Cleanly handle application window exit and guarantee config is saved"""
        self.is_running = False
        try:
            self.save_config(show_alert=False)
        except Exception:
            pass
        try:
            self.easyearn.close()
        except Exception:
            pass
        self.root.destroy()
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

# ============================================
# Entry Point
# ============================================

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    
    app = InstagramAutomationController()
    app.run()
