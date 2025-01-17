
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import threading
import time
import os
import logging
import json
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
import queue

@dataclass
class TestConfig:
    """Configuration class to hold all test settings.
    
    Attributes:
        base_url (str): Base URL of the application being tested
        email (str): Login email
        password (str): Login password
        num_sessions (int): Number of concurrent test sessions
        response_timeout (int): Maximum time to wait for responses (seconds)
        file_path (str): Path to file for upload testing (optional)
        headless (bool): Whether to run browsers in headless mode
    """
    base_url: str
    email: str
    password: str
    num_sessions: int
    response_timeout: int = 30
    file_path: str = None
    headless: bool = True

# Initialize logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('load_test.log'),
        logging.StreamHandler()
    ]
)

class ChatLoadTester:
    """Main class for running chat load tests.
    
    This class manages multiple browser sessions to simulate concurrent users
    interacting with a chat interface.
    """
    
    def __init__(self, config: TestConfig):
        """Initialize the load tester with configuration.
        
        Args:
            config (TestConfig): Configuration object containing test settings
        """
        self.config = config
        self.results_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Create responses directory if it doesn't exist
        os.makedirs('responses', exist_ok=True)
        
        # Load test prompts from JSON file
        with open('test_prompts.json', 'r', encoding='utf-8') as f:
            self.test_prompts = json.load(f)['prompts']

    def setup_driver(self) -> webdriver.Chrome:
        """Configure and initialize a Chrome WebDriver instance.
        
        Returns:
            webdriver.Chrome: Configured Chrome WebDriver instance
            
        Example:
            driver = self.setup_driver()
            driver.get("https://example.com")
        """
        chrome_options = Options()
        if self.config.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})

        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

    def login(self, driver: webdriver.Chrome) -> bool:
        """Perform login on the website.
        
        Args:
            driver (webdriver.Chrome): WebDriver instance
            
        Returns:
            bool: True if login successful, False otherwise
            
        Example:
            if not self.login(driver):
                logging.error("Login failed")
                return
        """
        try:
            driver.get(f"{self.config.base_url}/login")
            
            # Wait for and fill email field
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
            )
            email_input.send_keys(self.config.email)
            
            # Fill password field
            password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            password_input.send_keys(self.config.password)
            
            # Click login button
            login_button = driver.find_element(By.CLASS_NAME, "login-btn")
            login_button.click()
            
            
            # Wait for successful login indicator with a 5-second loop for up to 60 seconds
            for _ in range(12):
                try:
                    if driver.current_url.endswith("/playground") and driver.execute_script("return document.readyState") == "complete": ##driver.find_element(By.CLASS_NAME, "chat-container")
                        return True
                except Exception:
                    time.sleep(5)
            
            return False
        
            
            
        except Exception as e:
            logging.error(f"Login failed: {str(e)}")
            return False

    def check_for_errors(self, driver: webdriver.Chrome) -> List[str]:
        """Check for various types of errors in the browser session.
        
        Args:
            driver (webdriver.Chrome): WebDriver instance
            
        Returns:
            List[str]: List of error messages found
            
        Example:
            errors = self.check_for_errors(driver)
            if errors:
                logging.error("Errors found: %s", errors)
        """
        errors = []
        try:
            # Check browser console for errors
            for log in driver.get_log('browser'):
                if log['level'] in ['SEVERE', 'ERROR']:
                    errors.append(f"Browser Error: {log['message']}")
            
            # Check for visible error messages in UI
            error_elements = driver.find_elements(By.CLASS_NAME, "error-message")
            for error in error_elements:
                if error.is_displayed():
                    errors.append(f"UI Error: {error.text}")
            
            # Check for failed network requests
            performance_logs = driver.execute_script("""
                return window.performance
                    .getEntries()
                    .filter(entry => entry.entryType === 'resource' && !entry.responseStatus);
            """)
            for failed_request in performance_logs:
                errors.append(f"Network Error: Failed to load {failed_request['name']}")
                
        except Exception as e:
            errors.append(f"Error checking for errors: {str(e)}")
            
        return errors

    def send_prompt_and_wait(self, driver: webdriver.Chrome, prompt: str) -> Dict:
        """Send a prompt to the chat interface and wait for response.
        
        Args:
            driver (webdriver.Chrome): WebDriver instance
            prompt (str): The prompt to send
            
        Returns:
            Dict: Result dictionary containing prompt, response, errors, and timing
            
        Example:
            result = self.send_prompt_and_wait(driver, "What is the main theme?")
            if result['errors']:
                logging.error("Errors occurred: %s", result['errors'])
            else:
                logging.info("Response received in %.2f seconds", result['response_time'])
        """
        result = {
            'prompt': prompt,
            'response': None,
            'errors': [],
            'response_time': None
        }
        
        start_time = time.time()
        try:
            # Wait for and locate input box
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "question-input"))
            )
            
            # Check for errors before sending
            result['errors'].extend(self.check_for_errors(driver))
            
            # Send the prompt
            input_box.clear()
            input_box.send_keys(prompt)
            
            send_button = driver.find_element(By.CLASS_NAME, "submit-btn")
            send_button.click()
            
            # Function to check if response has been received
            def response_received(driver):
                textareas = driver.find_elements(By.CLASS_NAME, "question-input")
                return len(textareas) > 1 and textareas[1].get_attribute("value") != ""
            
            # Wait for response
            WebDriverWait(driver, self.config.response_timeout).until(response_received)
            
            # Get the response
            response = driver.find_elements(By.CLASS_NAME, "question-input")[1].get_attribute("value")
            result['response'] = response
            result['response_time'] = time.time() - start_time
            
            # Final error check
            result['errors'].extend(self.check_for_errors(driver))
            
        except Exception as e:
            result['errors'].append(f"Error sending prompt: {str(e)}")
            result['errors'].extend(self.check_for_errors(driver))
            
        return result

    def upload_file(self, driver: webdriver.Chrome) -> bool:
        """Upload a file if configured.
        
        Args:
            driver (webdriver.Chrome): WebDriver instance
            
        Returns:
            bool: True if upload successful or no file configured, False otherwise
            
        Example:
            if not self.upload_file(driver):
                logging.error("File upload failed")
                return
        """
        if not self.config.file_path:
            return True
            
        try:
            # Wait for and locate file input  למחוק
            file_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Send file path to input
            file_input.send_keys(os.path.abspath(self.config.file_path))
            
            # Wait for upload success
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "upload-success"))
            )
            return True
            
        except Exception as e:
            logging.error(f"File upload failed: {str(e)}")
            return False

    def run_chat_session(self, session_id: int):
        """Run a single chat session in a separate thread.
        
        Args:
            session_id (int): Unique identifier for this session
            
        Example:
            thread = threading.Thread(target=self.run_chat_session, args=(1,))
            thread.start()
        """
        thread_name = f"Session-{session_id}"
        threading.current_thread().name = thread_name
        
        driver = None
        try:
            driver = self.setup_driver()
            
            if not self.login(driver):
                raise Exception("Login failed")
                
            if not self.upload_file(driver):
                raise Exception("File upload failed")
            
            # Get prompt for this session
            prompt = self.test_prompts[session_id % len(self.test_prompts)]
            result = self.send_prompt_and_wait(driver, prompt)
            
            # Save results
            self.results_queue.put({
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                **result
            })
            
        except Exception as e:
            logging.error(f"Session {session_id} failed: {str(e)}")
            if driver:
                self.results_queue.put({
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat(),
                    'errors': [str(e)],
                    'prompt': None,
                    'response': None,
                    'response_time': None
                })
        finally:
            if driver:
                driver.quit()

    def save_results(self):
        """Save all test results to a JSON file.
        
        Example:
            tester.run_load_test()
            tester.save_results()
        """
        results = []
        while not self.results_queue.empty():
            results.append(self.results_queue.get())
            
        filename = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"Results saved to {filename}")

    def run_load_test(self):
        """Run the complete load test with multiple sessions.
        
        Example:
            tester = ChatLoadTester(config)
            tester.run_load_test()
        """
        threads = []
        
        # Start test sessions
        for i in range(self.config.num_sessions):
            thread = threading.Thread(target=self.run_chat_session, args=(i+1,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            time.sleep(1)  # Stagger thread starts
            
        # Wait for all sessions to complete
        for thread in threads:
            thread.join()
            
        self.save_results()

def main():
    """Main entry point for the load test script.
    
    Example usage:
        # Command line:
        $ python chat_load_test.py
        
        # Or in Python:
        if __name__ == "__main__":
            main()
    """
    # Load configuration from file
    with open('config.json', 'r') as f:
        config_data = json.load(f)
    
    config = TestConfig(**config_data)
    
    tester = ChatLoadTester(config)
    
    try:
        tester.run_load_test()
    except KeyboardInterrupt:
        logging.info("Load test interrupted by user")
    finally:
        tester.save_results()

if __name__ == "__main__":
    main()