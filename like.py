# like.py

import os, logging, sqlite3, tweepy, time
from dotenv import load_dotenv
from google import genai  # Only needed if you want to generate comments (not used here)

# ─── Load environment variables ─────────────────────────────────────────────────
load_dotenv()
TW_BEARER_TOKEN  = os.getenv("TWITTER_BEARER_TOKEN")
TW_API_KEY       = os.getenv("TWITTER_API_KEY")
TW_API_SECRET    = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN  = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ─── Basic logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def main():
    client = tweepy.Client(
        bearer_token=TW_BEARER_TOKEN,
        consumer_key=TW_API_KEY,
        consumer_secret=TW_API_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SECRET,
        wait_on_rate_limit=True
    )
    me = client.get_me()
    user_id = me.data['id'] if isinstance(me.data, dict) else me.data.id
    logging.info(f"like.py running for user {user_id}")

    query = "#python -is:retweet lang:en"
    try:
        search_resp = client.search_recent_tweets(query=query, max_results=3)
        tweets = search_resp.data or []
        for t in tweets:
            try:
                client.like(user_id, t.id)
                logging.info(f"Liked tweet {t.id}")
                time.sleep(2)
            except Exception as e:
                logging.error(f"Like error for {t.id}: {e}")
    except Exception as e:
        logging.error(f"Search error: {e}")

if __name__ == "__main__":
    main()
