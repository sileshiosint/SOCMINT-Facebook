# text_analyzer.py
from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import warnings

def translate_text(text_to_translate: str, target_language: str = "en"):
    """
    Translates a given text to the target language using GoogleTranslator.
    Args:
        text_to_translate (str): The text to be translated.
        target_language (str): The target language code (e.g., "en", "es", "fr").
    Returns:
        str: The translated text, or the original text if translation fails or input is invalid.
    """
    if not text_to_translate or not isinstance(text_to_translate, str) or not text_to_translate.strip():
        return text_to_translate

    try:
        # Auto-detects source language
        translated_text = GoogleTranslator(target=target_language).translate(text_to_translate)
        if translated_text is None: # Should not happen often with GoogleTranslator but good practice
            warnings.warn(f"Translation of '{text_to_translate[:50]}...' to '{target_language}' resulted in None. Returning original.", UserWarning)
            return text_to_translate
        return translated_text
    except Exception as e:
        warnings.warn(f"Translation failed for '{text_to_translate[:50]}...' to '{target_language}': {e}. Returning original.", UserWarning)
        return text_to_translate

def analyze_sentiment(text_to_analyze: str):
    """
    Analyzes the sentiment of a given text using VADER.
    Args:
        text_to_analyze (str): The text to be analyzed.
    Returns:
        dict: VADER sentiment scores (neg, neu, pos, compound), or None if input invalid/analysis fails.
    """
    if not text_to_analyze or not isinstance(text_to_analyze, str) or not text_to_analyze.strip():
        return None

    try:
        analyzer = SentimentIntensityAnalyzer()
        sentiment_scores = analyzer.polarity_scores(text_to_analyze)
        return sentiment_scores
    except Exception as e:
        warnings.warn(f"Sentiment analysis failed for '{text_to_analyze[:50]}...': {e}", UserWarning)
        return None

if __name__ == '__main__':
    print("--- Testing text_analyzer.py ---")

    # Translation Tests
    spanish_text = "Hola Mundo, este es un texto de prueba."
    english_translation = translate_text(spanish_text, "en")
    print(f"Original (es): '{spanish_text}'")
    print(f"Translated (en): '{english_translation}'")

    english_text = "This is a test sentence."
    french_translation = translate_text(english_text, "fr")
    print(f"Original (en): '{english_text}'")
    print(f"Translated (fr): '{french_translation}'")

    no_translation_needed = translate_text("Hello", "en")
    print(f"No translation needed: '{no_translation_needed}'")

    empty_translate = translate_text("", "es")
    print(f"Empty text translation: '{empty_translate}' (should be empty)")

    # Sentiment Tests
    positive_text = "This is a wonderfully fantastic and joyous occasion!"
    positive_sentiment = analyze_sentiment(positive_text)
    print(f"Sentiment for '{positive_text}': {positive_sentiment}")

    negative_text = "This is a terribly awful and sad situation."
    negative_sentiment = analyze_sentiment(negative_text)
    print(f"Sentiment for '{negative_text}': {negative_sentiment}")

    neutral_text = "The sky is blue and the grass is green."
    neutral_sentiment = analyze_sentiment(neutral_text)
    print(f"Sentiment for '{neutral_text}': {neutral_sentiment}")

    # Test with translated text
    if english_translation and english_translation != spanish_text:
        sentiment_on_translated = analyze_sentiment(english_translation)
        print(f"Sentiment for translated text '{english_translation}': {sentiment_on_translated}")

    empty_sentiment = analyze_sentiment("   ")
    print(f"Empty text sentiment: {empty_sentiment} (should be None or neutral if VADER processes spaces)")
