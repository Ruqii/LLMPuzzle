# src/sentiment_tagger.py
import openai
import time

def init_openai(api_key):
    openai.api_key = api_key

def classify_sentiment(text):
    prompt = f"""Classify the sentiment of this Reddit post as Positive, Neutral, or Negative. Only return the one word.
Post: \"{text}\\""".strip()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ Error: {e}")
        return "Error"

def classify_batch(df, text_column="combined_text", delay=1):
    results = []
    for i, text in enumerate(df[text_column]):
        print(f"Tagging sentiment for row {i+1}/{len(df)}")
        sentiment = classify_sentiment(text[:2000])  # Token-safe
        results.append(sentiment)
        time.sleep(delay)  # rate limit safety
    return results
