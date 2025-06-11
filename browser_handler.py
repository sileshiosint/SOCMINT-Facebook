# browser_handler.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import os

def connect_to_remote_chrome(port=9222):
    """
    Attempts to connect to a remotely debugging Chrome instance.
    Assumes Chrome was started with --remote-debugging-port=<port>
    """
    print(f"Attempting to connect to Chrome remote debugging on port {port}...")
    try:
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
        driver = webdriver.Chrome(options=options)
        print("Successfully connected to remote Chrome instance.")
        # Perform a simple action to confirm connection
        _ = driver.current_url
        return driver
    except Exception as e:
        print(f"Failed to connect to remote Chrome on port {port}: {e}")
        print("Make sure Chrome is running with --remote-debugging-port=<port> enabled.")
        return None

def launch_selenium_with_profile(profile_path=None):
    """
    Launches a new Chrome instance with Selenium, using a specified user profile.
    If profile_path is None, it uses the default profile behavior.
    """
    print("Attempting to launch new Chrome instance with Selenium...")
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox") # Necessary for some environments
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems
    # options.add_argument("--headless") # Optional: run headless
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars") # Disable "Chrome is being controlled by automated test software"
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) # To remove the automation bar
    options.add_experimental_option('useAutomationExtension', False)

    if profile_path:
        abs_profile_path = os.path.abspath(profile_path)
        if not os.path.exists(abs_profile_path):
            print(f"Error: Chrome profile path does not exist: {abs_profile_path}")
            return None
        print(f"Using Chrome user data directory: {abs_profile_path}")
        # Selenium expects the parent directory of the 'Default' or 'Profile X' directory
        # For example, if your profile is at /path/to/chrome/User Data/Default
        # You should provide /path/to/chrome/User Data
        # However, some setups might be different. We'll assume profile_path is the User Data Directory for now.
        options.add_argument(f"user-data-dir={abs_profile_path}")
        # If you know the specific profile directory name (e.g., "Profile 1", "Default")
        # you can add it like this: options.add_argument("profile-directory=Default")
        # For simplicity, we'll let Chrome pick the default profile within the user-data-dir
        # or the last used one. User might need to specify more if they have multiple profiles
        # in that user-data-dir and want a non-default one.
    else:
        print("No profile path specified, using default Selenium browser session.")

    try:
        # Use webdriver_manager to automatically download and manage ChromeDriver
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("Successfully launched new Chrome instance with Selenium.")
        return driver
    except Exception as e:
        print(f"Failed to launch Chrome with Selenium: {e}")
        return None

def get_browser_driver(remote_port=9222, chrome_profile_path=None):
    """
    Main function to get a browser driver.
    First, tries to connect to a remote debugging instance.
    If fails, falls back to launching a new Selenium instance with a profile.
    """
    driver = connect_to_remote_chrome(port=remote_port)
    if driver:
        return driver

    print("Remote debugging connection failed or not available. Falling back to launching new instance.")
    driver = launch_selenium_with_profile(profile_path=chrome_profile_path)
    return driver

if __name__ == '__main__':
    # Example Usage (for testing this module directly)
    # Test 1: Try connecting to remote debugging (start Chrome with --remote-debugging-port=9222 first)
    # driver = get_browser_driver(remote_port=9222)

    # Test 2: Try launching with a specific profile path
    # Replace with your actual Chrome user data directory path
    # e.g., on Windows: C:\Users\YourUser\AppData\Local\Google\Chrome\User Data
    # e.g., on Linux: /home/youruser/.config/google-chrome
    # e.g., on macOS: /Users/youruser/Library/Application Support/Google/Chrome

    # IMPORTANT: For this test to work, you'd need to replace 'YOUR_CHROME_PROFILE_PATH'
    # with an actual path on the system where this script runs.
    # Since this runs in a sandboxed environment, direct testing with a real profile path here is not feasible.
    # The code is structured to be used by the main facebook_scraper.py script.

    # profile_path_example = "YOUR_CHROME_PROFILE_PATH"
    # driver = get_browser_driver(chrome_profile_path=profile_path_example)

    # if driver:
    #     print("Successfully obtained driver. Navigating to Google as a test.")
    #     driver.get("https://www.google.com")
    #     print(f"Page title: {driver.title}")
    #     # driver.quit() # Keep alive for remote, quit for new instance.
    #                    # The main script will handle quitting.
    # else:
    #     print("Failed to obtain driver.")
    pass
