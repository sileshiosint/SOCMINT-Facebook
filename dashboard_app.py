# dashboard_app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import json # For loading/saving last scrape data if needed, though not fully implemented here
import datetime

# Assuming other .py files (scraper_core, browser_handler, etc.) are in the same root directory
# or accessible via PYTHONPATH
import scraper_core
import browser_handler # Needed to get a driver
import report_generator # For generating reports
# text_utils and risk_analyzer are used by scraper_core

# --- Flask App Setup ---
app = Flask(__name__, template_folder='dashboard/templates', static_folder='dashboard/static')
# Ensure a secret key for session management, etc., if you use sessions
app.secret_key = os.urandom(24)

# --- Configuration ---
# Path for storing generated reports (ensure this directory exists or is created)
REPORTS_DIR = os.path.join(os.getcwd(), 'reports')
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

# Store the last driver instance globally for simplicity in this single-user local tool.
# Not suitable for production or multi-user. A proper browser management strategy would be needed.
# And ensure it's quit properly. For now, dashboard interactions will create/quit driver per request.
# This approach is simpler: one driver active while dashboard is used.
# driver_instance = None

def get_active_driver(remote_port_str=None, profile_path_str=None):
    # For this version, we'll get a new driver for each request to simplify state.
    # This is less efficient but more robust for a local tool if browser crashes.
    # User provides remote_port and profile_path via form or defaults are used.
    try:
        remote_port = int(remote_port_str) if remote_port_str else 9222
    except ValueError:
        remote_port = 9222 # Default if parsing fails

    print(f"Attempting to get browser driver (port: {remote_port}, profile: {profile_path_str})")
    driver = browser_handler.get_browser_driver(
        remote_port=remote_port,
        chrome_profile_path=profile_path_str
    )
    return driver

def close_driver(driver):
    if driver:
        try:
            print("Closing browser driver...")
            driver.quit()
        except Exception as e:
            print(f"Error closing driver: {e}")

# --- Routes ---
@app.route('/')
def index():
    return render_template('dashboard.html')

common_error_response = {
    "error": "Failed to initialize browser. Ensure Chrome is running with remote debugging or profile path is correct.",
    "captcha_detected": False, # Default
    "data": None,
    "report_generated": False,
    "report_url": None
}

@app.route('/scrape_profile')
def scrape_profile_route():
    global common_error_response
    url = request.args.get('url')
    analyze_sentiment = request.args.get('analyze_sentiment', 'false').lower() == 'true'
    translate_to = request.args.get('translate_to')
    # TODO: Get remote_port and profile_path from request.args if we add them to the form

    if not url:
        return jsonify({"error": "Profile URL is required.", "data": None}), 400

    driver = get_active_driver() # Using default port/profile for now from browser_handler
    if not driver:
        return jsonify(common_error_response), 500

    response_data = {"query": url}
    try:
        data = scraper_core.get_public_profile_data(driver, url, analyze_sentiment, translate_to)
        response_data["data"] = data

        # Generate report
        try:
            report_filename = report_generator.generate_report(data, "profile_report", url)
            response_data["report_generated"] = True
            response_data["report_url"] = f"/reports/{report_filename}"
        except Exception as e:
            print(f"Error generating report: {e}")
            response_data["report_generated"] = False
            response_data["report_error"] = str(e)

    except Exception as e:
        print(f"Error during profile scraping: {e}")
        response_data["error"] = str(e)
        if "CAPTCHA" in str(e) or (hasattr(e, 'msg') and "CAPTCHA" in e.msg): # Basic check
            response_data["captcha_detected"] = True
    finally:
        close_driver(driver)

    return jsonify(response_data)

@app.route('/scrape_search')
def scrape_search_route():
    global common_error_response
    keywords = request.args.get('keywords')
    analyze_sentiment = request.args.get('analyze_sentiment', 'false').lower() == 'true'
    translate_to = request.args.get('translate_to')

    if not keywords:
        return jsonify({"error": "Search keywords are required.", "data": None}), 400

    driver = get_active_driver()
    if not driver:
        return jsonify(common_error_response), 500

    response_data = {"query": keywords}
    try:
        data = scraper_core.search_facebook(driver, keywords, analyze_sentiment, translate_to)
        response_data["data"] = data
        try:
            report_filename = report_generator.generate_report(data, "search_report", keywords)
            response_data["report_generated"] = True
            response_data["report_url"] = f"/reports/{report_filename}"
        except Exception as e:
            print(f"Error generating report: {e}")
            response_data["report_generated"] = False
            response_data["report_error"] = str(e)

    except Exception as e:
        print(f"Error during search scraping: {e}")
        response_data["error"] = str(e)
        if "CAPTCHA" in str(e) or (hasattr(e, 'msg') and "CAPTCHA" in e.msg):
            response_data["captcha_detected"] = True
    finally:
        close_driver(driver)

    return jsonify(response_data)

@app.route('/scrape_post')
def scrape_post_route():
    global common_error_response
    post_url = request.args.get('url')
    analyze_sentiment = request.args.get('analyze_sentiment', 'false').lower() == 'true'
    translate_to = request.args.get('translate_to')

    if not post_url:
        return jsonify({"error": "Post URL is required.", "data": None}), 400

    driver = get_active_driver()
    if not driver:
        return jsonify(common_error_response), 500

    response_data = {"url": post_url} # Use 'url' to match JS expectation for context
    try:
        # This function should return the main_post dict inside the result
        data = scraper_core.get_post_details(driver, post_url, analyze_sentiment, translate_to)
        response_data["data"] = data
        try:
            report_filename = report_generator.generate_report(data, "post_detail_report", post_url)
            response_data["report_generated"] = True
            response_data["report_url"] = f"/reports/{report_filename}"
        except Exception as e:
            print(f"Error generating report: {e}")
            response_data["report_generated"] = False
            response_data["report_error"] = str(e)

    except Exception as e:
        print(f"Error during post detail scraping: {e}")
        response_data["error"] = str(e)
        if "CAPTCHA" in str(e) or (hasattr(e, 'msg') and "CAPTCHA" in e.msg):
            response_data["captcha_detected"] = True
    finally:
        close_driver(driver)

    return jsonify(response_data)

@app.route('/reports/<filename>')
def serve_report(filename):
    try:
        # Ensure filename is safe (e.g., not trying to access parent directories)
        if ".." in filename or filename.startswith("/"):
            return "Invalid filename", 400
        return send_from_directory(REPORTS_DIR, filename, as_attachment=False) # Serve as plain text/markdown
    except FileNotFoundError:
        return "Report not found.", 404

@app.route('/view_report') # This route might be better if report_viewer.html is a static page or served by index
def view_last_report_page():
    # This route is for the HTML page that might display a report.
    # The actual report content is served by /reports/<filename>
    # For now, we assume report_viewer.html is just a template that JS might populate,
    # or the link on dashboard.html directly points to /reports/<filename>.
    # The current JS points to /reports/<filename> directly.
    # If report_viewer.html needs to be served with specific context:
    # last_report_filename = request.args.get('file') # Or get from session/db
    # report_content = ""
    # if last_report_filename:
    #     try:
    #         with open(os.path.join(REPORTS_DIR, last_report_filename), 'r', encoding='utf-8') as f:
    #             report_content = f.read()
    #     except Exception:
    #         pass # Handle error
    # return render_template('report_viewer.html', report_content=report_content)
    # For now, this route is not strictly necessary if JS directly links to /reports/<filename>
    # and that link is opened in a new tab.
    # Let's make it serve the report_viewer.html template for consistency.
    return render_template('report_viewer.html', report_content="Select a report to view from the main dashboard, or the last generated report will be linked there.")


# --- Main Execution ---
if __name__ == '__main__':
    print(f"Dashboard server starting...")
    print(f"Reports will be saved in: {os.path.abspath(REPORTS_DIR)}")
    print(f"Open http://127.0.0.1:5000 in your web browser.")
    # Use threaded=False for simplicity with Selenium driver management if keeping one driver.
    # However, since we get a new driver per request, threaded=True is fine.
    app.run(debug=True, host='0.0.0.0', port=5000)
