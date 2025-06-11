# facebook_scraper.py
import argparse
import json
import traceback
from browser_handler import get_browser_driver
from scraper_core import get_public_profile_data, search_facebook, get_post_details

def main():
    parser = argparse.ArgumentParser(
        description="Facebook OSINT Tool using browser automation.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
                 "  # Scrape a public profile (Chrome with --remote-debugging-port=9222)\n"
                 "  python facebook_scraper.py --profile-url \"https://www.facebook.com/somepublicprofile\"\n\n"
                 "  # Scrape a public profile using a specific Chrome profile\n"
                 "  python facebook_scraper.py --profile-url \"https://www.facebook.com/somepublicprofile\" --profile-path \"/path/to/chrome/userdatadirectory\"\n\n"
                 "  # Search for public posts\n"
                 "  python facebook_scraper.py --search \"climate change activism\"\n\n"
                 "  # Get details for a specific post\n"
                 "  python facebook_scraper.py --post-url \"https://www.facebook.com/username/posts/postid\"\n\n"
                 "Notes:\n"
                 "- Ensure Chrome is running with --remote-debugging-port=9222 OR provide --profile-path.\n"
                 "- Selectors are experimental and may need adjustment."
    )
    parser.add_argument("--remote-port", type=int, default=9222,
                        help="Port for Chrome remote debugging (default: 9222).")
    parser.add_argument("--profile-path", type=str, default=None,
                        help="Path to Chrome user data directory. Used if remote debugging fails.")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--profile-url", type=str, help="URL of the Facebook profile to scrape.")
    action_group.add_argument("--search", type=str, help="Keywords to search on Facebook (public posts).")
    action_group.add_argument("--post-url", type=str, help="URL of a single Facebook post to get details.")

    args = parser.parse_args()

    print("Facebook OSINT Tool")
    print("Initializing browser... This might take a moment.")

    driver = get_browser_driver(remote_port=args.remote_port, chrome_profile_path=args.profile_path)

    if driver:
        print("Browser initialized successfully.")
        output_data = None
        try:
            if args.profile_url:
                print(f"--- Scraping Profile: {args.profile_url} ---")
                output_data = get_public_profile_data(driver, args.profile_url)

            elif args.search:
                print(f"--- Searching Facebook for: '{args.search}' ---")
                output_data = search_facebook(driver, args.search)

            elif args.post_url:
                print(f"--- Getting details for post: {args.post_url} ---")
                output_data = get_post_details(driver, args.post_url)

            if output_data:
                print("\n--- Results ---")
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
                print("--- End of Results ---")
            else:
                print("No data structure returned or the action produced no data.")

            print("\nScraping tasks attempted. Review console for details/TODOs.")
            input("Press Enter to close the browser and quit...")

        except Exception as e:
            print(f"An critical error occurred: {e}")
            traceback.print_exc()
        finally:
            print("Closing browser...")
            driver.quit()
            print("Browser closed.")
    else:
        print("Failed to initialize browser. Check Chrome setup. Exiting.")

if __name__ == "__main__":
    main()
