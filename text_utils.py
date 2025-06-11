# text_utils.py
from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer # Import VADER

# --- Translation Function (from previous step) ---
def translate_text(text_to_translate: str, target_language: str = "en"):
    if not text_to_translate or not isinstance(text_to_translate, str):
        return text_to_translate
    try:
        translated_text = GoogleTranslator(target=target_language).translate(text_to_translate)
        if translated_text is None:
             print(f"Warning: Translation of '{text_to_translate[:50]}...' resulted in None. Returning original.")
             return text_to_translate
        return translated_text
    except Exception as e:
        print(f"Warning: Translation failed for '{text_to_translate[:50]}...': {e}")
        return text_to_translate

# --- Sentiment Analysis Function ---
def analyze_sentiment_vader(text_to_analyze: str):
    """
    Analyzes the sentiment of a given text using VADER.

    Args:
        text_to_analyze (str): The text to be analyzed.

    Returns:
        dict: A dictionary containing VADER sentiment scores
              (e.g., {'neg': 0.0, 'neu': 0.0, 'pos': 0.0, 'compound': 0.0})
              Returns None if input is invalid or analysis fails.
    """
    if not text_to_analyze or not isinstance(text_to_analyze, str):
        return None # Or return default neutral scores

    try:
        analyzer = SentimentIntensityAnalyzer()
        sentiment_scores = analyzer.polarity_scores(text_to_analyze)
        return sentiment_scores
    except Exception as e:
        print(f"Warning: Sentiment analysis failed for '{text_to_analyze[:50]}...': {e}")
        return None # Or return default neutral scores

if __name__ == '__main__':
    # --- Translation Examples (from previous step) ---
    text1 = "Hola, ¿cómo estás?"
    translated1_en = translate_text(text1, "en")
    print(f"Original ('{text1}') -> Translated to 'en': '{translated1_en}'")

    text2 = "Hello, how are you?"
    translated2_es = translate_text(text2, "es")
    print(f"Original ('{text2}') -> Translated to 'es': '{translated2_es}'")

    text3 = "これは日本語のテキストです。"
    translated3_en = translate_text(text3, "en")
    print(f"Original ('{text3}') -> Translated to 'en': '{translated3_en}'")

    # --- Sentiment Analysis Examples ---
    print("\n--- Sentiment Analysis Examples ---")
    sentiment_text_positive = "This is a wonderful and fantastic event! I am very happy."
    scores_pos = analyze_sentiment_vader(sentiment_text_positive)
    print(f"Sentiment for '{sentiment_text_positive}': {scores_pos}")

    sentiment_text_negative = "This is a terrible, awful, and boring experience. I hate it."
    scores_neg = analyze_sentiment_vader(sentiment_text_negative)
    print(f"Sentiment for '{sentiment_text_negative}': {scores_neg}")

    sentiment_text_neutral = "The book is on the table."
    scores_neu = analyze_sentiment_vader(sentiment_text_neutral)
    print(f"Sentiment for '{sentiment_text_neutral}': {scores_neu}")

    # Example of analyzing translated text
    if translated1_en and translated1_en != text1 : # Check if translation happened and was different
        scores_translated = analyze_sentiment_vader(translated1_en)
        print(f"Sentiment for translated text '{translated1_en}': {scores_translated}")

    empty_text_sentiment = analyze_sentiment_vader("")
    print(f"Sentiment for empty text: {empty_text_sentiment}")

    none_text_sentiment = analyze_sentiment_vader(None)
    print(f"Sentiment for None text: {none_text_sentiment}")
