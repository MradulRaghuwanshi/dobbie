"""Open chat.openai.com in Chrome and send a query via Selenium.

Usage:
  python open_chatgpt.py "What is the capital of France?" --profile "C:/Users/you/AppData/Local/Google/Chrome/User Data"

Notes:
- If you want the script to use an already-logged-in session, pass a Chrome `--profile` (user-data-dir) path.
- If no logged-in session is available, the browser will open and you can sign in manually.
- Automation of third-party sites may be brittle and subject to the site's terms of use.
"""
import sys
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def find_input(driver, timeout=15):
    wait = WebDriverWait(driver, timeout)
    # Try common selectors used by chat.openai.com
    selectors = [
        'textarea',
        'div[contenteditable="true"]',
        'div[role="textbox"]',
    ]
    for sel in selectors:
        try:
            elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            if elem.is_displayed() and elem.is_enabled():
                return elem
        except TimeoutException:
            continue
    # fallback: try to find any visible textarea
    try:
        elems = driver.find_elements(By.TAG_NAME, 'textarea')
        for e in elems:
            if e.is_displayed() and e.is_enabled():
                return e
    except Exception:
        pass
    raise NoSuchElementException('Could not locate chat input field')


def main():
    parser = argparse.ArgumentParser(description='Open ChatGPT and send a query via Selenium')
    parser.add_argument('query', nargs='+', help='Query text to send')
    parser.add_argument('--profile', help='Chrome user data dir to reuse logged-in session')
    parser.add_argument('--headless', action='store_true', help='Run headless (may prevent login/profile reuse)')
    args = parser.parse_args()

    query = ' '.join(args.query)

    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    # Recommended: use an existing Chrome profile to keep your login session
    if args.profile:
        chrome_options.add_argument(f'--user-data-dir={args.profile}')
    if args.headless:
        chrome_options.add_argument('--headless=new')

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    try:
        driver.get('https://chat.openai.com/')

        try:
            input_elem = find_input(driver, timeout=20)
        except NoSuchElementException:
            print('Chat input not found automatically. If you are not logged in, please log in now in the opened browser window.')
            # wait for user to login and for input to appear
            try:
                input_elem = WebDriverWait(driver, 300).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
                )
            except TimeoutException:
                print('Timed out waiting for manual login. Exiting.')
                return

        # Focus and send the message
        try:
            input_elem.click()
        except Exception:
            pass
        # Some inputs are contenteditable divs; use send_keys
        input_elem.clear()
        input_elem.send_keys(query)
        input_elem.send_keys(Keys.ENTER)

        print('Query sent. Waiting a short while for a response to appear...')
        # Give the page some time to render the assistant response
        time.sleep(8)

        # Optionally, capture a screenshot for review
        ts = int(time.time())
        screenshot_path = f'chatgpt_response_{ts}.png'
        driver.save_screenshot(screenshot_path)
        print(f'Screenshot saved: {screenshot_path}')

    finally:
        print('Leaving browser open for review. Close it manually when finished.')


if __name__ == '__main__':
    main()
