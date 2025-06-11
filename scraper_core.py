# scraper_core.py
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import quote_plus
from text_utils import analyze_sentiment_vader # Import the new function

# --- CAPTCHA Detection and Handling ---
def check_for_captcha_and_pause(driver: WebDriver):
    """
    Checks for common CAPTCHA indicators and pauses for manual intervention.
    Returns True if a CAPTCHA was suspected and paused, False otherwise.
    """
    # Common CAPTCHA related keywords in title or URL
    captcha_keywords = [
        "captcha", "security check", "are you human", "verify your account",
        "recaptcha", "checkpoint", "puzzle"
    ]

    current_url = driver.current_url.lower()
    current_title = driver.title.lower()

    # Check URL and Title
    for keyword in captcha_keywords:
        if keyword in current_url or keyword in current_title:
            print(f"CAPTCHA or security check suspected based on keyword '{keyword}' in URL/Title.")
            print(f"URL: {driver.current_url}")
            print(f"Title: {driver.title}")
            input("!!! CAPTCHA/Security Check Detected !!!\nPlease solve it in the browser. After solving, press Enter here to continue...")
            return True

    # Check for common CAPTCHA iFrames (e.g., reCAPTCHA)
    # This is a basic check, more sophisticated iframe checks might be needed
    captcha_iframes_selectors = [
        "//iframe[contains(@src, 'recaptcha')]",
        "//iframe[contains(@title, 'captcha')]",
        "//iframe[contains(@name, 'cframe')]", # Common for hCaptcha
    ]
    for selector in captcha_iframes_selectors:
        iframes = driver.find_elements(By.XPATH, selector)
        if iframes:
            print(f"CAPTCHA or security check suspected based on iframe selector: {selector}")
            input("!!! CAPTCHA/Security Check (iframe) Detected !!!\nPlease solve it in the browser. After solving, press Enter here to continue...")
            return True

    # Check for common CAPTCHA input fields or images (very generic)
    # These are highly likely to need customization
    # captcha_elements_selectors = [
    #     "//input[contains(@aria-label, 'Enter the characters')]",
    #     "//img[contains(@alt, 'captcha')]",
    # ]
    # for selector in captcha_elements_selectors:
    #     elements = driver.find_elements(By.XPATH, selector)
    #     if elements:
    #         print(f"CAPTCHA or security check suspected based on element selector: {selector}")
    #         input("!!! CAPTCHA/Security Check (element) Detected !!!\nPlease solve it in the browser. After solving, press Enter here to continue...")
    #         return True

    return False


# --- Helper Functions --- (scroll_to_bottom, wait_for_element, wait_for_elements - kept as is)
def scroll_to_bottom(driver: WebDriver, max_scrolls=5, pause_time=2.5, scroll_element=None):
    print(f"Scrolling (element: {'body' if not scroll_element else 'specific element'})...")
    if scroll_element:
        script = "arguments[0].scrollTop = arguments[0].scrollHeight"
        target_element = scroll_element
    else:
        script = "window.scrollTo(0, document.body.scrollHeight);"
        target_element = driver.execute_script("return document.body")
    last_height_script = "return arguments[0].scrollHeight" if scroll_element else "return document.body.scrollHeight"
    last_height = driver.execute_script(last_height_script, target_element if scroll_element else driver.execute_script("return document.body"))
    scrolls = 0
    for _ in range(max_scrolls):
        driver.execute_script(script, target_element if scroll_element else driver.execute_script("return document.body"))
        time.sleep(pause_time)
        current_height = driver.execute_script(last_height_script, target_element if scroll_element else driver.execute_script("return document.body"))
        if current_height == last_height:
            print("Reached end of scrollable content for the target.")
            break
        last_height = current_height
        scrolls += 1
        print(f"Scroll {scrolls}/{max_scrolls}...")
    if scrolls == max_scrolls:
        print("Reached max scroll limit for the target.")

def wait_for_element(driver: WebDriver, by: By, value: str, timeout=10, parent_element=None):
    target = parent_element if parent_element else driver
    try:
        element = WebDriverWait(target, timeout).until(EC.presence_of_element_located((by, value)))
        return element
    except Exception: return None

def wait_for_elements(driver: WebDriver, by: By, value: str, timeout=10, parent_element=None):
    target = parent_element if parent_element else driver
    try:
        elements = WebDriverWait(target, timeout).until(EC.presence_of_all_elements_located((by, value)))
        return elements
    except Exception: return []


# --- Main Scraping Functions ---
# Modify existing scraping functions to call check_for_captcha_and_pause

def get_public_profile_data(driver: WebDriver, profile_url: str, analyze_sentiment_flag: bool = False):
    print(f"Navigating to profile: {profile_url}")
    driver.get(profile_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    if check_for_captcha_and_pause(driver): # Check after initial load
        # Optionally re-check or re-load elements if CAPTCHA was solved
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')


    profile_data = {"url": profile_url, "name": None, "posts": [], "photo_links": [], "friend_names_or_links": [], "group_names_or_links": []}
    print("Attempting to extract profile name...")
    # ... (rest of name extraction logic)
    name_selectors = [
        "//h1", "//div[@role='main']//h1",
        "//div[contains(@aria-label,'profile name')]//span[not(contains(@class,'visuallyhidden'))]",
        "//span[contains(@class,'profile-name')]", "//div[@id='cover-name-root']//h1",
        "//div[@data-testid='profile-name']//span[1]"
    ]
    name_element = None
    for selector in name_selectors:
        try:
            name_element = wait_for_element(driver, By.XPATH, selector, timeout=5)
            if name_element and name_element.text.strip():
                profile_data["name"] = name_element.text.strip()
                print(f"Profile Name Found: {profile_data['name']} (using selector: {selector})")
                break
        except: continue
    if not profile_data["name"]:
        print("Profile name could not be extracted with common selectors.")
        if check_for_captcha_and_pause(driver): # Check if name extraction failed due to CAPTCHA
             # Retry name extraction or relevant part if needed after CAPTCHA
            # For simplicity, we'll just re-try finding the name once.
            for selector in name_selectors:
                try:
                    name_element = wait_for_element(driver, By.XPATH, selector, timeout=5)
                    if name_element and name_element.text.strip():
                        profile_data["name"] = name_element.text.strip()
                        print(f"Profile Name Found after CAPTCHA: {profile_data['name']} (using selector: {selector})")
                        break
                except: continue
            if not profile_data["name"]:
                 print("Still could not extract profile name after CAPTCHA.")


    print("Checking for a 'Posts' tab/filter...")
    try:
        posts_tab_selectors = [
            "//a[normalize-space()='Posts']",
            "//div[@role='tablist']//div[@role='tab'][normalize-space()='Posts']",
            "//span[normalize-space()='Posts']/ancestor::a[@role='tab']",
            "//div[contains(@aria-label, 'Posts') and @role='tab']"
        ]
        posts_tab = None
        for selector in posts_tab_selectors:
            element = wait_for_element(driver, By.XPATH, selector, timeout=3)
            if element:
                posts_tab = element
                print(f"Found 'Posts' tab/filter with selector: {selector}. Clicking it.")
                try:
                    driver.execute_script("arguments[0].click();", posts_tab)
                    WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    time.sleep(3)
                except Exception as click_err:
                    print(f"Could not click 'Posts' tab: {click_err}")
                break
        if not posts_tab:
            print("'Posts' tab/filter not found or not clicked. Proceeding with current view.")
    except Exception as e:
        print(f"Error while trying to find or click 'Posts' tab: {e}")


    scroll_to_bottom(driver, max_scrolls=5, pause_time=3)
    if check_for_captcha_and_pause(driver): # Check after scrolling
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')


    print("Attempting to extract posts...")
    post_container_selectors = [
        "//div[@role='article']",
        "//div[contains(@class, 'userContentWrapper')]",
        "//div[starts-with(@id, 'mall_post_')]",
        "//div[contains(@data-pagelet, 'FeedUnit')]",
        "//div[contains(@class, '_5pcb')]",
        "//div[div//span[contains(text(), 'ago')] and div//a[contains(@href, '/posts/') or contains(@href, '/videos/') or contains(@href, '/photos/')]]"
    ]
    post_elements = []
    for selector in post_container_selectors:
        elements = wait_for_elements(driver, By.XPATH, selector, timeout=5)
        if elements:
            print(f"Found {len(elements)} potential post containers with selector: {selector}")
            post_elements = elements
            break

    if not post_elements:
        print("No post containers found with the tried selectors.")
        if check_for_captcha_and_pause(driver):
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            # Retry finding post_elements
            for selector in post_container_selectors: # Simplified retry
                elements = wait_for_elements(driver, By.XPATH, selector, timeout=5)
                if elements:
                    print(f"Found {len(elements)} post containers after CAPTCHA with selector: {selector}")
                    post_elements = elements
                    break
            if not post_elements:
                print("Still no post containers found after CAPTCHA.")


    for i, post_el in enumerate(post_elements):
        print(f"Processing post {i+1}/{len(post_elements)}...")
        post_data = {"content": None, "timestamp": None, "timestamp_text": None, "author": "Profile Owner (assumed)", "url": None, "sentiment": None}

        content_selectors = [
            ".//div[contains(@class, 'userContent')]/p",
            ".//div[@data-ad-preview='message']",
            ".//div[contains(@class, 'text_exposed_root')]",
            ".//div[contains(@data-testid, 'post_message') or contains(@data-ad-id, 'post_message')]",
            ".//div[@dir='auto' and string-length(normalize-space(.)) > 50 and not(.//article)]",
            ".//span[contains(@class, 'text_content')]"
        ]
        for selector in content_selectors:
            try:
                content_element = post_el.find_element(By.XPATH, selector)
                post_data["content"] = content_element.text.strip()
                if post_data["content"]:
                    if analyze_sentiment_flag:
                        post_data["sentiment"] = analyze_sentiment_vader(post_data["content"])
                    break
            except:
                continue

        timestamp_selectors = [
            ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php') or contains(@href,'/permalink/')]",
            ".//abbr/parent::a",
            ".//a[./span[contains(text(),'ago')] or ./span[contains(text(),'hr')] or ./span[contains(text(),'min')]]",
            ".//a[@data-testid='story-subtitle']//span//a"
        ]
        for selector in timestamp_selectors:
            try:
                timestamp_element = post_el.find_element(By.XPATH, selector)
                post_data["url"] = timestamp_element.get_attribute("href")
                post_data["timestamp_text"] = timestamp_element.text.strip()
                try:
                    abbr_element = timestamp_element.find_element(By.XPATH, ".//abbr[@data-utime]")
                    data_utime = abbr_element.get_attribute("data-utime")
                    post_data["timestamp"] = int(data_utime)
                except:
                    try:
                        data_utime_on_link = timestamp_element.get_attribute("data-utime")
                        if data_utime_on_link:
                             post_data["timestamp"] = int(data_utime_on_link)
                    except:
                        pass
                if post_data["url"]:
                    break
            except:
                continue

        if post_data["content"] or post_data["url"]:
            profile_data["posts"].append(post_data)


    print("TODO: Implement photo link extraction.")
    print("TODO: Implement friends list extraction (highly dependent on UI and privacy).")
    print("TODO: Implement groups list extraction.")
    print(f"Finished scraping profile data attempt for: {profile_url}")
    return profile_data


def search_facebook(driver: WebDriver, search_query: str, analyze_sentiment_flag: bool = False):
    print(f"Performing search for: '{search_query}'")
    encoded_query = quote_plus(search_query)
    search_url = f"https://www.facebook.com/search/posts/?q={encoded_query}"
    print(f"Navigating to search URL: {search_url}")
    driver.get(search_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    if check_for_captcha_and_pause(driver): # Check after initial load
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    search_results_data = {"query": search_query, "discussions": []}
    scroll_to_bottom(driver, max_scrolls=5, pause_time=3)
    if check_for_captcha_and_pause(driver): # Check after scrolling
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')


    print("Attempting to extract search results (posts/discussions)...")
    result_item_selectors = [
        "//div[@role='feed']/div//div[@role='article']",
        "//div[contains(@data-pagelet, 'SearchResults') or contains(@data-pagelet, 'SearchFeed')]//div[@role='article']",
        "//div[contains(@class,'search-result-item-class')]",
        "//div[contains(@aria-label, 'Search result') or contains(@aria-label, 'Search Result')]",
        "//div[h3//a[contains(@href, '/groups/') or contains(@href, '/profile.php') or contains(@href, '/pages/')]]"
    ]
    search_post_elements = []
    for selector in result_item_selectors:
        elements = wait_for_elements(driver, By.XPATH, selector, timeout=7)
        if elements:
            print(f"Found {len(elements)} potential search result items with selector: {selector}")
            search_post_elements = elements
            break

    if not search_post_elements:
        print("No search result items found with the tried selectors.")
        if check_for_captcha_and_pause(driver):
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            # Retry finding search_post_elements
            for selector in result_item_selectors: # Simplified retry
                elements = wait_for_elements(driver, By.XPATH, selector, timeout=7)
                if elements:
                    print(f"Found {len(elements)} search result items after CAPTCHA with selector: {selector}")
                    search_post_elements = elements
                    break
            if not search_post_elements:
                print("Still no search result items found after CAPTCHA.")

    # ... (rest of search result item processing logic remains the same)
    for i, item_el in enumerate(search_post_elements):
        print(f"Processing search result {i+1}/{len(search_post_elements)}...")
        discussion_data = {
            "content": None, "author_name": None, "author_url": None,
            "timestamp_text": None, "timestamp": None, "url": None,
            "source_group_or_page": None, "sentiment": None
        }
        content_selectors = [
            ".//div[@data-ad-preview='message']", ".//div[contains(@class, 'userContent')]/p",
            ".//div[contains(@data-testid, 'post_message')]",
            ".//div[@dir='auto' and string-length(normalize-space(.)) > 20 and not(.//article) and not(.//header)]",
            ".//span[contains(@class, 'text_content')]"
        ]
        for selector in content_selectors:
            try:
                content_element = item_el.find_element(By.XPATH, selector)
                discussion_data["content"] = content_element.text.strip()
                if discussion_data["content"]:
                    if analyze_sentiment_flag:
                        discussion_data["sentiment"] = analyze_sentiment_vader(discussion_data["content"])
                    break
            except: continue

        author_selectors = [
            ".//strong/parent::a[contains(@href,'facebook.com/') and not(contains(@href,'/groups/'))]",
            ".//h2//a[contains(@href,'facebook.com/')]",
            ".//a[@aria-label and contains(@href,'facebook.com/') and not(contains(@href,'/photos/')) and not(contains(@href,'/videos/')) and string-length(normalize-space(.)) > 0]",
            ".//header//a[contains(@href,'?id=') or contains(@href, 'profile.php') or (contains(@href,'facebook.com/') and not(contains(@href,'/groups/')) and not(contains(@href,'/events/')))]"
        ]
        for selector in author_selectors:
            try:
                author_link_element = item_el.find_element(By.XPATH, selector)
                discussion_data["author_name"] = author_link_element.text.strip()
                discussion_data["author_url"] = author_link_element.get_attribute("href")
                if discussion_data["author_name"] and discussion_data["author_url"]: break
            except: continue

        timestamp_selectors = [
            ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php') or contains(@href,'/permalink/') or contains(@href, '/watch/')]",
            ".//abbr/parent::a",
            ".//a[./span[contains(text(),'ago')] or ./span[contains(text(),'hr')] or ./span[contains(text(),'min')]]"
        ]
        for selector in timestamp_selectors:
            try:
                ts_element = item_el.find_element(By.XPATH, selector)
                discussion_data["url"] = ts_element.get_attribute("href")
                discussion_data["timestamp_text"] = ts_element.text.strip()
                try:
                    data_utime_abbr = ts_element.find_element(By.XPATH, ".//abbr[@data-utime]").get_attribute("data-utime")
                    discussion_data["timestamp"] = int(data_utime_abbr)
                except:
                    try:
                        data_utime_link = ts_element.get_attribute("data-utime")
                        if data_utime_link: discussion_data["timestamp"] = int(data_utime_link)
                    except: pass
                if discussion_data["url"]: break
            except: continue

        source_selectors = [
            ".//a[contains(@href, '/groups/') and normalize-space(.) != discussion_data['author_name']]",
            ".//span[contains(text(),'shared a post to the group:')]/following-sibling::a",
            ".//div[@role='article']//header//a[contains(@href,'/groups/') or contains(@href,'/pages/')]"
        ]
        for selector in source_selectors:
            try:
                source_link_element = item_el.find_element(By.XPATH, selector)
                discussion_data["source_group_or_page"] = source_link_element.get_attribute("href")
                if discussion_data["source_group_or_page"]: break
            except: continue

        if discussion_data["content"] or discussion_data["url"]:
            search_results_data["discussions"].append(discussion_data)


    print(f"Finished search attempt for: '{search_query}'")
    return search_results_data


def get_post_details(driver: WebDriver, post_url: str, analyze_sentiment_flag: bool = False):
    print(f"Navigating to post: {post_url}")
    driver.get(post_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    if check_for_captcha_and_pause(driver): # Check after initial load
        WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    post_details_data = {"url": post_url, "reactions": {"types": {}, "total_count": 0, "summary_text": None}, "comments": [], "comment_count_text": None}

    # Reaction extraction logic (kept brief for this example, but would be similar)
    print("Attempting to extract reactions...")
    reaction_summary_selectors = [
        "//span[@role='toolbar']//span[@role='button']/span[@aria-label]",
        "//div[@aria-label='Reactions']//span[contains(text(),'and')]",
        "//a[contains(@href,'/ufi/reaction/profile/browser/')]/@aria-label",
        "//span[contains(text(),'Like')]/parent::div/following-sibling::span"
    ]
    for selector in reaction_summary_selectors:
        summary_element = wait_for_element(driver, By.XPATH, selector, timeout=3)
        if summary_element:
            text = summary_element.text.strip() if summary_element.text else summary_element.get_attribute('aria-label')
            if text:
                post_details_data["reactions"]["summary_text"] = text.strip()
                try:
                    if "others" in text and text.split(' ')[-2].isdigit():
                        post_details_data["reactions"]["total_count"] = int(text.split(' ')[-2]) + text.count(',') + 1
                    elif text.isdigit():
                         post_details_data["reactions"]["total_count"] = int(text)
                except: pass
                break
    print("TODO: Advanced reaction extraction (clicking for details) is not yet implemented.")

    # Comment count
    comment_count_selectors = [
        "//span[contains(text(),'Comment') or contains(text(),'comment')][not(ancestor::div[@role='article'])]",
        "//div[@aria-label='Comments']//h3",
    ]
    for selector in comment_count_selectors:
        count_el = wait_for_element(driver, By.XPATH, selector, timeout=3)
        if count_el and count_el.text.strip():
            post_details_data["comment_count_text"] = count_el.text.strip()
            break

    # Load more comments & extract
    view_more_comments_selectors = [
        "//span[contains(text(),'View more comments') or contains(text(),'Load more comments')]/ancestor::div[@role='button']",
        "//a[contains(@href,'comment/replies') and contains(.,'more comment')]",
        "//div[@role='button'][.//span[starts-with(text(),'View') and contains(text(),'comment')]]"
    ]
    for _ in range(3):
        clicked_more = False
        for selector in view_more_comments_selectors:
            view_more_button = wait_for_element(driver, By.XPATH, selector, timeout=2)
            if view_more_button and view_more_button.is_displayed():
                try:
                    driver.execute_script("arguments[0].click();", view_more_button)
                    time.sleep(2.5)
                    clicked_more = True; break
                except: pass
            if clicked_more: break
        if not clicked_more:
            scroll_to_bottom(driver, max_scrolls=2, pause_time=2); break

    print("Attempting to extract comments...")
    comment_container_selectors = [
        "//div[@aria-label='Comment']", "//div[contains(@class,'comment-class-placeholder')]",
        "//ul/li[.//a[contains(@href,'/user/')]]", "//div[@role='comment']"
    ]
    comment_elements = []
    for selector in comment_container_selectors:
        elements = wait_for_elements(driver, By.XPATH, selector, timeout=5)
        if elements:
            comment_elements = elements; break

    if not comment_elements:
        print("  No comment containers found with the tried selectors.")
        if check_for_captcha_and_pause(driver):
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            # Retry finding comments
            for selector in comment_container_selectors: # Simplified retry
                elements = wait_for_elements(driver, By.XPATH, selector, timeout=5)
                if elements:
                    print(f"Found {len(elements)} comments after CAPTCHA with selector: {selector}")
                    comment_elements = elements
                    break
            if not comment_elements:
                print("Still no comments found after CAPTCHA.")

    for i, comment_el in enumerate(comment_elements):
        comment_data = {"author_name": None, "author_url": None, "content": None, "timestamp_text": None, "timestamp": None, "sentiment": None}
        author_selectors = [
            ".//a[contains(@href,'facebook.com/') and not(contains(@href,'/ufi/reaction')) and string-length(normalize-space(.)) > 0 and not(img)]",
            ".//div[@aria-label='Comment author']//a", ".//h3//a", ".//span[@class='_6qw4']"
        ]
        for selector in author_selectors:
            author_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if author_element and author_element.text.strip():
                comment_data["author_name"] = author_element.text.strip()
                comment_data["author_url"] = author_element.get_attribute("href")
                break
        content_selectors = [
            ".//span[contains(@class,'comment-text-class')]", ".//div[@data-testid='comment_text']",
            ".//div[@dir='auto' and not(.//div[@role='button'])]",
            ".//span[string-length(normalize-space(.)) > 0 and not(ancestor::a)]"
        ]
        for selector in content_selectors:
            content_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if content_element and content_element.text.strip():
                comment_data["content"] = content_element.text.strip()
                if analyze_sentiment_flag:
                    comment_data["sentiment"] = analyze_sentiment_vader(comment_data["content"])
                break
        timestamp_selectors = [
            ".//abbr[@data-utime]/parent::a", ".//a[contains(@href,'comment_id=')]",
            ".//span[contains(text(),'hr') or contains(text(),'min') or contains(text(),'Just now') or contains(text(),'Yesterday')]/ancestor::a"
        ]
        for selector in timestamp_selectors:
            ts_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if ts_element:
                comment_data["timestamp_text"] = ts_element.text.strip()
                try:
                    abbr = ts_element.find_element(By.XPATH, ".//abbr[@data-utime]")
                    comment_data["timestamp"] = int(abbr.get_attribute("data-utime"))
                except: pass
                break
        if comment_data["author_name"] and comment_data["content"]:
            post_details_data["comments"].append(comment_data)

    print(f"Finished scraping post details attempt for: {post_url}")
    return post_details_data

# Keep the if __name__ == '__main__': block as is
if __name__ == '__main__':
    print("scraper_core.py executed directly (for testing purposes).")
    pass
