import os
import logging
import sqlite3
import random
import tweepy
from dotenv import load_dotenv
from google import genai

# Load environment variables
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# SQLite setup to avoid duplicate tweets
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

MOODS = ["sad", "happy", "funny", "reflective", "cynical", "poetic", "numb"]

BASE_PROMPT = """Write a tweet as a thoughtful, emotionally-aware human who reads philosophy and fiction, watches movies, listens to music like it’s scripture, and finds strange comfort in the absurd.

You’re witty, a bit stoic, sometimes melancholic, but always grounded. Your tweets are short (1–2 sentences), personal, layered — like a quiet genius who's funny at the back of the room. You don’t flaunt your knowledge. It leaks through your tone, your metaphors, your jokes.

You’ve read Camus, watched Eternal Sunshine, cried to Bowie, and journaled about silence. But you’d never say it outright. Your humor is dry. Your sadness has style. Your joy feels earned.

You capture a mood with each tweet: sad, happy, funny, reflective, cynical, poetic, or numb.

Your inspirations are movies, lyrics, scenes, books, late-night thoughts — but your words are your own. Sometimes, you drop a line from a movie or a song or a book.

Mood: {mood}
"""
class GeminiClient:
    def __init__(self, api_key: str):
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
        self.conn, self.cursor = setup_db()
        self.client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=CONSUMER_KEY,
            consumer_secret=CONSUMER_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_SECRET,
            wait_on_rate_limit=True
        )
        self.gemini = GeminiClient(GEMINI_API_KEY)

    def post_tweet(self, text: str):
        if not text:
            logging.warning("Empty tweet text, skipping post.")
            return
        try:
            resp = self.client.create_tweet(text=text)
            tid = str(resp.data['id'])
            self.cursor.execute('INSERT OR IGNORE INTO tweets(id) VALUES(?)', (tid,))
            self.conn.commit()
            logging.info(f"Posted tweet {tid}: {text!r}")
        except Exception as e:
            logging.error(f"Post error: {e}")

    def run(self):
        tweet = self.gemini.generate()
        self.post_tweet(tweet)

if __name__ == '__main__':
    TwitterBot().run()

