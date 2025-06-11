# scraper_core.py
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from urllib.parse import quote_plus # Ensure it's imported if not already at top level

# --- Helper Functions --- (Keep existing helpers: scroll_to_bottom, wait_for_element, wait_for_elements)
def scroll_to_bottom(driver: WebDriver, max_scrolls=5, pause_time=2.5, scroll_element=None):
    """Scrolls to the bottom of the page or a specific element to load dynamic content."""
    print(f"Scrolling (element: {'body' if not scroll_element else 'specific element'})...")

    if scroll_element:
        # Scroll within a specific element
        script = "arguments[0].scrollTop = arguments[0].scrollHeight"
        target_element = scroll_element
    else:
        # Scroll the whole page
        script = "window.scrollTo(0, document.body.scrollHeight);"
        target_element = driver.execute_script("return document.body") # Fallback for height check

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
    """Waits for a single element to be present (optionally within a parent) and returns it."""
    target = parent_element if parent_element else driver
    try:
        element = WebDriverWait(target, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception:
        return None

def wait_for_elements(driver: WebDriver, by: By, value: str, timeout=10, parent_element=None):
    """Waits for multiple elements to be present (optionally within a parent) and returns them."""
    target = parent_element if parent_element else driver
    try:
        elements = WebDriverWait(target, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )
        return elements
    except Exception:
        return []

# --- Main Scraping Functions ---

def get_public_profile_data(driver: WebDriver, profile_url: str):
    # ... (Keep existing implementation) ...
    """
    Scrapes data from a public Facebook profile.
    Focuses on profile name and posts for this iteration.
    """
    print(f"Navigating to profile: {profile_url}")
    driver.get(profile_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')

    profile_data = {
        "url": profile_url,
        "name": None,
        "posts": [],
        "photo_links": [], # TODO
        "friend_names_or_links": [], # TODO
        "group_names_or_links": []   # TODO
    }

    print("Attempting to extract profile name...")
    name_selectors = [
        "//h1",
        "//div[@role='main']//h1",
        "//div[contains(@aria-label,'profile name')]//span[not(contains(@class,'visuallyhidden'))]",
        "//span[contains(@class,'profile-name')]",
        "//div[@id='cover-name-root']//h1",
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
        except:
            continue

    if not profile_data["name"]:
        print("Profile name could not be extracted with common selectors.")

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

    for i, post_el in enumerate(post_elements):
        print(f"Processing post {i+1}/{len(post_elements)}...")
        post_data = {"content": None, "timestamp": None, "timestamp_text": None, "author": "Profile Owner (assumed)", "url": None}

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
                content_element = post_el.find_element(By.XPATH, selector) # Changed to find_element from post_el
                post_data["content"] = content_element.text.strip()
                if post_data["content"]:
                    print(f"  Post content found (first 100 chars): {post_data['content'][:100]}...")
                    break
            except:
                continue
        if not post_data["content"]:
             print("  Post content not found for this post.")

        timestamp_selectors = [
            ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php') or contains(@href,'/permalink/')]",
            ".//abbr/parent::a",
            ".//a[./span[contains(text(),'ago')] or ./span[contains(text(),'hr')] or ./span[contains(text(),'min')]]",
            ".//a[@data-testid='story-subtitle']//span//a"
        ]
        for selector in timestamp_selectors:
            try:
                timestamp_element = post_el.find_element(By.XPATH, selector) # Changed to find_element from post_el
                post_data["url"] = timestamp_element.get_attribute("href")
                post_data["timestamp_text"] = timestamp_element.text.strip()

                try:
                    # Check for data-utime on abbr child first
                    abbr_element = timestamp_element.find_element(By.XPATH, ".//abbr[@data-utime]")
                    data_utime = abbr_element.get_attribute("data-utime")
                    post_data["timestamp"] = int(data_utime)
                except:
                    # If not on abbr, check the link itself
                    try:
                        data_utime_on_link = timestamp_element.get_attribute("data-utime")
                        if data_utime_on_link:
                             post_data["timestamp"] = int(data_utime_on_link)
                    except:
                        pass # Keep timestamp_text as fallback

                if post_data["url"]:
                    print(f"  Post timestamp/URL found: {post_data['timestamp_text']}, URL: {post_data['url']}")
                    break
            except:
                continue
        if not post_data["url"]:
            print("  Post timestamp/URL not found for this post.")

        if post_data["content"] or post_data["url"]:
            profile_data["posts"].append(post_data)

    print("TODO: Implement photo link extraction.")
    print("TODO: Implement friends list extraction (highly dependent on UI and privacy).")
    print("TODO: Implement groups list extraction.")
    print(f"Finished scraping profile data attempt for: {profile_url}")
    return profile_data

def search_facebook(driver: WebDriver, search_query: str):
    # ... (Keep existing implementation) ...
    print(f"Performing search for: '{search_query}'")
    encoded_query = quote_plus(search_query)
    search_url = f"https://www.facebook.com/search/posts/?q={encoded_query}"

    print(f"Navigating to search URL: {search_url}")
    driver.get(search_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    time.sleep(3)

    search_results_data = {
        "query": search_query,
        "discussions": []
    }

    scroll_to_bottom(driver, max_scrolls=5, pause_time=3)

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

    for i, item_el in enumerate(search_post_elements):
        print(f"Processing search result {i+1}/{len(search_post_elements)}...")
        discussion_data = {
            "content": None, "author_name": None, "author_url": None,
            "timestamp_text": None, "timestamp": None, "url": None,
            "source_group_or_page": None
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
                    print(f"  Content found (first 100 chars): {discussion_data['content'][:100]}...")
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
                if discussion_data["author_name"] and discussion_data["author_url"]:
                    print(f"  Author found: {discussion_data['author_name']} ({discussion_data['author_url']})")
                    break
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
                if discussion_data["url"]:
                    print(f"  Timestamp/URL found: {discussion_data['timestamp_text']}, URL: {discussion_data['url']}")
                    break
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
                if discussion_data["source_group_or_page"]:
                    print(f"  Source group/page found: {discussion_data['source_group_or_page']}")
                    break
            except: continue

        if discussion_data["content"] or discussion_data["url"]:
            search_results_data["discussions"].append(discussion_data)
        elif not discussion_data["content"] and not discussion_data["url"]:
             print("  Could not extract meaningful data (content or URL) for this search item.")

    print(f"Finished search attempt for: '{search_query}'")
    return search_results_data


def get_post_details(driver: WebDriver, post_url: str):
    """
    Extracts details from a single post page, like reactions and comments.
    """
    print(f"Navigating to post: {post_url}")
    driver.get(post_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    time.sleep(3) # Allow post to initially load

    post_details_data = {
        "url": post_url,
        "reactions": {"types": {}, "total_count": 0, "summary_text": None},
        "comments": [],
        "comment_count_text": None
    }

    # --- Extract Reactions ---
    # This is highly complex. Reactions are often in a summary string, or require clicking a button
    # to open a dialog, then scraping that dialog.
    print("Attempting to extract reactions...")
    reaction_summary_selectors = [
        "//span[@role='toolbar']//span[@role='button']/span[@aria-label]", # Summary text often in aria-label of a span inside a button
        "//div[@aria-label='Reactions']//span[contains(text(),'and')]", # e.g., "You, John Doe and 15 others"
        "//a[contains(@href,'/ufi/reaction/profile/browser/')]/@aria-label", # Links that open reaction lists
        "//span[contains(text(),'Like')]/parent::div/following-sibling::span" # Count next to "Like" button text
    ]
    reaction_details_button_selectors = [ # Button to open the detailed reaction list
        "//span[@role='toolbar']//span[@role='button'][span[@aria-label]]", # The button itself
        "//div[@aria-label='Reactions']//div[@role='button']"
    ]

    # Try to get a summary first
    for selector in reaction_summary_selectors:
        summary_element = wait_for_element(driver, By.XPATH, selector, timeout=3)
        if summary_element:
            text = summary_element.text.strip() if summary_element.text else summary_element.get_attribute('aria-label')
            if text:
                post_details_data["reactions"]["summary_text"] = text.strip()
                print(f"  Reaction summary found: {text.strip()}")
                # Basic parsing of total count from summary (e.g., "K L and N others" -> N+2)
                # This is a very rough heuristic
                parts = text.split(' ')
                try:
                    if "others" in text and parts[-2].isdigit():
                        post_details_data["reactions"]["total_count"] = int(parts[-2]) + text.count(',') + 1
                    elif text.isdigit(): # If summary is just a number
                         post_details_data["reactions"]["total_count"] = int(text)
                except: pass # Ignore parsing errors
                break

    # TODO: Implement clicking reaction_details_button_selectors and scraping the dialog if summary is not enough.
    # This would involve:
    # 1. Clicking the button.
    # 2. Waiting for the dialog/pop-up to appear.
    # 3. Scraping reaction types (e.g., img alt text or aria-labels) and counts from the dialog.
    # 4. Closing the dialog.
    print("TODO: Advanced reaction extraction (clicking for details) is not yet implemented.")


    # --- Extract Comment Count (Often displayed near comments section) ---
    comment_count_selectors = [
        "//span[contains(text(),'Comment') or contains(text(),'comment')][not(ancestor::div[@role='article'])]", # Text like "X Comments"
        "//div[@aria-label='Comments']//h3", # A heading for the comments section
    ]
    for selector in comment_count_selectors:
        count_el = wait_for_element(driver, By.XPATH, selector, timeout=3)
        if count_el and count_el.text.strip():
            post_details_data["comment_count_text"] = count_el.text.strip()
            print(f"  Comment count text found: {post_details_data['comment_count_text']}")
            break

    # --- Scroll to load comments / Click "View more comments" ---
    # Comments section might have its own scroll container or "view more" buttons.
    # First, try to find a general "View more comments" or similar button.
    view_more_comments_selectors = [
        "//span[contains(text(),'View more comments') or contains(text(),'Load more comments')]/ancestor::div[@role='button']",
        "//a[contains(@href,'comment/replies') and contains(.,'more comment')]",
        "//div[@role='button'][.//span[starts-with(text(),'View') and contains(text(),'comment')]]"
    ]
    for _ in range(3): # Try clicking "view more" a few times
        clicked_more = False
        for selector in view_more_comments_selectors:
            view_more_button = wait_for_element(driver, By.XPATH, selector, timeout=2)
            if view_more_button and view_more_button.is_displayed():
                print(f"  Found and clicking '{view_more_button.text.strip()}' button...")
                try:
                    driver.execute_script("arguments[0].click();", view_more_button)
                    time.sleep(2.5) # Wait for comments to load
                    clicked_more = True
                    break
                except Exception as e:
                    print(f"    Error clicking view more comments: {e}")
            if clicked_more: break
        if not clicked_more:
            # If no button found, try general scroll
            print("  No 'View more comments' button found or clickable, trying general scroll for comments.")
            scroll_to_bottom(driver, max_scrolls=2, pause_time=2) # Short scroll to trigger auto-load
            break # Break after one general scroll if no specific button

    # --- Extract Comments ---
    print("Attempting to extract comments...")
    comment_container_selectors = [
        "//div[@aria-label='Comment']", # ARIA label for individual comment
        "//div[contains(@class,'comment-class-placeholder')]", # Hypothetical class
        "//ul/li[.//a[contains(@href,'/user/')]]", # List item that seems to contain user link (comment)
        "//div[@role='comment']" # Role based
    ]

    comment_elements = []
    for selector in comment_container_selectors:
        elements = wait_for_elements(driver, By.XPATH, selector, timeout=5)
        if elements:
            print(f"Found {len(elements)} potential comment containers with selector: {selector}")
            comment_elements = elements
            break

    if not comment_elements:
        print("  No comment containers found with the tried selectors.")

    for i, comment_el in enumerate(comment_elements):
        print(f"  Processing comment {i+1}/{len(comment_elements)}...")
        comment_data = {"author_name": None, "author_url": None, "content": None, "timestamp_text": None, "timestamp": None}

        # Comment Author
        author_selectors = [
            ".//a[contains(@href,'facebook.com/') and not(contains(@href,'/ufi/reaction')) and string-length(normalize-space(.)) > 0 and not(img)]", # General link to a profile
            ".//div[@aria-label='Comment author']//a", # Specific ARIA label
            ".//h3//a", # Author name in a heading
            ".//span[@class='_6qw4']" # An old FB class for comment author
        ]
        for selector in author_selectors:
            author_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if author_element and author_element.text.strip():
                comment_data["author_name"] = author_element.text.strip()
                comment_data["author_url"] = author_element.get_attribute("href")
                break
        if not comment_data["author_name"]: print(f"    Author not found for comment {i+1}")

        # Comment Content
        content_selectors = [
            ".//span[contains(@class,'comment-text-class')]", # Hypothetical
            ".//div[@data-testid='comment_text']", # Test ID
            ".//div[@dir='auto' and not(.//div[@role='button'])]", # Div with text, not containing buttons
            ".//span[string-length(normalize-space(.)) > 0 and not(ancestor::a)]" # A span with text not part of a link (heuristic)
        ]
        for selector in content_selectors:
            content_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if content_element and content_element.text.strip():
                comment_data["content"] = content_element.text.strip()
                break
        if not comment_data["content"]: print(f"    Content not found for comment {i+1}")

        # Comment Timestamp
        timestamp_selectors = [
            ".//abbr[@data-utime]/parent::a", # Utime on abbr inside link
            ".//a[contains(@href,'comment_id=')]", # Link with comment_id usually has timestamp
            ".//span[contains(text(),'hr') or contains(text(),'min') or contains(text(),'Just now') or contains(text(),'Yesterday')]/ancestor::a"
        ]
        for selector in timestamp_selectors:
            ts_element = wait_for_element(driver, By.XPATH, selector, timeout=1, parent_element=comment_el)
            if ts_element:
                comment_data["timestamp_text"] = ts_element.text.strip()
                try:
                    abbr = ts_element.find_element(By.XPATH, ".//abbr[@data-utime]")
                    comment_data["timestamp"] = int(abbr.get_attribute("data-utime"))
                except: pass # Ignore if no data-utime abbr
                break
        if not comment_data["timestamp_text"]: print(f"    Timestamp not found for comment {i+1}")

        if comment_data["author_name"] and comment_data["content"]:
            post_details_data["comments"].append(comment_data)
            print(f"    Added comment by {comment_data['author_name']}: {comment_data['content'][:50]}...")
        else:
            print(f"    Could not extract full details for comment {i+1}.")

    print(f"Finished scraping post details attempt for: {post_url}")
    return post_details_data

if __name__ == '__main__':
    print("scraper_core.py executed directly (for testing purposes).")
    pass
