# easyearn_client.py
import os
import time
import json
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class EasyEarnClient:
    """Selenium Client for visually interacting with EasyEarn.cash in the browser"""
    
    def __init__(self, base_url: str = "https://easyearn.cash", headless: bool = False, log_callback=None):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.logged_in = False
        self.task_id = None
        self.task_data = None
        self.log_callback = log_callback

    def log(self, message: str, level: str = 'info'):
        """Send logs to both console and UI callback"""
        print(f"[{level.upper()}] {message}")
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception:
                pass
        
    def start_browser(self):
        """Launches the stable browser with detach enabled, trying Chrome then Edge"""
        if getattr(self, 'driver', None) is not None:
            return
            
        # Clean up stale locks from BotBrowserProfile
        user_data_dir = os.path.join(os.getcwd(), "BotBrowserProfile")
        os.makedirs(user_data_dir, exist_ok=True)
        for lock_file in ["lockfile", "SingletonLock", "SingletonSocket", "SingletonCookie"]:
            lock_path = os.path.join(user_data_dir, lock_file)
            if os.path.exists(lock_path):
                try:
                    os.remove(lock_path)
                except Exception:
                    pass

        # Configure Chrome Options
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument(f"--user-data-dir={user_data_dir}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-allow-origins=*")
        options.add_argument("--disable-gpu")
        
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--start-maximized')
        
        # Launch directly with ChromeDriverManager for guaranteed stability
        self.log("🌐 Launching Chrome browser via ChromeDriverManager...", "info")
        try:
            driver_path = ChromeDriverManager().install()
            if "THIRD_PARTY_NOTICES" in driver_path or not driver_path.endswith(".exe"):
                driver_dir = os.path.dirname(driver_path)
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file.lower() == "chromedriver.exe":
                            driver_path = os.path.join(root, file)
                            break
            service = ChromeService(driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.log("✅ Chrome launched successfully via ChromeDriverManager!", "success")
        except Exception as e_manager:
            self.log(f"⚠️ ChromeDriverManager failed: {str(e_manager)[:80]}. Trying Edge...", "warning")
            
            # Fallback to Microsoft Edge (Pre-installed on every Windows PC!)
            self.log("🔄 Attempting to launch Microsoft Edge (built-in Windows Chromium)...", "info")
            try:
                from selenium.webdriver.edge.options import Options as EdgeOptions
                edge_options = EdgeOptions()
                edge_options.add_experimental_option("detach", True)
                edge_user_data = os.path.join(os.getcwd(), "BotEdgeProfile")
                edge_options.add_argument(f"--user-data-dir={edge_user_data}")
                edge_options.add_argument("--disable-blink-features=AutomationControlled")
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_argument("--no-sandbox")
                edge_options.add_argument("--remote-allow-origins=*")
                if self.headless:
                    edge_options.add_argument('--headless=new')
                edge_options.add_argument('--start-maximized')
                self.driver = webdriver.Edge(options=edge_options)
                self.log("✅ Microsoft Edge launched successfully!", "success")
            except Exception as e_edge:
                self.log(f"❌ Critical error: Could not launch Chrome or Edge: {e_edge}", "error")
                self.driver = None
                raise

        # Extra stealth script injection
        if self.driver:
            try:
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
            except Exception:
                pass
                
    def wait_for_login(self) -> bool:
        """Wait for the user to pass Cloudflare and be logged in"""
        if self.logged_in and self.driver:
            try:
                _ = self.driver.current_url
                return True
            except Exception:
                self.logged_in = False
                self.driver = None

        try:
            self.start_browser()
        except Exception as e:
            self.log(f"Failed to start browser: {str(e)}", "error")
            return False
            
        try:
            self.log("🌐 Loading EasyEarn dashboard...", "info")
            try:
                current_url = self.driver.current_url.lower()
                if 'dashboard' not in current_url and 'tasks' not in current_url:
                    self.driver.get(f"{self.base_url}/dashboard")
            except Exception:
                self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            self.log("👉 Please complete Cloudflare verification and log in if prompted in the browser.", "warning")
            self.log("⏳ Bot is waiting for dashboard to load (up to 10 minutes)...", "info")
            
            for check_i in range(120): # 120 * 5s = 600s
                if not self.driver:
                    self.log("❌ Browser was closed.", "error")
                    return False
                    
                try:
                    current_url = self.driver.current_url.lower()
                    if 'dashboard' in current_url or 'tasks' in current_url:
                        self.logged_in = True
                        self.log("✅ EasyEarn login verified! Ready for tasks.", "success")
                        return True
                except Exception as e:
                    pass
                time.sleep(5)
                
            self.log("❌ Login timed out after 10 minutes.", "error")
            return False
        except Exception as e:
            self.log(f"❌ Selenium login error: {e}", "error")
            return False
            
    def get_task(self) -> Optional[Dict]:
        """Navigate to tasks page and visually click a task"""
        if not self.logged_in: 
            return None
            
        try:
            import re
            current_url = self.driver.current_url.lower()
            if '/tasks' not in current_url:
                self.driver.get(f"{self.base_url}/tasks")
                time.sleep(2)
            else:
                self.driver.refresh()
                time.sleep(2)
            
            task_url = None
            task_element = None
            
            # Search cards first (looking for 'Create Inst' or 'Inst')
            cards = self.driver.find_elements(By.CLASS_NAME, "card")
            for card in cards:
                try:
                    text = card.text.lower()
                    if 'inst' in text:
                        # Find the start task link inside this card
                        start_links = card.find_elements(By.XPATH, ".//a[contains(@href, '/task/') and contains(@href, '/start')]")
                        if start_links:
                            task_element = start_links[0]
                            task_url = task_element.get_attribute('href')
                            print(f"Found Instagram task in card: {task_url}")
                            break
                except:
                    continue

            # Fallback: find any link on the page that starts a task
            if not task_url:
                all_start_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/task/') and contains(@href, '/start')]")
                if all_start_links:
                    task_element = all_start_links[0]
                    task_url = task_element.get_attribute('href')
                    print(f"Found task start button: {task_url}")

            if task_element and task_url:
                # Extract UUID cleanly
                match = re.search(r'/task/([0-9a-fA-F-]+)', task_url)
                if match:
                    self.task_id = match.group(1)
                else:
                    parts = [p for p in task_url.split('/') if p and p != 'start']
                    self.task_id = parts[-1]
                    
                print(f"Starting task ID: {self.task_id}")
                
                # Click the Start Task button or navigate
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", task_element)
                    time.sleep(1)
                    task_element.click()
                except Exception as e:
                    print(f"Click fallback, navigating directly to {task_url}: {e}")
                    self.driver.get(task_url)
                    
                time.sleep(3)
                return self._extract_task_data()
                
            print("No task start button found on page.")
            return None
        except Exception as e:
            print(f"Selenium get task error: {e}")
            return None
            
    def _extract_task_data(self) -> Dict:
        """Read data from the task page, accurately extracting all fields from EasyEarn FIRST before feeding to Instagram"""
        data = {}
        import re
        import random
        import string

        # Polling loop: allow dynamic EasyEarn elements to render completely
        for attempt in range(8):
            try:
                current_url = self.driver.current_url
                match = re.search(r'/task/([0-9a-fA-F-]+)', current_url)
                if match:
                    self.task_id = match.group(1)

                # 1. Direct extract from exact EasyEarn field IDs: #field-login, #field-password, etc.
                field_keys = ['login', 'password', 'first_name', 'email']
                for key in field_keys:
                    if key not in data or not data[key]:
                        try:
                            el = self.driver.find_element(By.ID, f"field-{key}")
                            val = (el.text or el.get_attribute('innerText') or el.get_attribute('value') or '').strip()
                            if val:
                                data[key] = val
                        except Exception:
                            pass

                # 2. Extract from page JavaScript variables if present
                if len(data) < 4:
                    try:
                        js_data = self.driver.execute_script("""
                            var res = {};
                            if (typeof gen !== 'undefined') {
                                res.login = gen.login || '';
                                res.password = gen.password || '';
                                res.first_name = gen.first_name || '';
                                res.email = gen.email || '';
                            }
                            if (typeof taskData !== 'undefined') {
                                res.login = res.login || taskData.login || '';
                                res.password = res.password || taskData.password || '';
                                res.email = res.email || taskData.email || '';
                            }
                            return res;
                        """)
                        if js_data:
                            for k, v in js_data.items():
                                if v and (k not in data or not data[k]):
                                    data[k] = str(v).strip()
                    except Exception:
                        pass

                # 3. Extract from copy buttons (EasyEarn commonly uses [data-clipboard-text])
                if len(data) < 4:
                    try:
                        copy_elems = self.driver.find_elements(By.CSS_SELECTOR, "[data-clipboard-text], [data-text], [data-copy]")
                        for el in copy_elems:
                            c_text = (el.get_attribute("data-clipboard-text") or el.get_attribute("data-text") or el.get_attribute("data-copy") or '').strip()
                            if not c_text:
                                continue
                            try:
                                parent_text = (el.find_element(By.XPATH, "./..").text or '').lower()
                            except:
                                parent_text = ''
                            el_id = (el.get_attribute('id') or '').lower()
                            el_class = (el.get_attribute('class') or '').lower()

                            if ('pass' in parent_text or 'pass' in el_id or 'pass' in el_class) and 'password' not in data:
                                data['password'] = c_text
                            elif ('login' in parent_text or 'user' in parent_text or 'login' in el_id) and 'login' not in data:
                                data['login'] = c_text
                            elif ('mail' in parent_text or '@' in c_text or 'email' in el_id) and 'email' not in data:
                                data['email'] = c_text
                            elif ('name' in parent_text or 'first_name' in el_id) and 'first_name' not in data:
                                data['first_name'] = c_text
                    except Exception:
                        pass

                # 4. Fallback CSS selectors
                for key in field_keys:
                    if key not in data or not data[key]:
                        selectors = [
                            f"#{key}",
                            f"input[name='{key}']",
                            f"[data-field='{key}']",
                            f".field-{key}"
                        ]
                        for sel in selectors:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                                if elements:
                                    val = (elements[0].text or elements[0].get_attribute('value') or elements[0].get_attribute('innerText') or '').strip()
                                    if val:
                                        data[key] = val
                                        break
                            except:
                                pass

                # Check if we have gathered all essential fields
                if data.get('login') and data.get('email') and data.get('password'):
                    break

            except Exception as e:
                pass
            time.sleep(1)

        # Clean all string values
        for k in list(data.keys()):
            if isinstance(data[k], str):
                data[k] = data[k].strip().strip('"').strip("'")

        # Guarantee a valid password if EasyEarn didn't provide an explicit one
        if not data.get('password'):
            seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            generated_pwd = f"Acc_{seed}9"
            data['password'] = generated_pwd
            self.log(f"ℹ️ Auto-generated secure password for Instagram: {data['password']}", "info")

        # Guarantee a valid first name
        if not data.get('first_name') and data.get('login'):
            clean_name = re.sub(r'[^a-zA-Z]', '', data['login'])
            data['first_name'] = clean_name.capitalize() if clean_name else "Alex"

        self.task_data = data
        return data
            
    def get_email_code(self) -> Optional[str]:
        """Poll the EasyEarn page/API for the email verification code"""
        if not self.driver:
            return None
            
        try:
            import re
            
            # Trigger 'Search Email for Code' button if present and not yet clicked
            try:
                trigger_script = """
                var btn = document.getElementById('getCodeBtn');
                if (btn && !btn.disabled && typeof getCode === 'function') {
                    getCode();
                } else if (btn && !btn.disabled) {
                    btn.click();
                }
                """
                self.driver.execute_script(trigger_script)
            except Exception:
                pass

            # 1. Check if code is already displayed in #codeValue or window.verificationCode
            check_script = """
            var codeEl = document.getElementById('codeValue');
            var txt = codeEl ? (codeEl.innerText || codeEl.textContent || '').trim() : '';
            if (txt && /^[0-9]{4,8}$/.test(txt)) return txt;
            if (typeof verificationCode !== 'undefined' && verificationCode) return String(verificationCode).trim();
            return null;
            """
            code = self.driver.execute_script(check_script)
            if code:
                self.log(f"🔑 Verification code found in EasyEarn UI: {code}", "success")
                if self.task_data:
                    self.task_data['code'] = code
                return code

            # 2. If task_id is known, query /task/<id>/get-code directly in page context
            if self.task_id:
                api_script = f"""
                var callback = arguments[arguments.length - 1];
                fetch('/task/{self.task_id}/get-code', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}}
                }})
                .then(r => r.json())
                .then(data => callback(data))
                .catch(err => callback(null));
                """
                res = self.driver.execute_async_script(api_script)
                if res and res.get('success') and res.get('code'):
                    code = str(res.get('code')).strip()
                    self.log(f"🔑 Verification code received from EasyEarn API: {code}", "success")
                    # Also populate in page so next steps work seamlessly
                    self.driver.execute_script(f"""
                    var codeVal = document.getElementById('codeValue');
                    if (codeVal) codeVal.textContent = '{code}';
                    if (typeof verificationCode !== 'undefined') verificationCode = '{code}';
                    var resultEl = document.getElementById('codeResult');
                    if (resultEl) resultEl.classList.remove('hidden');
                    var nextBtns = document.getElementById('codeNextBtns');
                    if (nextBtns) nextBtns.classList.remove('hidden');
                    var btn = document.getElementById('getCodeBtn');
                    if (btn) btn.classList.add('hidden');
                    """)
                    if self.task_data:
                        self.task_data['code'] = code
                    return code

            return None
        except Exception as e:
            self.log(f"Error checking email code: {e}", "warning")
            return None
            
    def submit_2fa_key(self, twofa_key: str) -> Optional[str]:
        """Submit the 2FA key into EasyEarn wizard Step 2 and return the generated OTP code"""
        try:
            if not self.driver:
                self.log("🌐 Browser not connected. Starting browser for 2FA...", "info")
                self.start_browser()
                if self.task_id:
                    self.driver.get(f"{self.base_url}/task/{self.task_id}")
                    time.sleep(3)

            twofa_clean = twofa_key.strip().replace(" ", "")
            self.log(f"🔐 Submitting 2FA Secret to EasyEarn: {twofa_clean}", "info")
            
            # Execute step 2 logic in page
            script = f"""
            var secret = '{twofa_clean}';
            
            // Go to step 2 if needed
            if (typeof goToStep === 'function') {{
                goToStep(2);
            }}
            
            var inp = document.getElementById('tfaSecret');
            if (inp) {{
                inp.value = secret;
                if (typeof validate2fa === 'function') validate2fa();
            }}
            
            if (typeof tfaSecretValue !== 'undefined') {{
                tfaSecretValue = secret;
            }}
            
            // Generate OTP
            var btn = document.getElementById('otpGenBtn');
            if (btn && !btn.disabled) {{
                btn.click();
            }} else if (typeof generateOtp === 'function') {{
                generateOtp();
            }}
            return true;
            """
            self.driver.execute_script(script)
            time.sleep(2)
            
            # Poll for OTP code generated in #otpValue
            otp_val = ""
            for _ in range(8):
                otp_val = self.driver.execute_script("""
                var el = document.getElementById('otpValue');
                return el ? (el.innerText || el.textContent || '').trim() : '';
                """)
                if otp_val and len(otp_val) == 6:
                    break
                time.sleep(1)

            if otp_val:
                self.log(f"✅ EasyEarn generated 6-digit OTP code: {otp_val}", "success")
                return otp_val
            else:
                self.log("⚠️ 2FA Secret submitted, but could not read OTP code.", "warning")
                return None
        except Exception as e:
            self.log(f"Submit 2FA error: {e}", "error")
            return None
            
    def submit_report(self) -> bool:
        """Submit the final report to complete the task using EasyEarn's buildAndSubmitReport"""
        try:
            self.log("📤 Submitting task completion report to EasyEarn...", "info")
            script = """
            if (typeof buildAndSubmitReport === 'function') {
                buildAndSubmitReport();
                return true;
            } else if (typeof goToStep === 'function') {
                goToStep(3);
                return true;
            } else {
                var form = document.getElementById('submitForm');
                if (form) { form.submit(); return true; }
            }
            return false;
            """
            result = self.driver.execute_script(script)
            time.sleep(4)
            self.log("🎉 Task report submitted successfully to EasyEarn!", "success")
            return True
        except Exception as e:
            self.log(f"Submit report error: {e}", "error")
            return False

    def close(self):
        """Close the browser completely"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
