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
        
        # Initialize clients
        self.easyearn = EasyEarnClient(log_callback=self.log)
        self.ldplayer = LDPlayerAutomation()
        
        # UI Variables
        self.ldplayer_path = tk.StringVar(value="C:\\LDPlayer\\LDPlayer.exe")
        self.instance_name = tk.StringVar(value="LDPlayer")
        self.instance_index = tk.StringVar(value="0")
        self.auto_mode = tk.BooleanVar(value=True)
        self.headless_mode = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """Build the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # === Title ===
        title = ttk.Label(main_frame, text="🤖 Instagram Automation Suite", 
                         font=('Arial', 18, 'bold'))
        title.grid(row=0, column=0, columnspan=5, pady=10)
        
        # === Stats Bar ===
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Statistics", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
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
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Settings", padding="10")
        settings_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
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
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=5, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Start Automation", 
                                    command=self.start_automation, width=18)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", 
                                   command=self.stop_automation, width=15, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(control_frame, text="🧹 Clear Log", command=self.clear_log, width=15).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="💾 Save Config", command=self.save_config, width=15).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="📊 Test Connection", command=self.test_connection, width=15).grid(row=0, column=4, padx=5)
        ttk.Button(control_frame, text="🚀 Launch LDPlayer", command=self.manual_launch_ldplayer, width=16).grid(row=0, column=5, padx=5)
        ttk.Button(control_frame, text="📸 Open Instagram", command=self.manual_launch_instagram, width=16).grid(row=0, column=6, padx=5)
        ttk.Button(control_frame, text="🌐 Open Browser", command=self.manual_open_browser, width=16).grid(row=0, column=7, padx=5)
        
        # === Current Task ===
        task_frame = ttk.LabelFrame(main_frame, text="📋 Current Task", padding="10")
        task_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
        self.task_info = ttk.Label(task_frame, text="No active task", font=('Arial', 11))
        self.task_info.grid(row=0, column=0, sticky=tk.W)
        
        # === Log ===
        log_frame = ttk.LabelFrame(main_frame, text="📝 Log", padding="5")
        log_frame.grid(row=5, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=120, height=20, 
                                                  font=('Consolas', 9), bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.grid(row=0, column=0, padx=5, pady=5)
        
        # Log colors
        self.log_text.tag_config('success', foreground='#4ec9b0')
        self.log_text.tag_config('error', foreground='#f48771')
        self.log_text.tag_config('warning', foreground='#d7ba7d')
        self.log_text.tag_config('info', foreground='#9cdcfe')
        self.log_text.tag_config('task', foreground='#ce9178')
        
        # === Status Bar ===
        self.status_var = tk.StringVar(value="Ready - Press Start to begin")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=5)
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
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
    
    def browse_ldplayer(self):
        """Browse for LDPlayer executable"""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select LDPlayer.exe",
            filetypes=[("Executable", "*.exe")]
        )
        if path:
            self.ldplayer_path.set(path)
            self.log(f"LDPlayer path set", 'info')
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def load_config(self):
        """Load configuration"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    self.ldplayer_path.set(config.get('ldplayer_path', 'C:\\LDPlayer\\LDPlayer.exe'))
                    self.instance_name.set(config.get('instance_name', 'LDPlayer'))
                    self.instance_index.set(config.get('instance_index', '0'))
                    self.auto_mode.set(config.get('auto_mode', True))
                    self.headless_mode.set(config.get('headless_mode', False))
                self.log("Configuration loaded", 'info')
        except Exception as e:
            self.log(f"Config load error: {e}", 'error')
    
    def save_config(self):
        """Save configuration"""
        try:
            config = {
                'ldplayer_path': self.ldplayer_path.get(),
                'instance_name': self.instance_name.get(),
                'instance_index': self.instance_index.get(),
                'auto_mode': self.auto_mode.get(),
                'headless_mode': self.headless_mode.get()
            }
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            self.log("Configuration saved", 'success')
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
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
                
                # Step 2: Get task
                self.log("📋 Checking for tasks...", 'info')
                task = self.easyearn.get_task()
                if not task:
                    self.log("⚠️ No tasks available, waiting...", 'warning')
                    time.sleep(30)
                    continue
                
                self.current_task = task
                self.task_info.config(text=f"Task: {task.get('login', '')} | Email: {task.get('email', '')}")
                self.log(f"📋 Task found: {task.get('login')} (Email: {task.get('email', '')})", 'task')
                
                # Step 3: Ensure LDPlayer is ready before proceeding
                self.log("📱 Connecting to LDPlayer emulator...", 'info')
                if not self.ldplayer.ensure_device_connected():
                    self.log(f"❌ Could not connect to LDPlayer at {self.ldplayer.ldplayer_path}. Please make sure LDPlayer is open!", 'error')
                    time.sleep(10)
                    continue
                self.log("✅ LDPlayer connected and ready!", 'success')

                # Step 4: Create Instagram account
                self.log("📱 Creating Instagram account on LDPlayer...", 'task')
                
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
        """Cleanly handle application window exit"""
        self.is_running = False
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
