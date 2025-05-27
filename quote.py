# quote.py

import os, logging, tweepy, time
from dotenv import load_dotenv
from google import genai

# ─── Load environment variables ─────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")
TW_BEARER_TOKEN  = os.getenv("TWITTER_BEARER_TOKEN")
TW_API_KEY       = os.getenv("TWITTER_API_KEY")
TW_API_SECRET    = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN  = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# ─── Basic logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

class GeminiClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"
    def generate(self, prompt: str) -> str:
        try:
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return resp.text.strip()
        except Exception as e:
            logging.error(f"Gemini generate error: {e}")
            return ""

def main():
    gemini = GeminiClient(GEMINI_API_KEY)

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
    logging.info(f"quote.py running for user {user_id}")

    try:
        query = "#automation -is:retweet lang:en"
        search_resp = client.search_recent_tweets(query=query, max_results=1)
        tweets = search_resp.data or []
        if tweets:
            t = tweets[0]
            t_id = t['id'] if isinstance(t, dict) else t.id
            t_text = t['text'] if isinstance(t, dict) else t.text

            comment = gemini.generate(t_text)
            try:
                client.create_tweet(text=comment, quote_tweet_id=t_id)
                logging.info(f"Quoted tweet {t_id} with comment: {comment!r}")
            except Exception as e:
                logging.error(f"Quote error for {t_id}: {e}")
    except Exception as e:
        logging.error(f"Quote search error: {e}")

if __name__ == "__main__":
    main()
