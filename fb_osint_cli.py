# fb_osint_cli.py
import argparse
import json
import browser_handler
import scraper_engine
import report_writer # Import the new report writer
import traceback

def main():
    parser = argparse.ArgumentParser(
        description="Facebook OSINT CLI Tool - Phase 1",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example: python fb_osint_cli.py --profile-url <URL> --output-report my_profile_osint.md" # Updated epilog
    )
    # ... (browser arguments and action_group remain the same) ...
    parser.add_argument("--remote-port", type=int, default=9222, help="Port for Chrome remote debugging.")
    parser.add_argument("--profile-path", type=str, default=None, help="Path to Chrome user data directory.")

    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--profile-url", type=str, help="URL of the Facebook profile to scrape.")
    action_group.add_argument("--search", type=str, help="Keywords to search on Facebook (public posts).")
    action_group.add_argument("--post-url", type=str, help="URL of a single Facebook post to get details.")

    parser.add_argument("--analyze-sentiment", action="store_true", help="Enable sentiment analysis.")
    parser.add_argument("--translate-to", metavar='LANG_CODE', type=str, default=None, help="Translate extracted text.")

    # New argument for report output
    parser.add_argument("--output-report", metavar='FILENAME.md', type=str, default=None,
                        help="Save a Markdown report to the specified filename (e.g., report.md). If not specified, a default named report is generated.")

    args = parser.parse_args()
    print("Facebook OSINT CLI - Initializing...")

    driver = None
    report_type_for_generation = None
    query_for_report = None

    try:
        # ... (driver initialization - same as before) ...
        driver = browser_handler.get_browser_driver(remote_port=args.remote_port, chrome_profile_path=args.profile_path)
        if not driver: print("Failed to initialize browser driver. Exiting."); return

        scraped_data = None

        if args.profile_url:
            report_type_for_generation = "profile"
            query_for_report = args.profile_url
            print(f"Starting to scrape profile: {args.profile_url}")
            scraped_data = scraper_engine.scrape_profile_data(driver, args.profile_url, args.analyze_sentiment, args.translate_to)
        elif args.search:
            report_type_for_generation = "search"
            query_for_report = args.search
            print(f"Starting search for: "{args.search}"")
            scraped_data = scraper_engine.search_public_posts(driver, args.search, args.analyze_sentiment, args.translate_to)
        elif args.post_url:
            report_type_for_generation = "post_details"
            query_for_report = args.post_url
            print(f"Starting to get details for post: {args.post_url}")
            scraped_data = scraper_engine.get_post_details(driver, args.post_url, args.analyze_sentiment, args.translate_to)

        if scraped_data:
            print("\n--- SCRAPED DATA ---")
            print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
            print("--- END OF DATA ---")

            # Generate report
            print("\nGenerating report...")
            report_file_path = report_writer.generate_markdown_report(
                scraped_data,
                report_type_for_generation,
                query_for_report,
                custom_filename=args.output_report # Pass custom filename if provided
            )
            if report_file_path:
                print(f"Markdown report saved to: {report_file_path}")
            else:
                print("Failed to generate report.")
        else:
            print("No data was returned from the scraping function, report not generated.")

    except Exception as e:
        # ... (error handling - same as before) ...
        print(f"An error occurred: {e}"); traceback.print_exc()
    finally:
        # ... (driver quit - same as before) ...
        if driver:
            print("Closing browser driver...")
            driver.quit()
            print("Browser driver closed.")
        print("CLI Tool execution finished.")

if __name__ == "__main__":
    main()
