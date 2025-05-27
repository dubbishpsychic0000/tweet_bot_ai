# tweet_from_gemini.py

import os, logging
import tweepy
from google import genai
from dotenv import load_dotenv

# ─── Load environment variables ─────────────────────────────────────────────────
load_dotenv()
TW_BEARER_TOKEN  = os.getenv("TWITTER_BEARER_TOKEN")
TW_API_KEY       = os.getenv("TWITTER_API_KEY")
TW_API_SECRET    = os.getenv("TWITTER_API_SECRET")
TW_ACCESS_TOKEN  = os.getenv("TWITTER_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY")

# ─── Logging ─────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ─── Setup Gemini ────────────────────────────────────────────────────────────────
def generate_tweet():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

    prompt = "Generate a short, witty, and engaging tweet about Python programming."
    logging.info("Sending prompt to Gemini...")
    try:
        response = model.generate_content(prompt)
        tweet = response.text.strip()
        if len(tweet) > 280:
            tweet = tweet[:277] + "..."
        logging.info(f"Generated tweet: {tweet}")
        return tweet
    except Exception as e:
        logging.error(f"Error generating tweet with Gemini: {e}")
        return None

# ─── Tweet Posting Function ──────────────────────────────────────────────────────
def post_tweet(tweet):
    try:
        client = tweepy.Client(
            bearer_token=TW_BEARER_TOKEN,
            consumer_key=TW_API_KEY,
            consumer_secret=TW_API_SECRET,
            access_token=TW_ACCESS_TOKEN,
            access_token_secret=TW_ACCESS_SECRET
        )
        client.create_tweet(text=tweet)
        logging.info("Tweet posted successfully!")
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")

# ─── Main ────────────────────────────────────────────────────────────────────────
def main():
    tweet = generate_tweet()
    if tweet:
        post_tweet(tweet)

if __name__ == "__main__":
    main()
