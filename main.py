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
        self.root.geometry("1120x800")
        self.root.minsize(1000, 720)
        self.root.resizable(True, True)
        
        # State
        self.is_running = False
        self.current_task = None
        self.accounts_created = 0
        self.failed_accounts = 0
        
        # Load version info
        self.version_info = self.get_version_info()
        curr_ver = self.version_info.get("version", "1.5.7")
        self.root.title(f"🤖 Instagram Automation Suite - v{curr_ver}")
        
        # Initialize clients
        self.easyearn = EasyEarnClient(log_callback=self.log)
        self.ldplayer = LDPlayerAutomation()
        
        # UI Variables
        self.ldplayer_path = tk.StringVar(value="C:\\LDPlayer\\LDPlayer9\\dnplayer.exe")
        self.instance_name = tk.StringVar(value="LDPlayer")
        self.instance_index = tk.StringVar(value="0")
        self.default_password = tk.StringVar(value="")
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
        self._bind_auto_save(self.default_password)
        self._bind_auto_save(self.auto_mode)
        self._bind_auto_save(self.headless_mode)
        
    def get_version_info(self) -> dict:
        """Load version and release details from version.json"""
        default_info = {
            "version": "1.5.8",
            "release_date": "2026-09-11 21:50",
            "build_id": "v1.5.8-rel",
            "features": [
                "Smart Dual-Direction Birthday Wheel Scrolling: Dynamically detects whether Year wheel requires downward or upward drag to reach adult age (1995-2002)",
                "DatePicker Auto-Activation: Automatically taps the date display box if the wheel bottom sheet is not opened yet",
                "Direct NumberPicker Input Bypass: Automatically inputs 1999 directly into native NumberPicker EditText if available",
                "Age Confirmation & Error Popup Handling: Automatically detects and confirms 'Are you X years old?' dialogs and dismisses under-13 warnings",
                "Zero Disk Footprint: Removed account collection and disk saving (no collected_accounts.txt or .csv) for total PC privacy",
                "Live Ephemeral Credential Visibility: Passwords, Login, Full Name, and Email displayed unmasked in real time only during active task",
                "Instant Combo Copy: One-click 'Copy Combo' button in active task bar for username:password:email:name clipboard access",
                "IME & Position-Verified Password Submission: Uses dual-trigger (Enter key + Next button at y=0.52) and verifies screen transition before advancing"
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
        curr_ver = self.version_info.get("version", "1.5.5")
        
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
        
        # Options & Custom Password
        ttk.Label(settings_frame, text="Password (opt):").grid(row=3, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.default_password, width=20).grid(row=3, column=1, padx=5, sticky=tk.W)
        ttk.Checkbutton(settings_frame, text="🤖 Auto Mode", variable=self.auto_mode).grid(row=3, column=2, padx=5)
        ttk.Checkbutton(settings_frame, text="🖥️ Headless", variable=self.headless_mode).grid(row=3, column=3, padx=5)
        
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
        task_frame = ttk.LabelFrame(dashboard_tab, text="📋 Current Task — Account Credentials: Login, Name, Password & Email", padding="10")
        task_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=4)
        
        for c in range(4):
            task_frame.columnconfigure(c, weight=1)
        
        # Row 0: Summary Banner & Live Step Progress
        header_row = ttk.Frame(task_frame)
        header_row.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 6))
        
        self.task_info = ttk.Label(header_row, text="No active task (Waiting for next task from EasyEarn...)", font=('Arial', 9, 'bold'), foreground='#9cdcfe')
        self.task_info.pack(side=tk.LEFT)
        
        self.task_step_badge = ttk.Label(header_row, text="[IDLE]", font=('Arial', 9, 'bold'), foreground='#d7ba7d')
        self.task_step_badge.pack(side=tk.RIGHT)

        # Row 1: The 4 Core Requested Credentials (Login, Name, Password, Email)
        # 1. Login / Username
        f_login = ttk.LabelFrame(task_frame, text="👤 Login / Username", padding="4")
        f_login.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=3, pady=2)
        f_login.columnconfigure(0, weight=1)
        self.curr_login_entry = tk.Entry(f_login, font=('Consolas', 10, 'bold'), bg='#1e293b', fg='#38bdf8', relief=tk.FLAT, bd=2)
        self.curr_login_entry.pack(fill=tk.X, expand=True)
        self.curr_login_entry.insert(0, "-")
        self.curr_login_entry.config(state='readonly')

        # 2. Full Name
        f_name = ttk.LabelFrame(task_frame, text="📝 Full Name", padding="4")
        f_name.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=3, pady=2)
        f_name.columnconfigure(0, weight=1)
        self.curr_name_entry = tk.Entry(f_name, font=('Consolas', 10, 'bold'), bg='#1e293b', fg='#4ade80', relief=tk.FLAT, bd=2)
        self.curr_name_entry.pack(fill=tk.X, expand=True)
        self.curr_name_entry.insert(0, "-")
        self.curr_name_entry.config(state='readonly')

        # 3. Password (Plain Text Unmasked)
        f_pass = ttk.LabelFrame(task_frame, text="🔒 Password (Unmasked)", padding="4")
        f_pass.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=3, pady=2)
        f_pass.columnconfigure(0, weight=1)
        self.curr_pass_entry = tk.Entry(f_pass, font=('Consolas', 10, 'bold'), bg='#1e293b', fg='#fbbf24', relief=tk.FLAT, bd=2)
        self.curr_pass_entry.pack(fill=tk.X, expand=True)
        self.curr_pass_entry.insert(0, "-")
        self.curr_pass_entry.config(state='readonly')

        # 4. Email Address
        f_email = ttk.LabelFrame(task_frame, text="✉️ Email Address", padding="4")
        f_email.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=3, pady=2)
        f_email.columnconfigure(0, weight=1)
        self.curr_email_entry = tk.Entry(f_email, font=('Consolas', 10, 'bold'), bg='#1e293b', fg='#c084fc', relief=tk.FLAT, bd=2)
        self.curr_email_entry.pack(fill=tk.X, expand=True)
        self.curr_email_entry.insert(0, "-")
        self.curr_email_entry.config(state='readonly')

        # Row 2: Secondary Account Parameters (OTP Code, Birthday, 2FA Key, Task ID)
        # 5. OTP Code
        f_code = ttk.LabelFrame(task_frame, text="🔑 OTP Code", padding="3")
        f_code.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=3, pady=3)
        self.curr_code_entry = tk.Entry(f_code, font=('Consolas', 9, 'bold'), bg='#1e293b', fg='#2dd4bf', relief=tk.FLAT, bd=1)
        self.curr_code_entry.pack(fill=tk.X, expand=True)
        self.curr_code_entry.insert(0, "-")
        self.curr_code_entry.config(state='readonly')

        # 6. Birthday
        f_bday = ttk.LabelFrame(task_frame, text="🎂 Birthday", padding="3")
        f_bday.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=3, pady=3)
        self.curr_bday_entry = tk.Entry(f_bday, font=('Consolas', 9), bg='#1e293b', fg='#f472b6', relief=tk.FLAT, bd=1)
        self.curr_bday_entry.pack(fill=tk.X, expand=True)
        self.curr_bday_entry.insert(0, "-")
        self.curr_bday_entry.config(state='readonly')

        # 7. 2FA Key
        f_twofa = ttk.LabelFrame(task_frame, text="🔐 2FA Key", padding="3")
        f_twofa.grid(row=2, column=2, sticky=(tk.W, tk.E), padx=3, pady=3)
        self.curr_twofa_entry = tk.Entry(f_twofa, font=('Consolas', 9), bg='#1e293b', fg='#60a5fa', relief=tk.FLAT, bd=1)
        self.curr_twofa_entry.pack(fill=tk.X, expand=True)
        self.curr_twofa_entry.insert(0, "-")
        self.curr_twofa_entry.config(state='readonly')

        # 8. Task ID
        f_taskid = ttk.LabelFrame(task_frame, text="🆔 Task ID", padding="3")
        f_taskid.grid(row=2, column=3, sticky=(tk.W, tk.E), padx=3, pady=3)
        self.curr_taskid_entry = tk.Entry(f_taskid, font=('Consolas', 9), bg='#1e293b', fg='#94a3b8', relief=tk.FLAT, bd=1)
        self.curr_taskid_entry.pack(fill=tk.X, expand=True)
        self.curr_taskid_entry.insert(0, "-")
        self.curr_taskid_entry.config(state='readonly')

        # Row 3: Action & Quick Copy Buttons
        r3_frame = ttk.Frame(task_frame)
        r3_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(4, 2))
        
        ttk.Button(r3_frame, text="📋 Copy All Account Info", command=self.copy_current_task_combo, width=22).pack(side=tk.LEFT, padx=(2, 4))
        ttk.Button(r3_frame, text="👤:🔒 User:Pass", command=self.copy_user_pass, width=14).pack(side=tk.LEFT, padx=3)
        ttk.Button(r3_frame, text="✉️:🔑 Email:Code", command=self.copy_email_code, width=16).pack(side=tk.LEFT, padx=3)
        ttk.Button(r3_frame, text="🔒 Pass Only", command=self.copy_pass_only, width=13).pack(side=tk.LEFT, padx=3)
        ttk.Button(r3_frame, text="🔑 Code Only", command=self.copy_code_only, width=13).pack(side=tk.LEFT, padx=3)
        
        # === Log ===
        log_frame = ttk.LabelFrame(dashboard_tab, text="📝 Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=4)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=120, height=17, 
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

    def update_current_task_ui(self, login="-", name="-", password="-", email="-", code="-", birthday="-", task_id="-", twofa="-", step=""):
        """Update current task section with all account info fields and live step progress"""
        def _update():
            # Update header summary text
            if login and login != "-":
                summary = f"👤 {login}  |  📝 {name}  |  🔒 {password}  |  ✉️ {email}"
                if code and code != "-":
                    summary += f"  |  🔑 OTP: {code}"
                self.task_info.config(text=summary, foreground='#4ec9b0')
            else:
                self.task_info.config(text="No active task (Waiting for next task from EasyEarn...)", foreground='#9cdcfe')
                
            if step and hasattr(self, 'task_step_badge'):
                self.task_step_badge.config(
                    text=f"[{step}]", 
                    foreground='#4ec9b0' if 'complete' in step.lower() or 'success' in step.lower() else '#e5c07b'
                )
                
            for entry, val in [
                (self.curr_login_entry, login),
                (self.curr_name_entry, name),
                (self.curr_pass_entry, password),
                (self.curr_email_entry, email),
                (self.curr_code_entry, code),
                (self.curr_bday_entry, birthday),
                (self.curr_twofa_entry, twofa),
                (self.curr_taskid_entry, task_id)
            ]:
                try:
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    entry.insert(0, str(val) if val else "-")
                    entry.config(state='readonly')
                except Exception:
                    pass
        try:
            self.root.after(0, _update)
        except Exception:
            pass

    def copy_current_task_combo(self):
        """Copy all current task account info to clipboard"""
        login = self.curr_login_entry.get().strip()
        name = self.curr_name_entry.get().strip()
        pwd = self.curr_pass_entry.get().strip()
        email = self.curr_email_entry.get().strip()
        code = self.curr_code_entry.get().strip()
        bday = self.curr_bday_entry.get().strip()
        twofa = self.curr_twofa_entry.get().strip()
        
        if not login or login == "-":
            messagebox.showinfo("No Active Task", "There is currently no active task credentials to copy.")
            return
            
        parts = [login, pwd, email, name]
        if code and code != "-":
            parts.append(code)
        if bday and bday != "-":
            parts.append(bday)
        if twofa and twofa != "-":
            parts.append(twofa)
            
        combo = ":".join(parts)
        self.root.clipboard_clear()
        self.root.clipboard_append(combo)
        self.log(f"📋 Copied all task account info to clipboard: {combo}", 'info')
        messagebox.showinfo(
            "Copied to Clipboard",
            f"All Account Information Copied:\n\n"
            f"Username : {login}\n"
            f"Password : {pwd}\n"
            f"Email    : {email}\n"
            f"Name     : {name}\n"
            f"OTP Code : {code}\n"
            f"Birthday : {bday}\n"
            f"2FA Key  : {twofa}\n\n"
            f"Raw Combo:\n{combo}"
        )

    def copy_user_pass(self):
        login = self.curr_login_entry.get().strip()
        pwd = self.curr_pass_entry.get().strip()
        if not login or login == "-":
            messagebox.showinfo("No Active Task", "No active task available.")
            return
        combo = f"{login}:{pwd}"
        self.root.clipboard_clear()
        self.root.clipboard_append(combo)
        self.log(f"📋 Copied User:Pass to clipboard: {combo}", 'info')

    def copy_email_code(self):
        email = self.curr_email_entry.get().strip()
        code = self.curr_code_entry.get().strip()
        if not email or email == "-":
            messagebox.showinfo("No Active Task", "No active task available.")
            return
        combo = f"{email}:{code}"
        self.root.clipboard_clear()
        self.root.clipboard_append(combo)
        self.log(f"📋 Copied Email:Code to clipboard: {combo}", 'info')

    def copy_code_only(self):
        code = self.curr_code_entry.get().strip()
        if not code or code == "-":
            messagebox.showinfo("No Code", "No OTP confirmation code has been received yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(code)
        self.log(f"📋 Copied OTP Code to clipboard: {code}", 'info')

    def copy_pass_only(self):
        pwd = self.curr_pass_entry.get().strip()
        if not pwd or pwd == "-":
            messagebox.showinfo("No Password", "No password has been set for the current task.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(pwd)
        self.log(f"📋 Copied Password to clipboard: {pwd}", 'info')

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
                    self.default_password.set(config.get('default_password', ''))
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
                'default_password': self.default_password.get(),
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
                    self.ldplayer.ldplayer_path = self.ldplayer_path.get()
                    self.ldplayer.instance_index = self.instance_index.get()
                    is_installed = self.ldplayer.is_instagram_installed()
                    if not is_installed:
                        for line in dev_lines:
                            parts = line.split()
                            if len(parts) >= 2 and parts[1] == 'device':
                                s = parts[0]
                                check = subprocess.run(f'"{adb_cmd}" -s {s} shell pm list packages', shell=True, capture_output=True, text=True)
                                if "com.instagram" in check.stdout:
                                    is_installed = True
                                    break
                    if is_installed:
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
        if hasattr(self, 'ldplayer'):
            self.ldplayer.reset_stop()
        if hasattr(self, 'easyearn'):
            self.easyearn.reset_stop()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Running...")
        
        # Start in background thread
        thread = threading.Thread(target=self.run_automation_loop)
        thread.daemon = True
        thread.start()
        
        self.log("🚀 Automation started!", 'success')

    def interruptible_sleep(self, seconds: float) -> bool:
        """Sleep in tiny 50ms chunks while checking stop flags"""
        end_time = time.time() + seconds
        while time.time() < end_time:
            if not self.is_running:
                return False
            if hasattr(self, 'ldplayer') and self.ldplayer.stop_requested:
                return False
            if hasattr(self, 'easyearn') and getattr(self.easyearn, 'stop_requested', False):
                return False
            time.sleep(min(0.05, max(0.005, end_time - time.time())))
        return self.is_running
    
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
                    self.log("❌ Failed to detect login state or stop requested.", 'error')
                    break
                
                # Step 2: Get task - fetch and verify ALL info from EasyEarn first
                self.log("📋 Fetching all task details from EasyEarn first...", 'info')
                task = self.easyearn.get_task()
                if not task or not task.get('login'):
                    self.log("⚠️ No active tasks available, waiting...", 'warning')
                    if not self.interruptible_sleep(20):
                        break
                    continue
                
                self.current_task = task
                cfg_pwd = self.default_password.get().strip() if hasattr(self, 'default_password') else ''
                pwd_raw = str(task.get('password', '')).strip()
                if cfg_pwd:
                    pwd_raw = cfg_pwd
                    task['password'] = pwd_raw
                elif not pwd_raw or len(pwd_raw) < 6:
                    import random, string
                    seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
                    pwd_raw = f"Insta_{seed}9"
                    task['password'] = pwd_raw

                login_val = str(task.get('login', '')).strip()
                name_val = str(task.get('first_name', '')).strip() or login_val
                email_val = str(task.get('email', '')).strip()
                bday_val = str(task.get('birthday', '1999-05-14')).strip()
                task_id_val = str(task.get('task_id', '') or getattr(self.easyearn, 'task_id', '') or f"Task #{self.accounts_created + 1}").strip()
                
                # Maintain full live task state dictionary
                self.current_task_state = {
                    'login': login_val,
                    'name': name_val,
                    'password': pwd_raw,
                    'email': email_val,
                    'code': '-',
                    'birthday': bday_val,
                    'task_id': task_id_val,
                    'twofa': '-',
                    'step': 'Step 1/11: Connecting'
                }
                
                # Update UI Task Frame with ALL account info
                self.update_current_task_ui(**self.current_task_state)
                
                self.log(f"📦 Active Task Credentials Ready (Unmasked):", 'success')
                self.log(f"   👤 Login / User : {login_val} (From EasyEarn)", 'info')
                self.log(f"   🔒 Password     : {pwd_raw} (From EasyEarn)", 'info')
                self.log(f"   📝 Full Name    : {name_val} (From EasyEarn)", 'info')
                self.log(f"   ✉️ Email        : {email_val} (From EasyEarn)", 'info')
                self.log(f"   🎂 Birthday     : {bday_val} (Age 21+)", 'info')
                self.log(f"   🆔 Task ID      : {task_id_val}", 'info')
                
                # Step 3: Ensure LDPlayer is ready before proceeding
                self.log("📱 Connecting to LDPlayer emulator...", 'info')
                if not self.ldplayer.ensure_device_connected():
                    self.log(f"❌ Could not connect to LDPlayer at {self.ldplayer.ldplayer_path}. Please make sure LDPlayer is open!", 'error')
                    if not self.interruptible_sleep(10):
                        break
                    continue
                self.log("✅ LDPlayer connected and ready!", 'success')

                # Step 4: Feed pre-collected EasyEarn data to Instagram
                self.log("🚀 Feeding verified EasyEarn credentials into Instagram registration...", 'task')
                
                account_data = {
                    'email': email_val,
                    'username': login_val,
                    'password': pwd_raw,
                    'full_name': name_val,
                    'birthday': bday_val
                }
                
                # Live callback updating step on GUI
                def task_log_cb(msg, level='info'):
                    self.log(msg, level)
                    msg_l = msg.lower()
                    if 'step ' in msg_l:
                        import re
                        step_match = re.search(r'\[(Step [^\]]+)\]', msg, re.IGNORECASE)
                        if step_match:
                            self.current_task_state['step'] = step_match.group(1)
                            self.update_current_task_ui(**self.current_task_state)

                # Real-time OTP wrapper to immediately display code in GUI
                def wrapped_otp_fetcher():
                    self.current_task_state['step'] = 'Step 7/11: Polling Email OTP'
                    self.update_current_task_ui(**self.current_task_state)
                    code = self.easyearn.get_email_code()
                    if code:
                        self.current_task_state['code'] = str(code)
                        self.current_task_state['step'] = f'OTP Code: {code}'
                        self.update_current_task_ui(**self.current_task_state)
                        self.log(f"🔑 Live OTP verification code captured: {code}", 'success')
                    return code

                # Step 4: Launch registration workflow on LDPlayer
                result = self.ldplayer.create_instagram_account(
                    account_data=account_data,
                    otp_fetcher=wrapped_otp_fetcher,
                    twofa_enabled=True,
                    easyearn_client=self.easyearn,
                    log_cb=task_log_cb
                )
                
                if not self.is_running or self.ldplayer.stop_requested:
                    self.log("⏹️ Automation halted during account creation cycle.", 'warning')
                    break

                if result['success']:
                    self.accounts_created += 1
                    self.update_stats('accounts_created', self.accounts_created)
                    twofa_res = result.get('twofa_key', '')
                    if twofa_res:
                        self.current_task_state['twofa'] = str(twofa_res)
                    self.current_task_state['step'] = '✅ Account Created & Submitting Report'
                    self.update_current_task_ui(**self.current_task_state)
                    self.log(f"✅ Account created: {result['username']}", 'success')
                    
                    # Generate and submit final report on EasyEarn
                    self.log("📤 Submitting final completion report to EasyEarn...", 'info')
                    if self.easyearn.submit_report(account_data=self.current_task_state):
                        self.current_task_state['step'] = '🎉 Task Completed'
                        self.update_current_task_ui(**self.current_task_state)
                        self.log("✅ Task completed successfully!", 'success')
                        self.update_stats('earnings', f"${self.accounts_created * 0.025:.3f}")
                    else:
                        self.current_task_state['step'] = '⚠️ Report Pending'
                        self.update_current_task_ui(**self.current_task_state)
                        self.log("⚠️ Report submission failed", 'warning')
                else:
                    self.failed_accounts += 1
                    self.update_stats('failed_accounts', self.failed_accounts)
                    self.current_task_state['step'] = '❌ Registration Failed'
                    self.update_current_task_ui(**self.current_task_state)
                    self.log(f"❌ Account creation failed: {result.get('error', 'Unknown error')}", 'error')
                
                # Clean up and wait
                self.log("🔄 Cycle complete, waiting for next task...", 'info')
                if not self.interruptible_sleep(5):
                    break
                
        except Exception as e:
            import traceback
            full_error = traceback.format_exc()
            self.log(f"❌ Automation CRITICAL ERROR:\n{full_error}", 'error')
        finally:
            self.stop_automation()
    
    def stop_automation(self):
        """Immediately stop the automation loop and all emulator/browser actions"""
        self.is_running = False
        if hasattr(self, 'ldplayer'):
            self.ldplayer.request_stop()
            # Force kill instagram on device in background thread to unblock immediately
            threading.Thread(target=self.ldplayer.force_stop_instagram, daemon=True).start()
        if hasattr(self, 'easyearn'):
            self.easyearn.request_stop()
            
        if hasattr(self, 'current_task_state') and isinstance(self.current_task_state, dict):
            self.current_task_state['step'] = '⏹️ Automation Stopped by User'
            self.update_current_task_ui(**self.current_task_state)

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Stopped")
        self.log("⏹️ Automation stopped immediately.", 'warning')
    
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
