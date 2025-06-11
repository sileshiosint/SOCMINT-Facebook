# content_analyzer.py
import re
import warnings

# Predefined list of risky keywords (case-insensitive)
# This can be expanded or loaded from a configuration file in a future enhancement.
DEFAULT_RISKY_KEYWORDS = [
    # Example categories - customize heavily based on OSINT needs
    # Hate speech / Extremism related (examples only, use with caution and ethical consideration)
    "kill", "attack", "bomb", "genocide", "extremist", "radicalize",
    # Self-harm (examples only)
    "suicide", "self harm", "depressed a lot", "want to die",
    # Scams / Misinformation (examples only)
    "free money", "guaranteed profit", "miracle cure", "fake news", "hoax",
    # Weaponry / Violence (examples only)
    "buy gun", "illegal weapon", "explosive recipe"
]
# Normalize keywords to lowercase for case-insensitive matching
DEFAULT_RISKY_KEYWORDS = [keyword.lower() for keyword in DEFAULT_RISKY_KEYWORDS]


def extract_links(text_content: str):
    """
    Extracts all HTTP and HTTPS URLs from a given text.
    Args:
        text_content (str): The text to extract links from.
    Returns:
        list: A list of unique URLs found in the text. Returns empty list if no links or invalid input.
    """
    if not text_content or not isinstance(text_content, str):
        return []

    # Regex to find URLs (handles http, https, and common URL characters)
    # This regex is reasonably comprehensive but might not catch every edge case.
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    try:
        urls = re.findall(url_pattern, text_content)
        return list(set(urls)) # Return unique URLs
    except Exception as e:
        warnings.warn(f"Link extraction failed for text snippet '{text_content[:50]}...': {e}", UserWarning)
        return []

def score_risk(text_content: str, sentiment_obj: dict = None, risky_keywords: list = None):
    """
    Scores the risk of a given text based on keywords and sentiment.
    Args:
        text_content (str): The text to analyze.
        sentiment_obj (dict, optional): A sentiment dictionary (e.g., from VADER)
                                        containing a 'compound' score.
        risky_keywords (list, optional): A list of keywords to check for.
                                         Defaults to DEFAULT_RISKY_KEYWORDS.
    Returns:
        dict: A risk assessment dictionary: {'label': str, 'score': float, 'reasons': list}
              Returns None if input is invalid.
    """
    if not text_content or not isinstance(text_content, str):
        return None

    if risky_keywords is None:
        risky_keywords = DEFAULT_RISKY_KEYWORDS

    text_lower = text_content.lower()
    score = 0.0
    reasons = []

    # 1. Keyword-based scoring
    found_keywords = []
    for keyword in risky_keywords:
        if keyword in text_lower: # Basic substring check
            found_keywords.append(keyword)
            # More sophisticated weighting could be added here per keyword
            score += 0.2 # Increment score for each keyword category, cap later

    if found_keywords:
        reasons.append(f"Contains risky keywords: {', '.join(list(set(found_keywords)))}")

    # 2. Sentiment-based scoring (if sentiment_obj is provided)
    if sentiment_obj and isinstance(sentiment_obj, dict) and 'compound' in sentiment_obj:
        compound_score = sentiment_obj['compound']
        if compound_score < -0.5: # Strongly negative
            score += 0.3
            reasons.append(f"Strongly negative sentiment (compound: {compound_score:.2f})")
        elif compound_score < -0.05: # Negative
            score += 0.15
            reasons.append(f"Negative sentiment (compound: {compound_score:.2f})")

    # Normalize score (cap at 1.0 for simplicity)
    score = min(score, 1.0)

    # Determine label based on score
    label = "Low"
    if score >= 0.6: # Threshold for High risk
        label = "High"
    elif score >= 0.3: # Threshold for Medium risk
        label = "Medium"

    return {"label": label, "score": round(score, 2), "reasons": reasons}

if __name__ == '__main__':
    print("--- Testing content_analyzer.py ---")

    # Link Extraction Tests
    text_with_links = "Check out http://example.com and also https://www.google.com/search?q=test. This is a test."
    links = extract_links(text_with_links)
    print(f"Links in '{text_with_links}': {links}")

    text_no_links = "This text has no URLs."
    print(f"Links in '{text_no_links}': {extract_links(text_no_links)}")
    print(f"Links in empty text: {extract_links('')}")

    # Risk Scoring Tests
    text_safe = "This is a lovely day, the weather is nice."
    sentiment_safe = {"compound": 0.8} # Example sentiment
    risk_safe = score_risk(text_safe, sentiment_safe)
    print(f"Risk for '{text_safe}': {risk_safe}")

    text_risky_keywords = "We need to attack the system and buy illegal weapons."
    risk_keywords = score_risk(text_risky_keywords) # No sentiment
    print(f"Risk for '{text_risky_keywords}': {risk_keywords}")

    text_risky_sentiment = "I hate everything and everyone, it's all so pointless and awful."
    sentiment_risky = {"compound": -0.9}
    risk_sentiment = score_risk(text_risky_sentiment, sentiment_risky)
    print(f"Risk for '{text_risky_sentiment}': {risk_sentiment}")

    text_risky_both = "I will kill them all, this is such a terrible plan. Buy a bomb."
    sentiment_both = {"compound": -0.7}
    risk_both = score_risk(text_risky_both, sentiment_both)
    print(f"Risk for '{text_risky_both}': {risk_both}")

    # Test with custom keywords
    custom_keywords = ["urgent", "secret deal"]
    text_custom = "This is an urgent message about a secret deal."
    risk_custom = score_risk(text_custom, risky_keywords=custom_keywords)
    print(f"Risk for '{text_custom}' with custom keywords: {risk_custom}")
