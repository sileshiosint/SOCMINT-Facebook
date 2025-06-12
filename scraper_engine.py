# scraper_engine.py
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
from urllib.parse import quote_plus
import text_analyzer
from content_analyzer import score_risk, extract_links # Corrected import

# --- Helper: CAPTCHA Detection ---
def check_for_captcha(driver: WebDriver, context_message=""):
    captcha_keywords = ["captcha", "security check", "are you human", "verify your account", "recaptcha", "checkpoint", "puzzle", "unusual activity"]
    current_url = driver.current_url.lower()
    current_title = driver.title.lower()
    for keyword in captcha_keywords:
        if keyword in current_url or keyword in current_title:
            print(f"CAPTCHA or security check suspected ({context_message}) based on keyword '{keyword}'.")
            print(f"URL: {driver.current_url}"); print(f"Title: {driver.title}")
            input("!!! CAPTCHA/Security Check Detected !!!\nPlease solve it in the browser. After solving, press Enter here to continue script...")
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            return True
    captcha_iframes_selectors = ["//iframe[contains(@src, 'recaptcha')]", "//iframe[contains(@title, 'captcha')]", "//iframe[contains(@name, 'cframe')]"]
    for selector in captcha_iframes_selectors:
        if driver.find_elements(By.XPATH, selector):
            print(f"CAPTCHA or security check suspected ({context_message}) based on iframe: {selector}")
            input("!!! CAPTCHA/Security Check (iframe) Detected !!!\nPlease solve in browser. Press Enter here...")
            WebDriverWait(driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            return True
    return False

# --- Helper: Element Interaction & Scrolling ---
def wait_for_element_presence(driver_or_element, by: By, value: str, timeout=10):
    try: return WebDriverWait(driver_or_element, timeout).until(EC.presence_of_element_located((by, value)))
    except: return None
def wait_for_all_elements_presence(driver_or_element, by: By, value: str, timeout=10):
    try: return WebDriverWait(driver_or_element, timeout).until(EC.presence_of_all_elements_located((by, value)))
    except: return []
def scroll_page(driver: WebDriver, scrolls=3, delay=2.5):
    print("Scrolling page to load more content...")
    for i in range(scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(delay)
        print(f"Scroll {i+1}/{scrolls}")
    print("Scrolling complete.")

# --- Helper: Content Processing ---
def process_content_analyses(item_data_dict, content_key="content",
                             analyze_sentiment_flag=False, translate_to_lang=None):
    content = item_data_dict.get(content_key)
    if not content:
        item_data_dict["links"] = []
        # Initialize other keys to None or default empty state if content is not there
        item_data_dict["translation"] = None
        item_data_dict["sentiment"] = None
        item_data_dict["risk_assessment"] = score_risk("", None) # Score empty content for consistency
        return

    item_data_dict["links"] = extract_links(content) # Corrected call
    text_to_process = content
    if translate_to_lang:
        translated = text_analyzer.translate_text(text_to_process, translate_to_lang)
        if translated and translated.lower().strip() != text_to_process.lower().strip():
            item_data_dict["translation"] = {"original": content, "translated": translated, "lang": translate_to_lang}
            text_to_process = translated
        elif not translated: text_to_process = content
    current_sentiment = None
    if analyze_sentiment_flag:
        current_sentiment = text_analyzer.analyze_sentiment(text_to_process)
        item_data_dict["sentiment"] = current_sentiment
    # CORRECTED FUNCTION CALL HERE
    item_data_dict["risk_assessment"] = score_risk(text_to_process, current_sentiment)

# --- Main Scraping Functions ---
def scrape_profile_data(driver: WebDriver, profile_url: str,
                        analyze_sentiment_flag: bool = False, translate_to_lang: str = None):
    print(f"Navigating to profile: {profile_url}")
    driver.get(profile_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    check_for_captcha(driver, "profile page load")
    profile_info = {"url": profile_url, "name": None, "posts": []}
    name_selectors = ["//h1", "//div[@data-testid='profile-name']//span[1]", "//span[contains(@class, 'profileFullName')]", "//div[@id='fb-timeline-cover-name']//h1"]
    for selector in name_selectors:
        name_el = wait_for_element_presence(driver, By.XPATH, selector, timeout=5)
        if name_el and name_el.text.strip():
            profile_info["name"] = name_el.text.strip()
            print(f"Profile Name: {profile_info['name']}")
            break
    if not profile_info["name"]: print("Profile name not found.")
    scroll_page(driver, scrolls=3)
    post_container_selectors = ["//div[@role='article']", "//div[contains(@data-pagelet, 'FeedUnit')]", "//div[contains(@class,'userContentWrapper')]"]
    post_elements = []
    for selector in post_container_selectors:
        elements = wait_for_all_elements_presence(driver, By.XPATH, selector, timeout=7)
        if elements:
            print(f"Found {len(elements)} post containers with: {selector}")
            post_elements = elements; break
    for post_el in post_elements:
        post_data = {"content": None, "timestamp_text": None, "timestamp": None, "url": None,
                     "author": profile_info["name"], "translation": None, "sentiment": None, "links": [], "risk_assessment": None}
        try:
            content_el = wait_for_element_presence(post_el, By.XPATH, ".//div[@data-ad-preview='message'] | .//div[contains(@data-testid, 'post_message')]", timeout=2)
            if not content_el: content_el = wait_for_element_presence(post_el, By.XPATH, ".//div[contains(@class, 'userContent')]/p", timeout=1)
            if content_el: post_data["content"] = content_el.text.strip()
            ts_link_el = wait_for_element_presence(post_el, By.XPATH, ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php')]", timeout=2)
            if ts_link_el:
                post_data["url"] = ts_link_el.get_attribute("href")
                post_data["timestamp_text"] = ts_link_el.text.strip()
                abbr_el = wait_for_element_presence(ts_link_el, By.XPATH, ".//abbr[@data-utime]", timeout=1)
                if abbr_el: post_data["timestamp"] = int(abbr_el.get_attribute("data-utime"))
            process_content_analyses(post_data, "content", analyze_sentiment_flag, translate_to_lang)
            if post_data["content"] or post_data["url"]: profile_info["posts"].append(post_data)
        except Exception as e: print(f"Error processing a post element: {e}")
    print(f"Scraped {len(profile_info['posts'])} posts.")
    return profile_info

def search_public_posts(driver: WebDriver, keywords: str,
                        analyze_sentiment_flag: bool = False, translate_to_lang: str = None):
    print(f"Searching for: {keywords}")
    search_url = f"https://www.facebook.com/search/posts/?q={quote_plus(keywords)}"
    driver.get(search_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    check_for_captcha(driver, "search results page load")
    search_results = {"query": keywords, "discussions": []}
    scroll_page(driver, scrolls=4)
    item_selectors = ["//div[@role='article']", "//div[contains(@data-pagelet, 'SearchResults') or contains(@data-pagelet, 'SearchFeed')]//div[div[@role='article']]"]
    discussion_elements = []
    for selector in item_selectors:
        elements = wait_for_all_elements_presence(driver, By.XPATH, selector, timeout=7)
        if elements:
            print(f"Found {len(elements)} discussion items with: {selector}")
            discussion_elements = elements; break
    for item_el in discussion_elements:
        item_data = {"content": None, "author_name": None, "author_url": None, "timestamp_text": None,
                     "timestamp": None, "url": None, "source_group_or_page": None,
                     "translation": None, "sentiment": None, "links": [], "risk_assessment": None}
        try:
            author_el = wait_for_element_presence(item_el, By.XPATH, ".//strong/parent::a | .//h2//a | .//header//a[not(contains(@href,'/reactions/')) and string-length(normalize-space(.)) > 0]", timeout=2)
            if author_el and author_el.text.strip():
                item_data["author_name"] = author_el.text.strip()
                item_data["author_url"] = author_el.get_attribute("href")
            content_el = wait_for_element_presence(item_el, By.XPATH, ".//div[@data-ad-preview='message'] | .//div[contains(@data-testid, 'post_message')]", timeout=2)
            if content_el: item_data["content"] = content_el.text.strip()
            ts_link_el = wait_for_element_presence(item_el, By.XPATH, ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php') or contains(@href,'/permalink/')]", timeout=2)
            if ts_link_el:
                item_data["url"] = ts_link_el.get_attribute("href")
                item_data["timestamp_text"] = ts_link_el.text.strip()
                abbr_el = wait_for_element_presence(ts_link_el, By.XPATH, ".//abbr[@data-utime]", timeout=1)
                if abbr_el: item_data["timestamp"] = int(abbr_el.get_attribute("data-utime"))
            source_el = wait_for_element_presence(item_el, By.XPATH, ".//a[contains(@href,'/groups/') and count(ancestor::div[@role='article'])=1]", timeout=1)
            if source_el and source_el.get_attribute("href") != item_data.get("author_url"):
                item_data["source_group_or_page"] = source_el.get_attribute("href")
            process_content_analyses(item_data, "content", analyze_sentiment_flag, translate_to_lang)
            if item_data["content"] or item_data["url"]: search_results["discussions"].append(item_data)
        except Exception as e: print(f"Error processing a search item: {e}")
    print(f"Scraped {len(search_results['discussions'])} discussion items.")
    return search_results

def get_post_details(driver: WebDriver, post_url: str,
                     analyze_sentiment_flag: bool = False, translate_to_lang: str = None):
    print(f"Navigating to post for details: {post_url}")
    driver.get(post_url)
    WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    check_for_captcha(driver, "post details page load")
    post_details = {"url": post_url,
                    "main_post": {"content": None, "author_name": None, "author_url": None, "timestamp_text": None, "timestamp": None,
                                  "translation": None, "sentiment": None, "links": [], "risk_assessment": None},
                    "reactions": {"summary_text": None, "types": {}, "total_count": 0}, "comments": []}
    main_post_container = wait_for_element_presence(driver, By.XPATH, "(//div[@role='article'])[1] | (//div[contains(@data-pagelet,'permalink')])[1]", timeout=5)
    context = main_post_container if main_post_container else driver
    author_el = wait_for_element_presence(context, By.XPATH, ".//strong/parent::a | .//h2//a | .//header//a[not(contains(@href,'/reactions/')) and string-length(normalize-space(.)) > 0]", timeout=2)
    if author_el and author_el.text.strip():
        post_details["main_post"]["author_name"] = author_el.text.strip()
        post_details["main_post"]["author_url"] = author_el.get_attribute("href")
    content_el = wait_for_element_presence(context, By.XPATH, ".//div[@data-ad-preview='message'] | .//div[contains(@data-testid, 'post_message')]", timeout=2)
    if content_el: post_details["main_post"]["content"] = content_el.text.strip()
    ts_link_el = wait_for_element_presence(context, By.XPATH, ".//a[contains(@href,'/posts/') or contains(@href,'/videos/') or contains(@href,'/photos/') or contains(@href,'/story.php') or contains(@href,'/permalink/')]", timeout=2)
    if ts_link_el and (context == main_post_container or not wait_for_element_presence(ts_link_el, By.XPATH, "ancestor::div[@aria-label='Comment']", timeout=0.1)):
        post_details["main_post"]["timestamp_text"] = ts_link_el.text.strip()
        abbr_el = wait_for_element_presence(ts_link_el, By.XPATH, ".//abbr[@data-utime]", timeout=1)
        if abbr_el: post_details["main_post"]["timestamp"] = int(abbr_el.get_attribute("data-utime"))
    process_content_analyses(post_details["main_post"], "content", analyze_sentiment_flag, translate_to_lang)
    print(f"Main post author: {post_details['main_post']['author_name']}, Content snippet: {post_details['main_post']['content'][:50] if post_details['main_post']['content'] else 'N/A'}")
    reaction_summary_el = wait_for_element_presence(driver, By.XPATH, "//span[@role='toolbar']//span[@role='button']/span[@aria-label]", timeout=3)
    if reaction_summary_el:
        post_details["reactions"]["summary_text"] = reaction_summary_el.get_attribute('aria-label').strip()
        print(f"Reactions summary: {post_details['reactions']['summary_text']}")
    scroll_page(driver, scrolls=2, delay=1.5)
    comment_elements = wait_for_all_elements_presence(driver, By.XPATH, "//div[@aria-label='Comment'] | //div[@role='comment']", timeout=5)
    print(f"Found {len(comment_elements)} comment elements.")
    for comm_el in comment_elements:
        comment_data = {"author_name": None, "author_url": None, "content": None, "timestamp_text": None, "timestamp": None,
                        "translation": None, "sentiment": None, "links": [], "risk_assessment": None}
        try:
            c_author_el = wait_for_element_presence(comm_el, By.XPATH, ".//a[contains(@href,'facebook.com/') and string-length(normalize-space(.)) > 0 and not(img)]", timeout=1)
            if c_author_el and c_author_el.text.strip():
                comment_data["author_name"] = c_author_el.text.strip()
                comment_data["author_url"] = c_author_el.get_attribute("href")
            c_content_el = wait_for_element_presence(comm_el, By.XPATH, ".//div[@dir='auto' and not(.//div[@role='button'])] | .//span[contains(@class,'text_exposed_root')]", timeout=1)
            if c_content_el: comment_data["content"] = c_content_el.text.strip()
            c_ts_el = wait_for_element_presence(comm_el, By.XPATH, ".//a[contains(@href,'comment_id=')]//abbr[@data-utime]/parent::a | .//a[contains(@href,'comment_id=')]", timeout=1)
            if c_ts_el:
                comment_data["timestamp_text"] = c_ts_el.text.strip()
                abbr_el = wait_for_element_presence(c_ts_el, By.XPATH, ".//abbr[@data-utime]", timeout=0.5)
                if abbr_el: comment_data["timestamp"] = int(abbr_el.get_attribute("data-utime"))
            process_content_analyses(comment_data, "content", analyze_sentiment_flag, translate_to_lang)
            if comment_data["content"] or comment_data["author_name"]: post_details["comments"].append(comment_data)
        except Exception as e: print(f"Error processing a comment: {e}")
    print(f"Scraped {len(post_details['comments'])} comments.")
    return post_details

if __name__ == '__main__':
    print("scraper_engine.py executed directly.")
    pass
