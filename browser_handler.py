# browser_handler.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os

def connect_to_remote_chrome(port=9222):
    print(f"Attempting to connect to Chrome remote debugging on port {port}...")
    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        # Add headless and other common options for remote connection if desired
        # options.add_argument('--headless')
        # options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(options=options)
        print("Successfully connected to remote Chrome instance.")
        _ = driver.current_url # Verify connection
        return driver
    except Exception as e:
        print(f"Failed to connect to remote Chrome on port {port}: {e}")
        return None

def launch_selenium_with_profile(profile_path=None):
    print("Attempting to launch new Chrome instance with Selenium...")
    options = Options()
    options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu") # Often needed, but can cause issues in some envs
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless") # Enable if no UI is desired
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if profile_path:
        abs_profile_path = os.path.abspath(profile_path)
        if not os.path.exists(abs_profile_path):
            print(f"Error: Chrome profile path does not exist: {abs_profile_path}")
            # Fallback to default behavior or raise error? For now, just print and continue.
        else:
            print(f"Using Chrome user data directory: {abs_profile_path}")
            options.add_argument(f"user-data-dir={abs_profile_path}")
            # You might need to specify a profile directory if multiple profiles exist
            # options.add_argument("profile-directory=Default")
    else:
        print("No profile path specified, using default Selenium browser session.")

    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("Successfully launched new Chrome instance with Selenium.")
        return driver
    except Exception as e:
        print(f"Failed to launch Chrome with Selenium: {e}")
        return None

def get_browser_driver(remote_port=9222, chrome_profile_path=None):
    driver = connect_to_remote_chrome(port=remote_port)
    if driver:
        return driver

    print(f"Remote debugging on port {remote_port} failed or not available. Falling back to launching new instance.")
    driver = launch_selenium_with_profile(profile_path=chrome_profile_path)
    return driver

if __name__ == '__main__':
    print("Testing browser_handler.py...")
    # Test Case 1: Attempt remote connection (requires Chrome running with --remote-debugging-port=9222)
    # driver1 = get_browser_driver(remote_port=9222)
    # if driver1:
    #     print("Remote connection test: Navigating to example.com")
    #     driver1.get("http://example.com")
    #     print(f"Page title: {driver1.title}")
    #     # driver1.quit() # Quit if you opened it, or leave if it was pre-existing remote

    # Test Case 2: Launch new instance (no profile)
    driver2 = get_browser_driver(remote_port=0) # Force fail remote to test launch
    if driver2:
        print("New instance test: Navigating to example.com")
        driver2.get("http://example.com")
        print(f"Page title: {driver2.title}")
        driver2.quit()
    else:
        print("Failed to get driver for new instance test.")
