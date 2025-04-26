# src/reddit_scraper.py
import praw
import pandas as pd
from src.utils import convert_utc_to_date

def init_reddit():
    return praw.Reddit(
        client_id="DR8BeUQWlNnrHvtpu6ETiw",
        client_secret="kNI-2_5HPOzdJ_Yc7CDeW9tEzjbCiA",
        user_agent="boxoffice-comment-scraper by /u/West_Definition6659"
    )

def scrape_reddit_posts(movie, search_terms, max_posts=100):
    reddit = init_reddit()
    subreddit = reddit.subreddit("movies")
    
    all_data = []
    for term in search_terms:
        print(f"🔍 Searching Reddit for: '{term}'")
        posts = subreddit.search(term, sort="new", time_filter="all", limit=max_posts)
        
        for post in posts:
            post_date = convert_utc_to_date(post.created_utc)
            all_data.append({
                "movie": movie,
                "search_term": term,
                "post_id": post.id,
                "title": post.title,
                "text": post.selftext,
                "upvotes": post.score,
                "comments_count": post.num_comments,
                "created_utc": post.created_utc,
                "post_date": post_date
            })

    return pd.DataFrame(all_data)