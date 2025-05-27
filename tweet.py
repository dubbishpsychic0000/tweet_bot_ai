# tweet.py

import os, sqlite3, logging, tweepy, random
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

# ─── Database setup (same as before) ────────────────────────────────────────────
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

# ─── GeminiClient (uses google-genai) ────────────────────────────────────────────
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
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self) -> str:
        mood = random.choice(MOODS)
        prompt_payload = BASE_PROMPT.format(mood=mood)
        try:
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt_payload
            )
            return resp.text.strip()
        except Exception as e:
            logging.error(f"Gemini generate error: {e}")
            return ""

def main():
    conn, cursor = setup_db()
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
    logging.info(f"tweet.py running for user {user_id}")

    text = gemini.generate()
    if not text:
        logging.warning("Empty tweet, skipping.")
        return

    try:
        resp = client.create_tweet(text=text)
        tid = str(resp.data['id'])
        logging.info(f"Posted tweet {tid}: {text!r}")
        cursor.execute("INSERT OR IGNORE INTO tweets(id) VALUES(?)", (tid,))
        conn.commit()
    except Exception as e:
        logging.error(f"Post error: {e}")

if __name__ == "__main__":
    main()
