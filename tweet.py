import time
import sqlite3
import logging
import tweepy
import random
from schedule import every, run_pending
from dotenv import load_dotenv
import os
from google import genai

# ──────── Load environment variables ──────────────────────────────────────────
load_dotenv()

GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY")
BEARER_TOKEN      = os.getenv("TWITTER_BEARER_TOKEN")
CONSUMER_KEY      = os.getenv("TWITTER_API_KEY")
CONSUMER_SECRET   = os.getenv("TWITTER_API_SECRET")
ACCESS_TOKEN      = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_SECRET     = os.getenv("TWITTER_ACCESS_SECRET")

missing = [name for name, val in [
    ("GEMINI_API_KEY", GEMINI_API_KEY),
    ("TWITTER_BEARER_TOKEN", BEARER_TOKEN),
    ("TWITTER_API_KEY", CONSUMER_KEY),
    ("TWITTER_API_SECRET", CONSUMER_SECRET),
    ("TWITTER_ACCESS_TOKEN", ACCESS_TOKEN),
    ("TWITTER_ACCESS_SECRET", ACCESS_SECRET),
] if not val]
if missing:
    raise RuntimeError(f"Missing environment variables: {missing}")

# ──────── Logging setup ────────────────────────────────────────────────────────
def setup_logging():
    logging.basicConfig(
        filename='twitter_bot.log',
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

# ──────── Database setup ───────────────────────────────────────────────────────
def setup_db():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tweets (
            id TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    return conn, cursor

# ──────── Gemini prompt ────────────────────────────────────────────────────────
MOODS = ["sad", "happy", "funny", "reflective", "cynical", "poetic", "numb"]

BASE_PROMPT = """Write a tweet as a thoughtful, emotionally-aware human who reads philosophy and fiction...

Mood: {mood}
"""

class GeminiClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("Gemini API key is missing.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self, prompt: str = None) -> str:
        if prompt is None:
            mood = random.choice(MOODS)
            prompt_payload = BASE_PROMPT.format(mood=mood)
        else:
            prompt_payload = prompt
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_payload
            )
            return response.text.strip()
        except Exception as e:
            logging.error(f"Gemini generate error: {e}")
            return ""

class TwitterBot:
    def __init__(self):
        setup_logging()
        self.conn, self.cursor = setup_db()

        self.client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET,
            wait_on_rate_limit=True
        )

        me = self.client.get_me()
        self.user_id = me.data['id'] if isinstance(me.data, dict) else me.data.id

        self.gemini = GeminiClient(GEMINI_API_KEY)
        logging.info(f"Bot initialized for user ID {self.user_id}")

    def post_tweet(self, text: str):
        if not text:
            logging.warning("Empty tweet text, skipping post.")
            return None
        try:
            resp = self.client.create_tweet(text=text)
            tid = str(resp.data['id'])
            logging.info(f"Posted tweet {tid}: {text!r}")
            self.cursor.execute('INSERT OR IGNORE INTO tweets(id) VALUES(?)', (tid,))
            self.conn.commit()
            return tid
        except Exception as e:
            logging.error(f"Post error: {e}")
            return None

    def run(self):
        first_tweet = self.gemini.generate()
        self.post_tweet(first_tweet)

        every(60).minutes.do(lambda: self.post_tweet(self.gemini.generate()))

        logging.info("Starting scheduled tasks. Press Ctrl+C to exit.")
        while True:
            run_pending()
            time.sleep(5)

if __name__ == '__main__':
    TwitterBot().run()
