
# main.py
import os
import pandas as pd
from src.scraper import scrape_reddit_posts
from src.utils import is_pre_release

release_dates = {
    "dune2": "2024-03-01",
    "venom2": "2021-10-01",
    "thewildrobot": "2024-09-20",
    "gladiator": "2000-05-05",
    "backtoblack": "2024-04-12"
}

search_terms_map = {
    "dune2": ["dune 2", "dune part two", "dune sequel"],
    "venom2": ["venom 2", "venom sequel", "carnage"],
    "thewildrobot": ["the wild robot movie"],
    "gladiator": ["gladiator", "gladiator movie", "gladiator 2000"],
    "backtoblack": ["back to black", "amy winehouse movie"]
}

all_data = []

for movie, terms in search_terms_map.items():
    print(f"🎬 Scraping Reddit for {movie}...")
    df = scrape_reddit_posts(movie, terms, max_posts=50)
    if df.empty:
        print(f"⚠️ No data for {movie}")
        continue

    df["pre_release"] = df["post_date"].apply(lambda d: is_pre_release(d, release_dates[movie]))
    all_data.append(df)

# Save all scraped data
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv("data/reddit_comments_raw.csv", index=False)
    pre_release_df = combined_df[combined_df["pre_release"] == True]
    pre_release_df.to_csv("data/reddit_comments_prerelease.csv", index=False)
    print(f"✅ Saved {len(pre_release_df)} pre-release posts across {len(pre_release_df['movie'].unique())} movies.")
else:
    print("❌ No Reddit data collected.")

