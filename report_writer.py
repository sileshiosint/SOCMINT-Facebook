# report_writer.py
import os
import datetime
import json # For pretty printing parts of the data if needed, or fallback
import warnings

REPORTS_DIR = "reports"

def ensure_reports_dir():
    """Ensures the reports directory exists."""
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)

def generate_markdown_report(data: dict, report_type: str, query: str, custom_filename: str = None):
    """
    Generates a Markdown report from the scraped data and saves it to a file.

    Args:
        data (dict): The scraped data from scraper_engine.
        report_type (str): Type of report ("profile", "search", "post_details").
        query (str): The original query (URL or keywords).
        custom_filename (str, optional): A custom filename (without path).
                                         If None, a default name is generated.

    Returns:
        str: The full path to the saved report file, or None if error.
    """
    ensure_reports_dir()

    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")

    if custom_filename:
        if not custom_filename.lower().endswith(".md"):
            filename = f"{custom_filename}_{timestamp_str}.md" # Add timestamp to custom name for uniqueness
        else:
            # Insert timestamp before extension if custom_filename already has .md
            base, ext = os.path.splitext(custom_filename)
            filename = f"{base}_{timestamp_str}{ext}"
    else:
        filename = f"{report_type}_report_{timestamp_str}.md"

    filepath = os.path.join(REPORTS_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Facebook OSINT Report: {report_type.replace('_', ' ').title()}\n\n")
            f.write(f"**Query:** `{query}`\n")
            f.write(f"**Report Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\n---\n\n")

            if report_type == "profile" and data:
                f.write(f"## Profile Information\n")
                f.write(f"- **Name:** {data.get('name', 'N/A')}\n")
                f.write(f"- **URL:** {data.get('url', 'N/A')}\n\n")
                f.write(f"### Posts ({len(data.get('posts', []))})\n\n")
                for i, post in enumerate(data.get('posts', [])):
                    f.write(f"**Post {i+1}**\n")
                    if post.get('url'): f.write(f"- **Link:** [{post.get('timestamp_text', 'Link')}]({post.get('url')})\n")
                    else: f.write(f"- **Timestamp:** {post.get('timestamp_text', 'N/A')}\n")
                    f.write(f"    ```text\n    {post.get('content', 'No content')}\n    ```\n")
                    _write_analysis_section(f, post)
                    f.write("\n")

            elif report_type == "search" and data:
                f.write(f"## Search Results for: "{data.get('query', '')}"\n")
                f.write(f"Total discussions found: {len(data.get('discussions', []))}\n\n")
                for i, item in enumerate(data.get('discussions', [])):
                    f.write(f"**Result {i+1}**\n")
                    f.write(f"- **Author:** [{item.get('author_name', 'N/A')}]({item.get('author_url', '#')})\n")
                    if item.get('url'): f.write(f"- **Link:** [{item.get('timestamp_text', 'Link')}]({item.get('url')})\n")
                    else: f.write(f"- **Timestamp:** {item.get('timestamp_text', 'N/A')}\n")
                    if item.get('source_group_or_page'): f.write(f"- **Source:** [{item.get('source_group_or_page')}]({item.get('source_group_or_page')})\n")
                    f.write(f"    ```text\n    {item.get('content', 'No content')}\n    ```\n")
                    _write_analysis_section(f, item)
                    f.write("\n")

            elif report_type == "post_details" and data:
                main_post = data.get('main_post', {})
                f.write(f"## Post Details: {data.get('url', 'N/A')}\n\n")
                f.write(f"### Main Post\n")
                f.write(f"- **Author:** [{main_post.get('author_name', 'N/A')}]({main_post.get('author_url', '#')})\n")
                f.write(f"- **Timestamp:** {main_post.get('timestamp_text', 'N/A')}\n")
                f.write(f"    ```text\n    {main_post.get('content', 'No content')}\n    ```\n")
                _write_analysis_section(f, main_post)
                f.write("\n")

                reactions = data.get('reactions', {})
                f.write(f"### Reactions\n")
                f.write(f"- **Summary:** {reactions.get('summary_text', 'N/A')}\n")
                # TODO: Add detailed reaction types if available
                f.write("\n")

                f.write(f"### Comments ({len(data.get('comments', []))})\n\n")
                for i, comment in enumerate(data.get('comments', [])):
                    f.write(f"**Comment {i+1}**\n")
                    f.write(f"- **Author:** [{comment.get('author_name', 'N/A')}]({comment.get('author_url', '#')})\n")
                    f.write(f"- **Timestamp:** {comment.get('timestamp_text', 'N/A')}\n")
                    f.write(f"    ```text\n    {comment.get('content', 'No content')}\n    ```\n")
                    _write_analysis_section(f, comment)
                    f.write("\n")

            else:
                f.write("No data or unknown report type.\n")
                f.write("```json\n")
                f.write(json.dumps(data, indent=2, ensure_ascii=False))
                f.write("\n```\n")

        print(f"Report generated: {filepath}")
        return filepath
    except Exception as e:
        warnings.warn(f"Failed to generate report '{filename}': {e}", UserWarning)
        return None

def _write_analysis_section(file_writer, item_dict):
    """Helper to write common analysis sections (translation, sentiment, risk, links) to the report."""
    if item_dict.get('translation'):
        trans = item_dict['translation']
        file_writer.write(f"- **Translation ({trans.get('lang', '')}):**\n")
        file_writer.write(f"    ```text\n    Original: {trans.get('original', '')[:100]}...\n    Translated: {trans.get('translated', '')}\n    ```\n")

    if item_dict.get('sentiment'):
        sent = item_dict['sentiment']
        label = "Neutral"
        if sent['compound'] > 0.05: label = "Positive"
        elif sent['compound'] < -0.05: label = "Negative"
        file_writer.write(f"- **Sentiment:** {label} (Compound: {sent['compound']:.2f}, Pos: {sent['pos']:.2f}, Neu: {sent['neu']:.2f}, Neg: {sent['neg']:.2f})\n")

    if item_dict.get('risk_assessment'):
        risk = item_dict['risk_assessment']
        file_writer.write(f"- **Risk Assessment:** {risk.get('label', 'N/A')} (Score: {risk.get('score', 0):.2f})\n")
        if risk.get('reasons'):
            file_writer.write(f"  - Reasons: {', '.join(risk.get('reasons', []))}\n")

    if item_dict.get('links'):
        links = item_dict['links']
        if links:
            file_writer.write("- **Extracted Links:**\n")
            for link_url in links:
                file_writer.write(f"  - [{link_url}]({link_url})\n")

if __name__ == '__main__':
    print("--- Testing report_writer.py ---")
    ensure_reports_dir()
    # Dummy data for testing
    test_profile_data = {
        "name": "Test User", "url": "http://facebook.com/testuser",
        "posts": [
            {"content": "This is a great post! #positive", "timestamp_text": "2 hours ago", "url": "http://facebook.com/testuser/posts/1",
             "sentiment": {"compound": 0.8, "pos": 0.7, "neu": 0.3, "neg": 0.0},
             "risk_assessment": {"label": "Low", "score": 0.1, "reasons": []},
             "links": ["http://example.com/great"]},
            {"content": "Feeling sad and I will attack.", "timestamp_text": "1 day ago", "url": "http://facebook.com/testuser/posts/2",
             "sentiment": {"compound": -0.7, "pos": 0.1, "neu": 0.2, "neg": 0.7},
             "risk_assessment": {"label": "High", "score": 0.7, "reasons": ["Contains risky keywords: attack", "Negative sentiment"]},
             "translation": {"original": "Original sad text", "translated": "Translated sad text", "lang": "en"},
             "links": []}
        ]
    }
    report_path = generate_markdown_report(test_profile_data, "profile", "http://facebook.com/testuser", custom_filename="MyTestProfileReport.md")
    if report_path: print(f"Test profile report generated at {report_path}")

    test_search_data = {
        "query": "test query",
        "discussions": [
            {"author_name": "Author1", "author_url": "#auth1", "content": "Search result 1 content with http://link1.com",
             "timestamp_text": "yesterday", "url": "#item1",
             "sentiment": {"compound": 0.0, "pos": 0.1, "neu": 0.8, "neg": 0.1},
             "risk_assessment": {"label": "Low", "score": 0.0}, "links": ["http://link1.com"]}
        ]
    }
    report_path_search = generate_markdown_report(test_search_data, "search", "test query")
    if report_path_search: print(f"Test search report generated at {report_path_search}")
