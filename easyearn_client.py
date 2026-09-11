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
    
    def __init__(self, base_url: str = "https://easyearn.cash", headless: bool = False):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.logged_in = False
        self.task_id = None
        self.task_data = None
        
    def start_browser(self):
        """Launches the stable Chrome browser with detach enabled"""
        if getattr(self, 'driver', None) is not None:
            return
            
        try:
            options = webdriver.ChromeOptions()
            
            # CRITICAL: This physically prevents Chrome from closing when Python processes shift
            options.add_experimental_option("detach", True)
            
            # Use a dedicated profile folder so it remembers your login and you can paste cookies
            user_data_dir = os.path.join(os.getcwd(), "BotBrowserProfile")
            options.add_argument(f"--user-data-dir={user_data_dir}")
            
            # Stealth flags
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            if self.headless:
                options.add_argument('--headless=new')
            options.add_argument('--start-maximized')
            
            print("Launching Stable Browser...")
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Extra stealth script injection
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            
            print("Successfully launched browser!")
            
        except Exception as e:
            print(f"CRITICAL ERROR Launching Browser: {str(e)}")
            self.driver = None
            raise
                
    def wait_for_login(self) -> bool:
        """Wait for the user to pass Cloudflare and be logged in"""
        # If we already validated login and the driver is alive, don't restart or navigate away
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
            print(f"Failed to start browser: {str(e)}")
            return False
            
        try:
            print("Loading EasyEarn...")
            # Check current URL before navigating
            try:
                current_url = self.driver.current_url.lower()
                if 'dashboard' not in current_url and 'tasks' not in current_url:
                    self.driver.get(f"{self.base_url}/dashboard")
            except:
                self.driver.get(f"{self.base_url}/dashboard")
            time.sleep(3)
            
            # Wait for the user to pass Cloudflare and login if needed
            print("Waiting for you... (Please click the Cloudflare checkbox and log in if you haven't)")
            print("You have 10 minutes to log in before the bot times out.")
            
            for _ in range(120): # Wait up to 10 minutes (120 * 5s = 600s)
                if not self.driver:
                    print("Browser was unexpectedly closed.")
                    return False
                    
                try:
                    current_url = self.driver.current_url.lower()
                    # If we made it to the dashboard or tasks, we passed Cloudflare and Login!
                    if 'dashboard' in current_url or 'tasks' in current_url:
                        self.logged_in = True
                        print("Login detected! Taking over...")
                        return True
                except Exception as e:
                    # Ignore errors if the browser is mid-navigation
                    print(f"Waiting for page load... (Code: {str(e)[:30]})")
                    pass
                time.sleep(5)
                
            print("Timeout. You didn't log in or pass Cloudflare within 10 minutes.")
            return False
        except Exception as e:
            print(f"Selenium login error: {e}")
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
        """Read data from the task page"""
        data = {}
        time.sleep(3) # Wait for task page to fully render
        
        try:
            import re
            current_url = self.driver.current_url
            match = re.search(r'/task/([0-9a-fA-F-]+)', current_url)
            if match:
                self.task_id = match.group(1)

            field_keys = ['login', 'password', 'first_name', 'email']
            for key in field_keys:
                selectors = [
                    f"#field-{key}",
                    f"#{key}",
                    f"input[name='{key}']",
                    f"[data-field='{key}']",
                    f".field-{key}"
                ]
                for sel in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if elements:
                            val = elements[0].text.strip() or elements[0].get_attribute('value') or elements[0].get_attribute('data-value') or ''
                            if val:
                                data[key] = val
                                break
                    except:
                        pass

            # Fallback: check all inputs with values
            if len(data) < 2:
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    for inp in inputs:
                        name = (inp.get_attribute("name") or inp.get_attribute("id") or "").lower()
                        val = inp.get_attribute("value")
                        if val:
                            for key in field_keys:
                                if key in name and key not in data:
                                    data[key] = val.strip()
                except:
                    pass

            print(f"Extracted task data: {data}")
            self.task_data = data
            return data
        except Exception as e:
            print(f"Extract error: {e}")
            return {}
            
    def get_email_code(self) -> Optional[str]:
        """Poll the page/API for the email verification code"""
        if not self.task_id: 
            return None
            
        try:
            # We use JS fetch in the browser context so it shares the authenticated cookies perfectly
            script = f"""
            var callback = arguments[arguments.length - 1];
            fetch('/task/{self.task_id}/get-code', {{method: 'POST'}})
                .then(r => r.json())
                .then(data => callback(data))
                .catch(err => callback(null));
            """
            
            for _ in range(47):
                try:
                    # execute_async_script allows us to wait for the fetch promise
                    res = self.driver.execute_async_script(script)
                    if res and res.get('success') and res.get('code'):
                        return res.get('code')
                except:
                    pass
                time.sleep(3)
            return None
        except Exception as e:
            print(f"Email code error: {e}")
            return None
            
    def submit_2fa_key(self, twofa_key: str) -> bool:
        """Submit the 2FA key visually or via fetch"""
        try:
            # Try to visually fill it first
            inputs = self.driver.find_elements(By.NAME, "tfa_secret")
            if inputs:
                inputs[0].clear()
                inputs[0].send_keys(twofa_key)
                time.sleep(1)
                submit = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Save')]")
                submit.click()
                time.sleep(2)
                return True
            
            # Fallback to in-browser JS API call if fields are hidden
            script = f"""
            var callback = arguments[arguments.length - 1];
            fetch('/task/{self.task_id}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: 'tfa_secret={twofa_key}'
            }}).then(r => callback(r.status)).catch(e => callback(0));
            """
            status = self.driver.execute_async_script(script)
            return status == 200
        except Exception as e:
            print(f"Submit 2fa error: {e}")
            return False
            
    def submit_report(self) -> bool:
        """Submit the final report to complete the task"""
        try:
            report_data = {
                'login': self.task_data.get('login', ''),
                'password': self.task_data.get('password', ''),
                'email': self.task_data.get('email', ''),
                'first_name': self.task_data.get('first_name', ''),
                'code': self.task_data.get('code', ''),
                '2fa': self.task_data.get('2fa_secret', '')
            }
            
            # Use JS to submit report safely with current browser cookies
            script = f"""
            var callback = arguments[arguments.length - 1];
            fetch('/task/{self.task_id}', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
                body: 'report_data=' + encodeURIComponent(JSON.stringify({json.dumps(report_data)}))
            }}).then(r => callback(r.status)).catch(e => callback(0));
            """
            status = self.driver.execute_async_script(script)
            return status == 200
        except Exception as e:
            print(f"Submit report error: {e}")
            return False

    def close(self):
        """Close the browser completely"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
