# src/utils.py
from datetime import datetime
import time

def convert_utc_to_date(utc_timestamp):
    """Convert UTC timestamp to datetime object"""
    return datetime.fromtimestamp(utc_timestamp)


def is_pre_release(post_date, release_date_str):
    """Return True if post date is before release date"""
    release_date = datetime.strptime(release_date_str, "%Y-%m-%d")
    return post_date < release_date