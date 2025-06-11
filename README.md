# Facebook OSINT Tool (Browser Automation Based)

This Python tool is designed for OSINT tasks on Facebook, operating by automating a web browser session rather than using Facebook's official APIs. This approach allows for potentially richer data gathering and bypasses API limitations but is subject to breaking if Facebook changes its website structure.

**Disclaimer: Experimental Selectors & Maintenance**

The HTML selectors used in this tool to find and extract data are based on observed Facebook structures at the time of development. Facebook frequently updates its website, which **will likely break these selectors**.

Users of this tool should be prepared to:
1.  Inspect Facebook's HTML using browser developer tools.
2.  Update the XPath or CSS selectors in `scraper_core.py` to match the current website structure.
This is an inherent challenge with web scraping tools that do not use official APIs.

**Features (Current Version)**

*   Connects to an active Chrome browser session via remote debugging (preferred) or launches a new session using a local Chrome profile (to maintain login).
*   Scrapes public Facebook profiles for:
    *   Profile Name
    *   Posts (content, timestamp, URL)
*   Performs keyword searches on Facebook for public posts, extracting:
    *   Post content
    *   Author name and profile URL
    *   Timestamp and post URL
*   Extracts details from individual post pages:
    *   Basic reaction summary (e.g., "John Doe and 15 others")
    *   Comments (author, content, timestamp)

**Ethical Considerations & Terms of Service**

Automated data collection can be against Facebook's Terms of Service. Users should be aware of the legal and ethical implications of using this tool and use it responsibly.

**Setup and Installation**

1.  **Python:** Ensure you have Python 3.8+ installed.
2.  **Google Chrome:** This tool is designed for Google Chrome.
3.  **Dependencies:** Install the necessary Python libraries:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `selenium` and `webdriver-manager`. `webdriver-manager` will automatically download the correct ChromeDriver version.

**Running the Tool**

The script `facebook_scraper.py` is the main entry point.

**Connection Methods (Choose One):**

*   **Method 1: Chrome Remote Debugging (Preferred)**
    1.  Close all instances of Google Chrome.
    2.  Launch Chrome from the command line with the remote debugging flag.
        *   **Windows:**
            ```bash
            "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
            ```
            (Adjust path to your Chrome installation if necessary)
        *   **macOS:**
            ```bash
            /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
            ```
        *   **Linux:**
            ```bash
            google-chrome --remote-debugging-port=9222
            ```
            (Or `chromium-browser`)
    3.  Run the script. It will attempt to connect to this Chrome instance.

*   **Method 2: Selenium with Chrome Profile (Fallback)**
    1.  If you don't use remote debugging, or if it fails, the script can launch a new Chrome instance using your existing Chrome profile (this helps with being logged into Facebook).
    2.  You'll need to provide the path to your Chrome **User Data directory**.
        *   **Windows:** `C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data`
        *   **macOS:** `/Users/YOUR_USERNAME/Library/Application Support/Google/Chrome`
        *   **Linux:** `/home/YOUR_USERNAME/.config/google-chrome`
        (Replace `YOUR_USERNAME` accordingly)
    3.  Pass this path using the `--profile-path` argument.

**Command-Line Usage:**

```bash
python facebook_scraper.py [ACTION] [OPTIONS]
```

**Actions (Choose ONE):**

*   `--profile-url "PROFILE_URL"`: Scrapes a specific public Facebook profile.
    *   Example: `python facebook_scraper.py --profile-url "https://www.facebook.com/zuck"`
*   `--search "KEYWORDS"`: Performs a keyword search for public posts.
    *   Example: `python facebook_scraper.py --search "artificial intelligence ethics"`
*   `--post-url "POST_URL"`: Scrapes details (reactions, comments) from a single post URL.
    *   Example: `python facebook_scraper.py --post-url "https://www.facebook.com/zuck/posts/1011..."`

**Options:**

*   `--remote-port PORT`: (Optional) Specify the port for Chrome remote debugging if not using the default 9222.
*   `--profile-path "PATH"`: (Optional) Path to your Chrome User Data directory. Used if remote debugging is not available or fails.

**Example Full Commands:**

*   **Scrape profile via remote debugging:**
    ```bash
    python facebook_scraper.py --profile-url "https://www.facebook.com/somepublicuser"
    ```
*   **Scrape profile using a specific Chrome profile path:**
    ```bash
    python facebook_scraper.py --profile-url "https://www.facebook.com/somepublicuser" --profile-path "/home/user/.config/google-chrome"
    ```
*   **Search for posts:**
    ```bash
    python facebook_scraper.py --search "OSINT tools"
    ```

**Future Development (Based on User Feedback):**

The following features have been requested and will be considered for future development:
*   CAPTCHA handling mechanism
*   Sentiment analysis and risk scoring for posts
*   Link analysis between posts
*   Language translation
*   Report generation

**Troubleshooting Selectors:**

If the scraper fails to extract data, it's almost certainly due to changes in Facebook's HTML structure.
1.  Open the target Facebook page in your Chrome browser.
2.  Right-click on the element you expect to be scraped (e.g., a post's text, an author's name) and select "Inspect" or "Inspect Element".
3.  This will open Developer Tools. Find the HTML for the element.
4.  Identify stable attributes (like `id`, `role`, `aria-label`, `data-testid`) or structural relationships.
5.  Update the corresponding XPath or CSS selectors in the functions within `scraper_core.py` (`get_public_profile_data`, `search_facebook`, `get_post_details`).
    *   Look for lists of selectors (e.g., `post_container_selectors`, `content_selectors`) and try modifying or adding to them.
