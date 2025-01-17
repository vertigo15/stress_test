from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import os
from selenium.common.exceptions import TimeoutException, WebDriverException

# List of test prompts
TEST_PROMPTS = [
    "מה הניע את נועם לצאת ליער באותו בוקר?",
    "אילו תחושות תיאר נועם כאשר נכנס ליער?",
    "מה גרם לנועם לעצור בדרכו כאשר הגיע לנחל?",
    "    כיצד תיאר נועם את הסביבה ואת הקולות ביער?",
    "מהו האירוע המרכזי שהתרחש במהלך ההרפתקה של נועם?",
    "איך נועם התמודד עם האתגר של הצלת גור הארנבות?",
    "מה הייתה תגובת גור הארנבות לאחר שנועם שחרר אותו?",
    "כיצד השפיעה החוויה ביער על תחושותיו של נועם?",
    "איך ההרפתקה השפיעה על היחסים של נועם עם הוריו?",
    "מה נועם למד או הבין על הטבע ועל החיים בעקבות החוויה?"
]

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # Enable logging
    chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def get_timestamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def login(driver):
    try:
        print(f"[{get_timestamp()}] Navigating to login page")
        driver.get("https://example.com/login")
        
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
        )
        print(f"[{get_timestamp()}] Entering email")
        email_input.clear()
        email_input.send_keys("your_email@example.com")
        
        password_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
        print(f"[{get_timestamp()}] Entering password")
        password_input.clear()
        password_input.send_keys("your_password")
        
        login_button = driver.find_element(By.CLASS_NAME, "login-btn")
        print(f"[{get_timestamp()}] Clicking login button")
        login_button.click()
        
        time.sleep(3)
        print(f"[{get_timestamp()}] Login successful")
        
    except Exception as e:
        print(f"[{get_timestamp()}] Login failed: {str(e)}")

def check_for_errors(driver, thread_num):
    try:
        # Get browser console logs
        browser_logs = driver.get_log('browser')
        for log in browser_logs:
            if log['level'] in ['SEVERE', 'ERROR']:
                print(f"[{get_timestamp()}] Thread {thread_num} Browser Error: {log['message']}")
        
        # Check for visible error messages on the page
        error_elements = driver.find_elements(By.CLASS_NAME, "error-message")  # Update this selector based on your error class
        for error in error_elements:
            if error.is_displayed():
                print(f"[{get_timestamp()}] Thread {thread_num} UI Error: {error.text}")
                
        # Check for network errors in console
        performance_logs = driver.execute_script("""
            var performance = window.performance || {};
            var network = performance.getEntries() || [];
            return network.filter(entry => entry.entryType === 'resource' && !entry.responseStatus);
        """)
        for failed_request in performance_logs:
            print(f"[{get_timestamp()}] Thread {thread_num} Network Error: Failed to load {failed_request['name']}")
            
    except Exception as e:
        print(f"[{get_timestamp()}] Thread {thread_num} Error checking for errors: {str(e)}")

def send_prompt_and_wait(driver, prompt, thread_num):
    try:
        print(f"[{get_timestamp()}] Thread {thread_num}: Waiting for input box")
        input_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-input"))
        )
        
        # Check for errors before sending prompt
        check_for_errors(driver, thread_num)
        
        print(f"[{get_timestamp()}] Thread {thread_num}: Typing prompt")
        input_box.clear()
        input_box.send_keys(prompt)
        
        print(f"[{get_timestamp()}] Thread {thread_num}: Clicking send button")
        send_button = driver.find_element(By.CLASS_NAME, "submit-btn")
        send_button.click()
        
        def response_received(driver):
            # Check for errors while waiting for response
            check_for_errors(driver, thread_num)
            textareas = driver.find_elements(By.CLASS_NAME, "question-input")
            return len(textareas) > 1 and textareas[1].get_attribute("value") != ""
        
        print(f"[{get_timestamp()}] Thread {thread_num}: Waiting for response")
        try:
            WebDriverWait(driver, 30).until(response_received)
        except TimeoutException:
            print(f"[{get_timestamp()}] Thread {thread_num} ERROR: Response timeout")
            check_for_errors(driver, thread_num)
            raise
        
        response = driver.find_elements(By.CLASS_NAME, "question-input")[1].get_attribute("value")
        
        timestamp = get_timestamp()
        print(f"\n[{timestamp}] Thread {thread_num} Conversation:")
        print(f"Prompt: {prompt}")
        print(f"Response: {response}\n")
        
        # Final error check after response
        check_for_errors(driver, thread_num)
        
        with open(f"responses/response_{thread_num}.txt", "w", encoding="utf-8") as f:
            f.write(f"Time: {timestamp}\nPrompt: {prompt}\nResponse: {response}\n")
            
    except Exception as e:
        print(f"[{get_timestamp()}] Thread {thread_num} ERROR: {str(e)}")
        check_for_errors(driver, thread_num)

def upload_file(driver):
    try:
        pdf_path = "/path/to/your/file.pdf"
        
        print(f"[{get_timestamp()}] Waiting for file input element")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'][accept='.doc, .docx, .pdf']"))
        )
        
        print(f"[{get_timestamp()}] Attempting to upload file: {pdf_path}")
        file_input.send_keys(pdf_path)
        
        time.sleep(5)
        print(f"[{get_timestamp()}] File upload completed")
        
        return True
        
    except Exception as e:
        print(f"[{get_timestamp()}] File upload failed: {str(e)}")
        return False

def run_chat_session(thread_num):
    try:
        print(f"[{get_timestamp()}] Starting chat session {thread_num}")
        driver = setup_driver()
        
        login(driver)
        upload_file(driver)
        
        prompt = TEST_PROMPTS[thread_num % len(TEST_PROMPTS)]
        print(f"[{get_timestamp()}] Session {thread_num}: Sending prompt: {prompt}")
        send_prompt_and_wait(driver, prompt, thread_num)
        
        print(f"[{get_timestamp()}] Chat session {thread_num} completed")
        
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"[{get_timestamp()}] Error in thread {thread_num}: {str(e)}")

def main():
    print(f"[{get_timestamp()}] Starting load test")
    
    if not os.path.exists('responses'):
        os.makedirs('responses')
        print(f"[{get_timestamp()}] Created responses directory")
    
    num_sessions = 7
    threads = []
    
    for i in range(num_sessions):
        thread = threading.Thread(target=run_chat_session, args=(i+1,))
        thread.daemon = False
        threads.append(thread)
        thread.start()
        print(f"[{get_timestamp()}] Started thread {i+1}")
        time.sleep(1)
    
    print(f"[{get_timestamp()}] All threads started")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[{get_timestamp()}] Press Ctrl+C again to exit")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n[{get_timestamp()}] Exiting...")

if __name__ == "__main__":
    main()