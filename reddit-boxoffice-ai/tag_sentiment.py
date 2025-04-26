# tag_sentiment.py
import pandas as pd
from dotenv import load_dotenv
import os
from openai import OpenAI
import time

print("Loading .env and API key...")
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found in .env")
    exit()

client = OpenAI(api_key=api_key)
print("🔑 OpenAI client initialized.")

# Load scraped Reddit data
df_path = "data/reddit_comments_prerelease.csv"
if not os.path.exists(df_path):
    print(f"❌ Data file {df_path} not found.")
    exit()

df = pd.read_csv(df_path)
print(f"🧾 Loaded {len(df)} comments from {df_path}")

# Drop rows with missing content
df = df.dropna(subset=["title", "text"]).copy()
df["combined_text"] = df["title"].fillna("") + " " + df["text"].fillna("")
df = df[df["combined_text"].str.strip().astype(bool)]

print(f"🧹 {len(df)} rows remaining after cleaning")

if df.empty:
    print("⚠️ No usable comments to process.")
    exit()

# Define inline sentiment classification function using updated API
def classify_sentiment(text):
    prompt = f"""Classify the sentiment of this Reddit post as Positive, Neutral, or Negative. Only return the one word.\nPost: \"{text}\\""".strip()
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return "Error"

# Run sentiment tagging
sentiments = []
for i, row in df.iterrows():
    print(f"Tagging sentiment for row {i+1}/{len(df)}")
    sentiment = classify_sentiment(row["combined_text"][:2000])
    sentiments.append(sentiment)
    time.sleep(1)

df["sentiment"] = sentiments

# Save results
output_path = "data/reddit_sentiment.csv"
df.to_csv(output_path, index=False)
print(f"✅ Sentiment tagging complete. Saved to {output_path}")